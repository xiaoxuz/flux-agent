"""
知识库管理器

提供知识库创建、加载、检索能力。
"""

from typing import List, Optional, Dict, Any
import logging
import os
import json
from dataclasses import dataclass, field

from langchain_core.documents import Document

from .embeddings import OpenAIEmbeddings
from .document_loader import DocumentLoader
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeChunkConfig:
    """文档块配置"""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunk_separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])


@dataclass
class KnowledgeEmbeddingConfig:
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class KnowledgeBaseConfig:
    """配置基类"""

    name: str = ""
    persist_directory: str = ""
    vector_store_type: str = "chroma"
    embedding_config: KnowledgeEmbeddingConfig = KnowledgeEmbeddingConfig()
    chunk_config: KnowledgeChunkConfig = KnowledgeChunkConfig()


class KnowledgeBase:
    """知识库管理器"""

    def __init__(self, name: str, config: KnowledgeBaseConfig, **kwargs):
        self.name = name
        self._config = config
        self._embedding = kwargs.get("embedding")
        self._vector_store = kwargs.get("vector_store")
        self._persist_directory = config.persist_directory
        self._vector_store_type = config.vector_store_type
        self._chunk_size = config.chunk_config.chunk_size
        self._chunk_overlap = config.chunk_config.chunk_overlap
        self._chunk_separators = config.chunk_config.chunk_separators
        self._documents: List[Document] = []  # 待处理的文档

    @classmethod
    def create(
        cls,
        name: str,
        config: KnowledgeBaseConfig,
    ) -> "KnowledgeBase":
        """
        创建全新的知识库

        Args:
            name: 知识库名称
            persist_directory: 持久化目录
            embedding_model: Embedding 模型
            embedding_api_key: API 密钥
            embedding_base_url: 自定义端点
            vector_store_type: 向量存储类型 (chroma | file)
            chunk_size: 文档块大小
            chunk_overlap: 文档块重叠

        Returns:
            知识库实例
        """
        kb = cls(
            name=name,
            config=config,
        )

        kb._embedding = OpenAIEmbeddings(
            model=config.embedding_config.model,
            api_key=config.embedding_config.api_key,
            base_url=config.embedding_config.base_url,
        )

        logger.info(f"创建知识库: {name}")
        return kb

    @classmethod
    def load(
        cls,
        name: str,
        config: KnowledgeBaseConfig,
    ) -> "KnowledgeBase":
        """
        加载已存在的知识库

        Args:
            name: 知识库名称
            persist_directory: 持久化目录
            embedding_model: Embedding 模型（需与创建时一致）
            embedding_api_key: API 密钥
            embedding_base_url: 自定义端点

        Returns:
            知识库实例
        """
        config.name = name
        persist_directory = config.persist_directory
        if not os.path.exists(persist_directory):
            raise FileNotFoundError(f"知识库目录不存在: {persist_directory}")

        vector_store_type = "file"
        if os.path.exists(os.path.join(persist_directory, "chroma.sqlite3")):
            vector_store_type = "chroma"
        elif os.path.exists(os.path.join(persist_directory, "index.faiss")):
            vector_store_type = "file"
        config.persist_directory = persist_directory

        kb = cls(
            name=name,
            config=config,
        )

        kb._embedding = OpenAIEmbeddings(
            model=config.embedding_config.model,
            api_key=config.embedding_config.api_key,
            base_url=config.embedding_config.base_url,
        )

        kb._vector_store = VectorStore.load(
            vector_store_type,
            persist_directory,
            kb._embedding.client,
            collection_name=name,
        )

        logger.info(f"加载知识库: {name}")
        return kb

    def add_documents(self, sources: List[str]) -> None:
        """
        添加文档（仅解析+切分，不执行 embedding）

        Args:
            sources: 文件路径列表
        """
        loader = DocumentLoader(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=self._chunk_separators,
        )

        documents = loader.load_batch(sources)
        self._documents.extend(documents)

        logger.info(f"添加文档: {len(documents)} 个文档块")

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        添加文本（仅解析+切分，不执行 embedding）

        Args:
            texts: 文本列表
            metadatas: 元数据列表
        """
        loader = DocumentLoader(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=self._chunk_separators,
        )

        documents = loader.split_texts(texts, metadatas)
        self._documents.extend(documents)

        logger.info(f"添加文本: {len(documents)} 个文档块")

    def generate(self) -> None:
        """
        执行 embedding 并保存到本地
        """
        if not self._documents:
            logger.warning("没有待处理的文档")
            return

        self._vector_store = VectorStore.create(
            self._vector_store_type,
            self._embedding.client,
            self._persist_directory,
            self.name,
        )

        texts = [doc.page_content for doc in self._documents]
        metadatas = [doc.metadata for doc in self._documents]

        self._vector_store.add_texts(texts, metadatas)

        if self._vector_store_type == "file":
            self._vector_store.save_local(self._persist_directory)

        logger.info(f"生成知识库: {len(texts)} 个文档块")

        self._documents.clear()

    def search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """检索相似文档

        Args:
            query: 查询文本
            k: 返回数量
            filter: 过滤条件，如 {"category": "寓言类"}
        """
        if self._vector_store is None:
            raise ValueError("请先加载或生成知识库")

        search_kwargs = {"k": k}
        if filter:
            search_kwargs["filter"] = filter

        retriever = self._vector_store.as_retriever(search_kwargs=search_kwargs)
        return retriever.invoke(query)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """相似度搜索

        Args:
            query: 查询文本
            k: 返回数量
            filter: 过滤条件，如 {"category": "寓言类"}
        """
        if self._vector_store is None:
            raise ValueError("请先加载或生成知识库")

        return self._vector_store.similarity_search(query, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple]:
        """带分数的相似度搜索

        Args:
            query: 查询文本
            k: 返回数量
            filter: 过滤条件，如 {"category": "寓言类"}
        """
        if self._vector_store is None:
            raise ValueError("请先加载或生成知识库")

        return self._vector_store.similarity_search_with_score(query, k=k, filter=filter)

    def get_by_metadata(self, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据 metadata 过滤获取文档

        Args:
            filter: 过滤条件，如 {"category": "寓言类"}

        Returns:
            文档列表，每项包含 id, content, metadata
        """
        if self._vector_store is None:
            raise ValueError("请先加载或生成知识库")

        docs = self._vector_store.get()
        if not isinstance(docs, dict):
            return []

        results = []
        for i, (doc_id, content, metadata) in enumerate(
            zip(docs.get("ids", []), docs.get("documents", []), docs.get("metadatas", []))
        ):
            # 检查 metadata 是否匹配
            match = True
            for key, value in filter.items():
                if metadata.get(key) != value:
                    match = False
                    break
            if match:
                results.append({"id": doc_id, "content": content, "metadata": metadata})

        return results

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """删除文档"""
        if self._vector_store is None:
            return False

        try:
            all_docs = self._vector_store.get()
            if not hasattr(all_docs, "ids"):
                return False

            ids_to_delete = [doc_id for doc_id in doc_ids if doc_id in all_docs.ids]
            if not ids_to_delete:
                return False

            self._vector_store.delete(ids_to_delete)

            if self._vector_store_type == "chroma":
                self._vector_store.persist()
            else:
                self._vector_store.save_local(self._persist_directory)

            logger.info(f"删除文档: {len(ids_to_delete)} 个")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def clear(self) -> bool:
        """清空知识库"""
        if self._vector_store is None:
            return False

        try:
            if self._vector_store_type == "chroma":
                self._vector_store.delete_collection()
                self._vector_store = VectorStore.create(
                    self._vector_store_type,
                    self._embedding.client,
                    self._persist_directory,
                    self.name,
                )
            else:
                self._vector_store = VectorStore.create(
                    self._vector_store_type,
                    self._embedding.client,
                    self._persist_directory,
                    self.name,
                )

            logger.info(f"清空知识库: {self.name}")
            return True
        except Exception as e:
            logger.error(f"清空知识库失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            count = 0
            if self._vector_store and hasattr(self._vector_store, "get"):
                all_docs = self._vector_store.get()
                if isinstance(all_docs, dict) and "ids" in all_docs:
                    count = len(all_docs["ids"])
                elif hasattr(all_docs, "ids"):
                    count = len(all_docs.ids)

            return {
                "name": self.name,
                "document_count": count,
                "embedding_model": self._embedding.model if self._embedding else None,
                "vector_store_type": self._vector_store_type,
                "persist_directory": self._persist_directory,
                "pending_documents": len(self._documents),
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def __repr__(self) -> str:
        return f"<KnowledgeBase {self.name} docs={self.get_stats().get('document_count', 0)}>"
