import os
import pandas as pd
import logging
from functools import lru_cache
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
)
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.node_parser import SemanticSplitterNodeParser
from . import config

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 使用单例模式确保全局只有一个 IndexManager 实例
_query_engine = None
_index = None

# 缓存装饰器，缓存查询结果，减少重复查询
@lru_cache(maxsize=100)
def cached_query(question: str):
    """缓存查询结果"""
    query_engine = get_query_engine()
    return query_engine.query(question)


def _initialize_index():
    """内部函数，用于初始化或加载索引"""
    global _index, _query_engine

    logger.info("正在初始化 Milvus 向量存储...")
    try:
        vector_store = MilvusVectorStore(
            uri=config.MILVUS_URI,
            collection_name=config.COLLECTION_NAME,
            dim=config.DIMENSION,
            overwrite=False,  # 设置为 False 以便重用现有集合
        )
        
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        if not os.path.exists(config.FAQ_FILE):
            logger.warning(f"数据文件 {config.FAQ_FILE} 不存在。创建一个空索引。")
            # 如果数据文件不存在，创建一个空索引
            _index = VectorStoreIndex.from_documents(
                [], storage_context=storage_context
            )
        else:
            # 检查集合是否已存在且有数据
            try:
                # 尝试从已有的 vector_store 加载索引
                _index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                )
                logger.info("从现有 Milvus 集合加载索引。")
            except Exception as e:
                 # 如果加载失败（例如集合为空），则从文档构建
                logger.warning(f"无法从现有集合加载，将从文件构建索引: {str(e)}")
                _index = _build_index_from_file(storage_context)

        _query_engine = _index.as_query_engine(similarity_top_k=3)
        logger.info("索引和查询引擎初始化完成。")
    except Exception as e:
        logger.error(f"初始化索引时出错: {str(e)}")
        raise


def _build_index_from_file(storage_context: StorageContext) -> VectorStoreIndex:
    """从 CSV 文件构建索引"""
    logger.info(f"从文件 {config.FAQ_FILE} 构建新索引...")
    try:
        df = pd.read_csv(config.FAQ_FILE)
        documents = []
        for _, row in df.iterrows():
            doc_text = f"问题: {row['question']}\n答案: {row['answer']}"
            documents.append(Document(text=doc_text, metadata={"question": row['question']}))

        # 使用语义切分器优化文档切片
        splitter = SemanticSplitterNodeParser.from_defaults(
            embed_model=config.EMBED_MODEL
        )
        
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            transformations=[splitter]
        )
        logger.info("索引构建完成。")
        return index
    except Exception as e:
        logger.error(f"构建索引时出错: {str(e)}")
        raise


def get_query_engine():
    """获取查询引擎的公共接口"""
    if _query_engine is None:
        _initialize_index()
    return _query_engine


def update_index():
    """
    热更新索引。
    这将清空现有集合并从文件中重新构建索引。
    """
    global _index, _query_engine
    logger.info("开始热更新索引...")
    
    try:
        # 创建一个新的 Milvus 存储，并设置 overwrite=True 来清空旧集合
        vector_store = MilvusVectorStore(
            uri=config.MILVUS_URI,
            collection_name=config.COLLECTION_NAME,
            dim=config.DIMENSION,
            overwrite=True, 
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # 从文件重新构建索引
        _index = _build_index_from_file(storage_context)
        _query_engine = _index.as_query_engine(similarity_top_k=3)
        
        # 清除缓存
        cached_query.cache_clear()
        
        logger.info("索引热更新完成。")
        return {"message": "索引已成功更新。"}
    except Exception as e:
        logger.error(f"更新索引时出错: {str(e)}")
        raise


# 在模块加载时自动初始化
try:
    _initialize_index()
except Exception as e:
    logger.error(f"初始化索引失败: {str(e)}")
    # 不中断程序启动，允许后续手动初始化
