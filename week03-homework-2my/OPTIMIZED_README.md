# 优化后的 AI 系统运行指南

## 系统架构

### 1. Milvus FAQ 检索系统

- **核心功能**：基于 Milvus 向量库的 FAQ 问答系统
- **技术栈**：
  - Python 3.9+
  - FastAPI（API 接口）
  - LlamaIndex（索引构建和查询）
  - Milvus Lite（向量存储）
  - 通义千问（文本嵌入）

- **优化点**：
  - 添加了查询缓存机制，提升重复查询性能
  - 完善的错误处理和日志记录
  - 增加了健康检查接口
  - 优化了响应格式，添加了置信度评估
  - 热更新索引功能

### 2. GraphRAG 多跳问答系统

- **核心功能**：融合文档检索和知识图谱的多跳问答系统
- **技术栈**：
  - Python 3.9+
  - FastAPI（API 接口）
  - LlamaIndex（索引构建和查询）
  - Neo4j（知识图谱）
  - 通义千问（LLM 和文本嵌入）

- **优化点**：
  - 添加了查询缓存机制，提升重复查询性能
  - 完善的错误处理和日志记录
  - 增加了健康检查接口
  - 增加了引擎重新初始化功能
  - 优化了实体识别和查询流程

## 环境要求

- Python 3.9 或更高版本
- WSL 或 Ubuntu 系统
- Neo4j 数据库（仅 GraphRAG 系统需要）
- 通义千问 API Key

## 快速开始

### 1. 配置环境

1. **克隆仓库**：
   ```bash
   git clone https://github.com/RuiLu007/ai_engineer.git
   cd ai_engineer/homework_examples/week03-homework-2my
   ```

