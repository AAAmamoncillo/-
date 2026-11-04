from pathlib import Path
import json,sys
B=Path(__file__).resolve().parents[1]
unit,summary,scenes=sys.argv[1:4]
batch=sys.argv[4] if len(sys.argv)>4 else '002'
units=[json.loads(s) for s in (B/'索引/chapter_index.jsonl').read_text(encoding='utf-8').splitlines()]
u=next(x for x in units if x['unit_id']==unit)
progress=json.loads((B/'progress.json').read_text(encoding='utf-8'))
record={'unit_id':unit,'title':u['label_as_printed'],'start_line':u['heading_line'],'end_line':u['end_line'],'summary':summary,'scene_candidates':scenes,'status':'level_1_original_read_complete','date':'2026-11-04'}
path=B/'批次记录'/('batch_'+batch+'_read_log.jsonl')
prior=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
prior=[r for r in prior if r['unit_id']!=unit]+[record]
path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in prior),encoding='utf-8')
progress['completed_units']=[x for x in progress['completed_units'] if x['unit_id']!=unit]+[{k:record[k] for k in ['unit_id','start_line','end_line','status']}]
progress['continuous_read_range']['end_line']=u['end_line']
nextunit=next((x for x in units if x['book_id']=='II' and x['heading_line']==u['end_line']+1),None)
progress['next']={'unit_id':nextunit['unit_id'],'start_line':nextunit['heading_line'],'end_line':nextunit['end_line']} if nextunit else None
progress['canonical_research_directory']=str(B)
progress['current_batch']='batch_'+batch
(B/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded complete',unit,'through L'+str(u['end_line']))
