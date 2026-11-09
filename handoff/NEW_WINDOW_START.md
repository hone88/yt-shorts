# NEW_WINDOW_START｜新しいウィンドウの始め方

## 手順（ゆうき）
1. Claude で新しいタスク（会話）を開く。
2. 下の「完全起動プロンプト」をそのまま貼って送る。
3. Claudeが読み込みを終えたら、ふだんどおり「おはよう」と送る。
4. 古いウィンドウの17:50リマインドを止めるかは、新しいウィンドウのClaudeが確認してくる。

## 読み込み手順（Claude）
1. `add_repo`（owner: hone88, repo: yt-shorts, access: push）→ `git clone --depth 1 https://github.com/hone88/yt-shorts /home/claude/yt-shorts-repo`
2. `handoff/` の12ファイルを MASTER_CONTEXT.md から順に読む。
3. メモリ `/areas/ai-side-hustle-experiment.md` を読む（数字と決定の履歴。handoff と食い違うときは日付の新しいほう、ゆうきの明確な決定を優先）。
4. 17:50リマインドを新しい会話に `send_later` で予約し直すか、ゆうきに一言確認する（AUTOMATION_GUIDE.md）。
5. 「読み込み完了」と、今日の予定（PROGRESS_STATUS / NEXT_ACTIONS）を3行で伝えて待つ。

---

## 完全起動プロンプト（ここから下をコピー）

```
これから「1日1時間AI副業」の毎日の運用を、このウィンドウで続けます。前のウィンドウの内容は GitHub の hone88/yt-shorts の handoff/ フォルダにまとめてあります。

1. add_repo（owner: hone88, repo: yt-shorts, access: push）でつなぎ、git clone --depth 1 https://github.com/hone88/yt-shorts /home/claude/yt-shorts-repo する。
2. handoff/ の12ファイルを、MASTER_CONTEXT.md → DAILY_WORKFLOW.md → PROGRESS_STATUS.md → NEXT_ACTIONS.md → CONTENT_PRODUCTION.md → ANALYTICS_GUIDE.md → ASSET_AND_CODE_GUIDE.md → AUTOMATION_GUIDE.md → SNS_ACCOUNT_GUIDE.md → MONETIZATION_STRATEGY.md → DECISION_LOG.md の順に全部読む。
3. メモリの /areas/ai-side-hustle-experiment.md も読む。食い違いは、日付が新しいほう・僕がはっきり決めたほうを優先。
4. 毎日17:50の投稿リマインド（YouTube 18:00・Instagram 19:00・TikTok 20:00 の予約確認）を、このウィンドウに届くように send_later で予約し直す。古いウィンドウのリマインドを止めるかは僕に聞いて。
5. 読み終わったら「読み込み完了」と、今日やること・決めてほしいことを3行で教えて。

決まりごと：
- 僕が「おはよう」と送ったら DAILY_WORKFLOW.md のとおりに始める（公開ページ確認 → 足りないスクショだけ提示 → 届いたらnote記事・見出し画像・切り抜き → X・Threads → 次の動画）。
- 「後で送る」と言った素材は、届くまで記事を作り始めない。
- 数字は作らない。推測は推測と書く。一人称は「僕」。出力は完成版。説明は短く。
- SNSにログイン・投稿はしない。投稿は僕がする。
- 動画のルール（マイクラ風3D、カメラを動かし続ける、BGM一定、ハッシュタグ5個で #もしもの続き は4〜5個目、AI表示の注意）は CONTENT_PRODUCTION.md のとおり。勝手に変えない。
- 壁打ちのときは、番号付き見出し・短い段落・要点の一文を太字。
```
