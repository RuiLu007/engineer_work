# 学习笔记：Week03-Homework-2 项目解析

> 作者学习笔记 | 适合新手 | 由浅入深

---

## 一、项目介绍

### 这个项目是什么？

这是一个 **AI 问答系统实战项目**，包含两个独立子系统：

| 子系统 | 解决什么问题 | 核心场景 |
|--------|------------|---------|
| **Milvus FAQ** | 用户提问 → 从知识库找最相关答案 | 客服问答、FAQ 检索 |
| **GraphRAG** | 需要"多跳推理"的复杂问答 | "A 公司的最大股东是谁？" |

### 为什么需要两套系统？

- **FAQ 系统**：问题简单，一跳就能回答，用向量相似度搜索即可
- **GraphRAG**：问题复杂，需要：先找实体 → 再查关系 → 再补充背景 → 最后综合回答，至少 4 跳

---

## 二、架构设计

### 整体架构图

```
用户请求
    │
    ▼
FastAPI（HTTP API 层）
    │
    ├─── milvus_faq 子系统
    │        │
    │        ▼
    │    index_manager（索引管理）
    │        │
    │        ├── Milvus Lite（向量数据库，本地文件）
    │        └── DashScope Embedding（文本向量化）
    │
    └─── graph_rag 子系统
             │
             ▼
         query_engine（多跳查询引擎）
             │
             ├─ Step 1: LLM 提取实体
             ├─ Step 2: Neo4j 图谱查询（Cypher）
             ├─ Step 3: VectorIndex RAG 检索（本地 JSON 文件）
             └─ Step 4: LLM 综合生成答案
```

### 分层设计

```
config.py       ← 配置层：加载环境变量，初始化 LLM 和 Embedding 模型
    │
main.py         ← 入口层：启动 FastAPI 应用，注册路由
    │
api.py          ← 路由层：定义 HTTP 接口，处理请求/响应
    │
index_manager.py / query_engine.py  ← 业务逻辑层：核心查询逻辑
    │
graph_builder.py  ← 数据层：将 CSV 数据写入 Neo4j 图数据库
```

---

## 三、核心功能

### 3.1 Milvus FAQ 检索流程

```
用户问题 "如何退货？"
    │
    ▼
DashScope Embedding 模型 → 将问题转成 1536 维向量
    │
    ▼
Milvus 向量数据库 → 用余弦相似度找最近邻 FAQ 条目
    │
    ▼
返回 Top-3 相关问答（含相似度分数）
```

**关键代码位置**：`milvus_faq/index_manager.py` → `_initialize_index()` 函数

**热更新机制**：
- 调用 `/api/update-index` 接口
- 系统重新读取 `data/faqs.csv`，重建 Milvus 集合
- **不需要重启服务**，修改数据文件后立即生效

### 3.2 GraphRAG 多跳问答流程

以 "星辰科技的最大股东是谁？" 为例：

```
Step 1 【实体识别】
  输入：用户原始问题
  处理：LLM (qwen-plus) 提取关键实体
  输出："星辰科技"

Step 2 【图谱查询】
  输入："星辰科技"
  处理：关键词匹配到"最大股东" → 构造精确 Cypher 查询
  Cypher：MATCH (s)-[r:HOLDS_SHARES_IN]->(c {name:'星辰科技'})
          RETURN s.name, r.share_percentage ORDER BY percentage DESC LIMIT 1
  输出：启明资本，45%

Step 3 【RAG 检索】
  输入："星辰科技"
  处理：向量索引检索相关文档片段
  输出：公司简介文本

Step 4 【综合生成】
  输入：图谱结果 + 文档信息 + 原始问题
  处理：LLM 综合所有信息生成自然语言回答
  输出："星辰科技的最大股东是启明资本，持有45%的股份..."
```

**关键代码位置**：`graph_rag/query_engine.py` → `multi_hop_query()` 函数

---

## 四、技术栈

### 核心依赖

| 技术 | 用途 | 学习重点 |
|------|------|---------|
| **FastAPI** | HTTP API 框架 | 路由装饰器、Pydantic 数据校验 |
| **LlamaIndex** | RAG 框架，编排检索流程 | `VectorStoreIndex`、`StorageContext` |
| **Milvus Lite** | 向量数据库（本地文件版） | 向量存储、相似度搜索 |
| **Neo4j** | 图数据库 | Cypher 查询语言、节点/关系建模 |
| **DashScope** | 通义千问 LLM + Embedding | API 调用方式 |
| **Uvicorn** | ASGI 服务器 | 异步 Web 服务运行时 |
| **python-dotenv** | 环境变量管理 | `.env` 文件加载 |

### 设计亮点

> **⭐ 亮点 1：Milvus Lite 零运维**
>
> 传统 Milvus 需要部署独立服务，而 `Milvus Lite` 只需 `pip install pymilvus`，数据存在本地文件 `milvus_demo.db`，开发环境极其方便。

> **⭐ 亮点 2："Cypher + LLM" 协同策略**
>
> 对高频、关键的查询（如"最大股东"）使用固定 Cypher 模板，保证准确性；对复杂开放性问题使用 LLM 生成 Cypher，保证灵活性。两者结合，兼顾稳定与智能。

