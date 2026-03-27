"""
RAG 知识库文档操作示例

"""

import os

# 切换到项目根目录
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flux_agent.rag import KnowledgeBase, KnowledgeBaseConfig, KnowledgeChunkConfig, KnowledgeEmbeddingConfig
from create import EmbeddingConfig


def get_documents():
    kb = KnowledgeBase.load(
        name="idiom_docs",
        config=KnowledgeBaseConfig(
            persist_directory="./examples/rag/kb_data/idiom_docs",
            embedding_config=EmbeddingConfig
        )
    )

    # 通过 vector_store.get() 获取所有数据，然后过滤
    docs = kb._vector_store.get()

    # 返回的是 dict，包含 ids, documents, metadatas
    # for i, (doc_id, content, metadata) in enumerate(zip(docs["ids"], docs["documents"], docs["metadatas"])):
    #     print(f"doc_id: {doc_id}\n")
    #     print(f"content: {content}\n")
    #     print(f"metadata: {metadata}\n")

    docs = kb.similarity_search_with_score(
        query="形容不上进，不努力，等着天上掉馅饼",
        k=2,
        # filter={"category": "情感类"}  # Chroma 支持这种格式
    )
    for doc in docs:
        print(f"doc_id: {doc[0].id}\n")
        print(f"page_content: {doc[0].page_content}\n")
        print(f"metadata: {doc[0].metadata}\n")
        print(f"score: {doc[1]}\n")


if __name__ == "__main__":
    get_documents()
