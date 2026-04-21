# 智能客服系统学习笔记

## 一、项目概述

这是一个基于 **LangChain** 和 **LangGraph** 的多轮对话智能客服系统，支持工具调用和模型/插件热更新。

### 核心功能

| 功能 | 描述 |
|------|------|
| 多轮对话 | 基于 LangGraph 状态图管理对话流程 |
| 工具调用 | 订单查询、退款申请、发票开具、时间解析 |
| 热更新 | 运行时更新模型和工具，不中断服务 |
| REST API | FastAPI 提供 `/chat` 和 `/hot-update` 接口 |

### 技术栈

| 技术 | 版本要求 | 用途 |
|------|----------|------|
| Python | ≥ 3.11 | 运行环境 |
| LangChain | ≥ 0.3.27 | Chain 构建 |
| LangGraph | ≥ 0.6.7 | 流程编排 |
| FastAPI | ≥ 0.117.1 | Web API |
| DashScope | ≥ 1.24.6 | 通义千问 LLM |
| Uvicorn | ≥ 0.37.0 | ASGI 服务器 |

---

## 二、项目架构

```
week04-homework/
├── smart_customer_service/           # 核心代码包
│   ├── __init__.py                  # 包初始化，导出默认工具
│   ├── services.py                  # ServiceManager - 模型和工具管理
│   ├── graph.py                     # GraphManager - LangGraph 图管理
│   ├── api.py                       # FastAPI 应用入口
│   └── tools/                       # 工具模块
│       ├── __init__.py              # 默认工具列表
│       ├── order_tools.py           # 订单相关工具
│       └── time_tool.py             # 时间解析工具
├── tests/
│   └── test_features.py             # 自动化测试
├── pyproject.toml                   # 项目依赖配置
└── README.md                        # 作业说明
```

### 模块关系图

```
┌─────────────────────────────────────────────────────────┐
│                        API 层                           │
│                      (api.py)                           │
│  /health  /chat  /hot-update                           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   GraphManager                         │
│                    (graph.py)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   agent     │  │   tools     │  │ ask_for_order_id │ │
│  │   节点      │  │   节点       │  │     节点         │ │
│  └──────┬──────┘  └──────▲──────┘  └─────────────────┘ │
│         │               │                               │
│         └───────────────┼───────────────────────────────┤
│                         ▼                               │
│               ┌─────────────────┐                       │
│               │  ServiceManager  │                      │
│               │  (services.py)   │                      │
│               └────────┬─────────┘                      │
│                        │                                │
│         ┌───────────────┼────────────────┐              │
│         ▼               ▼                ▼              │
│   ┌──────────┐   ┌────────────┐   ┌────────────────┐   │
│   │   LLM    │   │ query_order│   │ get_date_for... │   │
│   │ (通义千问) │   │ apply_refund│   │                │   │
│   │          │   │ generate_.. │   │                │   │
│   └──────────┘   └────────────┘   └────────────────┘   │
│                  Tools                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 三、核心模块详解

### 3.1 ServiceManager（services.py）

**职责**：管理 LLM 模型和可用工具

```python
class ServiceManager:
    def __init__(self):
        self._llm = ChatTongyi(model_name="qwen-plus", temperature=0)
        self._tools = default_tools  # [query_order, apply_refund, generate_invoice, get_date_for_relative_time]

    def get_llm(self) -> ChatTongyi
    def get_tools(self) -> list
    def update_llm(self, model_name: str)      # 模型热更新
    def update_tools(self, new_tools: list)      # 工具热更新
```

**热更新原理**：调用 `update_llm()` 或 `update_tools()` 后，需要调用 `GraphManager.reload_graph()` 创建新的图实例。

### 3.2 GraphManager（graph.py）

**职责**：构建和管理 LangGraph 对话流程

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]  # 消息历史
```

**图节点**：

| 节点 | 作用 |
|------|------|
| `agent` | 调用 LLM，决定是否需要工具调用 |
| `tools` | 执行具体工具调用 |
| `ask_for_order_id` | 当用户未提供订单号时追问 |

**路由逻辑**（`_router`）：

```
用户输入
    │
    ├── 包含"查订单" 且 不包含订单号 ──→ ask_for_order_id（追问）
    │
    └── 其他 ──→ agent（LLM 处理）
```

**条件边**（`_should_continue`）：

```
agent 输出
    │
    ├── 有 tool_calls ──→ tools（执行工具）
    │
    └── 无 tool_calls ──→ END（结束）
```

