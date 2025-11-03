# bulk_register.py 詳細設計書

## 概要

このファイルは、ローカルファイル群を一括でベクトル化し、ChromaDBに登録するCLIツールです。
ワイルドカード指定、日付フィルタ、ignoreパターン、IDプレフィックスなどの機能を提供します。

## ファイルパス

`/home/pater/semche/src/semche/cli/bulk_register.py`

## 依存関係

### 外部ライブラリ

- `argparse`: コマンドライン引数解析
- `pathlib.Path`: ファイルパス操作
- `datetime`: 日付フィルタ処理

### 内部モジュール

- `semche.chromadb_manager.ChromaDBManager`: ChromaDBへの保存
- `semche.chromadb_manager.ChromaDBError`: ChromaDBエラーハンドリング
- `semche.embedding.Embedder`: テキストの埋め込み生成
- `semche.embedding.ensure_single_vector`: ベクトル形式の正規化

### 標準ライブラリ

- `logging`: ロギング
- `os`: ファイル操作
- `sys`: システム終了コード

### 利用しているクラス・モジュール

| モジュール/クラス      | インポート元              | 用途                   |
| ---------------------- | ------------------------- | ---------------------- |
| `ChromaDBManager`      | `semche.chromadb_manager` | ドキュメントの一括保存 |
| `ChromaDBError`        | `semche.chromadb_manager` | エラーハンドリング     |
| `Embedder`             | `semche.embedding`        | テキストのベクトル化   |
| `ensure_single_vector` | `semche.embedding`        | ベクトル形式の正規化   |

## 関数一覧

### `parse_args() -> argparse.Namespace`

コマンドライン引数を解析します。

**引数**: なし

**戻り値**: 解析済み引数オブジェクト

**主な引数**:

- `inputs` (位置引数): ファイル/ディレクトリ/ワイルドカードパターン（複数可）
- `--id-prefix`: ドキュメントIDのプレフィックス
- `--file-type`: メタデータのfile_type（デフォルト: `none`）
- `--filter-from-date`: 指定日時以降のファイルのみ対象
- `--ignore`: 除外パターン（複数指定可）
- `--chroma-dir`: ChromaDB保存先ディレクトリ

### `parse_date_filter(date_str: str) -> datetime`

日付フィルタ文字列をdatetimeオブジェクトに変換します。

**引数**:

- `date_str`: 日付文字列（`YYYY-MM-DD`、`YYYY-MM-DDTHH:MM:SS`、ISO8601）

**戻り値**: datetimeオブジェクト

**例外**:

- `ValueError`: 不正な日付形式の場合

**対応フォーマット**:

- `YYYY-MM-DD` (例: `2025-11-01`)
- `YYYY-MM-DDTHH:MM:SS` (例: `2025-11-01T12:30:45`)
- ISO8601フルフォーマット

### `should_ignore(path: Path, ignore_patterns: List[str]) -> bool`

パスがignoreパターンに一致するかチェックします。

**引数**:

- `path`: チェック対象のパス
- `ignore_patterns`: ignoreパターンのリスト（glob形式）

**戻り値**: 一致する場合`True`

### `is_binary_file(file_path: Path) -> bool`

ファイルがバイナリかどうかを判定します。

**引数**:

- `file_path`: チェック対象ファイルパス

**戻り値**: バイナリの場合`True`

**判定方法**: 先頭8KBを読み込み、null文字（`\0`）の有無で判定

### `resolve_inputs(inputs: List[str], ignore_patterns: List[str], filter_date: Optional[datetime], cwd: Path) -> List[Path]`

入力パターンを実際のファイルパスリストに解決します。

**引数**:

- `inputs`: ファイル/ディレクトリ/ワイルドカードパターン
- `ignore_patterns`: 除外パターン
- `filter_date`: 日付フィルタ（指定日時以降のファイルのみ）
- `cwd`: 現在の作業ディレクトリ

**戻り値**: 解決されたファイルパスのリスト

**処理フロー**:

1. ワイルドカード（`**/*.md`）を展開
2. ディレクトリを再帰的に走査
3. 単一ファイルを追加
4. ignoreパターンでフィルタ
5. 日付フィルタを適用（`os.path.getmtime()`で更新日時をチェック）
6. 重複を除去してソート

### `generate_document_id(file_path: Path, cwd: Path, prefix: str) -> str`

ファイルパスからドキュメントIDを生成します。

**引数**:

- `file_path`: 絶対ファイルパス
- `cwd`: 現在の作業ディレクトリ
- `prefix`: IDプレフィックス（オプション）

**戻り値**: ドキュメントID

**ID生成ルール**:

1. `cwd`からの相対パスを計算（`os.path.relpath()`）
2. パスセパレータを`/`に統一
3. プレフィックスがある場合: `{prefix}:{relative_path}`
4. プレフィックスがない場合: `{relative_path}`

**例**:

- `cwd=/var`, `file=/var/test/file.md`, `prefix=""` → `test/file.md`
- `cwd=/var`, `file=/var/test/file.md`, `prefix="abc"` → `abc:test/file.md`

### `read_file_content(file_path: Path) -> Optional[str]`

ファイル内容をUTF-8テキストとして読み込みます。

**引数**:

- `file_path`: 読み込み対象ファイルパス

**戻り値**: ファイル内容（スキップする場合は`None`）

