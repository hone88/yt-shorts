# ASSET_AND_CODE_GUIDE — ファイル・コード・実行方法

リポジトリ：**`hone88/yt-shorts`**（main）。ガクチカ・ループは **`loop_drama/`**。同じリポジトリの他のフォルダ（`dotjp_reels/`・`moshimo_tools/`・`channels/` など）とワークフロー（`_make.yml`・`ai1h.yml`・`moshimo.yml`）は別企画なので触らない。他のチャットも同じリポジトリに push するので、**push の前に必ず `git pull --rebase`**。

## 1. 必要なもの
- Python 3（Pillow・numpy）、ffmpeg、gh（GitHub CLI。声の作成を手動で起動するとき）
- フォント：リポジトリの `fonts/`（Noto Sans CJK Black/Bold。`ep1b.py` の `O.F(BLACK, size)` / `O.F(BOLD, size)` で使う）
- 環境づくり：`tools/setup.sh`

## 2. loop_drama/ の中身
| ファイル | 役割 |
| --- | --- |
| `characters.py` | キャラクター定義書（寸法・色・8×8の顔・表情）。`KANATA`・`KANATA_SUIT`・`MIO`・`INTERVIEWER`・`MORISHITA`・`RECEPTION`・`HARUTO`・`HOST`・`HR`・`LOCAL`・`KID`・`JUDGE`・`TEAM_A/B`、`tokei_boxes()`。表情 `KANATA_EXPR` に `resolve`（決心）・`sleep` を追加済み |
| `g3d.py` | ブロック3Dの描画。`Camera(位置, 注視点, 画角)`、`Rig(キャラ, 位置, 向き, tag)`、`render(boxes, cam, 背景, keep={...})` → (画像, マスク) |
| `engine.py` | `lerp`・`ease`・`fit_text`・`paste_center`・`pop`・`sky` など |
| `ep1b.py`（O） | 文字：`clock_big`（`CLOCK_Y=260`）・`counter`・`caption`・`rich_line`・`SPEAK`・`Shot`・`desat`・`glitch`・`cracks`・`F` |
| `ep1c.py`（P） | 第1話の映像。部屋・面接室のセット（`OFFICE`・`iv_rig`・`kanata_suit_rig`）、`slab`・`blocks`、`end_scene`（最後の画面の背景） |
| `ep2.py`（Q） | 第2話。`room_img`・`kanata_bed`・`face_cam`・`tokei_near`・`big_word`・`mio_tile`・通話画面の寸法 |
| `ep3.py`（R） | 第3話。面談室 `MEET`・`meet_img`・`kanata_seat`・`kanata_stand`・`OUTSIDE`（建物の外）・`cam_mio`/`cam_kanata` |
| `ep4.py`（F） | 第4話。2次選考会の部屋 `ROOM2`・`morishita_seat`・`host_seat`・`blanket()`・`bed_cam`・`kanata_phone_bed`・`msg_card`・`pill` |
| `ep5.py` | 第5話。ES・IS画面 `es_form`、通話 `call_img`、学生 `student_char`/`students()`、`stamp` |
| `ep6.py` | 第6話（別チャット制作）。キックオフ会場 |
| `ep7.py` | 第7話。受付 `visit_img`、車の中、`OTHER`（色ちがいの人）、`checks` |
| `ep8.py` | 第8話。議場 `COUNCIL`（傍聴席つき）・`members`、オープンチャット `phone_chat`、`bigbadge`、`rule4`、`iv_img`（面接＋色抜き）、巻き戻し |
| `case1.py` | 旧「議員さんが、いない。」。`LOBBY`・`STREET`・`morishita()`・`reception()`・`kanata()`・`card_info`（第7・8話が import しているので消さない） |
| `audio.py`（A） | BGM・効果音・環境音（STORY_BIBLE/PRODUCTION_RULES 参照）、`put`・`duck`・`fade`・`SR=24000` |
| `mix1.py`〜`mix3.py`、`mix_epN.py` | 各話の音（声＋効果音＋BGM → loudnorm → 映像に `-c:v copy` で合わせる） |
| `designsheet.py` | 設定画（`設定画/`）を作る |
| `voice/epN/NN.wav` | 各話の声（VOICEVOXで生成済み） |
| `企画書.md` | 11/1時点の企画書＋0章（11/3〜4追記）。**完全版企画書より古い** |
| `注意点.md` | ゆうきさんの指示のまとめ（一部古い：OPEN_ISSUES #7） |
| `README.md` | キャラクター定義書の説明 |
| `引き継ぎ/` | この引き継ぎ資料 |
| `out_*/` | 出力（**git管理外**）。`ガクチカループ_第N話.mp4` と `第N話_投稿文.txt` |

