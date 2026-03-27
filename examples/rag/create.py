"""
RAG 知识库创建示例

演示如何创建一个全新的知识库。
"""

from flux_agent.rag import KnowledgeBase, KnowledgeBaseConfig, KnowledgeChunkConfig, KnowledgeEmbeddingConfig
import glob
import json

APIKEY_EMBEDDING = ""
BASEURL = ""
EMBEDDING_MODEL = "text-embedding-3-small"
EmbeddingConfig = KnowledgeEmbeddingConfig(model=EMBEDDING_MODEL, api_key=APIKEY_EMBEDDING, base_url=BASEURL)

def create_knowledge_by_document():
    """ 基于文档生成 知识库 """
    kb = KnowledgeBase.create(
        name="product_docs",
        config=KnowledgeBaseConfig(
            persist_directory="./examples/rag/kb_data/product_docs",
            chunk_config=KnowledgeChunkConfig(
                chunk_size=1000,
                chunk_overlap=200,
            ),
            embedding_config=EmbeddingConfig
        )
    )

    kb.add_documents(glob.glob("./docs/*.md"))

    kb.generate()

    print(f"知识库创建成功: {kb.get_stats()}")
    return kb


def create_knowledge_by_text():
    """创建知识库 通过文本"""

    kb = KnowledgeBase.create(
        name="faq_docs",
        config=KnowledgeBaseConfig(
            persist_directory="./examples/rag/kb_data/faq_docs",
            chunk_config=KnowledgeChunkConfig(
                chunk_size=1000,
                chunk_overlap=200,
            ),
            embedding_config=EmbeddingConfig
        )
    )
    kb.add_texts(
        [
            "Q: 如何联系客服？ A: 拨打 400-123-4567",
            "Q: 退货政策是什么？ A: 7 天无理由退货",
            "Q: 如何申请退款？ A: 在订单详情页点击申请退款",
        ]
    )

    kb.generate()

    print(f"FAQ 知识库创建成功: {kb.get_stats()}")
    return kb

def create_knowledge_with_meta():
    """ 基于知识库 携带元数据生成 """
    # 转换为文本格式
    texts = []
    metadatas = []
    with open("./examples/rag/idioms.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        # 组合成一段文本
        text = f"成语：{item['idiom']}，拼音：{item['pinyin']}，释义：{item['note']}，出处：{item['source']}，分类：{item['category']}，感情色彩：{item['emotion']}"
        texts.append(text)
        metadatas.append({"id": item["id"], "category": item["category"]})

    kb = KnowledgeBase.create(
        name="idiom_docs",
        config=KnowledgeBaseConfig(
            persist_directory="./examples/rag/kb_data/idiom_docs",
            chunk_config=KnowledgeChunkConfig(
                chunk_size=2000,
                chunk_overlap=0,
            ),
            embedding_config=EmbeddingConfig
        )
    )

    kb.add_texts(texts, metadatas=metadatas)

    kb.generate()

    print(f"知识库创建成功: {kb.get_stats()}")
    return kb

if __name__ == "__main__":
    # kb1 = create_knowledge_by_document()
    # kb2 = create_knowledge_by_text()
    create_knowledge_with_meta()
    print("\n=== 知识库创建完成 ===")
