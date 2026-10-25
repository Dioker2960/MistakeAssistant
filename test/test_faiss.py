import faiss
import numpy as np

print("FAISS 版本:", faiss.__version__)
print("numpy 版本:", np.__version__)

# 简单测试
dim = 128
index = faiss.IndexFlatL2(dim)
vectors = np.random.random((5, dim)).astype("float32")
index.add(vectors)
print("索引中向量数:", index.ntotal)

# 测检索
query = np.random.random((1, dim)).astype("float32")
distances, indices = index.search(query, k=3)
print("最相似的 3 个位置:", indices)
print("对应距离:", distances)