"""
RAG 知识库查询示例

演示如何查询知识库。
"""

import os

# 切换到项目根目录
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flux_agent.rag import KnowledgeBase, KnowledgeBaseConfig, KnowledgeChunkConfig, KnowledgeEmbeddingConfig
from create import EmbeddingConfig

def search_faq_knowledge_base():
    kb = KnowledgeBase.load(
        name="faq_docs",
        config=KnowledgeBaseConfig(
            persist_directory="./examples/rag/kb_data/faq_docs",
            embedding_config=EmbeddingConfig
        )
    )

    print(f"知识库状态: {kb.get_stats()}")

    docs = kb.similarity_search_with_score(
        query="有人工客服么",
        k=1,
    )

    print(f"查询结果: {len(docs)} 条")
    for i, doc in enumerate(docs):
        print(doc[0].id, doc[0].page_content, "----", doc[1])


def search_docs_knowledge_base():
    kb = KnowledgeBase.load(
        name="product_docs",
        config=KnowledgeBaseConfig(
            persist_directory="./examples/rag/kb_data/product_docs",
            embedding_config=EmbeddingConfig
        )
    )

    print(f"知识库状态: {kb.get_stats()}")

    docs = kb.similarity_search_with_score(
        query="LLMNode节点有哪些配置参数",
        k=3,
    )

    print(f"查询结果: {len(docs)} 条")
    # for i, doc in enumerate(docs):
    #     print(f"[{i+1}] {doc.page_content}")

    for i, doc in enumerate(docs):
        print(doc[0].id, doc[0].page_content)
        print(doc[1])


if __name__ == "__main__":
    search_faq_knowledge_base()
    search_docs_knowledge_base()