## 3. 1話の作り方（コマンド）
```bash
cd yt-shorts && git pull --rebase
# 1) 台本の声：tools/voice/loop_ep9.json を作る（形式は下）→ push
git add tools/voice/loop_ep9.json && git commit -m "第9話の声" && git pull --rebase && git push
# push で voice.yml が動かないとき（JSONがHEADのコミットに無い等）：
gh api -X POST repos/hone88/yt-shorts/actions/workflows/voice.yml/dispatches -f ref=main -f "inputs[file]=loop_ep9.json"
gh run list -R hone88/yt-shorts -w voice.yml -L 1     # completed success を待つ
bash tools/get_voice.sh loop_ep9 loop_drama/voice/ep9  # 第1引数はJSONの名前（loop_ep9）
# 2) 映像と音
cd loop_drama
python3 ep9.py still <場面名> <秒>      # 静止画で確認 → out_ep9/still_*.png
python3 ep9.py build                     # 場面ごとのmp4（2並列）→ video.mp4
python3 mix_ep9.py                       # → out_ep9/ガクチカループ_第9話.mp4
# 1場面だけ直したとき：python3 -c "import ep9 as V; V.render_shot(i)" → out_ep9/list.txt で concat → mix
```
声のJSONの形：
```json
{"speaker": 12, "speed": 1.15, "reels": {"ep9": {"scenes": [
  {"id": "01", "speaker": 12, "say": "…また、このメッセージ。"},
  {"id": "02", "speaker": 3,  "say": "…"} ]}}}
```
話者：カナタ12／ミオ8／トケイ3／面接官13／森下議員11／受付・活動先・訪問先の方14／ハルト52。読み上げのクセがある語は `say` をかなにする。
同じ文を「台本（字幕）」は `epN.py` の `TEXT`（`[黄色にする語]`、`|` で改行、話者記号 K/M/T/I/Mo/H/V）に書く。

## 4. 各話のコードの型（ep5〜ep8 共通）
- `TEXT`・`vo()`・`L()`・`subtitle()`・`seq()`（セリフを順に並べて開始時刻を返す。`gap`・`extra`で間を調整）
- `plan()`：`O.Shot(名前, 長さ, lines)` を並べる。場面ごとに追加の時刻（`s.rev` など）を持たせる
- `frame(s, t)`：場面名で分岐して1コマを描く（3D描画 → 時計 → 札・文字 → 字幕）
- `render_shot(i)` と `build`（ProcessPoolExecutor 2並列）
- 確認：完成版から一定間隔でコマを抜いて並べる（`ffmpeg -vf "select=...,scale=180:-1,tile=10x2"`）、0.1秒ごとに音量を測って -45dB 未満を探す（各話の作業ログ参照）

## 5. 外部
- 声の生成：GitHub Actions `voice.yml`（VOICEVOX engine をサービスで起動）→ `voice-out` ブランチの `<JSON名>/` に置く。
- ゆうきさんのスキル `anthropic-skills:dotjp-shorts-video`（ドットジェイピー広報リール・ガクチカ・ループのマイクラ調動画を作る・直すときに使う）がこの環境にある。
- 関連資料（claude.aiの文書）：企画書 https://claude.ai/artifact/XvmCdR3bFzqP8vTDvD71GV、坂田さん向け作り方ガイド https://claude.ai/artifact/2b11MBZVVjaSrtKWnA8Jq3。リポジトリ直下の `動画の作り方プロンプト.md` は作り方とコツだけ（内容は引き継がない版）。
