"""Immutable-source inventory and line-addressable reading. No source text is copied."""
from pathlib import Path
import argparse, hashlib, json, re

BASE = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\ZhuanZ（无密码）\OneDrive\Desktop\龙族旧版txt 共八册')
FILES = [
    ('I', '龙族I·火之晨曦.txt', 'utf-8-sig'),
    ('II', '龙族II·悼亡者之瞳.txt', 'utf-8-sig'),
    ('III上', '龙族III·黑月之潮(上).txt', 'gb18030'),
    ('III中', '龙族III·黑月之潮(中).txt', 'utf-16'),
    ('III下', '龙族III·黑月之潮(下).txt', 'gb18030'),
    ('II前传', '龙族II前传·哀悼之翼.txt', 'gb18030'),
]

def load(key):
    _, name, enc = next(x for x in FILES if x[0] == key)
    data = (SOURCE / name).read_bytes()
    return data.decode(enc, errors='strict').splitlines()

def headings(key, lines):
    result = []
    for number, line in enumerate(lines, 1):
        t = line.strip()
        is_heading = bool(re.match(r'^第[一二三四五六七八九十百零〇\d]+[章幕](?:\s|$)', t))
        is_heading |= bool(re.match(r'^龙族3黑月之潮下 第[一二三四五六七八九十]+幕', t))
        is_heading |= t.replace(' ', '') in {'序章', '序幕', '尾声'}
        if not is_heading: continue
        if key == 'II' and number < 143: continue  # printed contents
        if key == 'III中' and number < 26: continue
        title = t
        if re.fullmatch(r'(第[一二三四五六七八九十]+[章幕]|序\s*[章幕])', t) or (key == 'II' and t.replace(' ', '') == '尾声'):
            following = next((x.strip() for x in lines[number:number+8] if x.strip()), '')
            title += ' ' + following
        result.append({'heading_line': number, 'label_as_printed': title, 'status': 'printed_heading'})
    # These title-only boundaries were checked against nearby source lines.
    if key == 'III上':
        result.append({'heading_line': 4969, 'label_as_printed': '格陵兰阴影',
                       'status': 'title_only_number_missing', 'note': 'Position between printed chapter 10 and 12; do not invent number in source.'})
    result.sort(key=lambda x: x['heading_line'])
    for i, entry in enumerate(result):
        entry['unit_id'] = f'{key}-{i+1:02d}'
        entry['end_line'] = result[i+1]['heading_line']-1 if i+1 < len(result) else len(lines)
        entry['nonempty_line_count'] = sum(bool(x.strip()) for x in lines[entry['heading_line']-1:entry['end_line']])
    return result

def inventory():
    (BASE/'索引').mkdir(parents=True, exist_ok=True)
    manifest, paras, units = [], [], []
    for key, name, enc in FILES:
        data = (SOURCE/name).read_bytes()
        text = data.decode(enc, errors='strict')
        lines = text.splitlines()
        hs = headings(key, lines)
        manifest.append({'id': key, 'filename': name, 'path': str(SOURCE/name), 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(), 'encoding': enc,
                         'characters_including_line_endings': len(text), 'lines': len(lines),
                         'nonempty_lines': sum(bool(x.strip()) for x in lines),
                         'structural_units': len(hs), 'read_status': 'see separate progress.json'})
        units.extend(dict(book_id=key, **h) for h in hs)
        p = 0
        for n, line in enumerate(lines, 1):
            if not line.strip(): continue
            p += 1
            unit = next((h for h in hs if h['heading_line'] <= n <= h['end_line']), None)
            paras.append({'book_id': key, 'P': p, 'L': n, 'unit_id': unit['unit_id'] if unit else None})
    (BASE/'索引'/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for name, rows in [('chapter_index.jsonl', units), ('paragraph_index.jsonl', paras)]:
        (BASE/'索引'/name).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    md = ['# 文件内结构索引', '', '自动编号只表示文件顺序；不是对出版社章次的校订。III中第六章标题未检出，见核查记录。', '']
    for row in manifest:
        md += [f"## {row['filename']}", '', f"编码 `{row['encoding']}`；{row['lines']} 行；{row['structural_units']} 个已定位单元。", '']
        md += [f"- `{u['unit_id']}` L{u['heading_line']}–L{u['end_line']}：{u['label_as_printed']}" for u in units if u['book_id']==row['id']]
        md += ['']
    (BASE/'索引'/'文件与章节索引.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', choices=[x[0] for x in FILES])
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    args = ap.parse_args()
    if not args.book:
        inventory()
    else:
        lines = load(args.book)
        p = sum(bool(x.strip()) for x in lines[:args.start-1])
        for n in range(args.start, min(args.end,len(lines))+1):
            if lines[n-1].strip():
                p += 1
                print(f'L{n}/P{p}: {lines[n-1]}')
