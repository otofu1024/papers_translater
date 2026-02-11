# **AGENTS.md — pdf-translate-local (Codex向け開発ガイド)**

このドキュメントは、**M4 MacBook Air（メモリ32GB）** で完全ローカル動作する「スキャンPDF翻訳ツール」の開発ガイドラインです。AIエージェント（Codex等）がコードを生成・修正する際の指針として使用します。

## **0\. プロジェクトの目的**

スキャンされた（画像化された）PDFを入力とし、ページ順を保った翻訳済みMarkdownを出力するツールを構築します。

* **入力**: スキャン画像PDF（各ページが画像となっているPDF）  
* **出力**: ページ順を維持した **Markdown**（レイアウトの細部は追わず、テキスト情報の復元を優先）  
* **OCR**: GLM-OCR（文書解析 / ブロック分割 / bbox付きJSON取得）  
* **翻訳**: Ollama 上の translategemma:12b-it-q4\_K\_M  
* **Backend**: Python \+ FastAPI（uv で管理）  
* **Frontend**: TypeScript \+ Vite（シンプルなWeb UI）

**Note**: 将来的に「レイアウト保持PDF再生成」へ拡張する可能性はありますが、**MVP（Minimum Viable Product）では実装しません**。

## **1\. アーキテクチャと前提**

### **1.1 GLM-OCRの構成**

GLM-OCRは以下の2つのコンポーネントに分離して扱います。

1. **GLM-OCR SDK**: このリポジトリ内で import して使用するクライアント/ユーティリティ。  
2. **OCR推論サーバ**: 別プロセスとして動作させる。Macローカル環境では **MLX (mlx\_vlm.server)** を使用する。  
   * Dockerには閉じ込めず、ホストのMetal/MLX環境を直接利用します。

### **1.2 理想的な起動体験**

開発者は ./bin/dev コマンド1発で開発環境を立ち上げられるようにします。

* **OCR推論サーバ**: mlx\_vlm.server が未起動なら起動。  
* **Ollama**: 起動済みであることを想定（疎通確認のみ実施）。  
* **FastAPI Backend**: uv 経由で起動。  
* **Vite Frontend**: 開発サーバを起動。

## **2\. スコープ（MVPの完了条件）**

### **MVP Done条件**

1. **Web UI**: PDFをアップロードできる。  
2. **Job管理**: バックエンドでジョブが作成され、ステータスと進捗が追跡できる。  
3. **パイプライン実行**:  
   * PDFをページ画像化（DPI指定）  
   * GLM-OCRで解析  
   * ブロック単位で翻訳  
   * ページ順にMarkdownを生成  
4. **結果確認**: 生成された result.md をUIで表示・ダウンロードできる。  
5. **デバッグ性**: 生成物が outputs/jobs/{job\_id}/... に保存され、検証可能である。

### **Non-Goals（MVPではやらない）**

* レイアウトを保持した翻訳PDFの再生成（PDF to PDF）  
* 原文/訳文の並列表示（UI上での対比）  
* 高度な表復元（Markdown tableの完全な再現）  
* GPU最適化・大規模バッチ処理の最適化（個人ユースのローカル動作のため）

## **3\. 推奨ディレクトリ構成**

SQLiteは使用せず、ファイルシステムベースで状態管理を行います。

