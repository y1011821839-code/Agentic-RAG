"""
API Routes - 文档管理接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.schemas import DocumentUploadResponse
from app.core.retriever import retriever
from app.core.document_processor import document_processor
import tempfile
import os

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传并处理文档"""
    try:
        # 读取文件内容
        content = await file.read()

        # 根据文件类型处理
        if file.filename.endswith('.txt'):
            text = content.decode('utf-8')
        elif file.filename.endswith('.md'):
            text = content.decode('utf-8')
        else:
            # 其他格式暂时只读取文本部分
            try:
                text = content.decode('utf-8')
            except:
                raise HTTPException(
                    status_code=400,
                    detail="暂不支持的文件格式，请上传 .txt 或 .md 文件"
                )

        # 处理文档
        documents = document_processor.process_file(
            file_path=file.filename,
            content=text
        )

        if not documents:
            raise HTTPException(status_code=400, detail="文档内容为空")

        # 添加到向量库
        await retriever.add_documents(documents)

        return DocumentUploadResponse(
            success=True,
            document_id=documents[0]["id"].split('_')[0],
            chunks_count=len(documents),
            message=f"成功处理 {len(documents)} 个文档块"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误，请稍后重试")


@router.delete("/clear")
async def clear_documents():
    """清空所有文档"""
    try:
        retriever.delete_all()
        return {"success": True, "message": "已清空所有文档"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count")
async def get_document_count():
    """获取文档数量"""
    try:
        count = retriever.get_count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
