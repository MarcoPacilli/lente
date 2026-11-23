"""Regressioni ricavate dallo ZIP e dai rapporti reali di produzione dell'utente."""
import copy,datetime as dt,json,tempfile,unittest,contextlib,io
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from pipeline.core import UTC,parse_feed,collect,build,base_story,load_json
from pipeline.update import main
from pipeline.ai import Ollama
ROOT=Path(__file__).resolve().parents[1]
SOURCE=next(x for x in json.loads((ROOT/'config/sources.json').read_text())['sources'] if x['id']=='gv-it')
NOW=dt.datetime(2026,11,20,12,tzinfo=UTC)
RAW=(ROOT/'tests/replay.xml').read_bytes()
def rows():return parse_feed(RAW,SOURCE,NOW,168)[0]

class RepairTests(unittest.TestCase):
 def test_actual_production_failure_identified(self):
  status=load_json(ROOT/'tests/fixtures/production-status.json',{})
  self.assertEqual(status['collected'],6);self.assertEqual(status['published'],1)
  self.assertEqual(len(status['ai_errors']),5)
  self.assertTrue(all('Evidenza non riscontrata' in e['error'] for e in status['ai_errors']))
  self.assertTrue(any('406' in x.get('error','') for x in status['sources']))
 def test_no_model_call_for_italian(self):
  class BrokenModel:
   def enrich(self,story):raise AssertionError('Il modello non deve riscrivere una fonte italiana')
  original=rows();edition=build(original,[],NOW,provider=BrokenModel())
  self.assertEqual(len(edition['articles']),len(original))
  self.assertTrue(all(a['mode']=='rss' and a['title']==a['sources'][0]['title'] and a['summary']==a['sources'][0]['description'] for a in edition['articles']))
  self.assertEqual(edition['pipeline']['ai_errors'],[])
 def test_real_bad_translation_cannot_enter_news(self):
  bad=load_json(ROOT/'tests/fixtures/production-news.json',{})['articles'][0]
  class LegacyModel:
   def enrich(self,story):return copy.deepcopy(bad)
  edition=build([bad['sources'][0]],[],NOW,provider=LegacyModel())
  self.assertEqual(edition['articles'],[])
  self.assertEqual(len(edition['drafts']),1)
  self.assertEqual(edition['drafts'][0]['review_status'],'unreviewed')
 def test_evidence_is_resolved_by_program_not_translated(self):
  item=rows()[0]
  reply={'language':'it','title':'Un approfondimento sulle manifestazioni','summary':'La fonte esamina la situazione.',
         'claims':[{'text':'La fonte tratta le manifestazioni.','kind':'interpretazione','evidence_id':'t'}]}
  with tempfile.TemporaryDirectory() as td:
   model=Ollama(Path(td))
   with patch.object(model,'generate',return_value=reply):draft=model.enrich(base_story(item))
  self.assertEqual(draft['claims'][0]['evidence'],item['title'])
  self.assertEqual(draft['claims'][0]['source_id'],item['id'])
 def test_one_story_does_not_replace_last_edition(self):
  with tempfile.TemporaryDirectory() as td:
   output=Path(td)/'news.json';output.write_text('precedente edizione valida')
   argv=['update','--config',str(ROOT/'config/sources.json'),'--output',str(output)]
   with patch('sys.argv',argv),patch('pipeline.update.collect',return_value=(rows()[:1],[])),contextlib.redirect_stdout(io.StringIO()):code=main()
   status=json.loads(output.with_name('status.json').read_text())
   self.assertEqual(code,2);self.assertFalse(status['success']);self.assertEqual(status['candidate_count'],1)
   self.assertEqual(status['published'],0);self.assertEqual(output.read_text(),'precedente edizione valida')
 def test_cache_can_expand_window_after_304(self):
  with tempfile.TemporaryDirectory() as td:
   first,_=collect([SOURCE],NOW,48,td,lambda *args:(RAW,{'ETag':'fixture'}))
   self.assertEqual(len(first),1)
   def unchanged(*args):raise HTTPError(SOURCE['feed'],304,'not modified',{},None)
   later,status=collect([SOURCE],NOW,168,td,unchanged)
   self.assertEqual(len(later),4);self.assertEqual(status[0]['status'],'not_modified')
 def test_cache_policy_change_forces_new_fetch(self):
  with tempfile.TemporaryDirectory() as td:
   collect([SOURCE],NOW,48,td,lambda *args:(RAW,{'ETag':'fixture'}))
   changed={**SOURCE,'ai_allowed':not SOURCE['ai_allowed']};seen=[]
   def transport(url,hosts,headers):seen.append(headers);return RAW,{}
   collect([changed],NOW,48,td,transport)
   self.assertEqual(seen,[{}])
 def test_raw_metadata_not_silently_cut(self):
  raw=RAW.replace(b'<description>',b'<description>'+b'A'*600+b' ',1)
  item=parse_feed(raw,SOURCE,NOW,168)[0][0]
  self.assertGreater(len(item['description']),480)
  self.assertEqual(base_story(item)['summary'],item['description'])
 def test_euronews_does_not_use_ai_or_claim_cc_license(self):
  sources=json.loads((ROOT/'config/sources.json').read_text())['sources']
  euronews=[x for x in sources if x['group']=='Euronews']
  self.assertEqual(len(euronews),7)
  self.assertTrue(all(x['language']=='it' and not x['ai_allowed'] and x['rights']=='metadata_only' and not x.get('license') for x in euronews))
if __name__=='__main__':unittest.main()
