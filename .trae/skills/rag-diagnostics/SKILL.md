---
name: "rag-diagnostics"
description: "Diagnoses common RAG system issues (chunk sizing, retrieval recall, hybrid search overlap, tool calling accuracy, embedding dimensions, API latency, empty chunks). Invoke when user asks to audit, diagnose, or optimize a RAG project."
---

# RAG System Diagnostics

Diagnose a RAG (Retrieval-Augmented Generation) project and produce a structured report with scores, findings, and optimization suggestions.

## When to Invoke

- User asks to "check", "diagnose", "audit", or "review" a RAG system
- User wants to know if their RAG setup is optimal
- User asks about retrieval quality, chunk strategy, or embedding health
- User says "审视项目" or "检查 RAG" in the context of a RAG codebase

## Diagnostic Checklist

Run the following 8 checks against the target RAG project. Score each 0-100, classify as `pass` (≥80), `warning` (60-79), or `fail` (<60).

### 1. Chunk Size Distribution

Check the text splitter / document processor code. Analyze:
- What is `chunk_size`? Ideal range: **300-800** characters for Chinese, **500-1000** tokens for English
- Is there overlap? `chunk_overlap` should be 10-20% of `chunk_size`
- Splitting strategy: semantic (by sentence/paragraph) or naive (by character count)?
- Edge case: what happens to the last chunk if it's very short?

**Scoring:**
- Chunk size in ideal range: +40
- Has overlap: +20
- Semantic splitting: +30
- Handles short tail chunks: +10

**Suggestion format:** "将 chunk_size 从 X 调整为 Y" or "建议添加 chunk_overlap = Z"

### 2. Retrieval Recall (Self-Retrieval Test)

If ChromaDB is available and has documents:
- Pick 3-5 random chunks from the vector store
- Extract a key sentence from each as the query
- Search with that sentence as query
- Check if the original chunk appears in top-3 results

**Scoring:**
- Each chunk found in top-3: +25 (max 100 for 4 tests)

**Suggestion format:** "top_k 建议增大到 N" or "建议添加重排序（Reranker）" if recall < 70

### 3. Vector-BM25 Overlap Rate

For hybrid retrieval systems:
- Run the same query through both vector and BM25
- Compare top-5 results between the two
- Calculate overlap = |intersection| / 5

**Interpretation:**
- Overlap < 30%: Vector and BM25 are **complementary** — hybrid is very beneficial
- Overlap 30-60%: Normal
- Overlap > 60%: Redundant — one of them could be simplified, or the corpus is too homogeneous
- Overlap = 0%: Either BM25 index is broken or the corpus has no keyword overlap

**Scoring:**
- 20-50% overlap: +100 (ideal complementarity)
- 0-20%: +60 (complementary but may indicate BM25 issues)
- 50-70%: +70 (functional but redundant)
- >70%: +40 (too much overlap, wasted computation)

### 4. Query Rewriting Effectiveness

If query rewriting is enabled:
- Count how many user queries get rewritten vs. passed through
- Check if rewritten queries are actually shorter/more keyword-like
- Verify rewrite doesn't strip critical context

**Scoring:**
- Rewriting enabled: +30
- Has length threshold (only long queries rewritten): +30
- Rewritten output is ≤ original length: +20
- Fallback to original on error: +20

**Suggestion:** "将改写阈值从 X 字调整为 Y 字" or "改写 prompt 建议添加示例"

### 5. Tool Calling Accuracy

For Agent-based RAG with tools:
- Check tool detection method: regex-first + LLM fallback is optimal
- Verify parsed tool arguments are validated before execution
- Check that the calculator uses safe eval (AST, not built-in eval)
- Check API tools have timeout and error handling

**Scoring:**
- Two-tier decision (regex + LLM FC): +40
- Arguments validated: +20
- Safe calculator (AST whitelist): +20
- API tools have timeout: +20

### 6. Embedding Configuration

- Check embedding model dimensions (e.g., text-embedding-v2 = 1536, text-embedding-v3 = 1024)
- Verify ChromaDB collection distance metric (cosine is preferred for text)
- Check if embedding API has retry logic for rate limits (429)
- Verify batch embedding is used for bulk uploads (not one-by-one)

**Scoring:**
- Correct dimensions: +30
- Cosine distance: +30
- Retry logic: +20
- Batch embedding: +20

### 7. API Call Performance

- Check if embedding/chat calls have timeout configured
- Retry logic for 429 rate limits present?
- SSE streaming enabled for chat?
- Any sync blocking calls in async context?

**Scoring:**
- Timeout configured: +25
- 429 retry: +25
- SSE streaming: +25
- Async/non-blocking: +25

### 8. Data Quality

- Scan for empty or whitespace-only chunks in vector store
- Check for chunks shorter than 20 characters
- Check document metadata completeness (source, chunk_index present?)
- Check that sensitive data (.env, API keys) is gitignored

**Scoring:**
- No empty chunks: +30
- No ultra-short chunks: +30
- Metadata complete: +20
- .env gitignored: +20

## Output Format

Produce a markdown report:

```markdown
## RAG 系统诊断报告

**总体评分：XX / 100** | 通过: X | 警告: X | 失败: X

| # | 检查项 | 状态 | 得分 | 问题 | 建议 |
|---|--------|------|------|------|------|
| 1 | 分块大小分布 | 🟢/🟡/🔴 | XX | ... | ... |
| 2 | 检索召回率 | ... | ... | ... | ... |
| ... |

### 🔴 必须修复
### 🟡 建议优化
### 🟢 表现良好
```

## Execution Notes

- Read the relevant source files first — don't guess
- For checks 2, 3, 6: run actual queries against ChromaDB if available
- For checks 1, 4, 5, 7, 8: inspect source code only
- If ChromaDB is empty or inaccessible, skip checks 2, 3 and note "数据不足"
- Always provide **specific, actionable** suggestions with file/line references