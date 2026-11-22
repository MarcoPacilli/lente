"""python -m pipeline.update --help"""
import argparse, datetime as dt, json, sys
from pathlib import Path
from .core import collect,build,atomic_json,iso,load_json

def main():
    p=argparse.ArgumentParser(description='Aggiorna Lente dai feed, senza dipendenze Python aggiuntive.')
    p.add_argument('--config',default='config/sources.json')
    p.add_argument('--profile',choices=['personal','public'],default='personal')
    p.add_argument('--limit',type=int,default=30)
    p.add_argument('--hours',type=int,default=48)
    p.add_argument('--ai',choices=['none','ollama'],default='none')
    p.add_argument('--output',default='web/data/news.json')
    p.add_argument('--cache',default='.cache')
    args=p.parse_args()
    if not 1<=args.limit<=100 or not 1<=args.hours<=168: p.error('limit 1–100; hours 1–168')
    config=json.loads(Path(args.config).read_text())
    sources=[s for s in config['sources'] if s.get('enabled') and (args.profile=='personal' or s.get('public_allowed'))]
    if not sources: p.error('Nessuna fonte abilitata per questo profilo')
    now=dt.datetime.now(dt.timezone.utc)
    items,statuses=collect(sources,now,args.hours,Path(args.cache)/'feeds')
    provider=None
    if args.ai=='ollama':
        from .ai import Ollama
        provider=Ollama(Path(args.cache)/'ai')
    edition=build(items,statuses,now,args.limit,provider)
    status_path=Path(args.output).with_name('status.json')
    report={'attempted_at':iso(now),'success':bool(edition['articles']),'sources':statuses,
            'collected':len(items),'published':len(edition['articles']),'skipped':edition['pipeline']['skipped'],
            'ai_errors':edition['pipeline']['ai_errors'],'warnings':edition['warnings']}
    if not edition['articles']:
        # La precedente edizione rimane intatta. Il processo fallisce, così scheduler/CI lo segnalano.
        atomic_json(status_path,report)
        print(json.dumps(report,ensure_ascii=False,indent=2)); return 2
    edition['profile']=args.profile
    atomic_json(args.output,edition); atomic_json(status_path,report)
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': sys.exit(main())
