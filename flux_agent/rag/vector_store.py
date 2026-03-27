"""
向量存储管理器

支持 Chroma 和 File 两种向量存储。
"""

from typing import Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储封装"""

    @staticmethod
    def create(
        store_type: str,
        embedding: Any,
        persist_directory: Optional[str] = None,
        collection_name: str = "default",
    ) -> Any:
        """
        创建向量存储

        Args:
            store_type: 存储类型 (chroma | file)
            embedding: Embedding 实例
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        store_type = store_type.lower()

        if store_type == "chroma":
            return VectorStore._create_chroma(embedding, persist_directory, collection_name)
        elif store_type == "file":
            return VectorStore._create_file(embedding, persist_directory, collection_name)
        else:
            raise ValueError(f"不支持的向量存储类型: {store_type}")

    @staticmethod
    def _create_chroma(
        embedding: Any,
        persist_directory: Optional[str],
        collection_name: str,
    ) -> Any:
        from langchain_chroma import Chroma

        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)

        return Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding,
            collection_name=collection_name,
        )

    @staticmethod
    def _create_file(
        embedding: Any,
        persist_directory: Optional[str],
        collection_name: str,
    ) -> Any:
        from langchain_community.vectorstores import FAISS

        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)

        return FAISS(embedding_function=embedding, index_name=collection_name)

    @staticmethod
    def load(
        store_type: str, persist_directory: str, embedding: Any, collection_name: str = None
    ) -> Any:
        """加载向量存储"""
        store_type = store_type.lower()

        if store_type == "chroma":
            return VectorStore._load_chroma(persist_directory, embedding, collection_name)
        elif store_type == "file":
            return VectorStore._load_file(persist_directory, embedding)
        else:
            raise ValueError(f"不支持的向量存储类型: {store_type}")

    @staticmethod
    def _load_chroma(persist_directory: str, embedding: Any, collection_name: str = None) -> Any:
        from langchain_chroma import Chroma

        if not os.path.exists(persist_directory):
            raise FileNotFoundError(f"目录不存在: {persist_directory}")

        return Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding,
            collection_name=collection_name,
        )

    @staticmethod
    def _load_file(persist_directory: str, embedding: Any) -> Any:
        from langchain_community.vectorstores import FAISS

        if not os.path.exists(persist_directory):
            raise FileNotFoundError(f"目录不存在: {persist_directory}")

        return FAISS.load_local(
            persist_directory,
            embedding,
            allow_dangerous_deserialization=True,
        )

    @staticmethod
    def exists(store_type: str, persist_directory: str) -> bool:
        """检查向量存储是否存在"""
        if not persist_directory or not os.path.exists(persist_directory):
            return False

        if store_type.lower() == "chroma":
            return True

        if store_type.lower() == "file":
            index_file = os.path.join(persist_directory, "index.faiss")
            return os.path.exists(index_file)

        return False
