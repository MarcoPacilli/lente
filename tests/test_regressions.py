import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from pipeline.ai import Ollama
from pipeline.core import base_story,classify,TOPICS,GEOGRAPHY
ROOT=Path(__file__).resolve().parents[1]
class RegressionTests(unittest.TestCase):
 def item(self):return json.loads((ROOT/'web/data/news.json').read_text())['articles'][0]['sources'][0]
 def reply(self):
  r=self.item()
  return {'language':'it','title':'Un approfondimento sulle manifestazioni','summary':'Una sintesi in italiano.','category':'Scienza','region':'Non determinata','context':'','claims':[{'text':'La fonte tratta le manifestazioni.','kind':'interpretazione','source_id':r['id'],'evidence':r['title']}]}
 def test_grounded_metadata_survive_ai_override(self):
  with tempfile.TemporaryDirectory() as td:
   ai=Ollama(Path(td));story=base_story(self.item())
   with patch.object(ai,'generate',return_value=self.reply()):result=ai.enrich(story)
   self.assertEqual(result['region'],'Asia');self.assertEqual(result['category'],story['category'])
 def test_validation_retry_keeps_same_checks(self):
  bad=self.reply();bad['claims'][0]['evidence']='Citazione inventata e non presente'
  with tempfile.TemporaryDirectory() as td:
   ai=Ollama(Path(td))
   with patch.object(ai,'generate',side_effect=[bad,self.reply()]) as generate:
    result=ai.enrich(base_story(self.item()))
   self.assertEqual(generate.call_count,2);self.assertEqual(result['mode'],'ai')
   self.assertIn('Evidenza non riscontrata',generate.call_args.args[2])
 def test_two_invalid_attempts_are_not_published(self):
  bad=self.reply();bad['summary']='Sono presenti 999999 vittime'
  with tempfile.TemporaryDirectory() as td:
   ai=Ollama(Path(td))
   with patch.object(ai,'generate',return_value=bad) as generate:
    with self.assertRaises(ValueError):ai.enrich(base_story(self.item()))
   self.assertEqual(generate.call_count,2);self.assertEqual(list(Path(td).glob('*.json')),[])
 def test_json_parse_failure_can_retry(self):
  with tempfile.TemporaryDirectory() as td:
   ai=Ollama(Path(td))
   with patch.object(ai,'generate',side_effect=[ValueError('JSON non valido'),self.reply()]) as generate:
    self.assertEqual(ai.enrich(base_story(self.item()))['mode'],'ai')
   self.assertEqual(generate.call_count,2)
 def test_nepal_and_culinary_heritage(self):
  self.assertEqual(classify('Reclaiming indigenous food heritage in Nepal',GEOGRAPHY,'Non determinata'),'Asia')
  self.assertEqual(classify('Reclaiming indigenous food heritage in Nepal',TOPICS,'Società'),'Società')
  self.assertEqual(classify('Protestas en España',GEOGRAPHY,'Non determinata'),'Europa')
if __name__=='__main__':unittest.main()
