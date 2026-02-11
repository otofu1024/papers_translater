# Architecture

## Overview

本プロジェクトは、FastAPIバックエンドがジョブ単位でOCR/翻訳パイプラインを実行し、Reactフロントエンドが状態監視と結果表示を行う構成です。

## Components

- Backend: `backend/app`
  - API:
    - `backend/app/api/routes/jobs.py`
    - `backend/app/api/routes/health.py`
  - Pipeline:
    - `backend/app/pipeline/run_job.py`
    - `backend/app/pipeline/render_pdf.py`
    - `backend/app/pipeline/ocr_page.py`
    - `backend/app/pipeline/order_blocks.py`
    - `backend/app/pipeline/translate.py`
    - `backend/app/pipeline/to_markdown.py`
  - Clients:
    - `backend/app/clients/ocr_client.py`
    - `backend/app/clients/ollama_client.py`
  - State store:
    - `backend/app/store/paths.py`
    - `backend/app/store/state.py`

- Frontend: `frontend/src`
  - Upload page / Job page
  - Progress表示
  - Markdownプレビュー

- OCR submodule:
  - `backend/third_party/GLM-OCR`

## Data Flow

1. `POST /jobs` でPDFを受信
2. `outputs/jobs/<job_id>/input.pdf` に保存
3. `run_job.py` がバックグラウンド実行
4. PDFを `pages/*.png` にレンダリング
5. OCRサーバーへ `chat/completions` 形式で画像送信
6. OCR結果を正規化し、読み順整列
7. ブロック単位でOllama翻訳
8. `md/<page>.md` と `md/result.md` を生成
9. `GET /jobs/{job_id}` で状態確認、`GET /jobs/{job_id}/result` で取得

## Job Storage Layout

`outputs/jobs/<job_id>/`

- `input.pdf`
- `meta.json`
- `job.log`
- `pages/001.png ...`
- `ocr/001.json ...`
- `md/001.md ...`
- `md/result.md`

## Operational Notes

- OCRサーバーは `mlx_vlm.server` を想定 (port 8080)。
- 翻訳は Ollama `translategemma:12b-it-q4_K_M` を想定。
- `./bin/dev` は OCR確認/起動、Ollama疎通確認、API/UI起動、Ctrl+C停止を提供します。