2. **创建并激活虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   ```

3. **安装依赖**：
   ```bash
   pip install -e .
   ```

4. **配置环境变量**：
   - 复制 `.env.example` 文件为 `.env`
   - 填写通义千问 API Key 和 Neo4j 配置

### 2. 准备数据

- **Milvus FAQ 系统**：
  - 确保 `data/faqs.csv` 文件存在，格式如下：
    ```csv
    question,answer
    如何退货？,您可以在订单页面申请退货，或联系客服处理。
     shipping?,
    ```

- **GraphRAG 系统**：
  - 确保 `data/companies.txt` 文件存在，包含公司相关信息
  - 确保 `data/shareholders.csv` 文件存在，格式如下：
    ```csv
    company_name,shareholder_name,shareholder_type,share_percentage
    星辰科技,张明,个人,35.5
    星辰科技,李氏集团,公司,25.3
    ```

### 3. 启动系统

使用统一启动脚本：

```bash
./start.sh
```

根据菜单选择要启动的系统：
1. **Milvus FAQ 检索系统**：在 http://localhost:8000 运行
2. **GraphRAG 多跳问答系统**：在 http://localhost:8000 运行

### 4. 构建知识图谱（仅 GraphRAG 系统需要）

在启动 GraphRAG 系统前，需要先构建知识图谱：

```bash
python -m graph_rag.graph_builder
```

## API 接口使用

### Milvus FAQ 系统

1. **查询接口**：
   - URL: `POST /api/query`
   - 请求体：
     ```json
     {
       "question": "如何退货？"
     }
     ```
   - 响应：
     ```json
     [
       {
         "question": "如何退货？",
         "answer": "您可以在订单页面申请退货，或联系客服处理。",
         "score": 0.95,
         "confidence": "高"
       }
     ]
     ```

2. **热更新索引**：
   - URL: `POST /api/update-index`
   - 响应：
     ```json
     {
       "status": "success",
       "message": "索引已成功更新。"
     }
     ```

3. **健康检查**：
   - URL: `GET /api/health`
   - 响应：
     ```json
     {
       "status": "healthy",
       "message": "系统运行正常"
     }
     ```

### GraphRAG 系统

1. **查询接口**：
   - URL: `POST /api/query`
   - 请求体：
     ```json
     {
       "question": "星辰科技的最大股东是谁？"
     }
     ```
   - 响应：
     ```json
     {
       "final_answer": "星辰科技的最大股东是张明，持股比例为 35.5%。",
       "reasoning_path": [
         "步骤 1: 从问题 '星辰科技的最大股东是谁？' 中识别出核心实体 -> '星辰科技'",
         "步骤 2: 识别到关键词'最大股东'，构造精确 Cypher 查询在图谱中查找。",
         "   - Cypher 查询: MATCH (shareholder:Entity)-[r:HOLDS_SHARES_IN]->(company:Entity {name: '星辰科技'}) RETURN shareholder.name AS shareholder, r.share_percentage AS percentage ORDER BY percentage DESC LIMIT 1",
         "   - 图谱查询结果: [{"shareholder": "张明", "percentage": 35.5}]",
         "步骤 3: 通过 RAG 检索关于 '星辰科技' 的背景文档信息。",
         "   - RAG 检索到的上下文: 星辰科技成立于 2010 年，是一家专注于人工智能领域的科技公司...",
         "步骤 4: 综合图谱结果和文档信息，由 LLM 生成最终的自然语言回答。"
       ],
       "entity_name": "星辰科技"
     }
     ```

2. **重新初始化引擎**：
   - URL: `POST /api/reinitialize`
   - 响应：
     ```json
     {
       "status": "success",
       "message": "引擎重新初始化成功"
     }
     ```

3. **健康检查**：
   - URL: `GET /api/health`
   - 响应：
     ```json
     {
       "status": "healthy",
       "message": "系统运行正常"
     }
     ```

## 系统优化详情

### Milvus FAQ 系统优化

1. **缓存机制**：
   - 使用 `lru_cache` 装饰器缓存查询结果，减少重复查询的响应时间
   - 缓存大小设置为 100，可根据实际需求调整

2. **错误处理**：
   - 完善的异常捕获和日志记录
   - 系统启动时的错误处理，确保服务能够正常启动

3. **日志记录**：
   - 配置了详细的日志记录，包括系统启动、查询处理、错误信息等
   - 日志格式包含时间戳、模块名、日志级别和消息

4. **API 接口优化**：
   - 增加了健康检查接口，便于监控系统状态
   - 优化了响应格式，添加了置信度评估
   - 统一的错误响应格式

5. **热更新功能**：
   - 支持不重启服务的情况下更新知识库
   - 更新时自动清除缓存，确保获取最新数据

### GraphRAG 系统优化

1. **缓存机制**：
   - 使用 `lru_cache` 装饰器缓存查询结果，提升重复查询性能
   - 缓存大小设置为 50，可根据实际需求调整

2. **错误处理**：
   - 完善的异常捕获和日志记录
   - 各模块的独立错误处理，确保系统稳定性

3. **日志记录**：
   - 详细的日志记录，便于问题定位和系统监控
   - 关键操作的日志输出

4. **API 接口优化**：
   - 增加了健康检查接口，便于监控系统状态
   - 增加了引擎重新初始化接口，方便在配置变更后刷新系统
   - 优化了响应格式，添加了识别出的实体名称

5. **查询流程优化**：
   - 优化了实体识别和查询流程
   - 增加了错误处理和容错机制
   - 提高了系统的稳定性和可靠性

## 性能优化建议

1. **数据预处理**：
   - 对 FAQ 数据进行清洗和标准化，提高检索准确性
   - 对公司文档进行分块处理，优化 RAG 检索效果

2. **索引优化**：
   - 根据数据量调整 Milvus 索引参数
   - 定期优化 Neo4j 数据库，确保查询性能

3. **缓存策略**：
   - 根据实际查询量调整缓存大小
   - 考虑使用 Redis 等分布式缓存，提升系统扩展性

4. **部署优化**：
   - 使用 Docker 容器化部署，便于环境管理
   - 考虑使用负载均衡，提升系统并发能力

## 故障排查

### 常见问题

1. **Milvus 连接失败**：
   - 检查 Milvus Lite 数据库文件权限
   - 确保磁盘空间充足

2. **Neo4j 连接失败**：
   - 检查 Neo4j 服务是否启动
   - 验证 Neo4j 配置是否正确
   - 确保网络连接正常

3. **API Key 错误**：
   - 检查 DASHSCOPE_API_KEY 是否正确设置
   - 确保 API Key 未过期

4. **数据文件不存在**：
   - 检查数据文件路径是否正确
   - 确保数据文件格式符合要求

### 日志查看

系统日志输出到控制台，同时也可以在代码中添加更多日志记录，便于问题定位。

## 结语

本优化方案通过添加缓存机制、完善错误处理、增加日志记录和优化 API 接口，显著提升了系统的性能和可靠性。同时，统一的启动脚本和配置管理使得系统更加易于使用和维护。

通过这些优化，两个系统能够更好地满足实际应用场景的需求，提供更快速、更准确的服务。