# YouTube Shorts 2D Simulation MVP

1080x1920 の縦長画面で、複数のボールが壁に反射しながら HP ボスを攻撃する 2D 物理シミュレーションです。

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## フレーム生成

```powershell
python src/simulate.py --frames 600 --no-window
```

`output/frames/` に `frame_000001.png` から PNG フレームが保存されます。既存の PNG フレームは実行前に削除されます。

主なオプション:

```powershell
python src/simulate.py --frames 600 --no-window --balls 10 --boss-hp 10000 --damage 10 --seed 1
```

- `--balls`: 初期ボール数。デフォルトは `10`
- `--boss-hp`: ボス初期HP。デフォルトは `10000`
- `--damage`: 各ボールの初期ダメージ。デフォルトは `10`
- `--seed`: ランダム生成のシード
- `--window`: 画面に収まる縮小プレビューを表示
- `--no-window`: ヘッドレスでフレーム生成

## ボスとアイテム

画面上部に HP ボス、HP バー、HP 数値を表示します。ボールがボスに衝突すると、そのボールの現在ダメージ分だけ HP が減ります。

一定間隔でアイテムが出現します。ボールが触れると短いリングエフェクトが出て、ボールが強化されます。

- `damage_up`: 取得したボールのダメージを増やす
- `speed_up`: 取得したボールの速度を少し上げる

制限フレーム内に HP が 0 になれば `CLEAR`、倒せなければ `FAILED` です。結果は `output/metadata/simulation_result.json` に保存されます。

CLEAR確認用の短い実行例:

```powershell
python src/simulate.py --frames 600 --no-window --boss-hp 100 --damage 20
```

## MP4 動画生成

動画生成には FFmpeg が必要です。`ffmpeg` コマンドが PATH から実行できる状態にしてください。

```powershell
ffmpeg -version
```

フレーム生成後、次のコマンドで MP4 を作成します。

```powershell
python src/make_video.py
```

入力:

```text
output/frames/frame_%06d.png
```

出力:

```text
output/videos/simulation_001.mp4
```

動画は 60fps、1080x1920、H.264、`yuv420p`、faststart 付きの YouTube にアップロードしやすい MP4 として生成されます。

## 現在の範囲

- 画面サイズ: 1080x1920
- FPS: 60
- 物理エンジン: pymunk
- 描画: pygame-ce
- 初期ボール数: 10
- 重力: なし
- アイテム: `damage_up`, `speed_up`
- フレーム出力: `output/frames/`
- 動画出力: `output/videos/simulation_001.mp4`
- YouTube アップロード: 未実装
