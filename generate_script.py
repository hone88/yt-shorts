"""台本を作る。CHANNEL（ai1h / moshimo）ごとに channels/<名前>/ の型とテーマを使う。
ANTHROPIC_API_KEY があれば Claude API で生成し、2回目の呼び出しで事実の誤りをチェックする。
キーがなければ channels/<名前>/sample.json を使う。"""
import json, os, sys, urllib.request, datetime, pathlib

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
CHANNEL = os.environ.get("CHANNEL", "ai1h")
CH_DIR = pathlib.Path("channels") / CHANNEL
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "out/script.json")

CHECK_PROMPT = """次のショート動画の台本を、科学・事実の観点から厳しくチェックしてください。
- 明らかな誤り、言い過ぎ、根拠の弱い数字、誤解を招く表現を挙げる
- 直すべき箇所は修正案も出す
- 問題がなければ issues を空にする

台本:
{script}

次のJSONだけを返してください:
{{"issues": [{{"scene": 番号(1始まり), "problem": "何が問題か", "fix": "修正案"}}], "fixed_scenes": 修正を反映したscenes配列（問題がなければ元と同じ）}}"""


def pick_topic() -> str:
    f = CH_DIR / "topics.txt"
    topics = [t.strip() for t in f.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]
    return topics[datetime.date.today().toordinal() % len(topics)]


def ask_claude(prompt: str) -> dict:
    body = json.dumps({"model": MODEL, "max_tokens": 3000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        text = json.load(r)["content"][0]["text"].strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


def from_queue():
    """channels/<名前>/queue/ に台本JSONがあれば、一番古いものを使って used/ へ移す。
    APIキーなしで回すときは、ここに台本を置いておく（Claudeのスケジュールタスクや手作業で）。"""
    q = CH_DIR / "queue"
    want = os.environ.get("SCRIPT_ID")
    if want:
        # クリップをアップロードしたときは、そのクリップ用の台本を名前で選ぶ
        for f in (q / f"{want}.json", CH_DIR / "used" / f"{want}.json"):
            if f.exists():
                script = json.loads(f.read_text(encoding="utf-8"))
                script["id"] = want
                if f.parent == q:
                    used = CH_DIR / "used"; used.mkdir(exist_ok=True)
                    f.rename(used / f.name)
                print(f"台本 {want} を使います")
                return script
        raise SystemExit(f"台本 {want}.json が queue にも used にも見つかりません")
    files = sorted(q.glob("*.json")) if q.exists() else []
    if not files:
        return None
    f = files[0]
    script = json.loads(f.read_text(encoding="utf-8"))
    used = CH_DIR / "used"; used.mkdir(exist_ok=True)
    f.rename(used / f.name)
    script["id"] = f.stem
    print(f"キューの台本を使います: {f.name}（残り {len(files) - 1} 本）")
    return script


def main():
    topic = pick_topic()
    queued = from_queue()
    if queued:
        script = queued
        script.setdefault("factcheck", [])
        topic = script.get("topic", script["title"])
    elif os.environ.get("ANTHROPIC_API_KEY"):
        prompt = (CH_DIR / "prompt.txt").read_text(encoding="utf-8").format(topic=topic)
        script = ask_claude(prompt)
        check = ask_claude(CHECK_PROMPT.format(script=json.dumps(script["scenes"], ensure_ascii=False, indent=1)))
        if check.get("fixed_scenes"):
            script["scenes"] = check["fixed_scenes"]
        script["factcheck"] = check.get("issues", [])
    else:
        print("ANTHROPIC_API_KEY がないのでサンプル台本を使います")
        script = json.loads((CH_DIR / "sample.json").read_text(encoding="utf-8"))
        script["factcheck"] = []
        topic = "（サンプル）" + script["title"]
    script["topic"] = topic
    script["channel"] = CHANNEL
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{CHANNEL}] 台本: {script['title']}（{len(script['scenes'])}シーン、指摘 {len(script['factcheck'])} 件を修正済み）")


if __name__ == "__main__":
    main()
