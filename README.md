# 高機能LP生成システム (Advanced LP Factory)

企画書（JSON）とデザインスタイルを選択するだけで、高品質なランディングページ（LP）を自動生成するシステムです。
複数のデザインテーマ（Standard, Manga）に対応し、画像資産の管理やコンポーネントの柔軟な組み換えが可能です。

## 特徴
*   **マルチスタイル対応**: 「信頼感のある標準デザイン」と「親しみやすいマンガ風デザイン」を瞬時に切り替え可能。
*   **柔軟な構成**: JSONの記述順序を変えるだけで、セクションの入れ替えや追加が自由自在。
*   **スマホ最適化**: 全コンポーネントがレスポンシブ対応。徹底したモバイルファースト設計。
*   **ハイブリッドコンポーネント**: 画像の「表現力」とテキストの「SEO/可読性」を両立した設計。

## ディレクトリ構成
```
html_LP_making/
├── generator.py            # 生成スクリプト本体
├── input/                  # 企画書（JSONプラン）置き場
│   ├── busy_mom_plan.json      # 例: 子育てママ向けプラン
│   ├── spring_break_acne_plan.json # 例: 春休み向けプラン
│   └── ...
├── templates/              # デザインテンプレート
│   ├── standard/           # [Style] 標準・医療向け
│   ├── manga/              # [Style] マンガ・ポップ向け
│   └── common/             # 共通テンプレート (Base, Meta等)
├── static/
│   ├── images/
│   │   └── generated/      # プランごとの生成画像置き場
│   │   └── common/         # 【NEW】プラン共通・固定画像 (icon等)
│   │       ├── busy_mom/
│   │       └── ...
│   └── ...
└── output/                 # 成果物出力先
```

## 使い方

### 1. セットアップ
```bash
# 仮想環境の作成と有効化
python3 -m venv .venv
source .venv/bin/activate

# 依存ライブラリのインストール
pip install jinja2
```

### 2. LPの生成
企画書ファイルと、適用したいスタイルを指定してコマンドを実行します。

```bash
# 基本コマンド
python generator.py input/【企画書ファイル名】.json --style 【スタイル名】

# 例1: ニキビ治療LPを「マンガ風」で生成
python generator.py input/spring_break_acne_plan.json --style manga

# 例2: クリニックLPを「標準スタイル」で生成
python generator.py input/tokyo_bihadado_plan.json --style standard
```

### 3. 利用可能なスタイル (`--style`)
| スタイル名 | 特徴 | 用途 |
| :--- | :--- | :--- |
| `standard` | 清潔感、信頼感、余白、グラデーション | クリニック、医療、コーポレート |
| `manga` | ポップ、親近感、太枠線、ドット背景 | 若年層、キャンペーン、ストーリー訴求 |
| `premium` | 高級感、明朝体、ゴールド、余白 | アンチエイジング、高価格帯、ブランディング |
| `natural` | 優しさ、丸ゴシック、グリーン、ベージュ | オーガニック、敏感肌、食品 |
| `cyber` | 先進的、角ゴシック、ブルー/シルバー、ガラス | レーザー治療、最新医療、男性向け |

### 4. 確認
- `output/【企画書名】/【スタイル名】/index.html` に生成されます。
- 例: `output/busy_mom_plan/manga/index.html`
- そのフォルダごとサーバーにアップロードすれば公開可能です（他のプランと干渉しません）。

## 企画書 (JSON) の書き方
`input/sample_plan.json` を参考にしてください。
`sections` 配列の中に、必要なコンポーネントを記述順に並べます。

### コンポーネント一覧 (JSON `type` 指定)

プランに合わせて最適なコンポーネントを選んでください。

#### 1. 基本コンポーネント (全スタイル共通)
| `type` | 説明 | 必須項目 (`data`) |
| :--- | :--- | :--- |
| `hero` | ページの顔となるトップ画像とキャッチコピー | `headline`, `image_url`, `cta` |
| `trouble` | ユーザーの悩み/共感チェックリスト | `title`, `items` (配列) |
| `features` | サービスの特徴・選ばれる理由 (3カラム) | `data` (配列: `title`, `description`, `icon_url`) |
| `flow` | 利用の流れ (ステップ表示) | `steps` (配列) |
| `pricing` | 料金プラン表示 | `plans` (配列) |
| `faq` | よくある質問 (アコーディオン) | `items` (配列: `q`, `a`) |
| `cta` | コンバージョンエリア (クロージング) | `title`, `button_text`, `url` |

#### 2. ブランディング・信頼性 (Standard / Premium / Natural)
| `type` | 説明 | 推奨スタイル |
| :--- | :--- | :--- |
| `message` | **医師・代表者からのメッセージ**。<br>顔写真と挨拶文を掲載し、信頼感を醸成します。 | `standard`, `premium` |
| `concept` | ブランドコンセプト・哲学の紹介。<br>情緒的な画像とテキストで世界観を伝えます。 | `premium`, `natural` |
| `voice` | ユーザーの口コミ・レビュー (スライダー)。<br>横スクロールで実績をアピールします。 | `standard`, `natural` |

#### 3. ストーリー・キャンペーン (Manga / Cyber)
| `type` | 説明 | 推奨スタイル |
| :--- | :--- | :--- |
| `comic_strip` | **[Manga専用]** 縦読みマンガ画像。<br>画像を隙間なく積み重ね、ストーリーを展開します。 | `manga` |
| `campaign_box` | バナー画像＋テキストのハイブリッド訴求。<br>クーポン詳細など、SEOを守りつつ派手に見せます。 | `manga`, `cyber` |
| `video` | YouTubeやMP4動画の埋め込み。 | `standard`, `cyber` |

### 医師・権威性画像の掲載方法 (`message` コンポーネント)
「Standard」「Premium」スタイルでは、医師の信頼感がCVを左右します。
`message` コンポーネントに `image_url` を指定することで、丸アイコン(Standard)やポートレート(Premium)として表示されます。

```json
{
    "type": "message",
    "data": {
        "title": "貴方の肌のかかりつけ医として",
        "content": "忙しい毎日でも、美しさを諦めないでください。...",
        "doctor_name": "統括院長 田中 花子",
        "image_url": "static/images/doctor_tanaka.jpg" 
        // ↑ ここに画像パスを指定すると、自動的にレイアウトされます
    }
}
```

### ページ内リンク (アンカー)
主要セクションには自動的にIDが付与されます。
CTAボタンのURLを以下のように指定することで、ページ内スムーススクロールが可能です。

| ID | セクション |
| :--- | :--- |
| `#hero` | トップ (Hero) |
| `#trouble` | お悩み (Trouble) |
| `#features` | 特徴 (Features) |
| `#flow` | 流れ (Flow) |
| `#pricing` | 料金 (Pricing) |
| `#faq` | 質問 (FAQ) |
| `#cta` | 申し込み (CTA) |

### その他機能
*   **法的記載の自動挿入**: フッター直前に、医療広告ガイドライン準拠の「自由診療・リスク・料金目安」が自動的に挿入されます（フォントはゴシック体固定）。
*   **ディレクトリ分離**: 生成物は `output/【企画書名】/【スタイル名】/` に別々に保存されます。

## 開発者向け情報
*   **CSS設計**: `destyle.css` でリセットし、スタイルごとの `style.css` でデザインを定義しています。配色 (`--primary-color` 等) はJSONから動的に注入されます。
*   **画像生成**: `static/images/generated/【プラン名】/` 以下に資産を配置することを推奨します。JSON内のパスもそれに合わせて記述してください。