> **⭐ 亮点 3：可解释性推理路径**
>
> 每次查询不只返回答案，还返回 `reasoning_path` 列表，记录每一步的推理过程，让用户知道"系统怎么想的"。

> **⭐ 亮点 4：语义切分优化**
>
> 使用 `SemanticSplitterNodeParser` 而非固定长度切分，确保每个 FAQ 条目（问题+答案）作为完整语义单元存入向量库，提高检索精度。

---

## 五、学习重点 / 难点

### 🔴 难点 1：向量嵌入的原理

**核心问题**：文本怎么变成数字？为什么相似的文字对应相似的向量？

```
"如何退货" ──Embedding模型──> [0.12, -0.34, 0.89, ...]  (1536维)
"退款流程" ──Embedding模型──> [0.11, -0.32, 0.91, ...]  (1536维)
                                    ↓ 余弦相似度计算 ≈ 0.95（非常相似！）
```

**学习建议**：理解"语义空间"概念，相似语义 → 相近向量坐标

### 🔴 难点 2：RAG 与知识图谱的区别

| 维度 | RAG（向量检索） | 知识图谱 |
|------|--------------|---------|
| 数据形态 | 非结构化文本 | 结构化的节点和关系 |
| 查询方式 | 语义相似度 | 精确路径查询（Cypher） |
| 擅长场景 | "介绍一下...""背景是什么" | "谁持有...""A和B的关系" |
| 局限性 | 无法精确查"最大持股比例" | 无法理解模糊语义 |

**本项目的核心价值**：把两者结合，取长补短！

### 🔴 难点 3：LlamaIndex 的 StorageContext

```python
# StorageContext 是 LlamaIndex 的"存储适配器"
# 可以接入不同的后端（Milvus、Neo4j、本地文件等）
storage_context = StorageContext.from_defaults(
    vector_store=milvus_store   # 换成 Neo4j 也一样的接口！
)
```

**学习建议**：理解"依赖注入"设计模式，同一套代码，换不同存储后端

### 🟡 重点 1：FastAPI 的 Pydantic 模型

```python
class QueryRequest(BaseModel):
    question: str  # 自动校验：如果不是字符串会报 422 错误

class QueryResponse(BaseModel):
    answer: str
    score: float
```

**学习建议**：Pydantic 负责数据校验和序列化，是 FastAPI 的核心

### 🟡 重点 2：单例模式保护资源

```python
# milvus_faq/index_manager.py
_query_engine = None  # 全局单例

def get_query_engine():
    if _query_engine is None:  # 只初始化一次
        _initialize_index()
    return _query_engine
```

**学习建议**：避免每次请求都重新连接数据库，节省资源

---

## 六、代码阅读顺序

> 建议按照以下顺序阅读，从简单到复杂：

### 先看 Milvus FAQ（更简单）

```
1. milvus_faq/config.py       → 了解配置方式，看看哪些参数可以调
2. milvus_faq/index_manager.py → 核心！理解索引创建和查询流程
3. milvus_faq/api.py           → 看 HTTP 接口怎么定义的
4. milvus_faq/main.py          → 看启动流程
```

### 再看 GraphRAG（更复杂）

```
5. data/companies.txt          → 了解原始数据格式
6. data/shareholders.csv       → 了解关系数据格式
7. graph_rag/graph_builder.py  → 理解如何把 CSV 数据写入 Neo4j
8. graph_rag/config.py         → 配置 LLM 和 Neo4j 连接
9. graph_rag/query_engine.py   → 核心！多跳查询的完整逻辑
10. graph_rag/api.py           → 接口定义
11. graph_rag/main.py          → 启动流程
```

### 最后看测试

```
12. test_api.py                → 学习如何写 API 测试
```

---

## 七、总结

### 这个项目学到了什么？

| 知识点 | 掌握程度目标 |
|--------|------------|
| FastAPI 构建 RESTful API | 能独立创建路由、请求/响应模型 |
| 向量数据库（Milvus）基本操作 | 能理解向量存储和相似度搜索 |
| LlamaIndex 构建 RAG 系统 | 能用 VectorStoreIndex 做文档检索 |
| Neo4j 图数据库基础 | 能读懂 Cypher 查询，理解节点/关系概念 |
| GraphRAG 多跳推理 | 能理解 RAG + KG 协同的设计思想 |
| uv 项目管理 | 能用 `uv sync` 和 `uv run` 管理依赖 |

### 核心思想

> **RAG 是广度，图谱是深度。**
>
> 单独的 RAG 能找到相关文档，但无法精确查询关系数据；
> 单独的图谱能精确查询，但不理解模糊语义；
> **两者结合，才能处理真实世界的复杂问题。**

### 扩展学习方向

1. 📖 学习 Cypher 查询语言 → [Neo4j 官方教程](https://neo4j.com/docs/cypher-manual/current/)
2. 📖 深入 LlamaIndex → [官方文档](https://docs.llamaindex.ai/)
3. 📖 了解更多 RAG 优化技术 → HyDE、ReRank、Parent-Child 切分
4. 📖 了解 GraphRAG 的前沿研究 → Microsoft GraphRAG 论文
