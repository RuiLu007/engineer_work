import operator
from typing import Annotated, Sequence, Literal, TypedDict
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .order_utils import has_order_id
from .services import ServiceManager


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


class GraphManager:
    ORDER_QUERY_KEYWORDS = ("查订单", "查询订单", "订单状态", "物流", "快递")
    RELATIVE_TIME_KEYWORDS = ("昨天", "前天", "今天", "上周")

    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self._app = self._build_graph()

    def _build_graph(self):
        """构建或重新构建 LangGraph 应用"""
        workflow = StateGraph(AgentState)
        
        tools = self.service_manager.get_tools()
        tool_node = ToolNode(tools)

        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", tool_node)
        workflow.add_node("ask_for_order_id", self._ask_for_order_id)

        workflow.set_conditional_entry_point(
            self._router,
            {
                "ask_for_order_id": "ask_for_order_id",
                "agent": "agent",
            },
        )
        workflow.add_edge('ask_for_order_id', END)
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {"tools": "tools", "end": END}
        )
        workflow.add_edge('tools', 'agent')

        app = workflow.compile()
        print("✅ LangGraph graph built/rebuilt successfully!")
        return app

    def get_app(self):
        """获取编译好的 LangGraph 应用实例"""
        return self._app

    def reload_graph(self):
        """热重载图，应用新的服务（模型或工具）"""
        self._app = self._build_graph()

    def _call_model(self, state: AgentState):
        print("--- [Node] Agent: Thinking... ---")
        try:
            llm = self.service_manager.get_llm()
            tools = self.service_manager.get_tools()
            model_with_tools = llm.bind_tools(tools)
            response = model_with_tools.invoke(state['messages'])
            return {"messages": [response]}
        except Exception as e:
            print(f"模型调用错误: {e}")
            return {"messages": [AIMessage(content="抱歉，系统出现错误，请稍后再试。")]}

    @classmethod
    def _router(cls, state: AgentState) -> Literal["agent", "ask_for_order_id"]:
        print("--- [Node] Router: Analyzing user intent... ---")
        last_message = state['messages'][-1]
        if cls._needs_order_id(last_message.content):
            print("--- [Decision] Routing to 'ask_for_order_id'. ---")
            return "ask_for_order_id"

        print("--- [Decision] Routing to 'agent'. ---")
        return "agent"

    @classmethod
    def _needs_order_id(cls, message_content: str) -> bool:
        if has_order_id(message_content):
            return False

        if any(keyword in message_content for keyword in cls.RELATIVE_TIME_KEYWORDS):
            return False

        return any(keyword in message_content for keyword in cls.ORDER_QUERY_KEYWORDS)

    @staticmethod
    def _ask_for_order_id(state: AgentState):
        print("--- [Node] ask_for_order_id: Generating a follow-up question. ---")
        follow_up_message = AIMessage(content="好的，请问您的订单号是多少？")
        return {"messages": [follow_up_message]}

    @staticmethod
    def _should_continue(state: AgentState) -> Literal["tools", "end"]:
        last_message = state['messages'][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            print("--- [Decision] LLM requested a tool call, routing to tool node. ---")
            return "tools"
        print("--- [Decision] No tool call, ending turn. ---")
        return "end"
