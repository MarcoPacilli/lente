'use strict';
let articles=[], edition=null, runStatus=null, view='all', category='Tutte', region='Tutte le aree', query='', current=null, opener=null;
// BEGIN SERVER CLOCK
let serverClock=null;
function useServerClock(headers){
 const stamp=Date.parse(headers.get('Date')||'');
 const age=Number(headers.get('Age')||0);
 serverClock=Number.isFinite(stamp)&&Number.isFinite(age)&&age>=0?{ms:stamp+age*1000,at:performance.now()}:null;
}
function editionAge(stamp){
 const published=Date.parse(stamp);
 if(!serverClock||!Number.isFinite(published))return null;
 return Math.max(0,serverClock.ms+performance.now()-serverClock.at-published);
}
// END SERVER CLOCK
const $=id=>document.getElementById(id);
const categories=['Tutte','Geopolitica','Economia','Tecnologia','Scienza','Ambiente','Italia','Società'];
const modes={rss:'Estratto RSS',ai:'Sintesi automatica · da verificare',manual:'Sintesi iniziale verificata'};
const storageKey='lente-v02';
let stored={saved:[],read:[]};
try { const value=JSON.parse(localStorage.getItem(storageKey)); if(value&&typeof value==='object')stored=value; } catch {}
const saved=new Set(Array.isArray(stored.saved)?stored.saved:[]), read=new Set(Array.isArray(stored.read)?stored.read:[]);
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function safeURL(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'#';}catch{return '#';}}
function fmt(value,time=false){const d=new Date(value);if(Number.isNaN(d.getTime()))return 'Data non disponibile';return new Intl.DateTimeFormat('it-IT',{dateStyle:'medium',...(time?{timeStyle:'short'}:{}),timeZone:'Europe/Rome'}).format(d);}
function persist(){try{localStorage.setItem(storageKey,JSON.stringify({saved:[...saved],read:[...read]}));}catch{}}
function visible(){const q=query.toLocaleLowerCase('it').trim();return articles.filter(a=>(category==='Tutte'||a.category===category)&&(region==='Tutte le aree'||a.region===region)&&(view!=='brief'||a.rank<=5)&&(view!=='saved'||saved.has(a.id))&&(!q||[a.title,a.summary,a.region,a.category,...a.sources.map(s=>s.publisher)].join(' ').toLocaleLowerCase('it').includes(q)));}
function renderFilters(){$('filters').innerHTML=categories.map(c=>`<button type="button" class="chip ${category===c?'active':''}" data-category="${esc(c)}" aria-pressed="${category===c}">${esc(c)}</button>`).join('');}
function renderList(){
 const list=visible();$('statStories').textContent=articles.length;$('statTopics').textContent=new Set(articles.map(a=>a.category)).size;$('statTopics').nextElementSibling.textContent=Number($('statTopics').textContent)===1?'categoria':'categorie';$('statSaved').textContent=articles.filter(a=>saved.has(a.id)).length;
 $('listCount').textContent=`${list.length} ${list.length===1?'notizia':'notizie'}`;$('listTitle').textContent=view==='brief'?'Il briefing essenziale':view==='saved'?'Le tue notizie salvate':'Tutte le notizie';
 document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);b.setAttribute('aria-pressed',String(b.dataset.view===view));});renderFilters();
 $('storyList').innerHTML=list.length?list.map(a=>`<article class="story ${current===a.id?'selected':''}" data-story="${esc(a.id)}" tabindex="0" role="button" aria-label="Approfondisci: ${esc(a.title)}"><div class="rank">${String(a.rank).padStart(2,'0')}</div><div class="story-main"><div class="meta"><span>${esc(a.category)}</span><span class="point">·</span><span class="place">${esc(a.region)}</span></div><h3>${esc(a.title)}</h3><p>${esc(a.summary)}</p><div class="story-foot"><time datetime="${esc(a.published_at)}">${fmt(a.published_at)}</time><span class="source-count">${esc(a.sources[0].publisher)} · ${a.sources.length} ${a.sources.length===1?'fonte':'fonti'}</span><span class="type-tag">${esc(modes[a.mode]||'Estratto')}</span>${read.has(a.id)?'<span class="read-tag">✓ Letta</span>':''}</div></div><button class="save ${saved.has(a.id)?'saved':''}" aria-label="${saved.has(a.id)?'Rimuovi dai salvati':'Salva la notizia'}" aria-pressed="${saved.has(a.id)}" data-save="${esc(a.id)}" type="button"><svg viewBox="0 0 24 24" fill="${saved.has(a.id)?'currentColor':'none'}" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3.9h12v16.2l-6-4-6 4V3.9Z"/></svg></button></article>`).join(''):'<div class="empty"><b>Nessuna notizia trovata</b>Prova un’altra categoria, area geografica o ricerca.</div>';
}
function sourceHTML(s){return `<a class="source-link" href="${esc(safeURL(s.url))}" target="_blank" rel="noopener noreferrer"><span>${esc(s.publisher)}<small>${esc(s.title)}</small><small>${esc(s.author||'Autore non indicato nel feed')} · ${esc(s.language)} · ${fmt(s.published_at)}</small></span><span class="arrow" aria-hidden="true">↗</span></a>${s.license?`<p class="method-note"><a href="${esc(safeURL(s.license))}" target="_blank" rel="noopener noreferrer">Licenza della fonte e della rielaborazione</a> · Fonte e rielaborazioni di Lente sotto la licenza indicata; nessuna affiliazione.</p>`:''}`;}
function detailHTML(a){
 const facts=a.claims?.length?a.claims.map(c=>`<li><span class="kind">${esc(c.kind)}</span><br>${esc(c.text)}<small class="evidence">Evidenza nella fonte: «${esc(c.evidence)}»</small></li>`).join(''):'<li>Il feed offre solo titolo e anticipazione. Lente non ricostruisce fatti mancanti.</li>';
 return `<div class="detail-actual"><div class="detail-top"><span class="small-label">${esc(a.category)} · ${fmt(a.published_at)}</span><button class="close" id="closeDetail" type="button" aria-label="Chiudi approfondimento">×</button></div><h2 id="detailTitle">${esc(a.title)}</h2><div class="attribution">Da <a href="${esc(safeURL(a.sources[0].url))}" target="_blank" rel="noopener noreferrer">${esc(a.sources[0].publisher)}</a> · ${esc(a.sources[0].author||'autore non indicato')}${a.sources[0].translator?` · Traduzione: ${esc(a.sources[0].translator)}`:''}<br>${esc(modes[a.mode])}</div><div class="detail-summary">${esc(a.summary)}</div><div class="divider"></div><h3 class="blocktitle">Fatti, dichiarazioni e interpretazioni</h3><ul class="facts">${facts}</ul><div class="divider"></div><h3 class="blocktitle">Contesto disponibile</h3><p class="detail-copy">${esc(a.context)}</p><div class="caution"><strong>Limiti e incertezze</strong><br>${esc(a.uncertainty)}</div><div class="divider"></div><h3 class="blocktitle">Fonti originali · ${a.sources.length}</h3><div class="source-links">${a.sources.map(sourceHTML).join('')}</div>${a.related_sources?.length?`<div class="divider"></div><h3 class="blocktitle">Coperture correlate · abbinamento automatico</h3><p class="method-note">La somiglianza dei titoli non dimostra una conferma indipendente. Le fonti correlate non sostengono automaticamente tutti i punti della scheda.</p><div class="source-links">${a.related_sources.map(sourceHTML).join('')}</div>`:''}<p class="method-note">Una fonte non equivale a una verifica incrociata. Le versioni linguistiche dello stesso gruppo non sono redazioni indipendenti.</p><button type="button" class="read-button" id="markRead">${read.has(a.id)?'✓ Segnata come letta':'Segna come letta'}</button></div>`;
}
function openStory(id){const a=articles.find(x=>x.id===id);if(!a)return;opener=document.activeElement;current=id;read.add(id);persist();renderList();$('detail').innerHTML=detailHTML(a);$('detail').scrollTop=0;if(matchMedia('(max-width:760px)').matches){$('detail').classList.add('mobile-open');$('detail').setAttribute('role','dialog');$('detail').setAttribute('aria-modal','true');$('detail').setAttribute('aria-labelledby','detailTitle');const x=document.createElement('div');x.id='scrim';x.className='scrim';x.addEventListener('click',closeDetail);document.body.appendChild(x);document.body.classList.add('modal-open');}$('closeDetail').focus();}
function closeDetail(){document.querySelectorAll('#scrim').forEach(x=>x.remove());$('detail').classList.remove('mobile-open');$('detail').removeAttribute('role');$('detail').removeAttribute('aria-modal');$('detail').removeAttribute('aria-labelledby');document.body.classList.remove('modal-open');const old=current;current=null;$('detail').innerHTML='<div class="detail-empty"><div class="detail-icon">L.</div><h2>Il contesto, quando vuoi.</h2><p>Seleziona una notizia per leggere la sintesi, le evidenze disponibili e le fonti originali.</p></div>';renderList();document.querySelector(`[data-story="${CSS.escape(old||'')}"]`)?.focus();}
function renderStatus(){
 if(!edition)return;
 const age=editionAge(edition.last_success_at);
 const stale=age!==null&&age>36*3600*1000;
 const snapshot=edition.origin==='verified_snapshot';
 const failed=runStatus&&runStatus.success===false&&new Date(runStatus.attempted_at)>=new Date(edition.last_success_at);
 $('updateStatus').classList.toggle('warn',stale||snapshot||failed||edition.warnings.length>0);
 $('updateText').textContent=`${snapshot?'Edizione iniziale verificata manualmente':'Ultimo aggiornamento riuscito'}: ${fmt(edition.last_success_at,true)}${stale?' · Edizione non aggiornata da oltre 36 ore':''}${failed?' · Ultimo tentativo fallito, conservata l’edizione precedente':''}`;
 $('coverageText').textContent=[...edition.warnings,...(snapshot?['La raccolta live deve essere eseguita: questi articoli sono una fotografia iniziale, non un aggiornamento RSS.']:[])].join(' ');
 document.querySelector('.date-pill').textContent=fmt(edition.last_success_at);
 $('editionKind').textContent=snapshot?'Edizione iniziale · fonti consultate':'RSS · aggiornamento giornaliero';
}
async function loadEdition(){
 $('refreshBtn').disabled=true;
 try{
  const response=await fetch('data/news.json',{cache:'no-store'});if(!response.ok)throw Error(`HTTP ${response.status}`);
  const data=await response.json();if(data.schema_version!==2||!Array.isArray(data.articles)||!data.last_success_at)throw Error('Formato edizione non valido');
  for(const a of data.articles){if(!a.id||!a.title||!a.summary||!a.sources?.length||!a.published_at)throw Error('Notizia incompleta');}
  useServerClock(response.headers);
  if(current)closeDetail();edition=data;articles=data.articles;runStatus=null;
  try{const s=await fetch('data/status.json',{cache:'no-store'});if(s.ok)runStatus=await s.json();}catch{}
  $('regionFilter').innerHTML=['Tutte le aree',...new Set(articles.map(a=>a.region))].map(r=>`<option>${esc(r)}</option>`).join('');if(!articles.some(a=>a.region===region))region='Tutte le aree';$('regionFilter').value=region;
  const briefCount=Math.min(5,articles.length);document.querySelector('.brief-card p').textContent=`Le ${briefCount} storie in primo piano, senza perdere il contesto.`;
  renderList();renderStatus();
 }catch(e){$('updateStatus').classList.add('warn');$('updateText').textContent='Edizione non caricata. Riprova tra poco.';$('coverageText').textContent=String(e.message);if(!edition)$('storyList').innerHTML='<div class="empty"><b>Notiziario non disponibile</b>Servi la cartella web tramite HTTP, come descritto nel README.</div>';}
 finally{$('refreshBtn').disabled=false;}
}
function method(){const aiErrors=runStatus?.ai_errors||edition?.pipeline?.ai_errors||[];const statuses=runStatus?.sources||edition?.pipeline?.sources||[];$('methodContent').innerHTML=`<p>Raccolta giornaliera dei feed RSS, nessun aggiramento di paywall, nessuna immagine o articolo completo copiato.</p><p>La selezione favorisce freschezza, aree, categorie e gruppi editoriali meno rappresentati. Non garantisce una copertura completa né una neutralità assoluta. L’area è dedotta dal contenuto; se manca resta «Non determinata».</p><p>Gli estratti RSS mantengono il contenuto del feed in italiano. Il modello locale può tradurre e sintetizzare solo fonti abilitate: i testi sono etichettati come automatici e non revisionati. Le evidenze sono citazioni riscontrate nel feed; questo controllo non certifica la correttezza semantica. Senza traduzione valida, gli articoli stranieri sono esclusi.</p><p>Il pulsante «Ricarica edizione» scarica l’ultima edizione pubblicata; la raccolta viene eseguita separatamente dal computer o dallo scheduler.</p><p>Salvati e letture restano in questo browser, senza sincronizzazione cloud.</p><p>Gruppi editoriali: ${esc(Object.keys(edition?.coverage?.publishers||{}).join(', ')||'nessuno')}. Notizie raccolte: ${edition?.pipeline?.collected??0}. Duplicati rimossi: ${edition?.pipeline?.duplicates_removed??0}.</p><table><thead><tr><th>Fonte</th><th>Lingua</th><th>Stato / elementi</th></tr></thead><tbody>${statuses.map(s=>`<tr><td>${esc(s.name)}</td><td>${esc(s.language||'—')}</td><td>${esc(s.status)} / ${s.accepted??0}${s.error?`<br>${esc(s.error)}`:''}</td></tr>`).join('')}</tbody></table>${aiErrors.length?`<h3>Articoli esclusi dalla sintesi</h3><ul>${aiErrors.map(x=>`<li>${esc(x.title||x.id)}: ${esc(x.error)}</li>`).join('')}</ul>`:''}<p>Le fonti correlate sono abbinate per somiglianza di titolo, senza presumere una conferma indipendente.</p>`;$('methodDialog').showModal();}
$('filters').addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(b){category=b.dataset.category;renderList();}});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;renderList();}));
$('searchInput').addEventListener('input',e=>{query=e.target.value;renderList();});$('regionFilter').addEventListener('change',e=>{region=e.target.value;renderList();});
$('storyList').addEventListener('click',e=>{const b=e.target.closest('[data-save]');if(b){const id=b.dataset.save;saved.has(id)?saved.delete(id):saved.add(id);persist();renderList();document.querySelector(`[data-save="${CSS.escape(id)}"]`)?.focus();return;}const s=e.target.closest('[data-story]');if(s)openStory(s.dataset.story);});
$('storyList').addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)&&e.target.matches('[data-story]')){e.preventDefault();openStory(e.target.dataset.story);}});
$('briefBtn').addEventListener('click',()=>{view='brief';category='Tutte';region='Tutte le aree';query='';$('searchInput').value='';$('regionFilter').value=region;renderList();document.querySelector('.controls').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth',block:'start'});});
$('detail').addEventListener('click',e=>{if(e.target.closest('#closeDetail'))closeDetail();if(e.target.closest('#markRead')&&current){read.add(current);persist();renderList();e.target.textContent='✓ Segnata come letta';}});
$('howBtn').addEventListener('click',method);$('closeMethod').addEventListener('click',()=>$('methodDialog').close());$('refreshBtn').addEventListener('click',loadEdition);
document.addEventListener('keydown',e=>{if(!$('detail').classList.contains('mobile-open'))return;if(e.key==='Escape'){e.preventDefault();closeDetail();}if(e.key==='Tab'){const nodes=[...$('detail').querySelectorAll('button,a[href]')];const first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
window.addEventListener('resize',()=>{if(current)closeDetail();});
setInterval(renderStatus,60000);loadEdition();
