import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessage
from .tools import default_tools


load_dotenv()


class MockCustomerServiceLLM:
    """本地兜底模型，避免在未配置真实模型密钥时服务无法启动。"""

    def __init__(self, model_name: str = "mock-customer-service"):
        self.model_name = model_name
        self._tools = []

    def bind_tools(self, tools: list):
        self._tools = tools
        return self

    def invoke(self, messages):
        user_message = messages[-1].content if messages else ""

        if "发票" in user_message:
            return AIMessage(content="请提供订单号，我来为您开具发票。")
        if "退款" in user_message:
            return AIMessage(content="请提供订单号和退款原因，我来为您提交退款申请。")
        if "查订单" in user_message:
            return AIMessage(content="请提供订单号，我来帮您查询订单状态。")
        if any(keyword in user_message for keyword in ["昨天", "前天", "今天", "上周"]):
            return AIMessage(content="我可以帮您理解相对时间，请补充您的订单相关问题。")

        return AIMessage(content="您好，我可以帮您查询订单、申请退款或开具发票。")


class ServiceManager:
    """
    一个用于管理和提供模型及工具的服务管理器。
    """
    def __init__(self):
        print("正在初始化 LLM 和工具...")
        self._llm = self._create_llm()
        self._tools = default_tools
        print("✅ ServiceManager 初始化完成。")
        self.print_services()

    def _create_llm(self):
        return self._create_llm_by_name("qwen-plus")

    def _create_llm_by_name(self, model_name: str):
        if not os.environ.get("DASHSCOPE_API_KEY"):
            print("⚠️ 警告: DASHSCOPE_API_KEY 环境变量未设置，已切换到本地 Mock LLM。")
            return MockCustomerServiceLLM(model_name=f"mock-{model_name}")

        return ChatTongyi(
            model_name=model_name,
            temperature=0,
            streaming=True
        )

    def get_llm(self):
        return self._llm

    def get_tools(self) -> list:
        return self._tools

    def update_llm(self, model_name: str):
        print(f"🔄 [热更新] 正在更新LLM模型为: {model_name}")
        self._llm = self._create_llm_by_name(model_name)
        self.print_services()

    def update_tools(self, new_tools: list):
        print("🔄 [热更新] 正在更新工具列表...")
        self._tools = new_tools
        self.print_services()

    def print_services(self):
        print("--- 当前服务状态 ---")
        print(f"  模型: {self._llm.model_name}")
        print(f"  工具: {[tool.name for tool in self._tools]}")
        print("--------------------")

    def get_services_status(self) -> dict:
        return {
            "model": self._llm.model_name,
            "tools": [tool.name for tool in self._tools]
        }


# 创建一个单例
service_manager = ServiceManager()
