# ASSET_AND_CODE_GUIDE｜ファイル・コード・実行環境

## 1. つなぎ方（新しいウィンドウで最初に）
1. `add_repo`（owner: hone88, repo: yt-shorts, access: **push**）
2. `git clone --depth 1 https://github.com/hone88/yt-shorts /home/claude/yt-shorts-repo`（大きい動画が多いので浅く）
3. コミット：`git -c user.name=hone88 -c user.email=hone88@users.noreply.github.com commit`、最後に会話で指定される帰属行（Co-Authored-By など）
4. push前：`git pull -q --rebase https://github.com/hone88/yt-shorts main`（変更があれば stash してから）→ `git push origin HEAD:main`
5. gh は REST だけ使う（`gh api repos/hone88/yt-shorts/...`）。GraphQL・release の作成は使えない（403）。

## 2. リポジトリの中身（もしもの続きに関係するところ）
```
yt-shorts/
├─ render.py            # 字幕・見出し・時刻バッジ・点を重ねて動画にする（11/9：改行対応）
├─ tts.py               # VOICEVOX の声。scene["lines"] で話者を切りかえ（11/8〜）
├─ images.py / generate_script.py / make_short.sh
├─ .github/workflows/
│   ├─ moshimo.yml      # clips に push すると自動で組み立て（手動 dispatch も可）
│   ├─ ai1h.yml / _make.yml  # AI副業チャンネル（月水金7:13自動）
│   └─ voice.yml        # 別プロジェクト（ドットジェイピー）の声だけ作る
├─ channels/moshimo/
│   ├─ queue/   # これから使う台本（使うと used/ に移る）
│   ├─ used/    # 使った台本 20261030〜20261116
│   ├─ clips/<台本ID>/01.mp4〜  # 背景クリップ（push で自動ビルド）
│   ├─ design/kaguya/sheet1〜3.png  # パロディのデザイン定義シート
│   ├─ sample.json / prompt.txt / style.json / topics.txt
├─ moshimo_tools/
│   ├─ voxel.py         # マイクラ風3Dの描画エンジン（Scene, render, particles, finish 等）
│   ├─ elevator_voxel.py  # person(), put(), draw_x(), finish(), shake() など共通部品
│   ├─ suika/car2/friction/hole/kaguya/kaguya2_voxel.py など  # 各回の映像（見本）
│   ├─ taiyou_sound.py  # 音の部品（lofi, boom, whoosh, sparkle, chime_end, put, env, lp, noise …）
│   ├─ <回>_sound.py    # 各回の効果音（taiyou_sound.py の compose より前を exec して使う）
│   ├─ mix.py           # 完成版の音（BGM一定・声より12dB小さく・-14 LUFS）
│   └─ README.md / 作り方プロンプト.md（【旧設定】を含む。ダッキングの部分は古い）
├─ finals/              # 完成版MP4（BGM入り）とアイコン（11/9保存）
├─ handoff/             # この引き継ぎ資料
├─ dotjp_reels/ loop_drama/ tools/voice/  # 別プロジェクト（ドットジェイピー）。触らない
```

## 3. よく使うコマンド
- 静止画で確認：`cd <作業フォルダ> && python3 /home/claude/yt-shorts-repo/moshimo_tools/<回>_voxel.py stills 0:0.3,2:5.0`
- 書き出し（2本同時、run_in_background）：`python3 x.py 0,2,4 > r1.log 2>&1 & python3 x.py 1,3,5 > r2.log 2>&1 & wait`
- 作り直し（台本が used にあるとき）：`gh api -X POST repos/hone88/yt-shorts/actions/workflows/moshimo.yml/dispatches -f ref=main -f "inputs[script_id]=<台本ID>"`
- 完成待ち：最新リリースの **tag_name が変わるまで** 20秒おきに確認（created_at で判定しない）。失敗したら `actions/runs` → `jobs/<id>/logs` でエラーを見る。最後の push だけ失敗することがある（もう一度 dispatch）。
- クリップを**差しかえた**（同じ名前で上書き）ときは自動の組み立てが動かない（追加・名前変更だけ拾う）。上の dispatch で台本IDを指定して作り直す【11/9 確認】。
- ダウンロード：`gh api -H "Accept: application/octet-stream" repos/hone88/yt-shorts/releases/assets/<id> > short.mp4`
- シーン開始時刻：上の進捗の点（y≈215〜245px、黄色の大きい点の位置）か、見出しの変化を測る。
- 音：`python3 <回>_sound.py taiyou_sound.py <動画の長さ> <S0,S1,...>` → `python3 mix.py short.mp4 bgm.wav sfx.wav 完成.mp4 12`
- 赤い×の位置合わせ：中央を切り出して赤（R>210, G/B<100）が出るコマを探し、XFRAC を調整。

## 4. 環境
- Python 3（numpy, Pillow）、ffmpeg/ffprobe、日本語フォント Noto Sans CJK（/usr/share/fonts/opentype/noto/）。
- 声：GitHub Actions 上の VOICEVOX エンジン（Dockerサービス）。話者 13 青山龍星、2 四国めたん ノーマル、12 白上虎太郎 ふつう。
- APIキー：使っていない（ANTHROPIC/OPENAI は任意設定。queue に台本があれば不要）【要確認：Secretsの有無】。
- コンテナから TikTok・YouTube の画面は見られない（403/許可外）。WebFetch で note は見られる。

## 5. 作業フォルダの残り物（このコンテナだけにある。新しいウィンドウには無い）
- /home/claude/day5〜day12：noteの原稿・見出し画像・切り抜き（12日目以外は投稿済み）
- /home/claude/rel*：各回のビルド結果。完成版は finals/ にコピー済み
- 見出し画像の作り方：`/home/claude/day5/eye.py` と同じ。下に全文を残す。

```python
# note見出し画像（1280×670）。title1/2・hl（水色にする部分）・日目を変える
from PIL import Image, ImageDraw, ImageFont
W, H = 1280, 670; day = 12
img = Image.new("RGB", (W, H), "#0F172A"); d = ImageDraw.Draw(img)
for i, c in enumerate(["#13213B", "#16294A"]):
    r = 560 - i * 70; d.ellipse([W-120-r, H/2-r, W-120+r, H/2+r], fill=c)
B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; F = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
fb = ImageFont.truetype(F, 40); ft = ImageFont.truetype(B, 84); fs = ImageFont.truetype(F, 32); x = 110
d.rounded_rectangle([x, 120, x+270, 190], 35, outline="#22D3EE", width=4)
d.text((x+135, 155), f"実験{day}日目", font=fb, fill="#22D3EE", anchor="mm")
d.text((x, 290), "同じ作り方でも、", font=ft, fill="#F8FAFC", anchor="lm")
pre = "摩擦は"; d.text((x, 400), pre, font=ft, fill="#F8FAFC", anchor="lm")
d.text((x + d.textlength(pre, font=ft), 400), "2時間で止まった", font=ft, fill="#22D3EE", anchor="lm")
d.text((x, 500), "1日1時間で回すAI副業の仕組み", font=fs, fill="#94A3B8", anchor="lm")
d.rounded_rectangle([x, 555, x+600, 567], 6, fill="#1E293B")
d.rounded_rectangle([x, 555, x+600*day/30, 567], 6, fill="#22D3EE")
img.save(f"eyecatch_day{day}.png")
```
