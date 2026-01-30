# screenshot-to-code (日本語版)

スクリーンショット、モックアップ、Figmaデザインを、AIを使ってクリーンで機能的なコードに変換するシンプルなツールです。

## 🚀 最近の更新

- **画像自動トリミング & 背景透過**: AIが画像領域を識別し、自動でトリミング＆背景透過を実行。人物写真（`type:human`）とイラスト等（`type:general`）で最適なモデルを自動選択。
  - 保存先: `backend/static/cropped/{session_id}/`
- **コード内編集 & 保存**: GUIの「Code」タブでコードを直接編集し、「Save」ボタンでプレビューに即反映。
- **バッチ編集モード**: 複数の指示（「この文字を赤に」「もっと大きく」など）をキューに入れて、一括で適用可能。
- **「分割＆結合」生成**: 複数のスクリーンショットをアップロードすると、AIが各セクションのコードを生成し、1つのHTMLファイルに結合。
- **色精度の向上**: テキスト色と背景色の組み合わせを厳密に再現（白文字が白背景になるなどの問題を防止）。
- **テレメトリなし**: データ追跡なし。

## 対応スタック

- HTML + Tailwind
- HTML + CSS
- React + Tailwind
- Vue + Tailwind
- Bootstrap
- Ionic + Tailwind
- SVG

## 対応AIモデル

- Gemini 3 Flash / Pro（推奨）
- 画像生成: Nanobanana

## � セットアップ

### 必要なAPIキー

以下を取得してください:

- [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### バックエンドの起動

```bash
cd backend
echo "GEMINI_API_KEY=あなたのキー" > .env
# 必要に応じて他のキーも追加:
# echo "OPENAI_API_KEY=あなたのキー" >> .env
# echo "ANTHROPIC_API_KEY=あなたのキー" >> .env
poetry install
poetry run uvicorn main:app --reload --port 7003
```

### フロントエンドの起動

```bash
cd frontend
yarn
yarn dev
```

ブラウザで http://localhost:5173 を開いてください。

> **Note**: APIキーは設定画面（歯車アイコン）からも入力できます。

## 🎯 使い方

1. **スクリーンショットをアップロード**: ドラッグ＆ドロップでスクリーンショットを追加
2. **スタックを選択**: HTML/Tailwind、React、Vue などから選択
3. **AIモデルを選択**: Gemini 3 Flash を推奨（有料版APIならProでも良い）。画像生成はNanobananaを使用。
4. **「Generate Code」をクリック**: AIがコードを生成
5. **プレビュー & 編集**: 生成されたコードをプレビューし、必要に応じて修正

### 複数画像の場合（分割＆結合）

長いランディングページを複数のスクリーンショットに分割してアップロードすると、AIが各セクションを個別にコーディングし、最終的に1つのファイルに結合します。

### セレクションモード（要素編集）

1. プレビュー上で要素をクリックして選択
2. 修正指示を入力（例：「この文字を赤くして」）
3. 「Add Change」でキューに追加
4. サイドバーの「Apply X Changes」で一括適用

## Docker

```bash
echo "GEMINI_API_KEY=あなたのキー" > .env
docker-compose up -d --build
```

http://localhost:5173 でアクセス可能です。

## 🎬 ビデオ対応

Webサイトの動作を録画したビデオから、機能的なプロトタイプを生成する実験的機能もあります。

## ❓ FAQ

- **バックエンドのポートを変更したい場合**: `frontend/.env.local` で `VITE_WS_BACKEND_URL` を更新してください。
- **プロキシを使用する場合**: `backend/.env` に `OPENAI_BASE_URL=https://xxx.xxx/v1` を設定してください。

## ライセンス

MIT License
