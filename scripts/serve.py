"""Server statico della sola UI: non espone codice, cache o file di configurazione."""
import argparse, functools, webbrowser
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8000);p.add_argument('--open',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parents[1]/'web'
server=ThreadingHTTPServer((args.host,args.port),functools.partial(SimpleHTTPRequestHandler,directory=str(root)))
print(f'Lente: http://localhost:{args.port} — Ctrl+C per chiudere',flush=True)
if args.open:webbrowser.open(f'http://localhost:{args.port}')
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
