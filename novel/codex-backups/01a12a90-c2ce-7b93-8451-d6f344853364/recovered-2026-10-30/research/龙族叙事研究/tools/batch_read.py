from pathlib import Path
import json,sys,hashlib
B=Path(__file__).resolve().parents[1]
plan=json.loads((B/'批次记录'/('batch_'+(sys.argv[2] if len(sys.argv)>2 else '002')+'_plan.json')).read_text(encoding='utf-8'))
manifest=json.loads((B/'索引/source_manifest.json').read_text(encoding='utf-8'))
m=next(x for x in manifest if x['id']=='II')
raw=Path(m['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest()==m['sha256'],'Source changed; rebuild and compare index first'
lines=raw.decode(m['encoding']).splitlines()
n=int(sys.argv[1]);c=plan['chunks'][n-1]
print(f"ORIGINAL II CHUNK {n}/{len(plan['chunks'])} L{c['start']}-{c['end']} (blank lines omitted, other text unabridged)")
for i in range(c['start'],c['end']+1):
 if lines[i-1].strip():print(f'[{i}] {lines[i-1]}')
print(f"END CHUNK {n} L{c['end']}; next L{c['end']+1}. Printing does not mark read.")
