"""Integrazione su HTTP reale in loopback, senza confonderla con un test live degli editori."""
import datetime as dt,functools,json,shutil,tempfile,threading,unittest
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from pipeline.core import collect,build,atomic_json,UTC
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class HTTPIntegration(unittest.TestCase):
 def test_rss_http_pipeline_json_http(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);shutil.copy(ROOT/'tests/replay.xml',root/'feed.xml')
   server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   base=f'http://127.0.0.1:{server.server_port}'
   try:
    def transport(*args):
     with urlopen(base+'/feed.xml') as response:return response.read(),dict(response.headers)
    source=json.loads((ROOT/'config/sources.json').read_text())['sources'][0]
    now=dt.datetime(2026,11,20,12,tzinfo=UTC)
    rows,status=collect([source],now,168,root/'cache',transport)
    edition=build(rows,status,now)
    atomic_json(root/'news.json',edition)
    with urlopen(base+'/news.json') as response: downloaded=json.load(response)
    self.assertEqual(len(downloaded['articles']),4)
    self.assertEqual(downloaded['pipeline']['sources'][0]['accepted'],4)
    self.assertEqual(downloaded['articles'][0]['sources'][0]['publisher'],'Global Voices · Italiano')
   finally:server.shutdown();server.server_close();thread.join()
