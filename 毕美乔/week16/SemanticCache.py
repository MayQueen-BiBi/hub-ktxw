import os
import numpy as np
import redis
from typing import Optional, List, Union, Callable, Any
import faiss


class SemanticCache:
    def __init__(
            self,
            name: str,
            embedding_method: Callable[[Union[str, List[str]]], Any],
            ttl: int = 3600*24,  # 过期时间
            redis_url: str = "localhost",
            redis_port: int = 6379,
            redis_password: str = None,
            distance_threshold=0.1
    ):
        self.name = name
        self.redis = redis.Redis(
            host=redis_url,
            port=redis_port,
            password=redis_password
        )
        self.ttl = ttl
        self.distance_threshold = distance_threshold
        self.embedding_method = embedding_method
        self.index_path = f"{self.name}.index"
        self.index = None
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(f"{self.name}.index")

    def _to_float32(self, embedding):
        # 确保是 float32 类型的 numpy 数组
        return np.array(embedding).astype('float32')

    def store(self, prompt: Union[str, List[str]], response: Union[str, List[str]]):
        if isinstance(prompt, str):
            prompt, response = [prompt], [response]

        # 1. 处理 Embedding
        embedding = self._to_float32(self.embedding_method(prompt))
        if self.index is None:
            self.index = faiss.IndexFlatL2(embedding.shape[1])

        self.index.add(embedding)
        faiss.write_index(self.index, f"{self.name}.index")

        try:
            with self.redis.pipeline() as pipe:
                for q, a in zip(prompt, response):
                    # 使用前缀区分 key
                    pipe.setex(self.name + ":key:" + q, self.ttl, a)  # 提问和回答存储在redis
                    # 使用 rpush 保证顺序与 FAISS 索引一致
                    pipe.rpush(self.name + "list", q)   # 所有的提问都存储在list里面，方便后续使用
                return pipe.execute()
        except:
            import traceback
            traceback.print_exc()
            return -1

    def call(self, prompt: str):
        if self.index is None:
            return None

        # 新的提问进行编码
        embedding = self._to_float32(self.embedding_method(prompt))

        # 向量数据库中进行检索
        dis, ind = self.index.search(embedding, k=1)

        if ind[0][0] == -1 or dis[0][0] > self.distance_threshold:
            return None

        # 关键修复：根据 FAISS 返回的索引 ind[0][0] 去 Redis 列表找对应的 Prompt
        target_idx = int(ind[0][0])
        matched_prompt = self.redis.lindex(f"{self.name}list", target_idx)
        if matched_prompt:
            return self.redis.get(f"{self.name}:key:{matched_prompt.decode()}")
        return None

        # # 过滤不满足距离的结果
        # filtered_ind = [i for i, d in enumerate(dis[0]) if d < self.distance_threshold]
        # pormpts = self.redis.lrange(self.name + "list", 0, -1)
        # print("pormpts", pormpts)
        # filtered_prompts = [pormpts[i] for i in filtered_ind]

        # 获取得到原始的提问 ，并在redis 找到对应的回答
        # return self.redis.mget([self.name + ":key:" + q.decode() for q in filtered_prompts])

    def clear_cache(self):
        prompts = self.redis.lrange(f"{self.name}list", 0, -1)
        if prompts:
            keys_to_del = [f"{self.name}:key:{p.decode()}" for p in prompts]
            self.redis.delete(*keys_to_del)
        self.redis.delete(f"{self.name}list")
        if os.path.exists(self.index_path):
            os.unlink(f"{self.name}.index")
        self.index = None


if __name__ == "__main__":
    def get_embedding(text):
        if isinstance(text, str):
            text = [text]

        return np.array([np.ones(768) for t in text])


    embed_cache = SemanticCache(
        name="semantic_cache",
        embedding_method=get_embedding,
        ttl=360,
        redis_url="localhost",
    )

    embed_cache.clear_cache()

    embed_cache.store(prompt="hello world", response="hello world1232")
    print(embed_cache.call(prompt="hello world"))

    embed_cache.store(prompt="hello my bame", response="nihao")
    print(embed_cache.call(prompt="hello world"))


"""
有三个“进阶建议”：

- 增加自检逻辑：在 __init__ 初始化最后，比对一下 self.index.ntotal 和 self.redis.llen 的数量，如果不相等，说明上次程序崩溃导致了数据丢失，可以抛出警告。

- 向量归一化：在 store 和 call 之前，使用 faiss.normalize_L2(embedding)。这样可以把向量长度缩放到 1，让 L2 距离的计算结果更加稳定，阈值 distance_threshold 也更好设置（通常 0.1 左右就很精准）。

- 使用 ID 索引：进阶做法是使用 faiss.IndexIDMap，给每个向量手动分配一个 ID，然后把这个 ID 存入 Redis。这样就不再依赖 Redis List 的先后顺序，彻底解决错位问题。
"""