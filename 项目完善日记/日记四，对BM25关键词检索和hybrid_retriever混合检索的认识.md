## 近日完成：

- ##### 构建BM25关键词检索路径：

  - tokenize采用jieba（结巴）分词器：对中文分词效果好，对复杂英文长文本效果较差。关于tokenize的认识如下：

    - 编写STOPWORDS字典，写入高频废话，如“的”，“了”一类，减少token消耗

    - 使用jieba.lcut（）直接获取token列表

    - isalnum（）函数负责过滤“__”等特殊字符，标点符号

  - load_corpus加载语料库，经历获取集合collection（client.get_or_create_collection），获取data（get获取），构建chunks（list[dict]，注意zip压缩）

  - build_index构建索引，load_corpus获取语料后，BM25kapi构建索引（return BM25kapi（chunks））

  - invalidate清空目标缓存，直接将预先构建的cache列表进行pop（）栈顶弹出操作

    - 这是我第一次接触清空缓存的操作，我以为是cache = {}直接置空，结果是用pop，必要性还不清楚。

  - get_bm25串联管线，流程如下：按user_id检查缓存 -> （存在则直接返回）-> 实例化client -> 加载corpus -> 构建index -> 写入cache -> 返回cache["user_id"]

- ##### 实现混合检索（hybrid_retriever），纯向量检索与关键词检索并行：

  - RRF，倒数排名融合，用于合并多路召回结果。

    - 单路向量相似度无法直接比较，但排名可以。依据固定计算公式可以得出得分，得分越高越接近正确答案。

  - 认识了hybrid_retriever的基本流程：vector召回 -> bm25召回 -> RRF融合 -> 返回召回结果



## 笔者感想：

        其实这些天都把重心转向py刷题了，因为我发现我的py知识确实很欠缺。项目自然是怠慢了。后面还是报一下蓝桥吧，看看能不能拿个国奖。



### 2026.9.6最终完成
