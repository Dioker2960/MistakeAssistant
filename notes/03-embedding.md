# Embedding 与向量检索

## 解决什么问题
把文本转成向量，让语义相近的文本在向量空间中距离接近。
从而支持"按语义匹配"，不依赖关键词。

## 在项目中的位置
- `ai/embedding_service.py`：调 Embedding API，把文本转成 1024 维向量
- `ai/vector_store.py`：FAISS 索引，存向量 + 文本 + id 映射
- `ai/retriever.py`：根据用户问题检索 Top-K 错题

## 执行流程
### 索引构建（启动时）
1. 从 MySQL 读所有错题
2. 每条错题用 `build_question_text` 拼成一段文本
3. `embed_batch` 批量向量化
4. `vector_store.clear()` → 逐条 `add` → `save()` 写磁盘

### 检索（用户提问时）
1. 把用户问题 `embed` 成向量
2. `FAISS.search(vector, k)` → 返回位置 + 分数
3. 用 `_id_mapping[位置]` 查 question_id
4. 用 `_texts[question_id]` 查文本

## 关键概念
- **向量维度**：1024（千问 text-embedding-v3）
- **余弦相似度**：两个向量夹角的余弦值，越接近 1 越相似
- **归一化**：向量除以 L2 范数，变单位向量，此时内积 = 余弦相似度
- **FAISS**：C++ 实现的向量检索库，比纯 Python 快几十倍
- **IndexFlatIP**：内积索引，配合归一化向量实现余弦相似度

## 存储结构
```text
data/
├── faiss.index       # 纯向量（FAISS 管理）
└── faiss_meta.json   # {id_mapping: [...], texts: {...}}
```

- `_index`：FAISS 索引，位置 i 对应一个向量
- `_id_mapping`：list，位置 i 对应一个 question_id
- `_texts`：dict，question_id 对应文本

**三者靠 add 的顺序严格对齐。**

## 遇到过什么问题

1. 维度不匹配：FAISS 要求 float32，用 `np.array(vec, dtype="float32")`
2. 归一化：必须做，否则内积不等于余弦相似度
3. 零向量：加 `if norm == 0` 防御
4. `top_k` 超过索引数量会报错：用 `k = min(top_k, _index.ntotal)`
5. numpy 类型不能被 JSON 序列化：`int()` + `float()` 转换
6. FAISS 只返回位置，不返回 question_id：自己维护映射
7. 持久化：`faiss.write_index` + `json.dump`，加载时 `read_index` + `json.load`

## 面试怎么解释

- **Embedding 和 LLM 的区别**：Embedding 输出向量（用于匹配），LLM 输出文本（用于生成）
- **为什么用 FAISS 不用 Milvus**：数据量小（几千条），单机够用，零运维成本
- **FAISS 持久化的价值**：启动时几毫秒加载，不用重新调 Embedding API
- **FAISS 是库不是数据库**：不保证事务、不支持元数据过滤、不支持分布式
- **为什么可接受**：数据可从 MySQL 重建，最坏情况是丢最后一次改动
- **增量更新**：现在全量重建，将来可以做增量 add