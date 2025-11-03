# ユーザーはベクトルデータをChromaDBに保存できる

## 概要

ユーザーが生成したベクトルデータをChromaDBに保存できるようにします。
テキストデータとそのメタデータとともにベクトル埋め込みをChromaDBに永続化し、後続の検索や類似度計算に利用できるようにします。

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する
- [x] 実装する機能の詳細をユーザーと対話して決定する
  - ChromaDBの設定: ローカル永続化モードを採用、永続化ディレクトリは動的に指定可能。
  - コレクション名: デフォルト名 `documents` を使用（必要に応じて上書き指定可能）。
  - 保存するデータの形式（メタデータ）: `filepath`（必須・IDにも使用）、`updated_at`（ISO8601文字列）、`file_type`（任意文字列）。
  - 距離関数: `cosine` を採用（後から切替可能）。
  - 永続化ディレクトリの優先度: コンストラクタ引数 > 環境変数 `SEMCHE_CHROMA_DIR` > `./chroma_db`。
  - upsert方針: `ids` はファイルパスを使用し、同一パスは更新（上書き）。
- [x] 技術スタック（ChromaDB、依存ライブラリ）をユーザーと相談する
  - 依存: `chromadb` を追加。
- [x] ファイル構成案を提示し、ユーザーの承認を得る
  - 実装ファイル: `src/semche/chromadb_manager.py`
  - テスト: `tests/test_chromadb_manager.py`
  - 設計書: `src/semche/chromadb_manager.py.exp.md`
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [x] ChromaDBの依存関係がインストールされている
- [x] ChromaDBクライアントの初期化が実装されている
- [x] コレクションの作成・取得機能が実装されている
- [x] ベクトルデータの保存機能が実装されている
- [x] メタデータの保存機能が実装されている
- [x] 単一データの保存が正常に動作する
- [x] バッチデータの保存が正常に動作する
- [x] データの永続化が確認できる
- [x] エラーハンドリングが適切に実装されている
- [x] テストコードが作成されている
- [x] テストが全てパスする
- [ ] テストが全てパスする

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [x] 実装完了を報告し、ユーザーにレビューを依頼する
- [x] 手動での動作確認を行う
- [x] 今回更新したコードの詳細設計書を更新する
- [x] **全ての作業完了をユーザーに報告する**

## 実装内容

### 1. 環境セットアップ

- 必要なライブラリのインストール
  - `chromadb`
  - `chromadb-client` (必要に応じて)
- ChromaDBの初期化設定
  - 永続化ディレクトリの設定
  - クライアントモードの選択（ローカル/サーバー）

### 2. ChromaDBクライアントの実装

- クライアントの初期化
- コレクションの作成・取得
- 接続管理とリソース解放

### 3. データ保存機能の実装

- ベクトルデータの保存
  - embeddings: ベクトルデータ
  - documents: 元のテキストデータ
  - metadatas: メタデータ（任意）
  - ids: ドキュメントID
- バッチ保存機能
- 既存データの更新（upsert）機能

### 4. API設計

- 関数名: `save_to_chromadb()` または類似の名前
- パラメータ:
  - `collection_name`: コレクション名（str）
  - `embeddings`: ベクトルデータ（List[List[float]]）
  - `documents`: テキストデータ（List[str]）
  - `metadatas`: メタデータ（Optional[List[dict]]）
  - `ids`: ドキュメントID（Optional[List[str]]）
- 戻り値: 保存結果（成功/失敗、保存件数など）

### 5. エラーハンドリング

- ChromaDB接続エラー
- コレクション作成エラー
- データ保存エラー
- 不正なデータ形式の処理
- ディスク容量不足の処理

### 6. テスト実装

- 単体テスト:
  - クライアント初期化テスト
  - コレクション作成テスト
  - 単一データ保存テスト
  - バッチデータ保存テスト
  - メタデータ保存テスト
  - データ更新テスト
- 統合テスト:
  - エンドツーエンドの保存・取得テスト
  - 永続化確認テスト
  - パフォーマンステスト

### 7. ドキュメント作成

- 使用方法の説明
- ChromaDBの設定方法
- データ構造の説明
- 入出力例
- 詳細設計書の作成/更新

## 技術仕様

### ChromaDB設定

- データベースタイプ: ローカル永続化 or クライアント/サーバーモード
- 永続化ディレクトリ: `./chroma_db` (デフォルト、設定可能)
- 距離関数: コサイン類似度、L2距離、内積から選択可能

### 依存ライブラリ

```python
chromadb>=0.4.0
```

### データ構造

- **Collection**: データの論理的なグループ
- **Document**: 元のテキストデータ
- **Embedding**: ベクトルデータ（768次元など）
- **Metadata**: 任意のメタデータ（辞書形式）
  - 例: `{"source": "file.txt", "timestamp": "2025-11-03", "category": "tech"}`
- **ID**: 一意の識別子（文字列）

### 実装例（イメージ）

```python
import chromadb
from chromadb.config import Settings

class ChromaDBManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """ChromaDBクライアントを初期化"""
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

    def save_to_chromadb(
        self,
        collection_name: str,
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None
    ) -> dict:
        """
        ベクトルデータをChromaDBに保存する

        Args:
            collection_name: コレクション名
            embeddings: ベクトルデータ
            documents: 元のテキストデータ
            metadatas: メタデータ（オプション）
            ids: ドキュメントID（オプション）

        Returns:
            保存結果
        """
        # コレクションの取得または作成
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Vector embeddings collection"}
        )

        # IDの自動生成
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        # データの保存
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return {
            "status": "success",
            "collection": collection_name,
            "count": len(documents)
        }
```

## パフォーマンス考慮事項

- バッチ保存による効率化
- 大量データの分割保存
- インデックス作成の最適化
- メモリ使用量の管理
- 永続化ディレクトリのディスク容量監視

## セキュリティ考慮事項

- 永続化ディレクトリのアクセス権限設定
- メタデータに機密情報を含めない
- データのバックアップ戦略

## 今後の拡張性

- データの検索機能（別ストーリー）
- 類似度検索機能（別ストーリー）
- データの削除・更新機能
- コレクションの管理機能
- 統計情報の取得機能

## 参考資料

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [ChromaDB Python Client](https://docs.trychroma.com/reference/py-client)
- [ChromaDB Usage Guide](https://docs.trychroma.com/usage-guide)
