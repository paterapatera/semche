# ユーザーはCLIでドキュメントを一括登録できる

## 概要

ローカルのテキストファイル群をCLIから一括でベクトル化し、ChromaDBに保存（upsert）できるようにします。既存の埋め込み（`embedding.py`）とストレージ層（`chromadb_manager.py`）を活用し、MCPツールの `put_document` と同等の結果を得られることを目標とします。対象はUTF-8テキストを基本とし、バイナリや読み込み失敗したファイルはスキップします。

- 入力: ファイルパス/ディレクトリ/ワイルドカード（例: `/var/test/**/*.md`）（複数可）
- ID生成: 実行ディレクトリからの相対パス（`--id-prefix` でプレフィックス付与可能。例: `abc:test/test1.md`）
- 出力: ChromaDB（`SEMCHE_CHROMA_DIR` または `--chroma-dir` で指定）に保存、メタデータ（`filepath`, `updated_at`, `file_type`）
- 動作: 既存ID（= filepath）は更新（upsert）
- フィルタ: `--file-type`（単一指定）、`--filter-from-date`（指定日時より新しいファイル）、`--ignore`（特定パターン除外）
- 目的: コードベース、ドキュメント群、メモ等をまとめて登録・更新できる運用導線の提供

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する（CLI導線での一括登録ニーズ、運用フロー）
- [x] 実装する機能の詳細をユーザーと対話して決定する
  - [x] 入力指定: ワイルドカード（`/var/test/**/*.md`）、ディレクトリ、ファイル（複数指定可）
  - [x] ID生成: 実行ディレクトリからの相対パス + オプショナルプレフィックス（`--id-prefix`）
  - [x] `file_type` の扱い: 単一値のみ指定可能（例: `spec`）、未指定時は `none`
  - [x] フィルタ条件: `--file-type`（登録時のfile_type指定、単一値）、`--filter-from-date`（指定日時以降の更新ファイル）、`--ignore`（除外パターン）
  - [x] 不要オプション: `--max-bytes`, `--file-type-map`, `--normalize`, `--dry-run` は実装しない
  - [x] ChromaDB保存先: `SEMCHE_CHROMA_DIR` または `--chroma-dir`
  - [x] エラー時の継続方針: best-effort（失敗ファイルはスキップし、サマリに記録）
  - [x] エントリポイント: `doc-update = "semche.cli.bulk_register:main"`
- [x] 技術スタックを確認する（標準 `argparse` で実装。追加依存は避ける）
- [x] ファイル構成案を提示し、ユーザーの承認を得る
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [x] CLIエントリの追加
  - `src/semche/cli/` を新設し、`bulk_register.py` を作成
  - `argparse` で引数定義:
    - 位置引数: `inputs...`（ファイル/ディレクトリ/ワイルドカード `**/*.md` など複数可）
    - `--id-prefix PREFIX`: ID（filepath）に付与するプレフィックス（例: `abc`）
    - `--file-type TYPE`: 登録時のfile_type（単一値、未指定時は `none`）
    - `--filter-from-date YYYY-MM-DD` または `YYYY-MM-DDTHH:MM:SS`: 指定日時より新しいファイルのみ対象
    - `--ignore PATTERN`: 除外パターン（複数回指定可、グロブ形式）
    - `--chroma-dir DIR`: ChromaDB保存先（環境変数 `SEMCHE_CHROMA_DIR` より優先）
  - エントリポイント: `pyproject.toml` の `[project.scripts]` に `doc-update = "semche.cli.bulk_register:main"`
- [x] コア処理
  - 入力解決: ワイルドカード展開（`**` 対応のglob）、ディレクトリ再帰、ignoreパターン適用、重複排除
  - 相対パス化: 実行ディレクトリ（`cwd`）を基準とした相対パスを生成（例: `/var` で実行 → `/var/test/test1.md` → `test/test1.md`）
  - IDプレフィックス適用: `--id-prefix abc` なら `abc:test/test1.md`
  - 日付フィルタ: `--filter-from-date` 指定時は `os.path.getmtime()` で更新日時チェック
  - 読み込み: UTF-8、BOM許容、バイナリ検知でスキップ
  - `file_type` 付与: `--file-type spec` → 各ドキュメントに `spec` をメタデータとして設定（未指定は `none`）
  - バッチ構築: embeddings/documents/filepaths（ID）/updated_at/file_types
  - `Embedder` によりテキストを768次元ベクトル化（`ensure_single_vector()`）
  - `ChromaDBManager.save()` による一括保存（upsert）
  - 進捗/結果の要約を表示（成功件数、スキップ件数、失敗件数）
- [x] エラーハンドリング
  - 読み込み失敗/エンコード不明/バイナリ/空コンテンツはスキップし、警告収集
  - 保存時例外は件名と併せて一覧化
  - best-effort方針（失敗してもスキップして継続）
- [x] `CODE_REVIEW_GUIDE.md` に準拠してコードレビューが完了している
- [x] テストコードが作成されている（`tests/test_cli_bulk_register.py`）
- [x] テストが全てパスする
- [x] Lint（ruff）/ 型チェック（mypy）が通る
- [x] README.md を更新（CLIの使い方、オプション一覧、例）
- [x] 詳細設計書（`.exp.md`）を作成（`src/semche/cli/bulk_register.py.exp.md`）

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [ ] 実装完了を報告し、ユーザーにレビューを依頼する
- [ ] 手動での動作確認（小規模/中規模のディレクトリで）
- [ ] 更新したコードの詳細設計書を更新する
- [ ] **全ての作業完了をユーザーに報告する**

