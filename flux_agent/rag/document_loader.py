"""
文档加载器

使用 LangChain 的 UnstructuredFileLoader 加载各种格式的文档。
"""

from typing import List, Optional, Dict, Any
import logging
import os

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """文档加载器"""

    SUPPORTED_FORMATS = [
        "pdf",
        "docx",
        "doc",
        "txt",
        "md",
        "markdown",
        "html",
        "htm",
        "csv",
        "xlsx",
        "xls",
        "pptx",
        "json",
    ]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        """
        初始化文档加载器

        Args:
            chunk_size: 文档块大小
            chunk_overlap: 文档块重叠大小
            separators: 自定义分隔符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators

    def load(
        self,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        加载单个文档

        Args:
            source: 文件路径或 URL
            metadata: 自定义元数据

        Returns:
            文档块列表
        """
        if not source:
            raise ValueError("source 不能为空")

        source = source.strip()

        if source.startswith("http://") or source.startswith("https://"):
            return self._load_from_url(source, metadata)

        if os.path.isfile(source):
            return self._load_from_file(source, metadata)

        if os.path.isdir(source):
            return self._load_from_directory(source, metadata)

        raise ValueError(f"无法处理 source: {source}")

    def load_batch(
        self,
        sources: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Document]:
        """
        批量加载文档

        Args:
            sources: 文件路径或 URL 列表
            metadata_list: 元数据列表（可选）

        Returns:
            所有文档块列表
        """
        all_docs = []

        for i, source in enumerate(sources):
            meta = metadata_list[i] if metadata_list and i < len(metadata_list) else None
            try:
                docs = self.load(source, meta)
                all_docs.extend(docs)
                logger.info(f"加载文档成功: {source}, 块数: {len(docs)}")
            except Exception as e:
                logger.warning(f"加载文档失败: {source}, 错误: {e}")

        return all_docs

    def _load_from_file(self, file_path: str, metadata: Optional[Dict[str, Any]]) -> List[Document]:
        """从文件加载"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {ext}")

        loader = self._create_loader(file_path)
        documents = loader.load()

        return self._split_documents(documents, metadata)

    def _load_from_directory(
        self, dir_path: str, metadata: Optional[Dict[str, Any]]
    ) -> List[Document]:
        """从目录加载"""
        all_docs = []

        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    docs = self._load_from_file(file_path, metadata)
                    all_docs.extend(docs)
                except Exception as e:
                    logger.warning(f"加载文件失败: {file_path}, 错误: {e}")

        return all_docs

    def _load_from_url(self, url: str, metadata: Optional[Dict[str, Any]]) -> List[Document]:
        """从 URL 加载"""
        if url.endswith(".html") or url.endswith(".htm"):
            from langchain_community.document_loaders import WebBaseLoader

            loader = WebBaseLoader(web_paths=[url])
        else:
            raise ValueError(f"不支持的 URL 格式: {url}")

        documents = loader.load()
        return self._split_documents(documents, metadata)

    def _create_loader(self, file_path: str):
        """根据文件类型创建加载器"""
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        if ext == "pdf":
            try:
                from langchain_community.document_loaders import PyPDFLoader

                return PyPDFLoader(file_path)
            except ImportError:
                pass

        if ext in ("docx", "doc"):
            try:
                from langchain_community.document_loaders import UnstructuredWordDocumentLoader

                return UnstructuredWordDocumentLoader(file_path)
            except ImportError:
                pass

        if ext == "pptx":
            try:
                from langchain_community.document_loaders import UnstructuredPowerPointLoader

                return UnstructuredPowerPointLoader(file_path)
            except ImportError:
                pass

        if ext in ("xlsx", "xls", "csv"):
            try:
                from langchain_community.document_loaders import UnstructuredExcelLoader

                return UnstructuredExcelLoader(file_path)
            except ImportError:
                pass

        if ext in ("html", "htm"):
            from langchain_community.document_loaders import BSHTMLLoader

            return BSHTMLLoader(file_path)

        if ext in ("txt", "md", "markdown", "json"):
            from langchain_community.document_loaders import TextLoader

            encoding = "utf-8" if ext != "md" else None
            return TextLoader(file_path, encoding=encoding)

        from langchain_community.document_loaders import UnstructuredFileLoader

        return UnstructuredFileLoader(file_path)

    def _split_documents(
        self,
        documents: List[Document],
        metadata: Optional[Dict[str, Any]],
    ) -> List[Document]:
        """分割文档"""
        if not documents:
            return []

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            raise ImportError(
                "RAG 功能需要安装 langchain-text-splitters，"
                "请运行: pip install 'flux-agent[rag]'"
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )

        splits = splitter.split_documents(documents)

        for split in splits:
            if metadata:
                split.metadata.update(metadata)

        return splits

    def split_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Document]:
        """
        直接分割文本列表

        Args:
            texts: 文本列表
            metadatas: 元数据列表

        Returns:
            文档块列表
        """
        if not texts:
            return []

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            raise ImportError(
                "RAG 功能需要安装 langchain-text-splitters，"
                "请运行: pip install 'flux-agent[rag]'"
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )

        if metadatas:
            return splitter.create_documents(texts, metadatas=metadatas)
        else:
            return splitter.create_documents(texts)
