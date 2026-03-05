import os
import numpy as np
import redis
from typing import Optional, List, Union, Callable, Any
import faiss
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

class SemanticRouter:
    def __init__(self,
                 name,
                 embedding_method: Callable[[Union[str, List[str]]], Any],
                 dim: int = 768,  # 需要知道维度来初始化 FAISS
                 redis_url: str = "localhost",
                 redis_port: int = 6379,
                 redis_password: str = None,
    ):
        self.name = name
        self.embedding_method = embedding_method

        self.redis = redis.Redis(
            host=redis_url,
            port=redis_port,
            password=redis_password
        )

        self.index_path = f"{self.name}.index"
        # 1. 初始化 FAISS 索引 (如果不存在则新建)
        self.index_path = f"{self.name}.index"
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            # 使用简单的暴力搜索 L2 索引，dim 必须匹配向量维度
            self.index = faiss.IndexFlatL2(dim)

    def add_route(self, questions: List[str], target: str, threshold: float = 0.5):
        # vectors = np.array(self.embedding_method(questions)).astype('float32')
        vectors = self.embedding_method(questions)
        # 获取当前索引中的起始 ID
        start_id = self.index.ntotal
        self.index.add(vectors)

        # 1. 将阈值存入 Redis (使用 Hash 结构)
        self.redis.hset(f"{self.name}:configs", target, str(threshold))

        # 2. 将 ID 映射存入 Redis (使用 Hash 结构)
        mapping = {str(start_id + i): target for i in range(len(questions))}
        self.redis.hset(f"{self.name}:map", mapping=mapping)  # 👈 替代了 self.route_map

        # 自动保存索引文件
        faiss.write_index(self.index, self.index_path)

    def route(self, question: str, max_k: int = 5):
        # 1. 向量化输入
        # query_vector = np.array(self.embedding_method(question)).astype('float32')
        query_vector = self.embedding_method(question)
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        # 2. 执行 FAISS 搜索 (k 不能超过当前索引总量)
        actual_k = min(max_k, self.index.ntotal)
        if actual_k == 0:
            return []

        distances, indices = self.index.search(query_vector, k=actual_k)

        # 3. 按路由分组计算距离
        route_distances = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue  # FAISS 没搜够 k 个时会返回 -1

            # 3. 从 Redis 获取路由名称 (替代 self.route_map[idx])
            route_name_bytes = self.redis.hget(f"{self.name}:map", str(idx))
            if not route_name_bytes: continue
            route_name = route_name_bytes.decode('utf-8')

            if route_name not in route_distances:
                route_distances[route_name] = []
            route_distances[route_name].append(dist)

        # 4. 计算平均距离并过滤
        matches = []
        for route_name, dists in route_distances.items():
            avg_dist = sum(dists) / len(dists)

            # 从 Redis 读取该路由的阈值
            thresh_bytes = self.redis.hget(f"{self.name}:configs", route_name)
            threshold = float(thresh_bytes) if thresh_bytes else 0.5

            if avg_dist < threshold:
                matches.append({
                    "name": route_name,
                    "distance": float(avg_dist)
                })

        # 按距离从小到大排序
        return sorted(matches, key=lambda x: x['distance'])


if __name__ == "__main__":
    def get_embedding(text):
        # 确保输入是列表格式
        if isinstance(text, str):
            text = [text]

        # model.encode 直接返回 numpy 数组
        # convert_to_numpy=True 确保返回格式与你的 FAISS 逻辑兼容
        vectors = model.encode(text, convert_to_numpy=True)

        return vectors.astype('float32')

    router = SemanticRouter(
        name="semantic_router",
        dim=384,
        embedding_method=get_embedding,)

    router.add_route(
        questions=["Hi, good morning", "Hi, good afternoon"],
        target="greeting"
    )

    router.add_route(
        questions=["如何退货"],
        target="refund"
    )

    print(router.route("Hi, good morning"))