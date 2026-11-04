from pathlib import Path
import json,re,hashlib,shutil
B=Path(__file__).resolve().parents[1]
def js(p): return json.loads(p.read_text(encoding='utf-8'))
units=[json.loads(x) for x in (B/'索引/chapter_index.jsonl').read_text(encoding='utf-8').splitlines()]
logs=[]
for batch in ['002','003']:
 p=B/f'批次记录/batch_{batch}_read_log.jsonl'
 logs.extend(json.loads(x) for x in p.read_text(encoding='utf-8').splitlines())
assert len(logs)==20 and len({x['unit_id'] for x in logs})==20
for r in logs:
 if r['unit_id']=='II-20':
  r['summary']=r['summary'].replace('芬吞噬她后重生发动毁灭言灵','芬把她卷入口中，现场被解释为吞噬并重生，随后发动毁灭言灵；此解释在第二十幕末被推翻')
for batch in ['002','003']:
 selected=[r for r in logs if (int(r['unit_id'].split('-')[1])<=12)==(batch=='002')]
 (B/f'批次记录/batch_{batch}_read_log.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8')
manifest=js(B/'索引/source_manifest.json')
for f in manifest:
 assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['id']
source=next(f for f in manifest if f['id']=='II')
lines=Path(source['path']).read_text(encoding=source['encoding']).splitlines()
p=js(B/'progress.json')
p.update(read_nonempty_line_characters=sum(len(x) for x in lines[142:]),level_1_complete_units=22,current_batch_status='complete: batches 002 and 003, 20 additional units; volume II complete; other volumes unread',completed_volumes=['II'],whole_work_read=False,cross_volume_conclusions_ready=False)
n=next(u for u in units if u['book_id']=='III上')
p['next']={'book':'III上','unit_id':n['unit_id'],'start_line':n['heading_line'],'end_line':n['end_line'],'status':'not_read'}
p['actual_read_packets']['batch_003']={'packet_ids':list(range(1,22)),'continuous_range':[7729,13444],'all_packet_endpoints_reached':True,'output_truncated':False}
p['canonical_research_directory']=str(B)
(B/'progress.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cards=[]
md=['# 人物与场景索引','', '第二部序幕至尾声原文已连续通读；本页汇集新增第二至第二十幕及尾声20单元。序幕、第一幕详见旧02索引及精读文件。下列卡片是定位记录，尚非全部完成文学精读。','', '## 人物关系：卷末状态','', '| 关系 | 变化及证据 |','|---|---|','| 路—楚 | 从借光、自卑，到看见彼此的孤独并返回救人。楚的保护真诚，也替路安排逃亡；路并未因此只有感激。L12867–12927、L12975–12993。 |','| 楚—夏 | 学术与玩笑、照料、身份欺骗、互相攻击同时成立。她称夏弥人生全假，空屋中的生活物件却让这个断言无法简单收束。L12311–12349、L13341–13395。 |','| 夏—芬 | 她的爱不能消除养作食物的计划；他口含妹妹被解释为吞噬，末段才揭示保护。L12065–12129、L12425–12445、L13179–13191。 |','| 路—诺 | 关照真实，恋爱归属并不因此归路；生日短信被隐藏使受遗弃感加深，找回短信纠正了他的部分判断。L10295–10311、L12803–12823、L12901–12917、L13017–13019。 |','| 恺撒—家族—帕西 | 家族关爱含支配和预选，恺撒拒绝被作诱饵但可主动担风险；承认帕西个人的人情，后者仍认自己为他而生。L12711–12729、L13159–13169、L13421–13439。 |','| 路—陈—赵—柳 | 陈的求助含信任和失恋需要；路帮忙仍受伤。复合没有抹去催眠干预和柳的可能失落。L10651–10705、L13309–13327。 |','| 幕后保护者 | 帮助、利用、安排牺牲并存；魔鬼的独白与人物动机不能作作者客观定论。L9645–9657、L10811–10835、L12155–12175。 |','', '## 连续通读短记录','']
for r in logs:
 md.extend([f"### {r['title']} / {r['unit_id']}",'',f"原文L{r['start_line']}–L{r['end_line']}。{r['summary']}",''])
 for s in r['scene_candidates'].split('；'):
  ranges=[[int(a),int(b)] for a,b in re.findall(r'L(\d+)[–-](\d+)',s)]
  if not ranges:
   ranges=[[int(a),int(a)] for a in re.findall(r'L(\d+)',s)]
  assert ranges,s
  assert all(143<=a<=b<=13444 for a,b in ranges),s
  card={'scene_id':f'II-S{len(cards)+1:03d}','unit_id':r['unit_id'],'chapter':r['title'],'ranges':ranges,'question':s,'level_1':'original_read','level_2':'queued','book':'II'}
  cards.append(card)
  md.append(f"- {card['scene_id']}：{s}")
 md.append('')
(B/'人物与场景索引.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
(B/'索引/scene_index.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in cards),encoding='utf-8')
count=p['read_nonempty_line_characters']
progress=f'''# 阅读进度

更新：2026-11-04。以本文件和progress.json为准，旧编号进度为历史快照。

已连续阅读《龙族II·悼亡者之瞳》原文L143–L13444：序幕、20幕、尾声，共22个章节单元。累计非空行字符{count:,}（含标题标点，非纯汉字数）。本轮新增第二幕至尾声20单元，两批分别10单元；并非本轮只读一两章。

一级索引新增{len(cards)}张场景卡。首批序幕与第一幕已有二级精读；本轮20单元仅完成原文通读与简记，精选场景仍待二级精读。读取脚本不自动宣称模型读完。

断点：第二部已结束。下一处为第三部上册{n['label_as_printed']}，原文L{n['heading_line']}–L{n['end_line']}，尚未阅读。随后顺序III中、III下、I、II前传。

其余五文件目前只有结构清点和边界抽查，不能宣称通读全系列。91定位单元不是权威全书章数；第三部中缺章题、下册重复章题、上册仅标题单元仍待随通读核查。第二部文本中的年代及个别金额矛盾不自行改写，待版本核查。

证据：索引/chapter_index.jsonl与paragraph_index.jsonl，批次记录/batch_002_read_log.jsonl、batch_003_read_log.jsonl。L为原TXT行号，含空行；原文件指纹全部复核一致。

输出截断记录：批次002合并输出曾截断，原文L3339–3479已单独补读。后续改为每次一份受控原文包；批次003共21包，末包已到L13444。
'''
(B/'阅读进度.md').write_text(progress,encoding='utf-8')
(B/'README.md').write_text('''# 《龙族》文学研究

主目录为桌面“龙族文学研究”，D盘研究目录为镜像。原著保留原处，不修改、不随笔记上传。

第二部已通读：序幕、20幕、尾声，共22单元。本轮新增20单元；其他卷尚未通读，不能作全系列结论。

- [阅读进度](阅读进度.md)：覆盖范围、断点、未完成事项。
- [人物与场景索引](人物与场景索引.md)：逐章短记录与场景位置。
- [第二部呼应与判断修正](第二部_呼应与判断修正.md)：卷内核查及精读问题。
- [原著入口](原著入口.md)：六文件位置与编码。
- [执行策略](执行策略_批量通读优先.md)：瓶颈诊断、批量阅读及两级档案。
- [机器进度](progress.json)：恢复入口。
- [章节索引](索引/文件与章节索引.md)：完整文件清点及版本疑点。

文学技巧研究目录保存集中精读候选；精读目录保留首批两篇。旧00至04及01_阅读进度.md为历史记录，以当前阅读进度为准。

L是原TXT行号（含空行）；P是非空行定位序号。涉及细节须重新打开原文，不能以索引摘要替代阅读。人物自述、现场推测、后文揭示须分别记录。
''',encoding='utf-8')
print(json.dumps({'completed_units':22,'new_units':20,'scene_cards':len(cards),'characters':count,'next':p['next'],'source_hashes_verified':6},ensure_ascii=False))