### 3.3 工具模块（tools/）

#### 3.3.1 订单工具（order_tools.py）

| 工具 | 函数签名 | 功能 |
|------|----------|------|
| `query_order` | `order_id: str` | 查询订单状态和物流 |
| `apply_refund` | `order_id: str, reason: str` | 申请退款 |
| `generate_invoice` | `order_id: str` | 生成发票 |

#### 3.3.2 时间工具（time_tool.py）

```python
@tool
def get_date_for_relative_time(relative_time_str: str) -> str:
    """将"昨天"、"前天"、"上周三"转换为 YYYY-MM-DD"""
```

示例：
- "昨天" → "2025-09-25"
- "上周三" → "2025-09-17"

### 3.4 API 层（api.py）

FastAPI 应用，提供三个端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/chat` | POST | 发送对话 |
| `/hot-update` | POST | 热更新 |

**ChatRequest 模型**：

```python
class ChatRequest(BaseModel):
    user_id: str   # 会话追踪 ID
    query: str      # 用户输入
```

**热更新请求**：

```python
class HotUpdateRequest(BaseModel):
    type: str   # "model" 或 "tools"
    name: str   # 模型名或工具集名
```

---

## 四、启动方式

### 4.1 环境准备（WSL/Ubuntu）

```bash
# 1. 进入项目目录
cd /home/lurui/00ai_engineer/engineer_work/homework_examples/week04-homework

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 添加 DASHSCOPE_API_KEY
```

**`.env` 文件示例**：

```env
DASHSCOPE_API_KEY=your-api-key-here
```

### 4.2 启动服务

```bash
# 方式一：使用 uvicorn 直接运行
uvicorn smart_customer_service.api:app --host 0.0.0.0 --port 8000

# 方式二：作为模块运行
python -m smart_customer_service.api

# 方式三：在代码中运行
# 在 api.py 末尾有 if __name__ == "__main__": uvicorn.run(...)
```

### 4.3 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 测试对话
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "query": "查订单"}'
```

**预期响应**：

```json
{"user_id": "user123", "response": "好的，请问您的订单号是多少？"}
```

---

## 五、对话流程示例

### 5.1 查询订单（已提供订单号）

```
用户: 帮我查一下订单 SN20240924001
系统: 调用 query_order(order_id="SN20240924001")
系统: 订单状态：已发货，物流号：SF123456789
```

### 5.2 查询订单（未提供订单号）

```
用户: 我要查订单
系统: 好的，请问您的订单号是多少？
用户: SN20240924001
系统: 调用 query_order(order_id="SN20240924001")
系统: 订单状态：已发货，物流号：SF123456789
```

### 5.3 发票开具

```
用户: 开具发票，订单号是 SN20240924003
系统: 调用 generate_invoice(order_id="SN20240924003")
系统: 发票已生成，下载地址：https://example.com/invoices/SN20240924003.pdf
```

---

## 六、热更新机制

### 6.1 模型热更新

```bash
curl -X POST http://localhost:8000/hot-update \
  -H "Content-Type: application/json" \
  -d '{"type": "model", "name": "qwen-max"}'
```

**流程**：

```
ServiceManager.update_llm("qwen-max")
    ↓
GraphManager.reload_graph()  # 创建新的图实例
    ↓
新对话使用新模型，旧对话继续完成
```

### 6.2 工具热更新

```bash
# 仅保留查询订单工具
curl -X POST http://localhost:8000/hot-update \
  -H "Content-Type: application/json" \
  -d '{"type": "tools", "name": "query_only"}'

# 恢复默认工具
curl -X POST http://localhost:8000/hot-update \
  -H "Content-Type: application/json" \
  -d '{"type": "tools", "name": "default"}'
```

---

## 七、测试

### 7.1 运行测试

```bash
# 运行所有测试
cd /home/lurui/00ai_engineer/engineer_work/homework_examples/week04-homework
uv run python -m unittest discover -s tests -q

# 运行单个测试
uv run python -m unittest tests.test_features.TestFeatures.test_invoice_tool
```

### 7.2 测试用例

| 测试 | 验证内容 |
|------|----------|
| `test_invoice_tool` | 发票生成工具返回正确的 URL |
| `test_hot_update_preserves_sessions` | 热更新后旧会话不受影响 |

---

## 八、开发建议

### 8.1 添加新工具

1. 在 `tools/order_tools.py` 中定义新工具：

