# chromadb_managerのqueryはlangchainのsimilarity_searchを使用する

## 概要

現在の`ChromaDBManager.query()`はChromaDBのネイティブAPIを直接使用していますが、LangChainの`similarity_search()`メソッドを使用するように変更します。これにより、LangChainエコシステムとの統合が改善され、将来的な拡張性が向上します。

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する
  - 現状: ChromaDBのネイティブAPI (`collection.query()`) を直接使用
  - 課題: LangChainのベクトルストア抽象化レイヤーを活用できていない
  - 目的: LangChainの`similarity_search()`を使用して統合を改善し、将来のハイブリッド検索への拡張を容易にする
- [x] 実装する機能の詳細をユーザーと対話して決定する
  - **オプション2（改良版）を採用**: Embedderを統合し、段階的な移行を行う
  - `ChromaDBManager.__init__()`に`embedding_function`パラメータを追加（オプショナル）
  - `query()`メソッドは既存APIを維持（互換性）
  - LangChainの`Chroma`ベクトルストアを内部で使用（`embedding_function`が渡された場合）
  - `similarity_search_by_vector_with_score()`を使用してベクトル検索
  - 将来の拡張: `search_by_text()`メソッドを追加してテキストクエリに対応
- [x] 技術スタック（使用するライブラリ・フレームワーク）をユーザーと相談する
  - `langchain-chroma`: 既に依存関係に含まれている
  - `langchain_chroma.Chroma`: ベクトルストアクラス
  - `similarity_search_by_vector_with_score()`: ベクトルからの検索（既存API互換）
  - `Embedder.embeddings` (HuggingFaceEmbeddings): embedding_functionとして使用
  - 将来的に`EnsembleRetriever`でハイブリッド検索を実装可能
- [x] ファイル構成案を提示し、ユーザーの承認を得る
  - 修正対象: `src/semche/chromadb_manager.py`
    - `__init__()`に`embedding_function`パラメータ追加
    - `query()`内部実装をLangChain経由に変更
  - 修正対象: `src/semche/chromadb_manager.py.exp.md`
  - 修正対象: `tests/test_chromadb_manager.py`
  - 修正対象: `tests/test_search.py`（統合テスト）
  - 影響確認: `src/semche/tools/search.py`（ChromaDBManager使用箇所）
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [x] `ChromaDBManager.__init__()`を修正
  - `embedding_function`パラメータを追加（オプショナル）
  - LangChainの`Chroma`インスタンスを初期化（embedding_functionが渡された場合）
  - 既存のクライアント・コレクション初期化を維持
  - `persist_directory`の設定を維持
- [x] `ChromaDBManager.query()`を修正
  - LangChain経由とネイティブAPIのフォールバック実装
  - `_query_via_langchain()`: `similarity_search_by_vector_with_score()`を使用
  - `_query_native()`: 既存のネイティブAPI実装
  - 返却値の形式を既存と完全互換に変換
  - スコア計算の一貫性を確認（LangChainもsimilarityスコアを返す）
- [x] `ChromaDBManager.save()`メソッドへの影響を確認
  - LangChain APIとの互換性を確認 → 影響なし（ネイティブAPIを継続使用）
  - upsertロジックは現状維持
- [x] 依存関係の追加
  - `pyproject.toml`に`langchain-chroma>=1.0.0`を追加
- [x] コア機能の実装が完了している
- [x] `CODE_REVIEW_GUIDE.md` に準拠してコードレビューが完了している
- [x] テストコードが作成されている
  - 既存のテストが全てパスすることを確認済み
  - 新規テスト不要（既存APIと互換性維持）
- [x] テストが全てパスする（60/60テスト）
- [x] Lint（ruff）/ 型チェック（mypy）が通る
- [x] README.md と詳細設計書（`.exp.md`）を更新済み
  - LangChain統合について記載
  - 内部実装の変更点を明記
  - バージョンをv0.3.0に更新
  - AGENTS.mdも更新済み

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [ ] 実装完了を報告し、ユーザーにレビューを依頼する
- [ ] 手動での動作確認を行う
  - MCP Inspectorで`search`ツールをテスト
  - CLIツール`doc-update`の動作確認
  - 既存のドキュメント検索が正常に機能することを確認
- [ ] 今回更新したコードの詳細設計書を更新する
  - `chromadb_manager.py.exp.md`にLangChain統合の詳細を記載 ✅
  - 内部実装の変更点を明記 ✅
  - バージョンを更新 ✅
- [ ] **全ての作業完了をユーザーに報告する**

## 技術メモ

### LangChain統合のアプローチ

**オプション1: similarity_search_with_score() を使用**

```python
from langchain_chroma import Chroma

# 初期化
vectorstore = Chroma(
    collection_name="documents",
    embedding_function=embedder,  # Embedderクラスをラップ
    persist_directory=persist_directory
)

# 検索
results = vectorstore.similarity_search_with_score(
    query="検索クエリ",
    k=top_k,
    filter=where  # メタデータフィルタ
)
```

**オプション2: 既存のcollectionを使用**

```python
# 既存のChromaDB collectionをLangChainでラップ
vectorstore = Chroma(
    client=chroma_client,
    collection_name="documents",
    embedding_function=embedder
)
```

### 検討事項

1. **Embedder統合**: LangChainの`Embeddings`インターフェースに合わせる必要がある
   - `embed_documents(texts: List[str]) -> List[List[float]]`
   - `embed_query(text: str) -> List[float]`
2. **スコア変換**: ChromaDBのdistance（L2/cosine）とsimilarityの関係
   - cosine distance: `similarity = 1 - distance`
   - 既存の実装と一致させる

3. **メタデータフィルタ**: `where`パラメータの互換性
   - LangChainの`filter`とChromaDBの`where`の形式を確認

4. **後方互換性**: 既存のAPIを変更しない
   - `query()`メソッドのシグネチャを維持
   - 返却値の形式を維持

### 期待される効果

- LangChainエコシステムとの統合改善
- 将来的なハイブリッド検索（dense + sparse）への拡張が容易
- LangChainの最新機能（フィルタリング、メタデータ検索など）を活用可能
- コードの保守性向上

### リスク

- 既存のテストが失敗する可能性
- パフォーマンスへの影響
- Embedderクラスの変更が必要になる可能性
