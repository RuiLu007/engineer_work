#!/bin/bash

# 启动脚本 - 用于启动 Milvus FAQ 系统和 GraphRAG 系统

echo "========================================"
echo "        AI 系统启动脚本"
echo "========================================"

# 检查 Python 环境
echo "检查 Python 环境..."
python --version

# 检查依赖
echo "检查依赖..."
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 未找到 pyproject.toml 文件"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip install -e .

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cat > .env << EOF
# 通义千问 API Key
DASHSCOPE_API_KEY=

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
EOF
    echo ".env 文件已创建，请填写相应的配置值"
fi

# 启动菜单
while true; do
    echo ""
    echo "请选择要启动的系统:"
    echo "1. Milvus FAQ 检索系统"
    echo "2. GraphRAG 多跳问答系统"
    echo "3. 退出"
    read -p "请输入选项 (1-3): " choice

    case $choice in
        1)
            echo "启动 Milvus FAQ 检索系统..."
            echo "系统将在 http://localhost:8000 上运行"
            echo "API 文档地址: http://localhost:8000/docs"
            echo "按 Ctrl+C 停止服务"
            python -m milvus_faq.main
            ;;
        2)
            echo "启动 GraphRAG 多跳问答系统..."
            echo "系统将在 http://localhost:8000 上运行"
            echo "API 文档地址: http://localhost:8000/docs"
            echo "按 Ctrl+C 停止服务"
            python -m graph_rag.main
            ;;
        3)
            echo "退出..."
            exit 0
            ;;
        *)
            echo "无效选项，请重新输入"
            ;;
    esac
done