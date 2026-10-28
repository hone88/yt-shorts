"""各シーンの読み上げ音声を作る。VOICEVOX エンジンがあればそれを使い、なければ無音で長さだけ合わせる。"""
import json, os, sys, urllib.request, urllib.parse, pathlib, wave, struct

VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "11"))  # 11 = 玄野武宏（ノーマル）
SPEED = float(os.environ.get("VOICEVOX_SPEED", "1.15"))


def voicevox(text: str, path: pathlib.Path) -> None:
    q = urllib.parse.urlencode({"text": text, "speaker": SPEAKER})
    req = urllib.request.Request(f"{VOICEVOX_URL}/audio_query?{q}", method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        query = json.load(r)
    query["speedScale"] = SPEED
    query["postPhonemeLength"] = 0.25
    req = urllib.request.Request(
        f"{VOICEVOX_URL}/synthesis?speaker={SPEAKER}",
        data=json.dumps(query).encode(), headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        path.write_bytes(r.read())


def silent(text: str, path: pathlib.Path) -> None:
    secs = max(2.0, len(text) * 0.13)
    rate = 24000
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(struct.pack("<h", 0) * int(secs * rate))


def engine_up() -> bool:
    try:
        urllib.request.urlopen(f"{VOICEVOX_URL}/version", timeout=5)
        return True
    except Exception:
        return False


def main():
    script_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "out/script.json")
    out_dir = script_path.parent / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    global SPEAKER
    style_file = pathlib.Path("channels") / script.get("channel", "ai1h") / "style.json"
    if style_file.exists() and "VOICEVOX_SPEAKER" not in os.environ:
        SPEAKER = int(json.loads(style_file.read_text(encoding="utf-8")).get("voice_speaker", SPEAKER))
    use_vv = engine_up()
    if not use_vv:
        print("VOICEVOX エンジンに接続できないので、無音のプレビュー音声を作ります")
    for i, s in enumerate(script["scenes"]):
        p = out_dir / f"{i:02d}.wav"
        (voicevox if use_vv else silent)(s["narration"], p)
    script["voiced"] = use_vv
    script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"音声 {len(script['scenes'])} 本を作成（VOICEVOX: {'あり' if use_vv else 'なし'}）")


if __name__ == "__main__":
    main()
