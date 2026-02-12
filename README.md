# pdf-translate-local

ローカル環境でスキャンPDFをOCR+翻訳し、Markdownを生成するMVPです。

## What It Does

- 入力: スキャンPDF
- 処理: PDF画像化 -> GLM-OCR -> 読み順整列 -> TranslateGemma翻訳 -> Markdown生成
- 出力: `outputs/jobs/<job_id>/md/result.md`

## Requirements

- macOS (Apple Silicon推奨)
- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/)
- `translategemma:12b-it-q4_K_M` モデル

## Repository Setup

```bash
git clone https://github.com/otofu1024/papers_translater.git
cd papers_translater
git submodule update --init --recursive
```

## Environment Setup

1. Backend

```bash
cd backend
uv sync
cd ..
```

2. Frontend

```bash
cd frontend
npm install
cd ..
```

3. GLM-OCR (mlx) side-by-side envs

`backend/third_party/GLM-OCR/examples/mlx-deploy/README.md` の方針で2環境を作ります。

```bash
cd backend/third_party/GLM-OCR
uv venv .venv-mlx
uv venv .venv-sdk
uv pip install --python .venv-mlx/bin/python git+https://github.com/Blaizzy/mlx-vlm.git
uv pip install --python .venv-sdk/bin/python -e .
uv pip install --python .venv-sdk/bin/python "transformers @ https://github.com/huggingface/transformers/archive/refs/heads/main.zip"
cd ../../..
```

## Runtime Config

`.env.example` をコピーして `.env` を作成してください。

```bash
cp .env.example .env
```

主な項目:

- `OCR_BASE_URL` (default: `http://127.0.0.1:8080`)
- `OCR_MAX_TOKENS` (default: `2048`)
- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default: `translategemma:12b-it-q4_K_M`)
- `RENDER_DPI` (default: `350`)

## Start

ワンコマンド起動:

```bash
./bin/dev
```

個別起動:

```bash
./bin/ocr
./bin/api
./bin/ui
```

生成物クリア:

```bash
./bin/clean
```

## API Endpoints

- `POST /jobs` PDFアップロード
- `GET /jobs/{job_id}` ジョブ状態
- `GET /jobs/{job_id}/result` result.md取得
- `GET /jobs/{job_id}/pages/{n}` ページMarkdown取得
- `GET /health` OCR/Ollama疎通

## License and Model Notes

- TranslateGemma / Gemma 系モデルを利用する際は、Google/Gemmaの利用規約・配布条件を必ず確認してください。
- GLM-OCR は別リポジトリを submodule として参照しています。ライセンスは `backend/third_party/GLM-OCR/LICENSE` を確認してください。
