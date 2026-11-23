"""Aggiorna il notiziario. Un'edizione sottosoglia non sostituisce l'ultima valida."""
import argparse,datetime as dt,json,sys
from pathlib import Path
from .core import collect,build,atomic_json,iso

def main():
    parser=argparse.ArgumentParser(description='Lente: raccolta RSS italiana, con bozze AI locali opzionali.')
    parser.add_argument('--config',default='config/sources.json')
    parser.add_argument('--profile',choices=['personal','public'],default='public')
    parser.add_argument('--limit',type=int,default=50)
    parser.add_argument('--min-stories',type=int,default=10)
    parser.add_argument('--hours',type=int,default=48)
    parser.add_argument('--ai',choices=['none','ollama'],default='none',help='Ollama produce bozze, non notizie automaticamente approvate.')
    parser.add_argument('--output',default='web/data/news.json')
    parser.add_argument('--cache',default='.cache')
    args=parser.parse_args()
    if not 1<=args.limit<=100 or not 1<=args.hours<=168 or not 1<=args.min_stories<=args.limit:
        parser.error('limit 1–100; hours 1–168; min-stories 1–limit')
    config=json.loads(Path(args.config).read_text())
    sources=[s for s in config['sources'] if s.get('enabled') and (args.profile=='personal' or s.get('public_allowed'))]
    if not sources:parser.error('Nessuna fonte abilitata per il profilo')
    now=dt.datetime.now(dt.timezone.utc)
    rows,statuses=collect(sources,now,args.hours,Path(args.cache)/'feeds')
    provider=None
    if args.ai=='ollama':
        from .ai import Ollama
        provider=Ollama(Path(args.cache)/'ai')
    edition=build(rows,statuses,now,args.limit,provider)
    drafts=edition.pop('drafts',[])
    count=len(edition['articles']);success=count>=args.min_stories
    quality='partial' if edition['warnings'] else 'ready'
    report={'attempted_at':iso(now),'success':success,'state':quality if success else 'insufficient',
            'sources':statuses,'collected':len(rows),'candidate_count':count,'published':count if success else 0,
            'minimum_required':args.min_stories,'skipped':edition['pipeline']['skipped'],
            'ai_errors':edition['pipeline']['ai_errors'],'drafts':len(drafts),'warnings':edition['warnings']}
    output=Path(args.output)
    # Gli eventuali testi generati sono segregati e non letti dalla lista delle notizie.
    atomic_json(output.with_name('drafts.json'),{'status':'unreviewed','generated_at':iso(now),'articles':drafts})
    if not success:
        report['reason']=f'Edizione insufficiente: {count} notizie valide, minimo {args.min_stories}. Edizione precedente conservata.'
        report['warnings'].insert(0,report['reason'])
        atomic_json(output.with_name('status.json'),report)
        print(json.dumps(report,ensure_ascii=False,indent=2));return 2
    edition.update(profile=args.profile,quality=quality,window_hours=args.hours)
    atomic_json(output,edition);atomic_json(output.with_name('status.json'),report)
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':sys.exit(main())
