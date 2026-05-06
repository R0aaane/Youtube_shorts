# YouTube Shorts 2D Simulation MVP

YouTube Shorts 向けの縦型2D物理シミュレーション動画を生成するための最小構成です。

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 最初の実行

```powershell
python src/simulate.py
```

実行すると、デフォルト設定が `configs/default.json` に作成され、簡易シミュレーション結果が `output/metadata/simulation_result.json` に保存されます。

## 動画生成の入口

まだ本格的な動画生成は実装していません。次の段階でフレームを `output/frames/` に書き出し、ffmpeg で `output/videos/` に mp4 を保存します。

```powershell
python src/make_video.py
```

## ゲーム資産生成

ゲーム資産は `imagegen2` API を使う前提で、最小クライアントを `src/generate_assets.py` に用意しています。

```powershell
$env:IMAGEGEN2_API_URL="https://example.com/v1/images/generations"
$env:IMAGEGEN2_API_KEY="your_api_key"
python src/generate_assets.py
```

API URL とキーが未設定の場合、資産生成は失敗させずにスキップします。

## 現在の構成

```text
configs/
assets/
output/
  frames/
  videos/
  metadata/
src/
  generate_assets.py
  generate_config.py
  make_video.py
  render.py
  simulate.py
tests/
requirements.txt
README.md
```

## 方針

- まずはローカル動画生成を安定させる
- YouTubeアップロード機能はまだ作らない
- 複雑な物理や演出は後続ステップで追加する
