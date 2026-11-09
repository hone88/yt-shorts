# AUTOMATION_GUIDE｜予約・リマインド・自動化

## 1. 投稿時刻【確定】
| 媒体 | 時刻 | 誰が |
|---|---|---|
| YouTube | 18:00 | ゆうきが予約投稿 |
| Instagram | 19:00 | ゆうき |
| TikTok | 20:00 | ゆうき |
Claudeは各SNSにログインできない・しないので、**予約されたかどうかは直接確認できない**。翌朝のスクショ（投稿日時）で確かめる。

## 2. 17:50 リマインド【実行中・移行が必要】
- いまの設定：スケジュールされたタスク「17:50 投稿リマインド」（ID trig_01Ko9tyMYRYz97gn4qhDogdX）
  - 1回だけ動くタスクで、動いたときに `send_later` で翌日17:50の分を予約し直して毎日続ける方式
  - 届く先は **この古い会話（session_01CbnLWFuK7mHXBeBRpiQvW6）**
  - 次回：2026-11-09 17:50（日本時間）
  - 文面：「今日のもしもの続き、YouTube 18:00・Instagram 19:00・TikTok 20:00、3つとも予約できてる？まだならタイトルとキャプションを出すよ」（その日の動画名も添える）
- 新しいウィンドウに移るとき：
  1. 新しいウィンドウで `send_later`（at: 当日の `YYYY-MM-DDT17:50:00[Asia/Tokyo]`、initiation: human_request）で同じ文面を予約し、届いたら翌日分を予約し直す運用にする
  2. 古い会話のタスクを止めないと、2か所に届く → ゆうきに確認してから `delete_trigger`（trig_01Ko9tyMYRYz97gn4qhDogdX）【要確認】
- 「リマインド止めて」と言われたら予約をやめる。

## 3. GitHub Actions（hone88/yt-shorts）
| ワークフロー | いつ動く | 何をする |
|---|---|---|
| もしもチャンネル（moshimo.yml） | `channels/moshimo/clips/**` に push / 手動 | 台本＋クリップ＋VOICEVOXの声で動画を作り、Releases に short.mp4・upload_memo.txt。台本を used に移す |
| AI副業チャンネル（ai1h.yml） | 月・水・金 7:13（JST） | ai1h の台本から動画を作る。**使い道は要確認** |
| 読み上げ音声だけ作る（voice.yml） | 手動 | 別プロジェクト用。触らない |

## 4. 手動のまま残っている作業
- 各SNSへの投稿・予約・AI表示の設定（ゆうき）
- 数字のスクショ（ゆうき）。YouTube・Instagram・TikTok・X・Threads の数字はClaudeから見られない
- コメントへの返信（ゆうき）
- noteの投稿（ゆうき。Claudeは原稿・画像を作る）

## 5. PCとの連携
- この会話は、ゆうきのPC（Claudeデスクトップアプリ）と連携できるときがある。連携中はPC上のブラウザ（アプリ内ブラウザ）を使えるが、**SNSにログイン・投稿はしない**。
- 参考動画のBGMの大きさを測るなど、ブラウザで公開ページを見る用途なら使える。
