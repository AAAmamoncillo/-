from pathlib import Path
import os,json,subprocess,tempfile,hashlib,shutil
B=Path(__file__).resolve().parents[1]
OLD=Path('D:/1/ChatGPT/魔女不会死/research/龙族叙事研究')
for f in B.rglob('*'):
 if f.is_file() and '__pycache__' not in f.parts:
  target=OLD/f.relative_to(B);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
env=os.environ.copy();env['GH_CONFIG_DIR']='C:/Users/ZhuanZ（无密码）/Documents/Codex/2026-10-11/zhe/work/github-auth'
repo='repos/AAAmamoncillo/-'
branch='claude/chat-docs-realtime-sync-4hki3a'
prefix='novel/codex-backups/01a12a90-c2ce-7b93-8451-d6f344853364/recovered-2026-10-30/research/龙族叙事研究/'
def api(path,method='GET',body=None):
 args=['gh','api',repo+'/'+path,'--method',method]
 temp=None
 try:
  if body is not None:
   with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',delete=False,suffix='.json') as t:
    json.dump(body,t,ensure_ascii=False);temp=t.name
   args+=['--input',temp]
  run=subprocess.run(args,env=env,capture_output=True,encoding='utf-8',check=True)
  return json.loads(run.stdout)
 finally:
  if temp:Path(temp).unlink()
files=[];expected={}
for f in sorted(B.rglob('*')):
 if f.is_file() and f.suffix in ['.md','.json','.jsonl','.py'] and '__pycache__' not in f.parts:
  data=f.read_text(encoding='utf-8');path=prefix+f.relative_to(B).as_posix()
  files.append({'path':path,'mode':'100644','type':'blob','content':data})
  raw=data.encode('utf-8');expected[path]=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
head=api('git/ref/heads/'+branch)['object']['sha']
base=api('git/commits/'+head)['tree']['sha']
tree=api('git/trees','POST',{'base_tree':base,'tree':files})['sha']
commit=api('git/commits','POST',{'message':'Research: complete Dragon Raja II reading, batch workflow and scene index','tree':tree,'parents':[head]})['sha']
api('git/refs/heads/'+branch,'PATCH',{'sha':commit,'force':False})
actual={x['path']:x['sha'] for x in api('git/trees/'+tree+'?recursive=1')['tree'] if x['type']=='blob'}
assert all(actual.get(k)==v for k,v in expected.items())
assert api('git/ref/heads/'+branch)['object']['sha']==commit
print(json.dumps({'mirror':str(OLD),'files_verified':len(files),'commit':commit,'originals_uploaded':False},ensure_ascii=False))
