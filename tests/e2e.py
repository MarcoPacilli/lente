"""Replay RSS reale → pipeline → JSON → HTTP → browser desktop/mobile.
Non contatta gli editori e non simula una raccolta live riuscita.
"""
import datetime as dt,json,os,shutil,sys,tempfile,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.core import collect,build,atomic_json,UTC
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);shutil.copytree(ROOT/'web',root/'web');shutil.copy(ROOT/'tests/replay.xml',root/'web/replay.xml')
  server=ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**k:Quiet(*a,directory=str(root/'web'),**k))
  thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}'
  try:
   def replay_transport(*args):
    with urlopen(url+'/replay.xml') as r:return r.read(),dict(r.headers)
   source=next(x for x in json.loads((ROOT/'config/sources.json').read_text())['sources'] if x['id']=='gv-it')
   now=dt.datetime(2026,11,20,12,tzinfo=UTC)
   items,statuses=collect([source],now,168,root/'cache',replay_transport)
   edition=build(items,statuses,now,30)
   assert len(edition['articles'])==4
   atomic_json(root/'web/data/news.json',edition)
   atomic_json(root/'web/data/status.json',{'attempted_at':edition['generated_at'],'success':True,'sources':statuses})
   with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=(None if os.getenv('CHROMIUM_PATH')=='playwright' else os.getenv('CHROMIUM_PATH','/usr/bin/chromium')),args=['--no-sandbox'])
    for mobile in [False,True]:
     context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1440,'height':1000},is_mobile=mobile,has_touch=mobile)
     page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     page.goto(url);page.wait_for_selector('.story')
     assert page.locator('.story').count()==4
     assert page.locator('#regionFilter').count()==1
     assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
     page.locator('.story').first.click();assert page.locator('.source-link').count()>=1
     assert page.locator('.source-link').first.get_attribute('href').startswith('https://it.globalvoices.org/')
     if mobile:
      assert page.locator('#detail').get_attribute('aria-modal')=='true'
      page.keyboard.press('Shift+Tab');assert page.evaluate("document.activeElement.id === 'markRead'")
     page.keyboard.press('Escape') if mobile else page.locator('#closeDetail').click()
     page.locator('[data-save]').first.click();page.reload();page.wait_for_selector('.story')
     page.locator('[data-view=saved]').click();assert page.locator('.story').count()==1
     page.locator('[data-view=all]').click();page.locator('#searchInput').fill('Camerun');assert page.locator('.story').count()==1
     page.locator('#searchInput').fill('');page.locator('#regionFilter').select_option('Africa');assert page.locator('.story').count()==1
     page.locator('#briefBtn').click();assert page.locator('.story').count()==4
     page.locator('#howBtn').click();assert page.locator('#methodDialog').is_visible();page.locator('#closeMethod').click()
     page.locator('#refreshBtn').click();page.wait_for_function("!document.getElementById('refreshBtn').disabled")
     assert page.locator('.story').count()==4
     assert not errors,errors
     # XSS nel titolo e URL javascript ricevuto dal JSON: escaping + schema URL difensivo.
     bad=json.loads(json.dumps(edition));bad['articles'][0]['title']='<img src=x onerror="window.pwned=1">';bad['articles'][0]['sources'][0]['url']='javascript:window.pwned=2'
     page.route('**/data/news.json',lambda route:route.fulfill(json=bad))
     page.locator('#refreshBtn').click();page.wait_for_function("!document.getElementById('refreshBtn').disabled")
     assert page.locator('.story img').count()==0
     page.locator('.story').first.click();assert page.locator('.source-link').first.get_attribute('href')=='#'
     assert page.evaluate('window.pwned') is None
     page.keyboard.press('Escape') if mobile else page.locator('#closeDetail').click()
     # Errore fetch non distrugge l'edizione già caricata.
     page.unroute('**/data/news.json');page.route('**/data/news.json',lambda route:route.fulfill(status=503,body='unavailable'))
     page.locator('#refreshBtn').click();page.wait_for_function("!document.getElementById('refreshBtn').disabled")
     assert page.locator('.story').count()==4;assert 'non caricata' in page.locator('#updateText').inner_text()
     context.close();print('PASS browser '+('mobile 390px' if mobile else 'desktop 1440px'))
    browser.close()
  finally:server.shutdown();server.server_close();thread.join()
 print('PASS replay RSS → pipeline → JSON → HTTP → UI; filtri, fonti, persistenza, errori, escaping, focus mobile.')
if __name__=='__main__':main()
