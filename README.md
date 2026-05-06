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

`output/frames/` に `frame_000001.png` から `frame_000600.png` までの PNG フレームが保存されます。既存の PNG フレームは実行前に削除されます。

## 画面表示ありで確認

```powershell
python src/simulate.py --frames 600 --window
```

ウィンドウ表示時は、1080x1920 の生成フレームを画面に収まるよう縮小表示します。保存される PNG は 1080x1920 のままです。

## 現在の範囲

- 画面サイズ: 1080x1920
- FPS: 60
- 物理エンジン: pymunk
- 描画: pygame-ce
- ボール: 1 個
- 重力: なし
- フレーム出力: `output/frames/`
- 動画出力: 未実装
- YouTube アップロード: 未実装