pdf-translate-local/  
├── AGENTS.md  
├── README.md  
├── ARCHITECTURE.md  
├── .gitignore  
├── .env.example  
├── bin/  
│   ├── dev          \# OCR \+ API \+ UI をまとめて起動（ワンコマンド）  
│   ├── ocr          \# mlx\_vlm.server 起動（単体）  
│   ├── api          \# FastAPI 起動  
│   ├── ui           \# フロント起動  
│   └── clean        \# outputs配下の生成物削除  
├── third\_party/  
│   └── GLM-OCR/     \# git clone or submodule（※repo直下に配置）  
├── backend/  
│   ├── pyproject.toml  
│   ├── uv.lock  
│   └── app/  
│       ├── \_\_init\_\_.py  
│       ├── main.py  
│       ├── core/  
│       │   ├── \_\_init\_\_.py  
│       │   ├── config.py       \# 環境変数（OCR\_URL, OLLAMA\_URL, 作業DIR等）  
│       │   └── logging.py      \# ログ設定  
│       ├── api/  
│       │   ├── \_\_init\_\_.py  
│       │   ├── routes/  
│       │   │   ├── \_\_init\_\_.py  
│       │   │   ├── jobs.py     \# upload/status/result  
│       │   │   └── health.py  
│       ├── clients/  
│       │   ├── \_\_init\_\_.py  
│       │   ├── ocr\_client.py   \# GLM-OCR推論サーバ呼び出し  
│       │   └── ollama\_client.py \# Ollama呼び出し  
│       ├── pipeline/  
│       │   ├── \_\_init\_\_.py  
│       │   ├── run\_job.py      \# 1ジョブのオーケストレーション  
│       │   ├── render\_pdf.py   \# PDF→ページ画像 (PyMuPDF)  
│       │   ├── ocr\_page.py     \# 画像→OCR JSON  
│       │   ├── order\_blocks.py \# 読み順ソート  
│       │   ├── translate.py    \# ブロック翻訳  
│       │   └── to\_markdown.py  \# ページMarkdown生成  
│       ├── models/  
│       │   ├── \_\_init\_\_.py  
│       │   └── schemas.py      \# Pydantic: Job, Page, Block, Result  
│       ├── store/  
│       │   ├── \_\_init\_\_.py  
│       │   ├── paths.py        \# outputs/jobs/{job\_id}/ パス管理  
│       │   └── state.py        \# Job状態の永続化（meta.json読み書き）  
│       └── utils/  
│           ├── \_\_init\_\_.py  
│           ├── image.py        \# 画像処理  
│           └── text.py         \# テキスト前処理  
├── frontend/  
│   ├── package.json  
│   ├── vite.config.ts  
│   ├── tsconfig.json  
│   └── src/  
│       ├── main.tsx  
│       ├── App.tsx  
│       ├── api/  
│       │   └── client.ts       \# APIクライアント  
│       ├── pages/  
│       │   ├── UploadPage.tsx  
│       │   └── JobPage.tsx     \# Progress \+ MarkdownViewer  
│       └── components/  
│           ├── Dropzone.tsx  
│           ├── Progress.tsx  
│           └── MarkdownViewer.tsx  
├── data/  
│   └── sample.pdf    \# 動作確認用  
└── outputs/          \# .gitignore 対象  
    └── jobs/  
        └── \<job\_id\>/  
            ├── input.pdf  
            ├── meta.json      \# ジョブ状態・メタデータ  
            ├── job.log        \# 実行ログ  
            ├── pages/         \# レンダリングされた画像  
            │   └── 001.png  
            ├── ocr/           \# OCR解析結果  
            │   └── 001.json  
            └── md/            \# ページごとのMarkdown  
                ├── 001.md  
                └── result.md  \# 最終結合結果

### **構成のポイント**

* third\_party/GLM-OCR はバックエンド外（リポジトリ直下）に配置し、パスを通しやすくする。  
* outputs/ は .gitignore に含めるが、ジョブごとの成果物はデバッグ用に必ずファイルとして残す。  
* ジョブの状態管理（DBの代わり）は outputs/jobs/{job\_id}/meta.json を正として扱う。

## **4\. 依存・実行環境**

### **4.1 Python Backend (uv)**

* Python 3.11+ (3.12推奨)  
* **Web Framework**: FastAPI, Uvicorn, httpx, pydantic  
* **PDF/Image**: PyMuPDF (fitz), Pillow (必要に応じてopencv)

### **4.2 Frontend**

* TypeScript \+ Vite \+ React (最小構成)  
* **Markdown**: react-markdown 等の軽量レンダラ

### **4.3 外部サービス (Local)**

* **OCR**: mlx\_vlm.server (別ターミナルまたは bin/dev で起動)  
* **Translation**: Ollama (インストール済み前提)

## **5\. 環境変数 (.env)**

.env.example を作成し、バックエンド起動時に読み込みます。