```python
@tool
def new_tool(param: str) -> dict:
    """新工具描述"""
    # 实现逻辑
    return {"success": True, "data": "..."}
```

2. 在 `tools/__init__.py` 中添加到 `default_tools` 列表

3. 重启服务或调用热更新接口

### 8.2 修改对话流程

编辑 `graph.py` 中的 `_build_graph()` 方法：

- 添加新节点：`workflow.add_node("new_node", handler_function)`
- 添加新边：`workflow.add_edge("node_a", "node_b")`
- 添加条件边：`workflow.add_conditional_edges("node", condition_fn, mapping)`

### 8.3 意图识别优化

当前 `_router` 使用简单关键词匹配，可考虑：

- 接入专门的意图识别模型
- 使用 LangChain 的 Intent Classification 链

---

## 九、问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `DASHSCOPE_API_KEY` 警告 | 未设置环境变量 | 编辑 `.env` 添加 API Key |
| 工具调用失败 | 订单号不存在 | 使用测试订单号：SN20240924001 等 |
| 热更新无效 | 未调用 `reload_graph()` | 确保热更新后重新加载图 |
| 端口占用 | 8000 端口被占用 | 使用 `--port` 指定其他端口 |

---

## 十、总结

本项目展示了一个完整的 AI Agent 应用架构：

1. **状态管理**：通过 `AgentState` 维护对话历史
2. **流程编排**：通过 LangGraph 实现条件分支和节点路由
3. **工具调用**：LangChain Tools 自动绑定和执行
4. **热更新**：解耦 ServiceManager 和 GraphManager，支持不停机更新

这个架构适合作为生产级 AI 客服系统的起点，可进一步扩展为支持更多业务场景、更复杂的对话管理和更高性能的部署方案。

---

## 十一、小版本优化记录（订单识别与热更新安全）

这次优化保持了原有架构不变，只做了几处**小而实用**的增强，重点解决“输入识别过松”和“错误参数被悄悄吞掉”两个问题。

### 11.1 优化目标

| 优化点 | 原问题 | 优化后效果 |
|------|------|------|
| 订单号校验 | 只要包含 `SN` 就可能被视为合法订单号 | 改为统一格式校验，避免误判 |
| 查询意图识别 | 只识别“查订单”，像“查物流”“看订单状态”覆盖不到 | 支持更多自然表达，缺单号时自动追问 |
| 热更新参数处理 | 未知工具集会默认回退，容易掩盖配置错误 | 改为明确报错，行为更可控 |

### 11.2 本次新增/修改的文件

| 文件 | 修改内容 | 原因 |
|------|------|------|
| `smart_customer_service/order_utils.py` | 新增订单号标准化与正则校验辅助函数 | 抽离公共逻辑，避免各处重复判断 |
| `smart_customer_service/tools/order_tools.py` | 查询、退款、发票工具统一走严格订单号校验 | 提升工具结果可靠性 |
| `smart_customer_service/graph.py` | 扩展订单查询关键词路由逻辑 | 让“查物流/订单状态”这类表达也能触发补问 |
| `smart_customer_service/api.py` | 收紧热更新参数校验，未知工具集返回 400 | 防止错误配置被静默兜底 |
| `tests/test_features.py` | 增加非法订单号、物流追问、未知工具集测试 | 保证优化后的行为可回归验证 |

### 11.3 为什么这样优化

1. **订单号校验统一化**  
   原实现中退款和发票工具只判断字符串里是否包含 `SN`，例如 `invalid-sn` 这种输入也可能误入成功分支。优化后统一要求订单号满足类似 `SN20240924003` 的格式，工具返回会更稳定。

2. **路由逻辑更贴近真实用户表达**  
   用户不一定会说“查订单”，很多时候会说“帮我查下物流”“看下订单状态”。这类请求本质上都依赖订单号，因此在缺少订单号时应主动追问，而不是直接落回模型自由回答。

3. **热更新失败要显式暴露**  
   原来工具热更新里，只要不是 `query_only` 就会默认恢复 `default`，这会让拼写错误或错误配置被掩盖。改成显式报错后，问题更容易定位，也更符合服务端接口设计习惯。

### 11.4 优化后的收益

- 工具调用更稳，不容易把脏输入当成有效订单号
- 客服追问更自然，订单相关请求的命中率更高
- 热更新接口更安全，错误配置能尽快暴露
- 改动范围小，没有破坏原有模块解耦结构
