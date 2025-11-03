# hello.py 詳細設計書

## 概要

`hello` は FastMCP のツールとして公開されるシンプルな関数で、与えられた名前に対して挨拶メッセージ（`"Hello, {name}!"`）を返します。本プロジェクトでは、サーバー本体（`mcp_server.py`）から委譲される形で使用されます。

## ファイルパス

- 実装: `/home/pater/semche/src/semche/tools/hello.py`
- 呼び出し元: `/home/pater/semche/src/semche/mcp_server.py`
- テスト: `/home/pater/semche/tests/test_mcp_server.py`

## 利用クラス・ライブラリ

本モジュールでは外部クラスの依存はありません（標準Pythonのみ）。

- 依存クラス: なし
- 外部ライブラリ: なし

## 関数仕様

### `hello(name: str = "World") -> str`

- 役割: 名前を受け取り、`"Hello, {name}!"`を返す
- 引数:
  - `name` (str, デフォルト `"World"`): 挨拶する対象の名前
- 返り値: `str` 挨拶メッセージ
- エラー: なし（入力値に対して特別なバリデーションは行わない）

## データフロー

```
FastMCP (mcp_server.hello)
  → tools.hello.hello(name)
     → f-string で文字列生成
     ← 挨拶メッセージを返す
← mcp_server からクライアントへレスポンス
```

## パフォーマンス/設計上の注意

- 非常に軽量で計算コストは無視できる
- 依存がないため、ユニットテストが容易

## テスト

- `tests/test_mcp_server.py` にて、以下の観点を検証
  - 名前指定時・省略時の動作
  - 日本語や空文字列などの異常系に近い入力でも例外にならないこと

## 参考

- ツール登録: `src/semche/mcp_server.py`（`@mcp.tool()` デコレータで公開）
