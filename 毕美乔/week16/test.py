import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True  # 自动转成字符串
)

print(r.ping())  # True 表示连接成功

# 删除旧数据
r.delete("mylist")

# 左侧插入
r.lpush("mylist", "a")
r.lpush("mylist", "b")

# 右侧插入
r.rpush("mylist", "c")

# 查看全部
print(r.lrange("mylist", 0, -1))

print(r.lpop("mylist"))  # 左侧弹出
print(r.rpop("mylist"))  # 右侧弹出

print(r.llen("mylist"))


r.delete("myset")

r.sadd("myset", "apple")
r.sadd("myset", "banana")
r.sadd("myset", "apple")  # 不会重复

print(r.smembers("myset"))

# 判断是否存在
print(r.sismember("myset", "apple"))  # True

#删除元素
r.srem("myset", "apple")
print(r.scard("myset"))

#数量
print(r.scard("myset"))