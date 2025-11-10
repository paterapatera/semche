# ユーザーはchromaDBのSQLiteを利用して、ファイルパスの前方一致でドキュメントを取得できる

## 概要

ユーザーはChromaDBのSQLiteストレージを利用し、ファイルパスの前方一致（prefix検索）によって複数のドキュメントを一括取得できる機能を利用できるようにする。

### 目的・背景

searchツールで得た情報から、実際のコード（ドキュメント）をさらに確認したい場合がある。取得情報からファイルパスを推測し、そのパスの前方一致で関連ドキュメントを一括取得したい。

### ツール仕様（Phase 1合意内容）

- ツール名（仮）：get_documents_by_prefix
- 引数：
  - prefix（str, 必須）：検索対象のファイルパスprefix
  - file_type（str, 必須）：ドキュメント種別でのフィルタ
  - include_documents（bool, 任意, デフォルトTrue）：本文を含めるか
  - top_k（int, 任意）：最大取得件数（指定がなければ全件）
- 返却値：一致したドキュメントのリスト（dict形式、filepath/updated_at/file_type/内容 など）

### 技術スタック・ファイル構成案

- Python（既存MCPサーバーと同様）
- FastMCP（ツール公開）
- ChromaDB（SQLite永続化）
- `src/semche/tools/get_by_prefix.py`：前方一致取得ツール本体（@mcp.tool公開）
- `src/semche/chromadb_manager.py`：前方一致検索ロジック追加
- `src/semche/mcp_server.py`：ツール登録
- `tests/test_get_by_prefix.py`：テストコード
- `README.md`/`get_by_prefix.py.exp.md`：設計・仕様追記

#### get_documents_by_prefix()

- 目的: id（filepath）の前方一致＋file_type完全一致でドキュメントを取得（ChromaDBのSQLiteを直接操作）
- 入力:
  - `prefix: str` id（filepath）の前方一致条件（必須）
  - `file_type: str` 完全一致条件（必須）
  - `include_documents: bool` 本文を含めるか（デフォルト True）
  - `top_k: int | None` 最大取得件数（省略時は全件）
- 実装:
  - Pythonのsqlite3でChromaDBのSQLiteファイルを直接開く
  - `embeddings`テーブルの`id`で`LIKE 'prefix%'`検索
  - `metadatas`テーブルの`file_type`で完全一致
  - `collections`テーブルでcollection_nameを特定
  - JOINで必要な情報をまとめて取得
  - `top_k`指定時はSQLに`LIMIT`句を追加
- 戻り値: `[{"id": str, "document": str | None, "file_type": str}, ...]`
- 用途: search結果から得たファイルパスprefixで関連ドキュメントを一括取得したい場合など
- 注意:
  - ChromaDBのバージョンや内部構造変更によりSQLは要調整
  - 取得件数が多い場合はパフォーマンスに注意
  - SQLite直クエリのため、ChromaDBのAPIバージョンアップ時は要検証

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する
- [x] 実装する機能の詳細をユーザーと対話して決定する
- [x] 技術スタック（使用するライブラリ・フレームワーク）をユーザーと相談する
- [x] ファイル構成案を提示し、ユーザーの承認を得る
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [x] ChromaDBのSQLiteストレージでファイルパスの前方一致検索を実装する
- [x] MCPツールまたはAPIとして公開する
- [x] コア機能の実装が完了している
- [x] `CODE_REVIEW_GUIDE.md` に準拠してコードレビューが完了している
- [x] テストコードが作成されている
- [x] テストが全てパスする
- [x] Lint（ruff）/ 型チェック（mypy）が通る
- [x] README.md と詳細設計書（`.exp.md`）を更新済み（ツール一覧・引数/返却仕様）

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [x] 実装完了を報告し、ユーザーにレビューを依頼する
- [x] 手動での動作確認を行う
- [x] 今回更新したコードの詳細設計書を更新する
- [x] **全ての作業完了をユーザーに報告する**
