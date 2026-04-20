from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from . import index_manager

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    score: float
    confidence: str  # 新增置信度字段


class ErrorResponse(BaseModel):
    error: str
    detail: str


@router.post("/query", response_model=list[QueryResponse])
async def query_faq(request: QueryRequest):
    """
    接收用户问题并返回最相关的FAQ条目。
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    logger.info(f"收到查询: {request.question}")
    try:
        # 使用缓存的查询函数
        response = index_manager.cached_query(request.question)

        if not response.source_nodes:
            return []

        results = []
        for node in response.source_nodes:
            # 从节点文本中解析出原始问题和答案
            text_parts = node.get_text().split('\n答案: ')
            original_question = text_parts[0].replace('问题: ', '')
            answer = text_parts[1] if len(text_parts) > 1 else "答案未找到"
            score = node.get_score() or 0.0
            
            # 计算置信度
            confidence = "高" if score > 0.8 else "中" if score > 0.5 else "低"
            
            results.append(
                QueryResponse(
                    question=original_question,
                    answer=answer,
                    score=score,
                    confidence=confidence
                )
            )
        
        return results
    except Exception as e:
        logger.error(f"查询过程中出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/update-index")
async def update_faq_index():
    """
    触发知识库的热更新。
    系统将从 data/faqs.csv 重新加载并建立索引。
    """
    try:
        result = index_manager.update_index()
        logger.info("索引更新成功")
        return {"status": "success", "message": result["message"]}
    except Exception as e:
        logger.error(f"索引更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"索引更新失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    try:
        # 尝试获取查询引擎，验证系统状态
        index_manager.get_query_engine()
        return {"status": "healthy", "message": "系统运行正常"}
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {"status": "unhealthy", "message": f"系统异常: {str(e)}"}
