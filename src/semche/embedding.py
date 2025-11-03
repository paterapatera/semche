import logging
from typing import List, Union

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None  # type: ignore[misc] # Optional dependency


class EmbeddingError(Exception):
    pass


def ensure_single_vector(embedding: Union[List[float], List[List[float]]]) -> List[float]:
    """埋め込み結果を単一ベクトル形式に正規化する。

    addDocument()の戻り値は単一テキストの場合List[float]、
    バッチの場合List[List[float]]になる可能性があるため、
    常に単一ベクトルを返すように正規化する。

    Args:
        embedding: 埋め込みベクトル（単一またはバッチ）

    Returns:
        単一の埋め込みベクトル

    Raises:
        EmbeddingError: 不正な形式の場合
    """
    if isinstance(embedding, list) and len(embedding) > 0:
        if isinstance(embedding[0], list):
            # バッチ処理の結果: 最初の要素を返す
            return embedding[0]
        elif isinstance(embedding[0], (int, float)):
            # 単一ベクトル: そのまま返す
            return embedding  # type: ignore[return-value] # List[float]として安全
    raise EmbeddingError("不正な埋め込み形式です")

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/stsb-xlm-r-multilingual"):
        if HuggingFaceEmbeddings is None:
            logging.error("langchain_huggingfaceがインストールされていません。")
            raise EmbeddingError("langchain_huggingfaceがインストールされていません。")
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        except Exception as e:
            logging.error(f"モデルのロードに失敗しました: {e}")
            raise EmbeddingError(f"モデルのロードに失敗しました: {e}")

    def addDocument(
        self, text: Union[str, List[str]], normalize: bool = False
    ) -> Union[List[float], List[List[float]]]:
        if text is None or (isinstance(text, str) and text.strip() == "") or (isinstance(text, list) and not text):
            logging.error("空文字列または空リストが入力されました。")
            raise EmbeddingError("空文字列または空リストが入力されました。")
        try:
            if isinstance(text, str):
                vec = self.embeddings.embed_query(text)
                if normalize:
                    vec = self._normalize(vec)
                return vec
            elif isinstance(text, list):
                vecs = self.embeddings.embed_documents(text)
                if normalize:
                    vecs = [self._normalize(v) for v in vecs]
                return vecs
            else:
                logging.error("不正な入力形式です。strまたはList[str]のみ対応。")
                raise EmbeddingError("不正な入力形式です。strまたはList[str]のみ対応。")
        except MemoryError:
            logging.error("メモリ不足です。入力サイズを減らしてください。")
            raise EmbeddingError("メモリ不足です。入力サイズを減らしてください。")
        except Exception as e:
            logging.error(f"埋め込み処理でエラー: {e}")
            raise EmbeddingError(f"埋め込み処理でエラー: {e}")

    def _normalize(self, vec: List[float]) -> List[float]:
        import math
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            return vec
        return [x / norm for x in vec]
