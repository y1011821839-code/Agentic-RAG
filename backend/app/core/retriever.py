"""
Retriever - Chroma 向量检索 + BM25 混合检索
"""
import os
import math
import re
import chromadb
from typing import List, Dict, Optional
from app.core.llm_service import llm_service


class Retriever:
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            persist_directory = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "chroma_db"
            )
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "知识库文档集合"}
        )

        # BM25 索引
        self._bm25_docs: List[str] = []          # 原始文档文本
        self._bm25_tokens: List[List[str]] = []   # 分词后文档
        self._bm25_doc_ids: List[str] = []        # 文档 ID
        self._avgdl: float = 1.0
        self._bm25_idf: Dict[str, float] = {}
        self._bm25_ready = False

        # 启动时重建 BM25 索引
        self._rebuild_bm25_index()

    # ========= 分词 =========

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中文分词：字符 bigram + 英文单词"""
        tokens = []
        # 提取英文单词和数字连续块
        for part in re.findall(r'[a-zA-Z0-9]+|[\u4e00-\u9fff]+', text.lower()):
            if re.match(r'[a-zA-Z0-9]+', part):
                # 英文/数字：直接作为一个词
                tokens.append(part)
            else:
                # 中文：字符级 bigram
                chars = list(part)
                for i in range(len(chars)):
                    tokens.append(chars[i])
                    if i < len(chars) - 1:
                        tokens.append(chars[i] + chars[i + 1])
        return tokens

    # ========= BM25 索引管理 =========

    def _rebuild_bm25_index(self):
        """从 Chroma 重建 BM25 索引"""
        try:
            all_data = self.collection.get(include=["documents", "metadatas"])
            if not all_data or not all_data.get("ids"):
                self._bm25_ready = False
                return

            self._bm25_doc_ids = list(all_data["ids"])
            self._bm25_docs = list(all_data.get("documents", []))
            self._bm25_tokens = [self._tokenize(doc) for doc in self._bm25_docs]

            # 计算 IDF
            N = len(self._bm25_docs)
            df = {}
            for tokens in self._bm25_tokens:
                for token in set(tokens):
                    df[token] = df.get(token, 0) + 1

            self._bm25_idf = {
                token: math.log((N - count + 0.5) / (count + 0.5) + 1)
                for token, count in df.items()
            }

            # 平均文档长度
            total_len = sum(len(t) for t in self._bm25_tokens)
            self._avgdl = total_len / max(N, 1)

            self._bm25_ready = True
        except Exception as e:
            print(f"BM25 索引重建失败: {e}")
            self._bm25_ready = False

    def _bm25_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """计算单个文档的 BM25 分数"""
        k1 = 1.5
        b = 0.75
        doc_len = len(doc_tokens)
        score = 0.0

        for token in query_tokens:
            if token not in self._bm25_idf:
                continue
            tf = doc_tokens.count(token)
            if tf == 0:
                continue
            idf = self._bm25_idf[token]
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_len / self._avgdl)
            score += idf * numerator / denominator

        return score

    def _bm25_search(self, query: str, top_k: int = 10) -> List[tuple]:
        """BM25 检索，返回 (doc_index, score)"""
        if not self._bm25_ready:
            return []

        query_tokens = self._tokenize(query)
        scores = []
        for i, doc_tokens in enumerate(self._bm25_tokens):
            s = self._bm25_score(query_tokens, doc_tokens)
            if s > 0:
                scores.append((i, s))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    # ========= 对外接口 =========

    async def add_documents(self, documents: List[Dict]):
        """添加文档到向量库"""
        if not documents:
            return

        texts = [doc["content"] for doc in documents]
        embeddings = []

        for text in texts:
            embedding = await llm_service.get_embedding(text)
            embeddings.append(embedding)

        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=[doc.get("metadata", {}) for doc in documents],
            ids=[doc["id"] for doc in documents]
        )

        # 重建 BM25 索引
        self._rebuild_bm25_index()

    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict]:
        """混合检索：向量 + BM25，用 RRF 融合排序"""
        # ===== 向量检索 =====
        query_embedding = await llm_service.get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # 多取一些用于融合
            include=["documents", "metadatas", "distances"]
        )

        # 构建向量检索结果 map
        vector_docs = {}
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                doc_id = results["ids"][0][i]
                distance = results["distances"][0][i]
                similarity = 1 - distance
                vector_docs[doc_id] = {
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "similarity": similarity,
                    "id": doc_id
                }

        # ===== BM25 检索 =====
        bm25_results = self._bm25_search(query, top_k=top_k * 2)
        bm25_docs = {}
        for idx, score in bm25_results:
            doc_id = self._bm25_doc_ids[idx]
            metadata = self.collection.get(ids=[doc_id]).get("metadatas") or [{}]
            bm25_docs[doc_id] = {
                "content": self._bm25_docs[idx],
                "metadata": metadata[0],
                "bm25_score": score,
                "id": doc_id
            }

        # ===== RRF 融合 =====
        k = 60  # RRF 常数

        # 给向量结果按 similarity 降序排名
        vec_ranked = sorted(vector_docs.values(), key=lambda x: x["similarity"], reverse=True)
        bm25_ranked = sorted(bm25_docs.values(), key=lambda x: x.get("bm25_score", 0), reverse=True)

        rrf_scores = {}

        # 向量排名贡献
        for rank, doc in enumerate(vec_ranked):
            rrf_scores[doc["id"]] = rrf_scores.get(doc["id"], 0) + 1 / (k + rank + 1)

        # BM25 排名贡献
        for rank, doc in enumerate(bm25_ranked):
            rrf_scores[doc["id"]] = rrf_scores.get(doc["id"], 0) + 1 / (k + rank + 1)

        # 合并文档信息
        all_docs = {}
        for doc in vector_docs.values():
            all_docs[doc["id"]] = doc
        for doc in bm25_docs.values():
            if doc["id"] not in all_docs:
                doc["similarity"] = 0.3  # 仅 BM25 命中的给一个默认相似度
                all_docs[doc["id"]] = doc

        # 按 RRF 分数排序
        scored = [
            (rrf_scores.get(doc_id, 0), doc_id)
            for doc_id in all_docs
            if rrf_scores.get(doc_id, 0) > 0
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        # 输出 top_k 结果
        final_docs = []
        for rrf, doc_id in scored[:top_k]:
            doc = all_docs[doc_id]
            doc["rrf_score"] = rrf
            final_docs.append(doc)

        return final_docs

    def delete_all(self):
        """清空所有文档"""
        try:
            self.client.delete_collection("documents")
            self.collection = self.client.get_or_create_collection(name="documents")
        except:
            pass
        self._bm25_docs = []
        self._bm25_tokens = []
        self._bm25_doc_ids = []
        self._bm25_idf = {}
        self._bm25_ready = False

    def get_count(self) -> int:
        """获取文档数量"""
        return self.collection.count()


# 全局实例
retriever = Retriever()