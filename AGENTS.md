## ストーリー作成ガイドライン

作成場所: プロジェクトのルートディレクトリ直下の`story`フォルダ内

下記のテンプレートに従い、ストーリーを作成してください。

---

## MCPサーバー開発ガイドライン（README.mdより抜粋・補足）

### 概要

- 本プロジェクトは LangChain と ChromaDB のベクトル検索に BM25 を統合したハイブリッド検索（dense + sparse）を提供する MCP サーバー実装です。
- 実装済み機能:
  - `embedding.py`: sentence-transformers/stsb-xlm-r-multilingual による 768 次元ベクトル変換（ヘルパー `ensure_single_vector()` を提供）
  - `chromadb_manager.py`: ローカル永続化 ChromaDB への保存（upsert 対応、メタデータ: filepath/updated_at/file_type）、検索（query）、取得（get）、削除（delete）
    - **v0.3.0**: LangChain Chroma ベクトルストア統合（`similarity_search_by_vector_with_score()` 使用）
    - **v0.4.0**: ハイブリッド検索（dense + sparse, RRF）を標準化。BM25 スパースエンコーダと `HybridRetriever` を追加。`get_all_documents()` を実装
  - `mcp_server.py`: FastMCP でツールを登録（実装は `src/semche/tools/` へ委譲）
  - MCPツール:
    - `put_document`: ドキュメント登録
    - `search`: ハイブリッド検索（Dense + Sparse, RRF）。必須: `query`、オプション: `top_k`/`file_type`/`include_documents`
    - `delete_document`: 単一 ID 削除
  - CLIツール: `doc-update`（一括ドキュメント登録）
    - ワイルドカード対応、日付フィルタ、ignore パターン、ID プレフィックス
    - **デフォルト: 絶対パスで ID 生成**（v0.2.0 より）
    - `--use-relative-path` オプションで相対パスに切り替え可能
    - パス区切り文字を `/` に統一（Windows 互換性）
- 今後の拡張: スパースインデックスの永続管理、条件削除/バッチ削除、ツールの拡充、パフォーマンス最適化

### 開発・運用手順

1. 新規ツール追加は FastMCP の `@mcp.tool()` で公開し、実装は `src/semche/tools/*.py` に配置。テストは `tests/` 配下に追加。
2. 依存管理は `pyproject.toml` で行い、`uv sync` でインストール。
3. サーバー起動は `uv run python src/semche/mcp_server.py`。
4. MCP Inspector による対話テストが可能（`uv run mcp dev src/semche/mcp_server.py`）。
5. CLI 起動は `uv run doc-update`（一括ドキュメント登録）。
6. テストは `uv run pytest` で実行。
7. コード品質チェックは `uv run ruff check .`（Lint）と `uv run mypy src/semche`（型チェック）で実行。

### プロジェクト構成例

```
/home/pater/semche/
├── src/semche/         # サーバー・ツール実装
│   ├── mcp_server.py                # MCPサーバー本体（ツール登録のみ）
│   ├── mcp_server.py.exp.md         # サーバー設計（委譲方針）
│   ├── tools/                       # ツール実装（サーバーから委譲）
│   │   ├── __init__.py
│   │   ├── document.py              # put_documentツール
│   │   ├── document.py.exp.md       # put_documentツール詳細設計
│   │   ├── search.py                # searchツール
│   │   ├── search.py.exp.md         # searchツール詳細設計（ハイブリッド検索）
│   │   ├── delete.py                # delete_documentツール
│   │   └── delete.py.exp.md         # delete_documentツール詳細設計
│   ├── cli/                         # CLIツール
│   │   ├── __init__.py
│   │   ├── bulk_register.py         # doc-updateコマンド（一括登録）
│   │   └── bulk_register.py.exp.md  # CLI詳細設計
│   ├── embedding.py                 # ベクトル埋め込み機能
│   ├── embedding.py.exp.md          # 埋め込みモジュール詳細設計書
│   ├── chromadb_manager.py          # ChromaDB保存管理
│   ├── chromadb_manager.py.exp.md   # ChromaDBモジュール詳細設計書
│   ├── sparse_encoder.py            # BM25 スパースエンコーダ
│   ├── sparse_encoder.py.exp.md     # スパースエンコーダ詳細設計
│   ├── hybrid_retriever.py          # ハイブリッド検索（RRF統合）
│   └── hybrid_retriever.py.exp.md   # ハイブリッド検索詳細設計
├── tests/              # テストコード
│   ├── conftest.py                   # テスト分離（SEMCHE_CHROMA_DIRを一時ディレクトリに）
│   ├── test_delete.py                # 削除ツールのテスト
│   ├── test_search.py                # 検索ツールのテスト（ハイブリッド）
│   ├── test_sparse_encoder.py        # BM25 エンコーダのテスト
│   ├── test_embedding_helper.py      # ensure_single_vectorのテスト
│   ├── test_cli_bulk_register.py     # CLI一括登録のテスト
│   └── ...
├── story/              # ストーリー管理（要件・設計・完了記録）
├── pyproject.toml      # 依存管理
├── README.md           # プロジェクト概要
└── AGENTS.md           # 本ファイル（開発ガイドライン）
```

### ツール追加・拡張のポイント

- FastMCP の `@mcp.tool()` で公開し、実装は `src/semche/tools/*.py` に配置。関数のシグネチャは型ヒントと docstring で定義し、README のツール一覧にパラメータ・返却値を追記。
- 戻り値は辞書（dict）形式を推奨（MCP Inspector で構造化データとして表示される）。
- 検索機能は LangChain/ChromaDB + BM25 を前提（ハイブリッド検索）。
- 詳細設計書は `.exp.md` 形式で各コードファイルと同じ場所に配置（ツールごとに作成）。

### テスト・開発運用

- MCP Inspector で対話テスト可能。
- pytest で自動テスト・カバレッジ計測。
- Lint は ruff（`uv run ruff check .`）で実行、自動修正は `--fix` オプション付与。
- 型チェックは mypy（`uv run mypy src/semche`）で実行。
- 依存追加時は `uv sync` で反映。
- テスト分離: `tests/conftest.py` にて `SEMCHE_CHROMA_DIR` をテストごとに一意の一時ディレクトリへ設定（テスト間の DB 汚染を防止）。

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
- [ ] Lint（ruff）/ 型チェック（mypy）が通る
- [ ] README.md と詳細設計書（`.exp.md`）を更新済み（ツール一覧・引数/返却仕様）

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
