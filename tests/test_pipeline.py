import copy,datetime as dt,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError,URLError
from pipeline.core import *
from pipeline.ai import Ollama
from pipeline.update import main
ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/'config/sources.json').read_text())['sources'][0]
NOW=dt.datetime(2026,11,20,12,tzinfo=UTC)
RAW=(ROOT/'tests/replay.xml').read_bytes()

def items(): return parse_feed(RAW,SOURCE,NOW,168)[0]
class PipelineTests(unittest.TestCase):
 def test_replay_real_articles(self):
  rows,rejected=parse_feed(RAW,SOURCE,NOW,168)
  self.assertEqual(len(rows),4);self.assertEqual(rejected,{'expired':1})
  e=build(rows,[],NOW)
  self.assertEqual(len(e['articles']),4);self.assertTrue(all(a['mode']=='rss' for a in e['articles']))
 def test_urls_and_date(self):
  self.assertEqual(canonical('https://a.org/x?utm_source=x&id=7#f'),'https://a.org/x?id=7')
  for u in ['javascript:alert(1)','https://bad.org/x','https://it.globalvoices.org@bad.org/x']:
   with self.assertRaises(ValueError): allowed_url(u,SOURCE['article_hosts'])
  self.assertIsNone(date('2026-11-20T10:00:00'))
 def test_xml_safety_and_html(self):
  with self.assertRaises(ValueError): parse_feed(b'<!DOCTYPE x><rss/>',SOURCE,NOW,48)
  self.assertEqual(clean('<p>Test</p><script>evil()</script><b>bene</b>'),'Test bene')
 def test_future_missing_date_and_bad_url(self):
  raw=RAW.replace(b'2026-11-19T00:00:00Z',b'2099-11-19T00:00:00Z')
  rows,reject=parse_feed(raw,SOURCE,NOW,168);self.assertEqual(reject['future_date'],1)
  raw=RAW.replace(b'2026-11-19T00:00:00Z',b'')
  self.assertEqual(parse_feed(raw,SOURCE,NOW,168)[1]['missing_title_or_date'],1)
  raw=RAW.replace(b'https://it.globalvoices.org/2026/11/cambogia',b'https://bad.org/2026/11/cambogia')
  self.assertEqual(parse_feed(raw,SOURCE,NOW,168)[1]['unsafe_url'],1)
 def test_atom(self):
  raw=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Cambogia test</title><link href="https://it.globalvoices.org/test"/><published>2026-11-20T00:00:00Z</published><summary>Testo</summary><author><name>Autore</name></author></entry></feed>'
  self.assertEqual(parse_feed(raw,SOURCE,NOW,48)[0][0]['author'],'Autore')
 def test_duplicate_and_group(self):
  a=base_story(items()[0]);b=copy.deepcopy(a);b['sources'][0]['url']+='different';b['id']='other'
  merged=deduplicate([a,b]);self.assertEqual(len(merged),1);self.assertEqual(len(merged[0]['related_sources']),1)
  self.assertEqual(len(merged[0]['sources']),1)
  x=copy.deepcopy(a);y=copy.deepcopy(a);x['title']='Terremoto in paese: almeno 20 morti confermati';y['title']='Terremoto in paese: almeno 25 morti confermati';x['sources'][0]['url']='https://example.com/a';y['sources'][0]['url']='https://example.com/b';self.assertFalse(same_story(x,y))
 def test_foreign_skipped_not_fake_translation(self):
  r=items()[0];r['language']='en';e=build([r],[],NOW)
  self.assertEqual(e['articles'],[]);self.assertEqual(e['pipeline']['skipped']['translation_unavailable'],1)
 def test_coverage_unknown_not_publisher_country(self):
  r=items()[0];r.update(title='Una storia senza luogo',description='',tags=[])
  self.assertEqual(base_story(r)['region'],'Non determinata')
 def test_collect_partial_and_304(self):
  with tempfile.TemporaryDirectory() as td:
   rows,status=collect([SOURCE],NOW,168,td,lambda *args:(RAW,{'ETag':'tag'}))
   self.assertEqual(len(rows),4);self.assertEqual(status[0]['status'],'ok')
   def not_modified(*args): raise HTTPError('https://it.globalvoices.org/feed/',304,'not modified',{},None)
   rows,status=collect([SOURCE],NOW,168,td,not_modified)
   self.assertEqual(len(rows),4);self.assertEqual(status[0]['status'],'not_modified')
   def down(*args): raise URLError('unavailable')
   rows,status=collect([SOURCE],NOW,168,td,down)
   self.assertEqual(rows,[]);self.assertEqual(status[0]['status'],'error')
 def test_failed_update_preserves_last_edition(self):
  with tempfile.TemporaryDirectory() as td:
   target=Path(td)/'news.json';target.write_text('previous edition')
   with patch('sys.argv',['update','--config',str(ROOT/'config/sources.json'),'--output',str(target)]),patch('pipeline.update.collect',return_value=([],[])):
    self.assertEqual(main(),2)
   self.assertEqual(target.read_text(),'previous edition');self.assertFalse(json.loads((Path(td)/'status.json').read_text())['success'])
 def output(self):
  r=items()[0]
  return {'language':'it','title':r['title'][:180],'summary':'Sintesi breve in italiano.','category':'Geopolitica','region':'Asia','context':'','claims':[{'text':'La fonte tratta il diritto di manifestare.','kind':'interpretazione','source_id':r['id'],'evidence':r['title']}]}
 def test_ai_rejects_fake_evidence_numbers_urls(self):
  r=items()[0];good=self.output();Ollama.validate(good,r)
  for mutate in [lambda o:o['claims'][0].update(evidence='Inventata evidenza senza fonte'),lambda o:o.update(summary='Sono morte 999999 persone.'),lambda o:o.update(summary='Vedi https://inventata.org'),lambda o:o['claims'][0].update(source_id='unknown')]:
   o=copy.deepcopy(good);mutate(o)
   with self.assertRaises(ValueError):Ollama.validate(o,r)
 def test_ollama_real_http_protocol_stub_and_cache(self):
  # Contratto HTTP testato, NON un'inferenza reale: nessuna pretesa sulla qualità del modello.
  from http.server import BaseHTTPRequestHandler,HTTPServer
  import threading
  response=self.output()
  class Handler(BaseHTTPRequestHandler):
   calls=0
   def do_POST(self):
    self.__class__.calls+=1;body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
    self.server.received=body
    self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'message':{'content':json.dumps(response)}}).encode())
   def log_message(self,*args):pass
  server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with tempfile.TemporaryDirectory() as td:
    ai=Ollama(Path(td),endpoint=f'http://127.0.0.1:{server.server_port}')
    for _ in range(2):self.assertEqual(ai.enrich(base_story(items()[0]))['mode'],'ai')
    self.assertEqual(Handler.calls,1);self.assertEqual(server.received['stream'],False)
  finally:server.shutdown();server.server_close();thread.join()
 def test_ai_endpoint_only_local(self):
  with self.assertRaises(ValueError): Ollama(Path('.'),endpoint='https://paid.example.com')
 def test_snapshot_schema(self):validate_edition(json.loads((ROOT/'web/data/news.json').read_text()))
if __name__=='__main__': unittest.main()