---

## 受け入れ基準（Acceptance Criteria）

- ワイルドカード（`/var/test/**/*.md`）、ディレクトリ、ファイルを混在指定可能
- ID生成: 実行ディレクトリからの相対パスをベースに、`--id-prefix` 指定時はプレフィックスを付与（例: `abc:test/test1.md`）
- `--file-type` で単一値を指定可能、未指定時は `none` が設定される
- `--filter-from-date` で指定日時より新しいファイルのみ登録
- `--ignore` で除外パターン指定可能（複数回指定可）
- `SEMCHE_CHROMA_DIR` または `--chroma-dir` で保存先を切り替え可能
- 既存と同一 `filepath`（ID）を含む場合でもエラーにせず upsert される
- 失敗した項目がある場合でも処理は継続し、終了時にサマリ（成功/失敗/スキップ件数）を表示する
- エントリポイント `doc-update` で起動可能（`pyproject.toml` に定義）

## 設計メモ（高レベル）

- 実装方式
  - 直接ライブラリ呼び出し（`Embedder` + `ChromaDBManager`）。MCP経由に比べてオーバーヘッドが少ない
- ID生成
  - 実行ディレクトリ（`os.getcwd()`）からの相対パスを基準（`os.path.relpath()`）
  - `--id-prefix PREFIX` 指定時は `PREFIX:{相対パス}` 形式（例: `abc:test/test1.md`）
- file_type
  - `--file-type spec` → メタデータに `spec` を設定
  - 未指定時は `none`
- フィルタ
  - `--filter-from-date`: ISO8601形式（`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`）でパース、`os.path.getmtime()` と比較
  - `--ignore`: グロブパターン（複数指定可）、マッチしたパスをスキップ
- エンコーディング
  - UTF-8を既定。判別不能やバイナリはスキップ
- バッチ保存
  - 収集したファイル群を一括で `ChromaDBManager.save()` に投入（upsert）

## 想定CLI仕様（案）

```
doc-update [inputs ...]
  --id-prefix PREFIX
  --file-type TYPE
  --filter-from-date YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
  --ignore PATTERN (複数回指定可)
  --chroma-dir DIR
```

- 例1: `/var/test/` 配下のMarkdownファイルを `abc` プレフィックスで登録（実行場所: `/var`）

```bash
cd /var
doc-update "test/**/*.md" --id-prefix abc --file-type note
# → test/test1.md は abc:test/test1.md として登録される
```

- 例2: 2025年11月1日以降に更新されたファイルのみ登録

```bash
doc-update ./docs --filter-from-date 2025-11-01 --file-type spec
```

- 例3: `.git` や `node_modules` を除外

```bash
doc-update ./project --ignore "**/.git/**" --ignore "**/node_modules/**" --file-type code
```

- 例4: 保存先を指定

```bash
doc-update ./notes --chroma-dir /tmp/chroma --file-type note
# または環境変数で
SEMCHE_CHROMA_DIR=/tmp/chroma doc-update ./notes --file-type note
```

## テスト計画（概要）

- 単体
  - 入力解決: ワイルドカード/ディレクトリ/ignore/重複排除
  - 相対パス化: 実行ディレクトリ基準での相対パス生成
  - IDプレフィックス: `--id-prefix` 指定時の `PREFIX:相対パス` 形式
  - 日付フィルタ: `--filter-from-date` による更新日時比較
  - 読み込み: UTF-8/バイナリ検知
  - 変換: `Embedder` によるベクトル取得（1文書→1ベクトル）
  - 保存: `ChromaDBManager.save()` 呼び出し回数・引数の検証（モック）
- 結合
  - 一連のフロー（`tests/conftest.py` により `SEMCHE_CHROMA_DIR` は一時ディレクトリ）
  - upsert 挙動（同一 `filepath` を2回投入）
- CLI
  - `pytest` から `subprocess` 実行 or モジュールの `main()` 実行（戻りコード0、サマリ出力）

## 変更予定ファイル/追加ファイル

- 追加
  - `src/semche/cli/__init__.py`
  - `src/semche/cli/bulk_register.py`
  - `src/semche/cli/bulk_register.py.exp.md`
  - `tests/test_cli_bulk_register.py`
- 変更
  - `README.md`（CLI使い方の章を追加: `doc-update` コマンドの説明、オプション、例）
  - `pyproject.toml`（エントリポイント定義: `doc-update = "semche.cli.bulk_register:main"`）

## リスクと緩和策

- 大量ファイルでのメモリ使用量: バッチ単位で保存し、逐次フラッシュ
- 埋め込みモデルの初期化コスト: プロセス内で使い回す
- 文字コード/巨大ファイル: 安全側にスキップし、警告とサマリで可視化
- ワイルドカード展開の負荷: `pathlib` や `glob` の再帰検索を利用し、効率的に処理

## 次の一歩（スモールスタート）

1. Phase 1 の確認をユーザーと完了 ✅
2. 最小オプションで `bulk_register.py` を作成（`inputs`, `--id-prefix`, `--file-type`, `--filter-from-date`, `--ignore`, `--chroma-dir`）
3. 小さなディレクトリを対象にテストを通す
4. `README.md` にCLIセクション追記、`pyproject.toml` にエントリポイント定義
