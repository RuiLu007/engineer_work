from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import logging
from . import query_engine

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., example="星辰科技的最大股东是谁？")


class QueryResponse(BaseModel):
    final_answer: str
    reasoning_path: List[str]
    entity_name: str = Field(default="未知", description="识别出的实体名称")


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    接收多跳问答查询
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    logger.info(f"收到GraphRAG查询: {request.question}")
    try:
        # 使用缓存的查询函数
        result = query_engine.cached_multi_hop_query(request.question)
        # 确保返回的数据包含所有必要字段
        if "entity_name" not in result:
            result["entity_name"] = "未知"
        return result
    except Exception as e:
        # 打印详细错误信息到服务器日志，方便调试
        logger.error(f"查询处理时发生错误: {e}")
        raise HTTPException(status_code=500, detail=f"处理查询时发生内部错误: {str(e)}")


@router.post("/reinitialize")
async def reinitialize_engines():
    """
    重新初始化所有查询引擎
    """
    try:
        query_engine.reinitialize_engines()
        logger.info("引擎重新初始化成功")
        return {"status": "success", "message": "引擎重新初始化成功"}
    except Exception as e:
        logger.error(f"引擎重新初始化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新初始化失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    try:
        # 验证查询引擎是否初始化
        if query_engine._rag_query_engine and query_engine._kg_query_engine:
            return {"status": "healthy", "message": "系统运行正常"}
        else:
            return {"status": "warning", "message": "部分引擎未初始化"}
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {"status": "unhealthy", "message": f"系统异常: {str(e)}"}