OCR\_BASE\_URL=\[http://127.0.0.1:8080\](http://127.0.0.1:8080)  
OLLAMA\_BASE\_URL=\[http://127.0.0.1:11434\](http://127.0.0.1:11434)  
OLLAMA\_MODEL=translategemma:12b-it-q4\_K\_M  
RENDER\_DPI=350  
OUTPUT\_DIR=outputs

## **6\. パイプライン仕様 (MVP)**

### **6.1 処理フロー**

1. **Job作成**: PDFをMultipart uploadで受け取り、ジョブIDを発行。  
2. **画像化**: PDFをページごとに画像化 (PyMuPDF, RENDER\_DPI)。  
3. **OCR解析**: 各ページ画像をGLM-OCR SDK経由で解析（順次処理）。  
4. **整列**: 検出されたブロックを読み順にソート（軽量な列推定 \+ Y/X座標ソート）。  
5. **翻訳**: ブロック単位でOllamaに投げ翻訳。  
6. **生成**: ページごとにMarkdownを生成し、最後に結合して result.md を作成。

### **6.2 成果物の保存**

デバッグ最優先で、outputs/jobs/{job\_id}/ 以下にすべての中間ファイルを保存します。

* input.pdf  
* meta.json (Status, Progress, Error info)  
* pages/\*.png  
* ocr/\*.json  
* md/\*.md  
* result.md  
* job.log

## **7\. データ構造 (内部スキーマ)**

GLM-OCRの生出力は揺らぎがあるため、内部で正規化して扱います。

### **7.1 Block (最小限)**

* id: str  
* type: str (paragraph, title, table, etc.)  
* bbox: \[x1, y1, x2, y2\] (画像座標)  
* text: str (原文)  
* translated\_text: str (訳文、翻訳後に付与)  
* page: int

### **7.2 PageResult**

* page: int  
* img\_w: int  
* img\_h: int  
* blocks: List\[Block\]  
* markdown: str

## **8\. 翻訳方針 (Ollama)**

* **単位**: 1ブロック \= 1リクエスト（長文は文分割→再結合で対応）。  
* **プロンプト**: 制約は最小限にし、モデルの性能を阻害しないようにする。  
  * 数字、単位、URL、参照（Fig.1など）を保持するよう指示。  
  * 翻訳文のみを出力させる（余計な解説を禁止）。  
  * Markdown形式を崩さない。  
* **モデル**: TranslateGemmaを使用するため、Rules: 等の推奨フォーマットを崩さずにプロンプトを構成する。

## **9\. API設計 (MVP)**

### **Backend (FastAPI)**

* POST /jobs: PDFアップロード → Job ID返却  
* GET /jobs/{job\_id}: ステータス、進捗、エラー情報の取得（meta.json参照）  
* GET /jobs/{job\_id}/result: 最終成果物 result.md のダウンロード  
* GET /jobs/{job\_id}/pages/{n}: 特定ページのMarkdown取得（任意）  
* GET /health: OCRサーバおよびOllamaへの疎通確認

### **Frontend**

* **Upload画面**: PDFをドロップしてJob作成。  
* **Job画面**: プログレスバー表示 → 完了後にMarkdownプレビュー & ダウンロードボタン表示。

## **10\. 起動スクリプト (bin/dev)**

開発効率のため、以下の動作を行うスクリプトを用意します。

1. **OCRチェック**: OCRサーバのエンドポイントを確認。応答がなければ mlx\_vlm.server \--port 8080 をバックグラウンドで起動。  
2. **Ollamaチェック**: /api/tags 等で疎通確認。  
3. **Backend起動**: uv を使用してFastAPIを起動。  
4. **Frontend起動**: Viteサーバを起動。  
5. **終了処理**: trap を仕込み、Ctrl+Cで生成した子プロセスをまとめて終了させる。

## **11\. コーディング規約**

* **MVP優先**: 最短で動くものを作る。過度な抽象化や最適化は避ける。  
* **モジュール分割**: clients, pipeline, store の責務を守る。  
* **エラー処理**: ユーザー向けメッセージと、デバッグ用詳細ログを分ける。  
* **ログ**: コンソールだけでなく job.log にも出力する。  
* **ステート管理**: 複雑なDBは使わず、store/state.py 経由で meta.json を操作する。

## **12\. テストと動作確認**

* data/sample.pdf を配置し、動作確認に使用する（ファイルサイズは小さめ推奨）。  
* 手動テストで POST /jobs から result.md 生成まで通ることを確認する。  
* OCRサーバ未起動時などに、適切なエラーメッセージが返ることを確認する。

## **13\. README記載事項**

* TranslateGemma/Gemma モデルの利用規約および配布時の注意点。  
* third\_party/ に配置するGLM-OCRのセットアップ手順。

## **14\. 開発ステップ (推奨順序)**

1. **Backend基盤**: 雛形作成、/health 実装、Config周り。  
2. **Job管理**: /jobs 実装（PDF保存、meta.json 初期化）。  
3. **PDF処理**: render\_pdf.py（PDF→画像）。  
4. **OCR実装**: ocr\_client.py 実装と GLM-OCR SDK統合。  
5. **ブロック処理**: order\_blocks.py（読み順整列）。  
6. **翻訳実装**: translate.py（Ollama連携）。  
7. **Markdown生成**: to\_markdown.py 実装。  
8. **Frontend**: 最小構成のUI（Upload/Progress/Viewer）。  
9. **環境整備**: bin/dev スクリプト作成とドキュメント整備。