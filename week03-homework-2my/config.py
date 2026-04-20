# 统一配置管理

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 通义千问 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = "neo4j"

# 数据路径
DATA_DIR = "data"
FAQ_FILE = os.path.join(DATA_DIR, "faqs.csv")
COMPANY_DOC_PATH = os.path.join(DATA_DIR, "companies.txt")
SHAREHOLDER_CSV_PATH = os.path.join(DATA_DIR, "shareholders.csv")

# 索引路径
INDEX_DIR = "vector_index"
MILVUS_URI = "./milvus_demo.db"  # Milvus Lite 使用本地文件
COLLECTION_NAME = "faq_collection"
DIMENSION = 1536  # 通义千问 text-embedding-v2 模型的维度

# 验证配置
def validate_config():
    """验证配置是否正确"""
    errors = []
    
    if not DASHSCOPE_API_KEY:
        errors.append("DASHSCOPE_API_KEY 未设置")
    
    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
        errors.append("Neo4j 配置未完全设置")
    
    # 检查数据目录
    if not os.path.exists(DATA_DIR):
        errors.append(f"数据目录 {DATA_DIR} 不存在")
    else:
        # 检查必要的数据文件
        if not os.path.exists(FAQ_FILE):
            errors.append(f"FAQ 文件 {FAQ_FILE} 不存在")
        if not os.path.exists(COMPANY_DOC_PATH):
            errors.append(f"公司文档 {COMPANY_DOC_PATH} 不存在")
        if not os.path.exists(SHAREHOLDER_CSV_PATH):
            errors.append(f"股东数据 {SHAREHOLDER_CSV_PATH} 不存在")
    
    return errors

# 打印配置信息
def print_config():
    """打印当前配置信息"""
    print("========================================")
    print("           系统配置信息")
    print("========================================")
    print(f"DASHSCOPE_API_KEY: {'已设置' if DASHSCOPE_API_KEY else '未设置'}")
    print(f"NEO4J_URI: {NEO4J_URI}")
    print(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
    print(f"NEO4J_PASSWORD: {'已设置' if NEO4J_PASSWORD else '未设置'}")
    print(f"数据目录: {DATA_DIR}")
    print(f"FAQ 文件: {FAQ_FILE}")
    print(f"公司文档: {COMPANY_DOC_PATH}")
    print(f"股东数据: {SHAREHOLDER_CSV_PATH}")
    print(f"索引目录: {INDEX_DIR}")
    print(f"Milvus 数据库: {MILVUS_URI}")
    print("========================================")

if __name__ == "__main__":
    print_config()
    errors = validate_config()
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"- {error}")
    else:
        print("配置验证通过！")