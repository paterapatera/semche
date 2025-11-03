# ユーザーはMCPでセマンティック検索できる

## 概要

MCPツールとして「search」を提供し、クエリテキストに対してChromaDBに保存済みのベクトルデータから類似ドキュメントを検索できるようにする。単一クエリ・上位k件返却を基本とし、ファイルタイプやパス接頭辞などの軽量なフィルタ、スコアしきい値などをサポートする。戻り値は辞書（dict）形式で、結果リストとメタ情報を含む。

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する（MCP経由での横断検索のニーズ、応答形式の期待）
- [x] 実装する機能の詳細をユーザーと対話して決定する
  - [x] ツール名: `search`（単一クエリ）
  - [x] 入力パラメータ（案）
    - `query` (str, 必須): 検索クエリ文字列
    - `top_k` (int, 省略時5): 上位何件まで返すか
    - `file_type` (str | None): 指定時はメタデータのfile_typeでフィルタ
    - `filepath_prefix` (str | None): 指定時はパスの接頭辞でフィルタ
    - `normalize` (bool, 省略時False): クエリ埋め込みのL2正規化有無
    - `min_score` (float | None): 類似度の下限しきい値（cosineの想定）
    - `include_documents` (bool, 省略時True): ドキュメント本文のプレビューを含めるか
  - [x] 返却形式（案）: dict
    - `status`: "success" | "error"
    - `message`: 状態メッセージ
    - `results`: 検索結果の配列（成功時）
      - 各要素: `{ filepath, score, document?, metadata }`
        - `score`: コサイン類似度（1.0に近いほど類似）
        - `document`: 先頭N文字のプレビュー（`include_documents`がTrueのとき）
        - `metadata`: `{ file_type, updated_at }`
    - `count`: 返却件数
    - `query_vector_dimension`: ベクトル次元（例: 768）
    - `persist_directory`: ChromaDBの永続ディレクトリ
  - [x] スコア定義: cosine類似度を採用（ChromaDBの距離が必要な場合は1-距離で換算）
  - [x] 例外・エラー方針: ValidationError/EmbeddingError/ChromaDBError/その他
  - [x] パフォーマンス/制限: `top_k` 上限、プレビュー長上限、タイムアウト方針
- [x] 技術スタック（使用するライブラリ・フレームワーク）をユーザーと相談する（既存の LangChain/ChromaDB/Embedder を流用）
- [x] ファイル構成案を提示し、ユーザーの承認を得る
  - `src/semche/tools/search.py`（ツール実装）
  - `src/semche/tools/search.py.exp.md`（詳細設計）
  - `tests/test_mcp_server.py`（または `tests/test_search.py`）に検索テスト追加
  - `src/semche/mcp_server.py` に `@mcp.tool()` で登録
  - `README.md` に `search` ツールの使い方を追記
- [x] 受け入れ基準（案）
  - `put_document` で保存した内容に対し、関連クエリで上位件に当該ドキュメントが含まれる
  - フィルタ（`file_type`/`filepath_prefix`）が結果に反映される
  - `include_documents=False` の場合に本文が含まれない
  - `min_score` で低スコア結果が除外される
  - エラー時は `status=error` と `error_type` が返る
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [x] `src/semche/tools/search.py` を新規作成（`@mcp.tool()` から委譲される関数を実装）
- [x] クエリ埋め込み生成（`Embedder.addDocument(query, normalize)`）
- [x] ChromaDB での近傍検索（`top_k` とメタデータフィルタ、スコア算出）
- [x] レスポンス整形（dict: `status`, `results`, `count`, メタ情報）
- [x] `src/semche/mcp_server.py` に `search` を登録
- [x] テストコード（正常系/フィルタ/閾値/エラー）を追加
- [x] `README.md` に `search` のパラメータ・返却値・例を追記
- [x] `src/semche/tools/search.py.exp.md` を作成
- [x] `CODE_REVIEW_GUIDE.md` に準拠してレビュー
- [x] テストが全てパスする

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [ ] 実装完了を報告し、ユーザーにレビューを依頼する
- [ ] MCP Inspectorで手動の動作確認を行う（代表クエリでヒットすること）
- [ ] 今回更新したコードの詳細設計書を更新する
- [ ] **全ての作業完了をユーザーに報告する**
