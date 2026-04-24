# 项目启动步骤（完整 · 可直接运行）

> 本项目包含两个独立子系统，可分开启动：
> - **子系统 A** — `milvus_faq`：基于 Milvus 的 FAQ 检索系统（无需 Docker）
> - **子系统 B** — `graph_rag`：融合知识图谱的多跳问答系统（需要 Docker）

---

## 前置条件

| 工具 | 版本要求 | 验证命令 |
|------|---------|---------|
| Python | ≥ 3.11 | `python --version` |
| uv | 任意 | `uv --version` |
| Docker & Docker Compose | 任意 | `docker --version`（仅 graph_rag 需要） |

---

## 第一步：依赖安装

```bash
# 进入项目根目录
cd week03-homework-2

# uv 自动读取 pyproject.toml，创建虚拟环境并安装所有依赖
uv sync
```

> `uv sync` 会自动创建 `.venv` 虚拟环境，无需手动 `pip install`。

---

## 第二步：环境配置

项目根目录已有 `.env` 文件，检查并填入真实的 API Key：

```bash
# 查看当前配置
cat .env
```

`.env` 内容如下（请替换为你自己的 Key）：

```dotenv
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx   # 通义千问 API Key（必填）

# Neo4j 配置（仅 graph_rag 子系统需要）
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123
```

> **获取 DASHSCOPE_API_KEY**：登录 [阿里云百炼平台](https://bailian.console.aliyun.com/) → API-KEY 管理 → 创建 API Key

---

## 子系统 A：启动 Milvus FAQ 检索系统

> **入口文件：`milvus_faq/main.py`**
> **启动命令：`python -m milvus_faq.main`**

### 无需额外数据库初始化，直接启动：

```bash
# 在项目根目录下运行
uv run python -m milvus_faq.main
```

启动成功后输出类似：

```
启动 FastAPI 服务...
数据文件路径: data/faqs.csv
Milvus Lite 数据库路径: ./milvus_demo.db
嵌入模型: text-embedding-v2
正在初始化 Milvus 向量存储...
索引和查询引擎初始化完成。
INFO:     Started server process [xxxxx]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 访问服务：

- API 文档（Swagger UI）：http://localhost:8000/docs
- 根路径测试：http://localhost:8000/

### 测试接口：

```bash
# 查询 FAQ
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "如何申请退货？"}'

# 热更新知识库（修改 data/faqs.csv 后调用）
curl -X POST http://localhost:8000/api/update-index
```

---

## 子系统 B：启动 GraphRAG 多跳问答系统

> **入口文件：`graph_rag/main.py`**
> **启动命令：`python -m graph_rag.main`**

### 第一步：启动 Neo4j 数据库

```bash
# 在项目根目录下启动 Neo4j 容器
docker compose up -d

# 等待 Neo4j 完全启动（约 30 秒），验证：
docker compose ps
# 应看到 neo4j_faq 状态为 Up
```

> Neo4j Browser 管理界面：http://localhost:7474（账号 `neo4j` / 密码 `password123`）

### 第二步：初始化知识图谱（仅首次运行需要）

```bash
# 将 shareholders.csv 数据导入 Neo4j，构建公司-股东图谱
uv run python -m graph_rag.graph_builder
```

输出类似：

```
正在清空现有图谱数据...
正在创建节点和关系...
图谱节点和关系创建完成。
正在为 'Entity' 节点的 'name' 属性创建索引...
索引创建成功。
图谱构建流程结束。
```

### 第三步：启动服务

```bash
uv run python -m graph_rag.main
```

启动成功后输出类似：

```
启动 FastAPI 服务...
在启动服务前，请确保您已经运行了图谱构建脚本
未找到向量索引，正在从文件创建...  # 首次运行自动构建 RAG 索引
查询引擎已准备就绪。
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 测试接口：

```bash
# 多跳问答
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "星辰科技的最大股东是谁？"}'
```

---

## 运行测试脚本

```bash
# 先确保服务已在 8000 端口运行，然后执行：
uv run python test_api.py
# 测试结果将保存到 test_results.json
```

---

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| `请检查 .env 文件` 报错 | 确认 `.env` 中 `DASHSCOPE_API_KEY` 已填写 |
| Neo4j 连接失败 | 执行 `docker compose up -d` 并等待 30 秒 |
| 8000 端口被占用 | `lsof -i :8000` 找到进程后 `kill <PID>` |
| 首次启动慢 | 正常，首次需要构建向量索引（调用 Embedding API） |

---

## 目录结构速览

```
week03-homework-2/
├── .env                  # 环境变量（API Key 等）
├── pyproject.toml        # uv 项目依赖配置
├── docker-compose.yml    # Neo4j 容器配置
├── data/                 # 原始数据文件
├── milvus_faq/           # 子系统 A：FAQ 检索
│   └── main.py           # ← 入口文件 A
├── graph_rag/            # 子系统 B：GraphRAG 问答
│   └── main.py           # ← 入口文件 B
└── test_api.py           # 接口测试脚本
```
