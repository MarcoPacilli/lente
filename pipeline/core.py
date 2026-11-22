"""Raccolta RSS/Atom, provenienza, selezione e pubblicazione atomica."""
from __future__ import annotations
import collections, concurrent.futures, datetime as dt, email.utils, hashlib
import html, json, os, re, tempfile, unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib import request, parse, error
import xml.etree.ElementTree as ET

UTC = dt.timezone.utc
MAX_BYTES = 2_000_000
CATEGORIES = ['Geopolitica','Economia','Tecnologia','Scienza','Ambiente','Italia','Società']
REGIONS = ['Europa','Africa','Asia','Medio Oriente','Americhe','Oceania','Globale','Non determinata']
KINDS = ['fatto riportato','dichiarazione','interpretazione','incerto']

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden += 1
        if tag in ('p','br','div','li'): self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
        if tag in ('p','div','li'): self.parts.append(' ')
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)

def clean(value):
    p=Text(); p.feed(value or '')
    return re.sub(r'\s+', ' ', html.unescape(' '.join(p.parts))).strip()

def iso(t): return t.astimezone(UTC).isoformat(timespec='seconds').replace('+00:00','Z')
def date(value):
    if not value: return None
    try:
        try: t=dt.datetime.fromisoformat(value.strip().replace('Z','+00:00'))
        except ValueError: t=email.utils.parsedate_to_datetime(value)
        if t.tzinfo is None: return None # non inventare il fuso orario
        return t.astimezone(UTC)
    except (TypeError, ValueError, OverflowError): return None

def digest(text): return hashlib.sha256(text.encode()).hexdigest()[:24]
def canonical(url):
    p=parse.urlsplit(url)
    if p.scheme not in ('https','http') or not p.hostname or p.username or p.password: raise ValueError('URL non HTTP valido')
    if p.port not in (None,80,443): raise ValueError('Porta non consentita')
    q=[(k,v) for k,v in parse.parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')]
    return parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',parse.urlencode(q),''))

def allowed_url(url, hosts):
    u=canonical(url)
    if parse.urlsplit(u).scheme!='https' or parse.urlsplit(u).hostname not in hosts: raise ValueError('Dominio articolo non autorizzato')
    return u

class RestrictedRedirect(request.HTTPRedirectHandler):
    def __init__(self, hosts): self.hosts=hosts
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl,self.hosts)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url, hosts, headers=None, timeout=18):
    allowed_url(url,hosts)
    opener=request.build_opener(RestrictedRedirect(hosts))
    req=request.Request(url,headers={'User-Agent':'Lente/0.2 (personal RSS reader; daily fetch)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml',**(headers or {})})
    with opener.open(req,timeout=timeout) as r:
        data=r.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES: raise ValueError('Feed oltre 2 MB')
        return data, dict(r.headers)

