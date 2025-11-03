# ドキュメント登録機能をMCPから実行できる

## 概要

既に実装済みのEmbedderとChromaDBManagerを使用して、MCPツールとしてドキュメント登録機能を提供します。
ユーザーがMCPクライアント経由でテキストをベクトル化し、ChromaDBに保存できるようにします。

## 実行手順(上から順にチェックしてください)

### Phase 1: 要件定義・設計【対話フェーズ - ユーザー確認必須】

- [x] ストーリーの背景と目的を確認する
- [x] 実装する機能の詳細をユーザーと対話して決定する
  - MCPツール名: `put_document` （追加と更新を考慮）
  - 入力パラメータ: text（必須）、filepath（必須）、file_type（オプション）、normalize（オプション、デフォルト: false）
  - 出力フォーマット: JSON形式で成功/失敗、保存件数、ベクトル次元数、コレクション名、永続化ディレクトリを返す
  - エラーハンドリング: EmbeddingError、ChromaDBErrorを捕捉してJSON形式でエラーレスポンスを返す
  - バッチ処理対応: 単一ドキュメントのみ（将来的にput_documentsで拡張可能）
- [x] 技術スタック（既存モジュールの統合方針）をユーザーと相談する
  - 新規依存関係の追加なし、既存のEmbedder/ChromaDBManagerを統合
- [x] ファイル構成案を提示し、ユーザーの承認を得る
  - 修正: mcp_server.py, test_mcp_server.py, mcp_server.py.exp.md, README.md
  - 新規ファイル: なし
- [x] **Phase 1完了の確認をユーザーから得てから次に進む**
- [x] 承認を得た内容をストーリーに反映する

### Phase 2: 実装【実装フェーズ】

- [x] mcp_server.pyのlist_tools()に新ツール定義を追加している
- [x] call_tool()に新ツールのロジックを実装している
- [x] EmbedderとChromaDBManagerを統合している
- [x] 入力パラメータのバリデーションが実装されている
- [x] エラーハンドリングが適切に実装されている
- [x] 単一ドキュメント登録が正常に動作する
- [x] 適切なレスポンスメッセージを返している
- [x] テストコードが作成されている
- [x] テストが全てパスする（23テスト全てパス）

### Phase 3: 確認・ドキュメント【対話フェーズ - ユーザー確認必須】

- [x] 実装完了を報告し、ユーザーにレビューを依頼する
- [x] MCP Inspectorでの動作確認を行う
- [x] 今回更新したコードの詳細設計書を更新する
- [x] **全ての作業完了をユーザーに報告する**

## 実装内容

### 1. MCPツールの設計

#### ツール名

- `put_document` （追加と更新のupsert操作を表現）

#### 入力パラメータ

- `text` (string, 必須): 登録するテキスト
- `filepath` (string, 必須): ドキュメントの識別子となるファイルパス
- `file_type` (string, オプション): ファイルタイプ（例: "spec", "jira", "design"）
- `normalize` (boolean, オプション): ベクトル正規化を行うかどうか（デフォルト: false）

#### 出力フォーマット

```json
{
  "status": "success",
  "message": "ドキュメントを登録しました",
  "details": {
    "count": 1,
    "collection": "documents",
    "filepath": "/docs/spec.md",
    "vector_dimension": 768,
    "persist_directory": "./chroma_db"
  }
}
```

エラー時:

```json
{
  "status": "error",
  "message": "埋め込み生成に失敗しました: ...",
  "error_type": "EmbeddingError"
}
```

### 2. 実装方針

