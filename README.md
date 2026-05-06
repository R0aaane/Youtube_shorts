# YouTube Shorts 2D Simulation MVP

1080x1920 の縦長画面で、複数のボールが壁に反射しながら HP ボスを攻撃する 2D 物理シミュレーションです。

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## JSON設定ファイル

標準設定は `configs/boss_battle_001.json` です。

```json
{
  "video_width": 1080,
  "video_height": 1920,
  "fps": 60,
  "duration_seconds": 10,
  "initial_ball_count": 10,
  "boss_hp": 10000,
  "base_damage": 10,
  "item_spawn_interval": 75,
  "random_seed": 1,
  "output_name": "simulation_001"
}
```

JSONを書き換えるだけで、ボール数、ボスHP、ダメージ、アイテム出現間隔、乱数シード、動画名を変更できます。同じ `random_seed` なら同じ結果になりやすくなります。

## フレーム生成

```powershell
python src/simulate.py --config configs/boss_battle_001.json --no-window
```

`duration_seconds * fps` 枚のPNGが `output/frames/` に保存されます。標準設定では600フレームです。既存のPNGフレームは実行前に削除されます。

CLIで一部だけ上書きすることもできます。

```powershell
python src/simulate.py --config configs/boss_battle_001.json --no-window --balls 20 --boss-hp 20000
```

## 画面表示ありで確認

```powershell
python src/simulate.py --config configs/boss_battle_001.json --window
```

ウィンドウ表示時は、生成フレームを画面に収まるよう縮小表示します。保存されるPNGは設定ファイルの解像度のままです。

## MP4動画生成

動画生成には FFmpeg が必要です。`ffmpeg` コマンドが PATH から実行できる状態にしてください。

```powershell
ffmpeg -version
```

フレーム生成後、次のコマンドでMP4を作成します。

```powershell
python src/make_video.py --config configs/boss_battle_001.json
```

入力:

```text
output/frames/frame_%06d.png
```

出力:

```text
output/videos/<output_name>.mp4
```

標準設定では `output/videos/simulation_001.mp4` が生成されます。動画は設定ファイルの `fps` と解像度を使い、H.264、`yuv420p`、faststart 付きのMP4として生成されます。

## 現在の範囲

- 物理エンジン: pymunk
- 描画: pygame-ce
- 重力: なし
- ボスHPとHPバー表示
- 複数ボール
- アイテム: `damage_up`, `speed_up`
- フレーム出力: `output/frames/`
- 動画出力: `output/videos/<output_name>.mp4`
- YouTubeアップロード: 未実装
