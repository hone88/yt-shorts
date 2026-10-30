"""tools/voice/<名前>.json の各セリフを VOICEVOX で読み上げ、out/voice/<名前>/<リール>/<id>.wav に保存する。
JSON の形: {"speaker": 8, "speed": 1.15, "reels": {"r1": {"scenes": [{"id": "01", "say": "...", "speaker": 3}]}}}（scene の speaker・speed は省略可）"""
import json, os, sys, pathlib, urllib.request, urllib.parse

URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")


def synth(text, speaker, speed, path):
    q = urllib.parse.urlencode({"text": text, "speaker": speaker})
    with urllib.request.urlopen(urllib.request.Request(f"{URL}/audio_query?{q}", method="POST"), timeout=60) as r:
        query = json.load(r)
    query["speedScale"] = speed
    query["prePhonemeLength"] = 0.05
    query["postPhonemeLength"] = 0.2
    req = urllib.request.Request(f"{URL}/synthesis?speaker={speaker}", data=json.dumps(query).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        path.write_bytes(r.read())


for src in sys.argv[1:]:
    src = pathlib.Path(src)
    data = json.loads(src.read_text(encoding="utf-8"))
    for reel, body in data["reels"].items():
        out = pathlib.Path("out/voice") / src.stem / reel
        out.mkdir(parents=True, exist_ok=True)
        for s in body["scenes"]:
            synth(s["say"], s.get("speaker", data.get("speaker", 8)), s.get("speed", data.get("speed", 1.1)), out / f"{s['id']}.wav")
            print(reel, s["id"], "OK")
