import argparse, base64, hashlib, json, os, re, subprocess, time, zipfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
OLD = Path('C:/Users/ZhuanZ（无密码）/Documents/Codex/2026-10-11/zhe')
GH = OLD/'work/github-cli/portable/bin/gh.exe'
ENV = dict(os.environ, GH_CONFIG_DIR=str(OLD/'work/github-auth'), GH_PROMPT_DISABLED='1')
SID = '01a12a90-c2ce-7b93-8451-d6f344853364'
SESSION = Path('C:/Users/ZhuanZ（无密码）/.codex/sessions/2026/10/11')/f'rollout-2026-10-11T18-44-54-{SID}.jsonl'
REPO = 'AAAmamoncillo/-'
BRANCH = 'claude/chat-docs-realtime-sync-4hki3a'
BASE = 'novel/codex-backups/'+SID
STATE = ROOT/'work/sync-state.json'
LOG = ROOT/'work/sync-status.log'
PREFIX = 'repos/'+REPO+'/'
SOURCE = Path('D:/222/魔女不会死相关')
NAMES = ['00_读我_项目入口与阅读顺序.md','01_当前设定集.md','02_现行20章概要与续写起点.md','03_第一卷及后续大纲.md','04_修订说明与章节对照.md','05_文风样章_第01章_门外的歌声.md','06_文风样章_第13章_多一副碗筷.md','07_文风样章_第20章_你回来正好.md','novel-notes.txt','魔女不会死_精简前长稿_01-27章 (2).txt','魔女不会死_精简前长稿_01-27章.txt','魔女不会死修改版.docx']

def log(message):
    line=time.strftime('%Y-%m-%d %H:%M:%S')+' '+message
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')
    print(line,flush=True)