def atomic_json(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.lente-',suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:
            json.dump(value,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_json(path, default):
    try: return json.loads(Path(path).read_text())
    except (OSError, ValueError): return default

def local(tag): return tag.rsplit('}',1)[-1]
def field(node, *names):
    for name in names:
        for child in node:
            if local(child.tag)==name and child.text: return child.text
    return ''

def parse_feed(raw, source, now, window_hours):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper(): raise ValueError('DTD/entità XML non consentite')
    root=ET.fromstring(raw)
    if local(root.tag) not in ('rss','feed','RDF'): raise ValueError('Documento non RSS/Atom')
    rows=[]; rejected=collections.Counter()
    for node in root.iter():
        if local(node.tag) not in ('item','entry'): continue
        title=clean(field(node,'title'))
        description=clean(field(node,'description','summary'))[:480]
        # Mai content:encoded né articolo completo: solo metadati pubblicati nel feed.
        link=field(node,'link')
        if local(node.tag)=='entry':
            link=next((c.attrib.get('href','') for c in node if local(c.tag)=='link' and c.attrib.get('rel','alternate')=='alternate'),link)
        published=date(field(node,'pubDate','published','date'))
        if not title or not published:
            rejected['missing_title_or_date']+=1; continue
        if published>now+dt.timedelta(minutes=15): rejected['future_date']+=1; continue
        if published<now-dt.timedelta(hours=window_hours): rejected['expired']+=1; continue
        try: link=allowed_url(link,source['article_hosts'])
        except (ValueError,TypeError): rejected['unsafe_url']+=1; continue
        author=clean(field(node,'creator','author'))
        for child in node:
            if local(child.tag)=='author' and not author: author=clean(field(child,'name'))
        if source.get('requires_author') and not author:
            rejected['missing_author']+=1; continue
        tags=[clean(c.text) for c in node if local(c.tag)=='category' and c.text]
        rows.append({'id':digest(link),'url':link,'title':title[:260],'description':description,
                     'published_at':iso(published),'language':source['language'],'publisher':source['name'],
                     'group':source['group'],'author':author,'source_id':source['id'],
                     'license':source.get('license',''),'terms':source['terms'],
                     'ai_allowed':source.get('ai_allowed',False),'tags':tags})
    return rows, dict(rejected)

def collect(sources, now, window_hours, cache_dir, transport=fetch):
    def one(source):
        path=Path(cache_dir)/(source['id']+'.json'); cached=load_json(path,{})
        headers={k:v for k,v in {'If-None-Match':cached.get('etag'),'If-Modified-Since':cached.get('last_modified')}.items() if v}
        status={'id':source['id'],'name':source['name'],'language':source['language'],'feed':source['feed'],'status':'ok'}
        try:
            try:
                raw,h=transport(source['feed'],source['feed_hosts'],headers)
                rows,rejected=parse_feed(raw,source,now,window_hours)
                atomic_json(path,{'etag':h.get('ETag'),'last_modified':h.get('Last-Modified'),'items':rows})
            except error.HTTPError as e:
                if e.code!=304 or 'items' not in cached: raise
                rows=[r for r in cached['items'] if now-dt.timedelta(hours=window_hours)<=date(r['published_at'])<=now+dt.timedelta(minutes=15)]
                rejected={}; status['status']='not_modified'
            status.update(accepted=len(rows),rejected=rejected)
            return rows,status
        except Exception as e:
            # Non spostare la data dell'ultima edizione e non spacciare la cache per nuova raccolta.
            status.update(status='error',accepted=0,error=f'{type(e).__name__}: {str(e)[:150]}')
            return [],status
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(one,sources))
    return [item for rows,_ in results for item in rows], [s for _,s in results]

TOPICS={
 'Ambiente': ['clima','climate','climat','cop31','ambiente','emission','alluvion','flood','biodivers','ambiental'],
 'Economia': ['econom','inflaz','inflation','mercat','trade','commerc','banca','tariff','dazi'],
 'Tecnologia':['tecnolog','technology','digital','digitale','cyber','intelligenza artificiale','artificial intelligence','internet'],
 'Scienza':['scienz','science','ricerc','research','spazio','space','salute','health'],
 'Geopolitica':['guerra','war','election','elezion','governo','government','missil','diploma','politic','protest','parliament','parlament']}
GEOGRAPHY={
 'Medio Oriente':['iran','israel','israele','gaza','palestin','leban','libano','siria','syria','yemen','bahrain','bahrein','iraq','liban'],
 'Africa':['africa','camerun','cameroon','kenya','nigeria','sudan','congo','ethiopia','etiopia','senegal','sudafrica','south africa'],
 'Asia':['asia','cambog','cambod','china','cinese','chinese','india','japan','giappone','nepal','bangladesh','indonesia','korea','corea','pakistan'],
 'Europa':['europa','europe','italia','italy','france','francia','german','ucrain','ukrain','russia','finland','kosovo','serbia','georgia','poland','polonia','britain','unito','spain','spagna'],
 'Americhe':['america','brasil','brazil','messico','mexic','stati uniti','united states','canada','cile','chile','argentin','peru','perù','venezuela','haiti'],
 'Oceania':['australia','new zealand','nuova zelanda','pacific','oceania','fiji'],
 'Globale':['mondial','global','onu','united nations','cop31']}
def classify(text, mapping, default):
    value=unicodedata.normalize('NFKD',text.casefold())
    hits={k:sum(bool(re.search(r'\b'+re.escape(word),value)) for word in words) for k,words in mapping.items()}
    return max(hits,key=hits.get) if any(hits.values()) else default

def base_story(item):
    text=item['title']+' '+item['description']+' '+' '.join(item.get('tags',[]))
    return {'id':item['id'],'title':item['title'],'summary':item['description'][:240] or 'Il feed non contiene un sottotitolo. Apri la fonte originale.',
            'category':classify(text,TOPICS,'Società'),'region':classify(text,GEOGRAPHY,'Non determinata'),
            'published_at':item['published_at'],'mode':'rss','claims':[],
            'context':'Il feed non fornisce contesto sufficiente per una ricostruzione: consulta la fonte originale.',
            'uncertainty':'Una singola fonte non costituisce una verifica indipendente. Il feed può omettere dettagli e aggiornamenti.',
            'sources':[item], 'related_sources':[]}

def normalize(text):
    text=unicodedata.normalize('NFKD',text.casefold())
    return ' '.join(re.findall(r'\w+', ''.join(c for c in text if not unicodedata.combining(c))))
STOP=set('a al alle alla da dal della delle del di dei e gli i il in la le lo nel nella per su sul the and of to is as on un una con che si come sono'.split())
def tokens(text): return {w for w in normalize(text).split() if len(w)>2 and w not in STOP}
def same_story(a,b):
    if a['sources'][0]['url']==b['sources'][0]['url']: return True
    if abs((date(a['published_at'])-date(b['published_at'])).total_seconds())>48*3600: return False
    x,y=tokens(a['title']),tokens(b['title'])
    if len(x)<4 or len(y)<4: return normalize(a['title'])==normalize(b['title'])
    # Bilanci diversi possono essere aggiornamenti: non unirli automaticamente.
    if set(re.findall(r'\d+',a['title']))!=set(re.findall(r'\d+',b['title'])): return False
    return len(x&y)/len(x|y)>=.72

def deduplicate(stories):
    groups=[]
    for story in sorted(stories,key=lambda s:s['published_at'],reverse=True):
        found=next((g for g in groups if same_story(story,g)),None)
        if found:
            known={s['url'] for s in found['sources']+found['related_sources']}
            for source in story['sources']:
                if source['url'] not in known:
                    found['related_sources'].append(source); known.add(source['url'])
        else: groups.append(story)
    return groups

def select(stories, limit, now):
    remaining=list(stories); result=[]; regions=collections.Counter(); publishers=collections.Counter(); categories=collections.Counter()
    while remaining and len(result)<limit:
        def score(s):
            age=max(0,(now-date(s['published_at'])).total_seconds()/3600)
            freshness=max(0,5-age/12)
            # Copertura geografica, pluralità e freschezza: criterio esplicito, non giudizio di verità.
            return freshness + 5/(1+regions[s['region']]) + 3/(1+publishers[s['sources'][0]['group']]) + 2/(1+categories[s['category']])
        winner=max(remaining,key=score); remaining.remove(winner); result.append(winner)
        regions[winner['region']]+=1; publishers[winner['sources'][0]['group']]+=1; categories[winner['category']]+=1
    for rank,s in enumerate(result,1): s['rank']=rank
    return result

def validate_edition(edition):
    if edition.get('schema_version')!=2 or not isinstance(edition.get('articles'),list): raise ValueError('Edizione non valida')
    ids=set()
    for s in edition['articles']:
        if not s.get('title') or not s.get('summary') or s['id'] in ids: raise ValueError('Titolo/sottotitolo/ID non valido')
        ids.add(s['id'])
        if s['category'] not in CATEGORIES or s['region'] not in REGIONS or not date(s['published_at']): raise ValueError('Metadati non validi')
        if not s['sources']: raise ValueError('Fonte mancante')
        for source in s['sources']+s.get('related_sources',[]): canonical(source['url'])
        for claim in s.get('claims',[]):
            if claim['kind'] not in KINDS or not claim.get('text'): raise ValueError('Asserzione non valida')
            src=next((x for x in s['sources'] if x['id']==claim['source_id']),None)
            if src is None or claim['evidence'] not in src['title']+' '+src['description']: raise ValueError('Evidenza non riscontrata')
    return edition

def build(items, statuses, now, limit=30, provider=None):
    stories=[]; skipped=collections.Counter(); errors=[]
    # Dedup URL prima di spendere tempo nel modello.
    unique={}
    for item in items: unique.setdefault(item['url'],item)
    for item in unique.values():
        story=base_story(item)
        if provider and item['ai_allowed']:
            try: story=provider.enrich(story)
            except Exception as e:
                errors.append({'id':item['id'],'error':f'{type(e).__name__}: {str(e)[:100]}'})
                if item['language']!='it': skipped['translation_failed']+=1; continue
        elif item['language']!='it':
            skipped['translation_unavailable']+=1; continue
        stories.append(story)
    dedup=deduplicate(stories); selected=select(dedup,limit,now)
    groups=collections.Counter(s['sources'][0]['group'] for s in selected)
    regions=collections.Counter(s['region'] for s in selected)
    warnings=[]
    if any(s['status']=='error' for s in statuses): warnings.append('Alcuni feed non sono disponibili: copertura parziale.')
    if skipped: warnings.append('Alcuni articoli in lingua straniera esclusi: traduzione italiana non disponibile o non validata.')
    if len(groups)<3: warnings.append('Pluralità limitata: meno di tre gruppi editoriali presenti.')
    missing=[r for r in REGIONS[:6] if not regions[r]]
    if missing: warnings.append('Aree non coperte in questa edizione: '+', '.join(missing)+'.')
    return validate_edition({'schema_version':2,'version':'0.2','generated_at':iso(now),'last_success_at':iso(now),
        'origin':'rss','articles':selected,'warnings':warnings,
        'coverage':{'regions':dict(regions),'publishers':dict(groups)},
        'pipeline':{'sources':statuses,'collected':len(items),'duplicates_removed':len(items)-len(unique)+len(stories)-len(dedup),
                    'skipped':dict(skipped),'ai_errors':errors,'ai_enabled':provider is not None}})
