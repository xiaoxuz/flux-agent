# RAG 模块使用指南

Flux-Agent 提供了完整的 RAG (Retrieval-Augmented Generation) 能力。

## 安装依赖

```bash
pip install flux-agent[rag]
```

---

## 快速开始

### 1. 创建知识库

```python
from flux_agent.rag import (
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeChunkConfig,
    KnowledgeEmbeddingConfig,
)

# 配置
config = KnowledgeBaseConfig(
    name="idiom_docs",
    persist_directory="./kb_data/idiom_docs",
    chunk_config=KnowledgeChunkConfig(
        chunk_size=2000,  # 调大避免切分
        chunk_overlap=0,
    ),
    embedding_config=KnowledgeEmbeddingConfig(
        model="text-embedding-3-small",
        api_key="your-api-key",
        base_url="https://your-proxy.com/v1",
    )
)

# 创建知识库
kb = KnowledgeBase.create(name="idiom_docs", config=config)

# 添加数据
kb.add_texts(
    texts=[
        "成语：守株待兔，拼音：shǒu zhū dài tù，释义：比喻不主动努力...，分类：寓言类",
        "成语：画蛇添足，拼音：huà shé tiān zú，释义：比喻做了多余的事...，分类：寓言类",
    ],
    metadatas=[
        {"id": 1002, "category": "寓言类"},
        {"id": 1001, "category": "寓言类"},
    ]
)

# 执行 embedding 并保存
kb.generate()

print(kb.get_stats())
```

### 2. 加载知识库

```python
config = KnowledgeBaseConfig(
    persist_directory="./kb_data/idiom_docs",
    embedding_config=KnowledgeEmbeddingConfig(
        model="text-embedding-3-small",
        api_key="your-api-key",
        base_url="https://your-proxy.com/v1",
    )
)

kb = KnowledgeBase.load(name="idiom_docs", config=config)

# 搜索
docs = kb.similarity_search("守株待兔", k=3)
```

---

## 配置类说明

### KnowledgeBaseConfig

知识库主配置。

```python
@dataclass
class KnowledgeBaseConfig:
    name: str = ""                    # 知识库名称
    persist_directory: str = ""        # 持久化目录
    vector_store_type: str = "chroma"  # 向量存储类型: chroma | file
    embedding_config: KnowledgeEmbeddingConfig = KnowledgeEmbeddingConfig()
    chunk_config: KnowledgeChunkConfig = KnowledgeChunkConfig()
```

### KnowledgeChunkConfig

文档切分配置。

```python
@dataclass
class KnowledgeChunkConfig:
    chunk_size: int = 1000      # 文档块大小
    chunk_overlap: int = 200    # 文档块重叠
    chunk_separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
```

### KnowledgeEmbeddingConfig

Embedding 配置。

```python
@dataclass
class KnowledgeEmbeddingConfig:
    model: str = "text-embedding-3-small"  # Embedding 模型
    api_key: Optional[str] = None          # API 密钥
    base_url: Optional[str] = None         # 自定义端点
```

---

## API 参考

### 类方法

| 方法 | 说明 |
|------|------|
| `KnowledgeBase.create(name, config)` | 创建知识库 |
| `KnowledgeBase.load(name, config)` | 加载知识库 |

### 实例方法

| 方法 | 说明 |
|------|------|
| `add_documents(sources)` | 添加文档文件 |
| `add_texts(texts, metadatas)` | 添加文本 |
| `generate()` | 执行 embedding + 保存 |
| `search(query, k, filter)` | 检索 |
| `similarity_search(query, k, filter)` | 相似度搜索 |
| `similarity_search_with_score(query, k, filter)` | 带分数搜索 |
| `get_by_metadata(filter)` | 根据 metadata 获取 |
| `delete_documents(doc_ids)` | 删除文档 |
| `clear()` | 清空知识库 |
| `get_stats()` | 统计信息 |

### 参数说明

- **filter**: 过滤条件，用于筛选特定 metadata 的文档
  ```python
  # 示例
  filter={"category": "寓言类"}
  filter={"category": "寓言类", "emotion": "贬义"}
  ```

---

## 存储函数

全局知识库存储，供 WorkflowRunner 和节点使用。

```python
from flux_agent.rag import (
    add_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
    clear_knowledge_bases,
)

# 添加知识库
add_knowledge_base("my_kb", kb)

# 获取知识库
kb = get_knowledge_base("my_kb")

# 列出所有
print(list_knowledge_bases())

# 清空
clear_knowledge_bases()
```

---

## WorkflowRunner 集成

### 加载知识库

```python
from flux_agent import WorkflowRunner

runner = WorkflowRunner(
    config_path="workflow.json",
    knowledge_bases={
        "idiom_docs": "./kb_data/idiom_docs",
    },
)

result = runner.invoke({"data": {"question": "守株待兔的意思"}})
```

---

## 节点使用

### LLMNode

```yaml
nodes:
  - id: "llm"
    type: "llm"
    config:
      model_name: "gpt-4o"
      knowledge_base: "idiom_docs"
      rag_top_k: 3
      rag_mode: "prepend"
      user_prompt: "${data.question}"
```

### RagSearchNode

```yaml
nodes:
  - id: "search"
    type: "rag_search"
    config:
      knowledge_base: "idiom_docs"
      query: "${data.question}"
      top_k: 3
      output_key: "data.docs"
```

---

## 文档格式支持

- PDF (.pdf)
- Word (.docx, .doc)
- 文本 (.txt)
- Markdown (.md)
- HTML (.html)
- Excel (.xlsx, .xls, .csv)
- PowerPoint (.pptx)
- JSON (.json)

---

## 示例代码

参考 `examples/rag/` 目录：

| 文件 | 说明 |
|------|------|
| `create.py` | 创建知识库 |
| `search.py` | 搜索知识库 |
| `document.py` | 文档操作 |