```python
# mcp_server.py内での実装イメージ

from .embedding import Embedder, EmbeddingError
from .chromadb_manager import ChromaDBManager, ChromaDBError
from datetime import datetime

# グローバルインスタンス（またはlist_tools/call_tool内で初期化）
embedder = None
chromadb_manager = None

def list_tools():
    return [
        # 既存のhelloツール...
        types.Tool(
            name="put_document",
            description="テキストをベクトル化してChromaDBに保存します（upsert）",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "登録するテキスト"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "ドキュメントの識別子（ファイルパス）"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "ファイルタイプ（オプション）"
                    },
                    "normalize": {
                        "type": "boolean",
                        "description": "ベクトル正規化を行うか（デフォルト: false）"
                    }
                },
                "required": ["text", "filepath"]
            }
        )
    ]

async def call_tool(name: str, arguments: dict):
    if name == "put_document":
        # 初期化（必要に応じて遅延初期化）
        global embedder, chromadb_manager
        if embedder is None:
            embedder = Embedder()
        if chromadb_manager is None:
            chromadb_manager = ChromaDBManager()

        text = arguments.get("text")
        filepath = arguments.get("filepath")
        file_type = arguments.get("file_type")
        normalize = arguments.get("normalize", False)

        try:
            # ベクトル化
            embedding = embedder.addDocument(text, normalize=normalize)

            # ChromaDBに保存
            now = datetime.now().isoformat()
            result = chromadb_manager.save(
                embeddings=[embedding],
                documents=[text],
                filepaths=[filepath],
                updated_at=[now],
                file_types=[file_type] if file_type else None
            )

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "message": "ドキュメントを登録しました",
                    "details": {
                        "count": result["count"],
                        "collection": result["collection"],
                        "filepath": filepath,
                        "vector_dimension": len(embedding),
                        "persist_directory": result["persist_directory"]
                    }
                }, ensure_ascii=False, indent=2)
            )]
        except EmbeddingError as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"埋め込み生成に失敗しました: {str(e)}",
                    "error_type": "EmbeddingError"
                }, ensure_ascii=False, indent=2)
            )]
        except ChromaDBError as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"ChromaDB保存に失敗しました: {str(e)}",
                    "error_type": "ChromaDBError"
                }, ensure_ascii=False, indent=2)
            )]
```

### 3. テスト実装

- 単体テスト:
  - ツール定義の存在確認
  - 正常系: 単一ドキュメント登録
  - 正常系: normalize=trueでの登録
  - 異常系: 必須パラメータ不足
  - 異常系: 空文字列テキスト
  - 異常系: 埋め込み失敗のハンドリング
  - 異常系: ChromaDB保存失敗のハンドリング
- 統合テスト:
  - MCP Inspector経由での動作確認
  - 登録後のデータ取得確認

### 4. ドキュメント更新

- README.md:
  - 利用可能なツールセクションに`put_document`を追加
  - 使用例を追加
- mcp_server.py.exp.md:
  - サーバーはツール登録のみを行い、実装はtoolsに委譲する方針へ更新
  - 委譲のデータフロー簡略図を記載
- tools配下の詳細設計書を追加:
  - `src/semche/tools/hello.py.exp.md`
  - `src/semche/tools/document.py.exp.md`

## 技術仕様

### 依存モジュール

- `src/semche/embedding.py`: Embedder, EmbeddingError
- `src/semche/chromadb_manager.py`: ChromaDBManager, ChromaDBError
- 標準ライブラリ: `datetime`, `json`

### データフロー

```
1. MCPクライアント
   ↓ (text, filepath, file_type?, normalize?)
2. mcp_server.py (register_document)
   ↓ (text, normalize)
3. Embedder.addDocument()
   ↓ (768次元ベクトル)
4. ChromaDBManager.save()
   ↓ (embeddings, documents, filepaths, updated_at, file_types)
5. ChromaDB (永続化)
   ↓ (保存結果)
6. レスポンス生成
   ↓ (JSON)
7. MCPクライアント
```

### エラーハンドリング

| エラーケース       | 例外タイプ     | 処理方法                       |
| ------------------ | -------------- | ------------------------------ |
| 必須パラメータ不足 | -              | エラーレスポンス返却           |
| 空文字列テキスト   | EmbeddingError | エラーレスポンス返却、ログ出力 |
| 埋め込み生成失敗   | EmbeddingError | エラーレスポンス返却、ログ出力 |
| ChromaDB保存失敗   | ChromaDBError  | エラーレスポンス返却、ログ出力 |
| モジュール未初期化 | ImportError等  | エラーレスポンス返却、ログ出力 |

## パフォーマンス考慮事項

- Embedder/ChromaDBManagerのグローバルインスタンス化（初回のみ初期化）
- モデルロードは初回のみ（Embedder内部でキャッシュ）
- 単一ドキュメント処理（バッチ処理は将来的に`put_documents`として別ツール化）

## セキュリティ考慮事項

- filepathのパストラバーサル対策（必要に応じてバリデーション追加）
- テキスト長の制限（必要に応じて）
- メタデータに機密情報を含めない

## 今後の拡張性

- バッチ登録機能（`put_documents`として別ツール追加）
- ファイルアップロード対応（ファイルパスから自動読み込み）
- メタデータのカスタマイズ（任意キー・バリュー対応）
- 登録済みドキュメントの更新確認機能
- 登録統計情報の取得機能

## 参考資料

- 既存実装: `src/semche/embedding.py`, `src/semche/chromadb_manager.py`
- MCPプロトコル: [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- テスト例: `tests/test_mcp_server.py`