**スキップ条件**:

- バイナリファイル
- 空ファイルまたは空白のみのファイル
- エンコードエラー（UTF-8以外）
- 読み込みエラー

### `process_files(file_paths: List[Path], cwd: Path, id_prefix: str, file_type: str, embedder: Embedder) -> Tuple[...]`

ファイルリストを処理し、埋め込みベクトルとメタデータを生成します。

**引数**:

- `file_paths`: 処理対象ファイルパスのリスト
- `cwd`: 現在の作業ディレクトリ
- `id_prefix`: IDプレフィックス
- `file_type`: メタデータのfile_type
- `embedder`: Embedderインスタンス

**戻り値**: `(embeddings, documents, ids, updated_at_list, file_types)` のタプル

**処理フロー**:

1. ファイル内容を読み込み（`read_file_content()`）
2. ドキュメントIDを生成（`generate_document_id()`）
3. ファイルの更新日時を取得（`os.path.stat().st_mtime`）
4. テキストをベクトル化（`embedder.addDocument()`）
5. ベクトル形式を正規化（`ensure_single_vector()`）
6. バッチデータに追加

**エラーハンドリング**: 失敗したファイルはスキップし、警告ログを出力

### `main() -> int`

CLIのメインエントリポイントです。

**戻り値**: 終了コード（成功: 0、失敗: 1）

**処理フロー**:

1. コマンドライン引数を解析
2. 現在の作業ディレクトリを取得
3. 日付フィルタをパース
4. 入力ファイルを解決（`resolve_inputs()`）
5. Embedder と ChromaDBManager を初期化
6. ファイルを処理（`process_files()`）
7. ChromaDB に一括保存（`ChromaDBManager.save()`）
8. 結果サマリを出力

**ログ出力**:

- INFO: 処理進捗、成功件数、スキップ件数
- WARNING: スキップしたファイルの詳細
- ERROR: 致命的エラー

## データフロー

```
コマンドライン引数
    ↓
parse_args()
    ↓
resolve_inputs() → ファイルパスリスト
    ↓
process_files()
    ├→ read_file_content() → テキスト
    ├→ generate_document_id() → ID
    ├→ Embedder.addDocument() → ベクトル
    └→ ensure_single_vector() → 正規化ベクトル
    ↓
ChromaDBManager.save() → 一括保存
    ↓
結果サマリ出力
```

## エラーハンドリング

### ファイルレベルエラー

- バイナリファイル: スキップ（DEBUGログ）
- エンコードエラー: スキップ（WARNINGログ）
- 読み込みエラー: スキップ（WARNINGログ）
- 埋め込みエラー: スキップ（WARNINGログ）

### システムレベルエラー

- 不正な日付形式: 終了コード1
- 入力解決エラー: 終了コード1
- 初期化エラー: 終了コード1
- ChromaDB保存エラー: 終了コード1

## セキュリティ考慮事項

- ファイルパス: 絶対パスへ解決し、シンボリックリンク攻撃を防止
- バイナリ検知: null文字チェックで実行ファイル等を除外
- メモリ: 大量ファイルはスキップログで警告（現状は全件メモリ展開）

## パフォーマンス考慮事項

- バッチ保存: 全ファイルを一括で`ChromaDBManager.save()`に投入
- 埋め込み: ファイル毎に逐次処理（並列化は将来の拡張）
- ワイルドカード展開: `pathlib.glob()`の効率的な再帰検索を利用

## 改善案

- 並列処理: `concurrent.futures`で埋め込み生成を並列化
- バッチサイズ: 大量ファイル時は分割保存
- プログレスバー: `tqdm`でユーザーフィードバック向上
- リトライ: 一時的なエラーのリトライロジック

## テスト

関連テストファイル: `/home/pater/semche/tests/test_cli_bulk_register.py`

**テストカバレッジ**:

- 日付パース（正常/異常）
- ignoreパターンマッチング
- バイナリファイル検知
- ID生成（相対パス、プレフィックス）
- ファイル読み込み（UTF-8、空、バイナリ）
- 入力解決（単一ファイル、ディレクトリ、ignore、日付フィルタ）
- ファイル処理（単一、プレフィックス、バイナリスキップ）
- 統合テスト（基本フロー、ファイル未検出）

## 使用方法

### 基本的な使用例

```bash
# ディレクトリ配下のMarkdownファイルを登録
doc-update ./docs/**/*.md --file-type note

# プレフィックス付きで登録
doc-update ./project --id-prefix myproject --file-type code

# 日付フィルタとignoreパターン
doc-update ./wiki --filter-from-date 2025-11-01 --ignore "**/.git/**"

# ChromaDB保存先を指定
doc-update ./notes --chroma-dir /tmp/chroma --file-type memo
```

### エントリポイント

`pyproject.toml` に定義:

```toml
[project.scripts]
doc-update = "semche.cli.bulk_register:main"
```

インストール後、`doc-update` コマンドとして利用可能。

## バージョン情報

- 初版作成日: 2025-11-03
- バージョン: 0.1.0
- 最終更新日: 2025-11-03

## 変更履歴

| 日付       | バージョン | 変更内容                        |
| ---------- | ---------- | ------------------------------- |
| 2025-11-03 | 0.1.0      | 初版作成。CLI一括登録機能の実装 |
