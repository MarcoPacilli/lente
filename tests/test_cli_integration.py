"""RSS su HTTP locale → raccolta → CLI con soglia esplicita → JSON su HTTP.
Contenuti reali del replay, data congelata e soglia di tre SOLO per questo test controllato.
"""
import contextlib,datetime as dt,functools,io,json,tempfile,threading,unittest
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen
from pipeline.core import collect as real_collect,UTC
from pipeline.update import main
ROOT=Path(__file__).resolve().parents[1]
NOW=dt.datetime(2026,11,20,12,tzinfo=UTC)
class FrozenDatetime(dt.datetime):
 @classmethod
 def now(cls,tz=None):return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class CLIIntegration(unittest.TestCase):
 def test_cli_publishes_valid_replay_and_report(self):
  source=next(s for s in json.loads((ROOT/'config/sources.json').read_text())['sources'] if s['id']=='gv-it')
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'feed.xml').write_bytes((ROOT/'tests/replay.xml').read_bytes())
   config=root/'config.json';config.write_text(json.dumps({'sources':[source]}))
   server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
   try:
    def transport(*args):
     with urlopen(base+'/feed.xml') as response:return response.read(),dict(response.headers)
    def collector(sources,now,hours,cache):return real_collect(sources,now,hours,cache,transport)
    argv=['update','--config',str(config),'--output',str(root/'news.json'),'--cache',str(root/'cache'),'--hours','168','--min-stories','3']
    with patch('sys.argv',argv),patch('pipeline.update.collect',side_effect=collector),patch('pipeline.update.dt.datetime',FrozenDatetime),contextlib.redirect_stdout(io.StringIO()):code=main()
    self.assertEqual(code,0)
    with urlopen(base+'/news.json') as response:edition=json.load(response)
    with urlopen(base+'/status.json') as response:status=json.load(response)
    self.assertEqual(len(edition['articles']),4);self.assertEqual(edition['origin'],'rss')
    self.assertTrue(status['success']);self.assertEqual(status['minimum_required'],3)
    self.assertTrue(all(a['mode']=='rss' for a in edition['articles']))
    self.assertEqual(status['state'],'partial') # un solo gruppo: non dichiara copertura equilibrata
   finally:server.shutdown();server.server_close();thread.join()
