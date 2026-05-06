# YouTube Shorts 2D Simulation MVP

1080x1920 の縦長画面で、ボールが壁に反射し続ける最小 2D 物理シミュレーションです。

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

現在のMVPでは、画面上部にHP 10000のボスとHPバーが表示されます。ボールがボスに衝突すると10ダメージを与えます。制限フレーム内にHPが0になれば `CLEAR`、倒せなければ `FAILED` です。結果は `output/metadata/simulation_result.json` に保存されます。

CLEAR確認用の短い実行例:

```powershell
python src/simulate.py --frames 600 --no-window --boss-hp 10 --damage 10
```

画面表示ありで確認する場合:

```powershell
python src/simulate.py --frames 600 --window
```

ウィンドウ表示時は、1080x1920 の生成フレームを画面に収まるよう縮小表示します。保存される PNG は 1080x1920 のままです。

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
- ボール: 1 個
- 重力: なし
- フレーム出力: `output/frames/`
- 動画出力: `output/videos/simulation_001.mp4`
- YouTube アップロード: 未実装
