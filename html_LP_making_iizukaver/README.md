# LP生成ツール

これは「企画書」（JSONファイル）をもとに、参考サイト（`ans-skin.com`の広告LP）のようなランディングページ（HTML/CSS）を自動生成するツールです。

## プロジェクト構成

- `generator.py`: ウェブサイトを生成するPythonスクリプト
- `input/sample_plan.json`: テキストや画像URLなどを記述した「企画書」データ
- `templates/`: HTMLの雛形（テンプレート・Jinja2形式）
- `static/`: CSSやJavaScriptファイル
- `output/`: 生成されたサイトが出力されるフォルダ

## 使い方

1. **セットアップ** (初回のみ):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **企画書の編集**:
   - `input/sample_plan.json` を開いて編集します。
   - テキスト、画像URL、プラン内容などを、作りたいLPに合わせて書き換えてください。
   - リスト項目を増やしたり、セクションのタイトルを変更したりできます。

3. **サイト生成**:
   ```bash
   # 仮想環境が有効になっていることを確認してください
   # source venv/bin/activate
   
   python generator.py
   ```

4. **確認**:
   - `output/index.html` をブラウザで開いて確認してください。
   - `output` フォルダ一式をサーバーにアップロードすれば公開可能です。

## カスタマイズについて

- **デザインの変更**: `static/css/style.css` を編集してください。
- **構成の変更**: `templates/index.html` や `templates/components/` 内のファイルを編集してください。
