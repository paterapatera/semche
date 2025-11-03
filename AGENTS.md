## ストーリー作成ガイドライン

作成場所: プロジェクトのルートディレクトリ直下の`story`フォルダ内

下記のテンプレートに従い、ストーリーを作成してください。

---

## MCPサーバー開発ガイドライン（README.mdより抜粋・補足）

### 概要

- 本プロジェクトはLangChainとChromaDBによるベクトル検索機能を目指すMCPサーバー実装です。
- 実装済み機能:
  - `embedding.py`: sentence-transformers/stsb-xlm-r-multilingualによる768次元ベクトル変換
  - `chromadb_manager.py`: ローカル永続化ChromaDBへの保存（upsert対応、メタデータ: filepath/updated_at/file_type）
  - `mcp_server.py`: FastMCPでツールを登録（実装は`src/semche/tools/`へ委譲）
  - MCPツール: `hello`, `put_document`（テキストをベクトル化してChromaDBに保存・upsert）
- 今後の拡張: 類似検索ツール（search）、MCPツールの拡充

### 開発・運用手順

1. 新規ツール追加はFastMCPの`@mcp.tool()`で公開し、実装は`src/semche/tools/*.py`に配置。テストは`tests/`配下に追加。
2. 依存管理は`pyproject.toml`で行い、`uv sync`でインストール。
3. サーバー起動は`uv run python src/semche/mcp_server.py`。
4. MCP Inspectorによる対話テストが可能。
5. テストは`uv run pytest`で実行。

### プロジェクト構成例

```
/home/pater/semche/
├── src/semche/         # サーバー・ツール実装
│   ├── mcp_server.py                # MCPサーバー本体（ツール登録のみ）
│   ├── mcp_server.py.exp.md         # サーバー設計（委譲方針）
│   ├── tools/                       # ツール実装（サーバーから委譲）
│   │   ├── __init__.py
│   │   ├── hello.py                 # helloツール
│   │   ├── hello.py.exp.md          # helloツール詳細設計
│   │   ├── document.py              # put_documentツール
│   │   └── document.py.exp.md       # put_documentツール詳細設計
│   ├── embedding.py                 # ベクトル埋め込み機能
│   ├── embedding.py.exp.md          # 埋め込みモジュール詳細設計書
│   ├── chromadb_manager.py          # ChromaDB保存管理
│   └── chromadb_manager.py.exp.md   # ChromaDBモジュール詳細設計書
├── tests/              # テストコード
├── story/              # ストーリー管理（要件・設計・完了記録）
├── pyproject.toml      # 依存管理
├── README.md           # プロジェクト概要
└── AGENTS.md           # 本ファイル（開発ガイドライン）
```

### ツール追加・拡張のポイント

- FastMCPの`@mcp.tool()`で公開し、実装は`src/semche/tools/*.py`に配置。関数のシグネチャは型ヒントとdocstringで定義し、READMEのツール一覧にパラメータ・返却値を追記する。
- ベクトル埋め込み・検索機能はLangChain/ChromaDBのAPI設計に準拠。
- 詳細設計書は`.exp.md`形式で各コードファイルと同じ場所に配置（ツールごとに作成）。

### テスト・開発運用

- MCP Inspectorで対話テスト可能。
- pytestで自動テスト・カバレッジ計測。
- 依存追加時は`uv sync`で反映。

---

````markdown
# {ストーリーのタイトル}

## 概要

{ストーリーの概要を記載してください}

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [ ] ストーリーの背景と目的を確認する
- [ ] 実装する機能の詳細をユーザーと対話して決定する
- [ ] 技術スタック（使用するライブラリ・フレームワーク）をユーザーと相談する
- [ ] ファイル構成案を提示し、ユーザーの承認を得る
- [ ] **Phase 1完了の確認をユーザーから得てから次に進む**
- [ ] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [ ] {必要に応じて実装手順を追加してください}
- [ ] コア機能の実装が完了している
- [ ] `CODE_REVIEW_GUIDE.md` に準拠してコードレビューが完了している
- [ ] テストコードが作成されている
- [ ] テストが全てパスする

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [ ] 実装完了を報告し、ユーザーにレビューを依頼する
- [ ] 手動での動作確認を行う
- [ ] 今回更新したコードの詳細設計書を更新する
- [ ] **全ての作業完了をユーザーに報告する**

```

## 詳細設計書作成ガイドライン

以下の条件に従い、指定されたコードファイルをexplainしたドキュメントを作成してください。

- ドキュメントの配置場所：コードファイルと同じパスに配置する
- ドキュメントファイル名：{コードファイル名} + `.exp.md`
  - コードファイル名が`hoge.php`の場合は、explainドキュメント名は`hoge.php.exp.md`となる
- explainではコード内で利用しているクラスのファイルパスを一覧でまとめるのも必須です

注意: テストコードは除外してください。
```
````
