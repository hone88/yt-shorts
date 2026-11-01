# もしもの続き：背景クリップとBGM・効果音を作る道具

新しいチャットでは `作り方プロンプト.md` を最初に貼る。ここにあるのは、その中で使う道具と見本。

| ファイル | 中身 | 使い方 |
| --- | --- | --- |
| `voxel.py` | マイクラ調3Dの描画エンジン（ブロックの世界・光と影・粒子・マンモスの形） | 他の見本から `import voxel` で使う |
| `taiyou_voxel.py` | 「太陽が突然消えたら」7場面の見本（町・公園・四角い月・地球・霜・凍った海・深海） | `python3 taiyou_voxel.py stills 0:0.5,2:1.0`（場面:秒）で静止画、`python3 taiyou_voxel.py 0,1,2` で clips/ に書き出し |
| `gravity_2d.py` | 「重力が1秒消えたら」の2Dイラスト見本（歩く・跳ぶ・噴水・地球） | `mkdir clean && python3 gravity_2d.py stills 1.0` で静止画、`python3 gravity_2d.py 0,1` で clean/ に書き出し |
| `taiyou_sound.py` | 太陽の回のBGM・効果音（シーン開始時刻を上に書いて使う） | `python3 taiyou_sound.py` → bgm.wav と sfx.wav |
| `gravity_sound.py` | 重力の回のBGM・効果音 | 同上 |

- 新しい回は見本をコピーして、場面（`frame()` の中）とクリップの長さ（`CLIPS`）を書き換える。
- 書き出しは2つ同時（例：`python3 x.py 0,3,6 &` と `python3 x.py 1,2,4,5 &`）。
- 音の見本は、完成版のシーン開始時刻（S1〜S7）と出来事の時刻を、その回に合わせて書き直してから使う。
