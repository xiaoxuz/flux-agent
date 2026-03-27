"""
Embedding 管理器

基于 OpenAI Embeddings。
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class OpenAIEmbeddings:
    """OpenAI Embedding 封装"""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化

        Args:
            model: Embedding 模型名称
            api_key: API 密钥
            base_url: 自定义端点
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from langchain_openai import OpenAIEmbeddings as _OpenAI

            params = {"model": self.model}
            if self.api_key:
                params["api_key"] = self.api_key
            if self.base_url:
                params["base_url"] = self.base_url
            params.update(self.kwargs)

            self._client = _OpenAI(**params)

        return self._client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        if not texts:
            return []
        return self.client.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """向量化查询"""
        if not query:
            return []
        return self.client.embed_query(query)

    def __repr__(self) -> str:
        return f"<OpenAIEmbeddings model={self.model}>"