def api(endpoint, data=None, method='POST'):
    args=[str(GH),'api',PREFIX+endpoint]
    if data is not None:
        request=ROOT/'work/api-request.json'
        request.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        args+=['--method',method,'--input',str(request)]
    r=subprocess.run(args,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',timeout=180,creationflags=0x08000000)
    if r.returncode: raise RuntimeError(r.stderr.strip()[:1000])
    return json.loads(r.stdout)

def gitsha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def snapshot():
    messages=[]; images={}
    for line in SESSION.read_text(encoding='utf-8').splitlines():
        try: e=json.loads(line)
        except ValueError: continue
        p=e.get('payload',{})
        if e.get('type')!='response_item' or p.get('type')!='message' or p.get('role') not in ('user','assistant'): continue
        if p['role']=='assistant' and p.get('channel') not in ('commentary','final',None): continue
        text='\n'.join(b.get('text','') for b in p.get('content',[]) if b.get('type') in ('input_text','output_text','text'))
        text=re.sub(r'<environment_context>.*?</environment_context>|<external_codex_apps_open_page>.*?</external_codex_apps_open_page>|<in-app-browser-context.*?</in-app-browser-context>','',text,flags=re.S).strip()
        if not text: continue
        if p['role']=='user':
            for match in re.finditer(r'[A-Za-z]:[/\\][^\r\n<>"\u0000]+?\.png',text):
                source=Path(match.group().strip())
                if source.is_file(): images[source.name]=source
        messages.append(f"### {'🧑 用户' if p['role']=='user' else '🤖 Codex'} · {e.get('timestamp','')}\n\n{text}\n")
    transcript='# Codex 小说协作聊天记录\n\n本聊天可见的用户消息、助手回复与进度说明；不包含系统提示、内部推理、工具原始日志或登录凭据。时间戳为 UTC。\n\n'+'\n'.join(messages)
    files={}
    archive=OLD/'outputs/魔女不会死_聊天与原始资料_GitHub同步待上传备份.zip'
    for name in NAMES:
        path=BASE+'/user-files/'+name
        if (SOURCE/name).exists(): files[path]=(SOURCE/name).read_bytes()
        else:
            with zipfile.ZipFile(archive) as z: files[path]=z.read(path)
    for directory in (OLD/'outputs', ROOT/'outputs'):
        if not directory.exists(): continue
        for source in directory.iterdir():
            if source.suffix.lower() not in ('.docx','.md','.pdf','.txt'): continue
            files[BASE+'/generated/'+source.name]=source.read_bytes()
            transcript=transcript.replace(str(source),BASE+'/generated/'+source.name).replace(str(source).replace('\\','/'),BASE+'/generated/'+source.name)
    for name,source in images.items():
        files[BASE+'/images/'+name]=source.read_bytes()
        transcript=transcript.replace(str(source),BASE+'/images/'+name).replace(str(source).replace('\\','/'),BASE+'/images/'+name)
    previous=OLD/'work/previous_reply.txt'
    if previous.exists():
        chapter=previous.read_text(encoding='utf-8').split('\n——\n',1)[1].rsplit('\n——\n',1)[0].strip()
        files[BASE+'/generated/第15章_我答应过你_精修正文.md']=('# 第十五章 我答应过你\n\n'+chapter+'\n').encode('utf-8')
    for name in NAMES:
        source=SOURCE/name
        transcript=transcript.replace(str(source),BASE+'/user-files/'+name).replace(str(source).replace('\\','/'),BASE+'/user-files/'+name)
    files['chat-logs/codex-'+SID+'.md']=transcript.encode('utf-8')
    index='# Codex 小说协作备份\n\n保存本聊天记录、作者提供的原始资料、生成的章节文档和用户截图。原始资料与精修试稿分目录保存，不覆盖仓库里的小说版本。\n\n[聊天记录](../../../chat-logs/codex-'+SID+'.md)\n\n本地同步器在运行和联网时，每15秒检查变化；失败保留本地文件并重试。电脑重启后需重新启动同步器。它不会上传登录凭据、内部提示、内部推理或工具原始日志。\n\n| 文件 | 字节数 | SHA256 |\n| --- | ---: | --- |\n'
    for path,raw in sorted(files.items()):
        if path.startswith(BASE+'/'):
            rel=path[len(BASE)+1:]
            index+=f'| [{rel}]({quote(rel,safe="/")}) | {len(raw)} | `{hashlib.sha256(raw).hexdigest()}` |\n'
    files[BASE+'/README.md']=index.encode('utf-8')
    files[BASE+'/tools/sync_github.py']=Path(__file__).read_bytes()
    digest=hashlib.sha256(''.join(path+gitsha(raw) for path,raw in sorted(files.items())).encode()).hexdigest()
    return files,transcript,len(messages),digest

def sync():
    files,transcript,count,digest=snapshot()
    state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    if state.get('digest')==digest: return
    # Always preserve the newest remote tree and other chat sessions.
    head=api('git/ref/heads/'+quote(BRANCH,safe=''))['object']['sha']
    tree=api('git/commits/'+head)['tree']['sha']
    remote={e['path']:e for e in api('git/trees/'+tree+'?recursive=1')['tree']}
    entry=remote['chat-logs/conversation.md']
    oldblob=api('git/blobs/'+entry['sha'])
    old=base64.b64decode(oldblob['content']).decode('utf-8')
    start='<!-- session:codex-'+SID+' -->'; end='<!-- end:codex-'+SID+' -->'
    section=start+'\n## Codex 小说协作 '+SID+'\n\n'+transcript+'\n'+end+'\n'
    if start in old:
        a=old.index(start); b=old.index(end,a)
        old=old[:a]+section+old[b+len(end):]
    else: old=old.rstrip()+'\n\n'+section
    files['chat-logs/conversation.md']=old.encode('utf-8')
    # Keep a complete local mirror before attempting any writes.
    mirror=ROOT/'work/github-mirror'
    for path,raw in files.items():
        target=mirror/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
    known={e['sha'] for e in remote.values() if e['type']=='blob'}
    entries=[]
    for path,raw in files.items():
        sha=gitsha(raw)
        if path in remote and remote[path]['sha']==sha: continue
        if sha not in known:
            result=api('git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'})
            if result['sha']!=sha: raise RuntimeError('Blob integrity mismatch: '+path)
            known.add(sha)
        entries.append({'path':path,'mode':'100644','type':'blob','sha':sha})
    if entries:
        newtree=api('git/trees',{'base_tree':tree,'tree':entries})['sha']
        commit=api('git/commits',{'message':f'备份 Codex 小说协作：{count}条消息与文档','tree':newtree,'parents':[head]})['sha']
        # force=false prevents overwriting concurrent commits from another client.
        api('git/refs/heads/'+quote(BRANCH,safe=''),{'sha':commit,'force':False},method='PATCH')
        verify={e['path']:e['sha'] for e in api('git/trees/'+newtree+'?recursive=1')['tree'] if e['type']=='blob'}
        assert all(verify.get(path)==gitsha(raw) for path,raw in files.items())
        actual=api('git/ref/heads/'+quote(BRANCH,safe=''))['object']['sha']
        if actual!=commit: raise RuntimeError('Branch advanced during verification; retry needed')
    else: commit=head
    STATE.write_text(json.dumps({'digest':digest,'commit':commit,'messages':count,'files':len(files),'updated':time.strftime('%Y-%m-%d %H:%M:%S')},ensure_ascii=False,indent=2),encoding='utf-8')
    log(f'OK commit={commit} messages={count} files={len(files)} verified')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--watch',action='store_true'); args=parser.parse_args()
    if not args.watch: sync(); return
    log('Watcher started; poll=15s')
    while True:
        try: sync()
        except Exception as e: log('FAILED '+str(e)[:700])
        time.sleep(15)

if __name__=='__main__': main()
