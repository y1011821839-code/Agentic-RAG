"""
Document Processor - 文档处理模块
"""
import uuid
import re
from typing import List, Dict
from pathlib import Path


class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, min_chunk_size: int = 50):
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
        # 句子分隔符：句号、问号、感叹号、分号、换行
        self.sentence_endings = r'(?<=[。！？；\n])\s*'

    def process_file(self, file_path: str, content: str) -> List[Dict]:
        """处理上传的文件"""
        # 清理文本
        text = self.clean_text(content)

        # 分割成块
        chunks = self.split_text(text)

        # 添加到向量库
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{Path(file_path).stem}_{i}_{uuid.uuid4().hex[:8]}"
            documents.append({
                "id": doc_id,
                "content": chunk,
                "metadata": {
                    "source": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })

        return documents

    def clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        return text.strip()

    def split_text(self, text: str) -> List[str]:
        """语义分割：先在段落/句子边界切分，再按大小合并"""
        if len(text) <= self.chunk_size:
            return [text] if text else []

        # 第一步：按句子边界切分
        sentences = [s.strip() for s in re.split(self.sentence_endings, text) if s.strip()]

        # 第二步：将短句合并为接近 chunk_size 的块
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # 如果当前块加新句子仍在大小限制内，或当前块太小
            if not current_chunk:
                current_chunk = sentence
            elif len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                current_chunk += "。" + sentence if not current_chunk.rstrip().endswith(('。', '！', '？', '；')) else sentence
            else:
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                current_chunk = sentence

        # 最后一块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)
        elif current_chunk and chunks:
            # 太短的尾块合并到前一块
            chunks[-1] += "。" + current_chunk

        return chunks


# 全局实例
document_processor = DocumentProcessor()
