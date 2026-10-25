"""
RAG 检索评测集。

每条测试包含：
- question: 用户可能的问法
- expected_ids: 期望检索到的错题 ID 列表（任一命中即算 Hit）
- note: 备注，说明这条测什么
"""

# 注意：二叉树有 3 条重复（之前测试时重复录入的）
BAYES_TREE_IDS = [
    "2b4e8579a0bf4c949d93d48008baad7b",
    "98e135c89bd446db99c706531113b4e1",
    "dbd355d2219f468ca384d4298a7af554",
]

SORT_IDS = [
    "67d6ce0ac84a4caf8e0211a364ed1084",
    "dfbfd0b0e7df4ba29ff1a28936669728",
]

PROCESS_THREAD_IDS = [
    "01c167a7190d45e892e7ea35bab813eb",
    "c305f2a875ef465cb995f86e64d2d6f0",
]


EVAL_SET = [
    # ========== 直接问（对应原题）==========
    {
        "question": "二叉树那道题为什么选B？",
        "expected_ids": BAYES_TREE_IDS,
        "note": "直接问，含主题词",
    },
    {
        "question": "时间复杂度O(n log n)的排序算法有哪些？",
        "expected_ids": SORT_IDS,
        "note": "直接问，含主题词",
    },
    {
        "question": "哈希表在最坏情况下的查找时间复杂度是多少？",
        "expected_ids": ["3b88637aa0a94468a9faa5ad859e274e"],
        "note": "直接问",
    },
    {
        "question": "快速排序最坏情况的时间复杂度是？",
        "expected_ids": ["9772b67e1cba4d62a651ab92e173b435"],
        "note": "直接问",
    },
    {
        "question": "HTTP状态码404表示什么？",
        "expected_ids": ["b360fce86fab4952a1133c3cacf80d9e"],
        "note": "直接问",
    },

    # ========== 换种问法（语义匹配）==========
    {
        "question": "二叉树是不是线性结构？",
        "expected_ids": BAYES_TREE_IDS,
        "note": "换问法，问的是选项A的对错",
    },
    {
        "question": "栈是先进先出还是先进后出？",
        "expected_ids": ["4bf1e20f1e8b4b6b9ea4f898deeda3ec"],
        "note": "换问法，把选项内容直接问",
    },
    {
        "question": "二分查找需要对数组做什么预处理？",
        "expected_ids": ["b2052683fdca438da19a048171403b46"],
        "note": "换问法，问前提条件",
    },
    {
        "question": "BST中序遍历会得到什么顺序？",
        "expected_ids": ["f2d1794d91194ad784756acf450cd193"],
        "note": "换问法，用缩写BST",
    },
    {
        "question": "404错误是什么意思？",
        "expected_ids": ["b360fce86fab4952a1133c3cacf80d9e"],
        "note": "换问法，加'错误'二字",
    },

    # ========== 概念问（知识点匹配）==========
    {
        "question": "进程和线程的核心区别是什么？",
        "expected_ids": PROCESS_THREAD_IDS,
        "note": "概念问",
    },
    {
        "question": "死锁产生的必要条件有哪些？",
        "expected_ids": ["7abc2c5666f647e78657aee1bc031667"],
        "note": "概念问，注意原题问的是'不包括'",
    },
    {
        "question": "动态规划和分治法有什么不同？",
        "expected_ids": ["e829e7325f8240999daf51becc4ed2d8"],
        "note": "概念问",
    },
    {
        "question": "数据库索引能带来什么好处？",
        "expected_ids": ["950d92ab9ea0453b967f0187f2395d1e"],
        "note": "概念问，问作用",
    },
    {
        "question": "Java里==和equals该用哪个？",
        "expected_ids": ["849473ec4a8c47ba9fe0d6527ca4aec2"],
        "note": "概念问",
    },

    # ========== 偏门问法（考验语义匹配）==========
    {
        "question": "InnoDB默认用什么隔离级别？",
        "expected_ids": ["9fa7ea12075a40d89685ddec8298e73b"],
        "note": "偏门问法",
    },
    {
        "question": "HTTPS走哪个端口？",
        "expected_ids": ["d035bd623906410cbb673cfe17ad58cf"],
        "note": "偏门问法",
    },
    {
        "question": "单链表删节点要注意什么？",
        "expected_ids": ["3602f8c9224e4ec9931b49b8ebb2e09a"],
        "note": "偏门问法",
    },
    {
        "question": "TCP第二次握手发的是什么？",
        "expected_ids": ["20a0820316b04c0bb5852875481919f6"],
        "note": "偏门问法",
    },
    {
        "question": "HashMap和Hashtable有什么不同？",
        "expected_ids": ["de5d486a7e874c3e920f71ad23b53f25"],
        "note": "偏门问法",
    },

    # ========== 无对应题（测空结果处理）==========
    {
        "question": "什么是红黑树？",
        "expected_ids": [],
        "note": "题库里没有，应返回空或低分",
    },
    {
        "question": "什么是B+树？",
        "expected_ids": [],
        "note": "题库里没有",
    },

    # ========== 跨知识点模糊问 ==========
    {
        "question": "我数据结构有哪些错题？",
        "expected_ids": BAYES_TREE_IDS + ["f2d1794d91194ad784756acf450cd193", "4bf1e20f1e8b4b6b9ea4f898deeda3ec"],
        "note": "模糊问，涉及多个数据结构题",
    },
]