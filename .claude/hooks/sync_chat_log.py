#!/usr/bin/env python3
"""Stop hook: render the session transcript to chat-logs/conversation.md, commit and push."""
import json, re, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOG = REPO / "chat-logs" / "conversation.md"
HEADER = "# 对话记录\n\n每次回复后由 Stop 钩子自动更新。\n"


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def clean(t):
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    return t.strip()


def render(path):
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("isSidechain") or e.get("isMeta"):
            continue
        m = e.get("message") or {}
        if e.get("type") == "user" and m.get("role") == "user":
            t = clean(text_of(m.get("content", "")))
            if t:
                out.append(f"### 🧑 用户 · {e.get('timestamp','')}\n\n{t}\n")
        elif e.get("type") == "assistant":
            c = m.get("content", [])
            t = clean(text_of(c))
            files = [b["input"].get("file_path") for b in c if isinstance(b, dict) and b.get("type") == "tool_use"
                     and b.get("name") in ("Write", "Edit") and b.get("input", {}).get("file_path")]
            if t:
                out.append(f"### 🤖 Claude · {e.get('timestamp','')}\n\n{t}\n")
            if files:
                out.append("> 修改文件: " + ", ".join(f"`{f}`" for f in files) + "\n")
    return "\n".join(out)


def git(*a, check=True):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True, check=check)


def main():
    data = json.load(sys.stdin)
    sid, tp = data.get("session_id", "unknown"), data.get("transcript_path")
    if not tp or not Path(tp).exists():
        return
    marker = f"<!-- session:{sid} -->"
    section = f"{marker}\n## 会话 {sid}\n\n{render(tp)}\n<!-- end:{sid} -->\n"
    old = LOG.read_text(encoding="utf-8") if LOG.exists() else HEADER
    pat = re.compile(re.escape(marker) + r".*?<!-- end:" + re.escape(sid) + r" -->\n", re.S)
    new = pat.sub(lambda _: section, old) if pat.search(old) else old.rstrip("\n") + "\n\n" + section
    if new == old and LOG.exists():
        return
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(new, encoding="utf-8")
    git("add", "chat-logs/conversation.md")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    git("commit", "-m", "chat-log: update conversation record")
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for d in (0, 2, 4, 8, 16):
        time.sleep(d)
        if git("push", "-u", "origin", branch, check=False).returncode == 0:
            break


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:  # never break the session
        print(f"sync_chat_log: {ex}", file=sys.stderr)
