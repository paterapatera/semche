# ユーザーはCLIの一括登録時に相対パスではなく、絶対パスでも登録できる

## 概要

現在のCLI一括登録機能（`doc-update`）は相対パスでドキュメントIDを生成していますが、絶対パスでの登録もサポートすることで、より柔軟なドキュメント管理を可能にします。これにより、異なるディレクトリから実行した場合でも一貫したIDでドキュメントを管理でき、重複登録を防ぐことができます。

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する
  - 現在の実装: 相対パスでID生成（実行ディレクトリに依存）
  - 課題: 同じファイルでも実行場所によって異なるIDが生成される
  - 目的: 絶対パスをデフォルトとし、一貫したID管理を実現
- [x] 実装する機能の詳細をユーザーと対話して決定する
  - **デフォルト動作**: 絶対パスでID生成
  - **オプション**: `--use-relative-path` で相対パスに切り替え
  - 相対パス/絶対パスは別ドキュメントとして扱う（マイグレーション不要）
- [x] 技術スタック（使用するライブラリ・フレームワーク）をユーザーと相談する
  - argparseでコマンドラインオプション追加
  - pathlibでパス操作（`Path.as_posix()`でスラッシュ統一）
- [x] ファイル構成案を提示し、ユーザーの承認を得る
  - 修正対象: `src/semche/cli/bulk_register.py`
  - テスト追加: `tests/test_cli_bulk_register.py`
  - ドキュメント更新: `src/semche/cli/bulk_register.py.exp.md`, `README.md`
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

#### 確定した仕様

- デフォルト: 絶対パス（例: `/home/pater/semche/docs/README.md`）
- `--use-relative-path`: 相対パス（例: `docs/README.md`）
- パス区切り文字: `/` に統一（Windows互換性）
- `--id-prefix` との併用可能（例: `myproject:/home/pater/semche/docs/README.md`）

### Phase 2: 実装【実装フェーズ】

- [x] `bulk_register.py`の`parse_args()`に`--use-relative-path`オプションを追加
- [x] `generate_document_id()`を修正（デフォルト：絶対パス、`use_relative_path`パラメータ追加）
- [x] パス区切り文字を`/`に統一（`Path.as_posix()`使用）
- [x] `process_files()`に`use_relative_path`パラメータを追加・伝播
- [x] `main()`で`args.use_relative_path`を処理関数に渡す
- [x] コア機能の実装が完了している
- [x] `CODE_REVIEW_GUIDE.md` に準拠してコードレビューが完了している
- [x] テストコードが作成されている
  - デフォルト（絶対パス）での登録テスト
  - `--use-relative-path`オプションでの登録テスト
  - オプションの切り替えテスト
  - プレフィックスとの併用テスト
- [x] テストが全てパスする（60/60テスト成功）
- [x] Lint（ruff）/ 型チェック（mypy）が通る
- [x] README.md と詳細設計書（`.exp.md`）を更新済み
  - CLIコマンドの使用例を追加
  - `--use-relative-path`オプションの説明
  - デフォルト動作の変更を明記

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [x] 実装完了を報告し、ユーザーにレビューを依頼する
- [x] 手動での動作確認を行う
  - 絶対パスモード: `/home/pater/semche/test_docs/README.md` として登録
  - 相対パスモード: `test_docs/README.md` として登録
  - オプションの切り替えが正常に動作
- [x] 今回更新したコードの詳細設計書を更新する
  - `bulk_register.py.exp.md`: バージョン0.2.0に更新、オプション説明追加
  - `README.md`: 使用例とID生成ルールを更新
- [x] **全ての作業完了をユーザーに報告する**

## 実装完了サマリ

### 変更内容

- **デフォルト動作変更**: 相対パス → 絶対パス
- **新オプション追加**: `--use-relative-path` で相対パスに切り替え可能
- **パス区切り統一**: 全て `/` に統一（Windows互換性）

### テスト結果

- ✅ 全60テスト成功
- ✅ Lint（ruff）チェック通過
- ✅ 型チェック（mypy）通過
- ✅ 手動テスト完了

### 動作確認

```bash
# 絶対パス（デフォルト）
doc-update test_docs/*.md --file-type test
# → ID: /home/pater/semche/test_docs/README.md

# 相対パス
doc-update test_docs/*.md --use-relative-path --file-type test
# → ID: test_docs/README.md
```
