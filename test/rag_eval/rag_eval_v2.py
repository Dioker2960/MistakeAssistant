"""
RAG 评测集 v2——覆盖更多场景。

每条测试：
- question: 用户可能的问法
- expected_ids: 期望命中（任一命中即算 Hit）
- category: 类别（用于分类统计）
- note: 备注（可选）
"""

# ========== 错题 ID 别名（便于阅读）==========
# 二叉树
BT1 = "2b4e8579a0bf4c949d93d48008baad7b"
BT2 = "98e135c89bd446db99c706531113b4e1"
BT3 = "dbd355d2219f468ca384d4298a7af554"
BT_TEST = "080157f5a87b45f88d1edcce9cd2efe6"
BST = "f2d1794d91194ad784756acf450cd193"

# 排序算法
SORT1 = "67d6ce0ac84a4caf8e0211a364ed1084"
SORT2 = "dfbfd0b0e7df4ba29ff1a28936669728"
QUICK = "9772b67e1cba4d62a651ab92e173b435"

# 数据结构
HASH = "3b88637aa0a94468a9faa5ad859e274e"
STACK = "4bf1e20f1e8b4b6b9ea4f898deeda3ec"
LINKED = "3602f8c9224e4ec9931b49b8ebb2e09a"

# 算法
BINARY = "b2052683fdca438da19a048171403b46"
DP = "e829e7325f8240999daf51becc4ed2d8"

# 网络
TCP = "20a0820316b04c0bb5852875481919f6"
HTTP404 = "b360fce86fab4952a1133c3cacf80d9e"
HTTPS = "d035bd623906410cbb673cfe17ad58cf"
NET_TEST1 = "1b96ea19ed4f412ea8ab5cf45c9133a5"
NET_TEST2 = "75f1e759844c40f6899ee0d4913f843c"

# 操作系统
PROC1 = "01c167a7190d45e892e7ea35bab813eb"
PROC2 = "c305f2a875ef465cb995f86e64d2d6f0"
DEADLOCK = "7abc2c5666f647e78657aee1bc031667"

# 其他
JAVA_EQ = "849473ec4a8c47ba9fe0d6527ca4aec2"
INDEX = "950d92ab9ea0453b967f0187f2395d1e"
INNODB = "9fa7ea12075a40d89685ddec8298e73b"
HASHMAP = "de5d486a7e874c3e920f71ad23b53f25"


EVAL_SET = [
    # ============================================================
    # 类别 1：直接问（含主题词）
    # ============================================================
    {
        "question": "二叉树那道题为什么选B？",
        "expected_ids": [BT1, BT2, BT3],
        "category": "direct",
    },
    {
        "question": "时间复杂度 O(n log n) 的排序算法是？",
        "expected_ids": [SORT1, SORT2],
        "category": "direct",
    },
    {
        "question": "哈希表最坏情况下的查找时间复杂度是多少？",
        "expected_ids": [HASH],
        "category": "direct",
    },
    {
        "question": "栈有什么特点？",
        "expected_ids": [STACK],
        "category": "direct",
    },
    {
        "question": "单链表删除节点需要知道什么？",
        "expected_ids": [LINKED],
        "category": "direct",
    },
    {
        "question": "HTTP 状态码 404 表示什么？",
        "expected_ids": [HTTP404],
        "category": "direct",
    },
    {
        "question": "TCP 三次握手的第二次，服务端发送什么？",
        "expected_ids": [TCP],
        "category": "direct",
    },
    {
        "question": "快速排序最坏情况下的时间复杂度是多少？",
        "expected_ids": [QUICK],
        "category": "direct",
    },
    {
        "question": "二分查找的前提条件是什么？",
        "expected_ids": [BINARY],
        "category": "direct",
    },
    {
        "question": "动态规划和分治法的核心区别是什么？",
        "expected_ids": [DP],
        "category": "direct",
    },

    # ============================================================
    # 类别 2：换种问法（同义表达）
    # ============================================================
    {
        "question": "二叉树是不是线性结构？",
        "expected_ids": [BT1, BT2, BT3],
        "category": "paraphrase",
        "note": "问的是选项 A 的对错",
    },
    {
        "question": "二叉搜索树的中序遍历得到什么顺序？",
        "expected_ids": [BST],
        "category": "paraphrase",
    },
    {
        "question": "栈是先进先出还是先进后出？",
        "expected_ids": [STACK],
        "category": "paraphrase",
    },
    {
        "question": "HTTPS 走哪个端口？",
        "expected_ids": [HTTPS],
        "category": "paraphrase",
    },
    {
        "question": "404 错误是什么意思？",
        "expected_ids": [HTTP404],
        "category": "paraphrase",
    },
    {
        "question": "快速排序的平均时间复杂度是多少？",
        "expected_ids": [SORT1, SORT2, QUICK],
        "category": "paraphrase",
    },
    {
        "question": "数据库索引能带来什么好处？",
        "expected_ids": [INDEX],
        "category": "paraphrase",
    },
    {
        "question": "InnoDB 默认用的是什么隔离级别？",
        "expected_ids": [INNODB],
        "category": "paraphrase",
    },
    {
        "question": "Java 里 == 和 equals 该用哪个？",
        "expected_ids": [JAVA_EQ],
        "category": "paraphrase",
    },
    {
        "question": "HashMap 和 Hashtable 有什么不同？",
        "expected_ids": [HASHMAP],
        "category": "paraphrase",
    },

    # ============================================================
    # 类别 3：缩写（考验语义泛化）
    # ============================================================
    {
        "question": "BST 的中序遍历顺序是什么？",
        "expected_ids": [BST],
        "category": "abbreviation",
        "note": "BST = 二叉搜索树",
    },
    {
        "question": "HTTP 404 是什么错误？",
        "expected_ids": [HTTP404],
        "category": "abbreviation",
    },
    {
        "question": "TCP 三次握手第二次的标志位？",
        "expected_ids": [TCP],
        "category": "abbreviation",
        "note": "TCP 是标准缩写，应无压力",
    },
    {
        "question": "DP 和分治的区别？",
        "expected_ids": [DP],
        "category": "abbreviation",
        "note": "DP = 动态规划，缩写可能识别不了",
    },
    {
        "question": "HTTPS 的默认端口号？",
        "expected_ids": [HTTPS],
        "category": "abbreviation",
    },

    # ============================================================
    # 类别 4：模糊问法（缺主题词）
    # ============================================================
    {
        "question": "我数据结构有哪些错题？",
        "expected_ids": [BT1, BT2, BT3, BST, HASH, STACK, LINKED],
        "category": "vague",
    },
    {
        "question": "我网络相关的错题有哪些？",
        "expected_ids": [TCP, HTTP404, HTTPS, NET_TEST1, NET_TEST2],
        "category": "vague",
    },
    {
        "question": "我算法相关的错题有哪些？",
        "expected_ids": [SORT1, SORT2, QUICK, BINARY, DP],
        "category": "vague",
    },
    {
        "question": "我操作系统相关的错题有哪些？",
        "expected_ids": [PROC1, PROC2, DEADLOCK],
        "category": "vague",
    },
    {
        "question": "我数据库相关的错题有哪些？",
        "expected_ids": [INDEX, INNODB],
        "category": "vague",
    },

    # ============================================================
    # 类别 5：无答案（测空结果处理）
    # ============================================================
    {
        "question": "什么是红黑树？",
        "expected_ids": [],
        "category": "no_answer",
    },
    {
        "question": "什么是 B+ 树？",
        "expected_ids": [],
        "category": "no_answer",
    },
    {
        "question": "图论中的最大流算法是什么？",
        "expected_ids": [],
        "category": "no_answer",
    },
    {
        "question": "什么是 NP 完全问题？",
        "expected_ids": [],
        "category": "no_answer",
    },
    {
        "question": "CAP 定理指的是什么？",
        "expected_ids": [],
        "category": "no_answer",
    },

    # ============================================================
    # 类别 6：跨知识点
    # ============================================================
    {
        "question": "二叉树和二叉搜索树有什么区别？",
        "expected_ids": [BT1, BT2, BT3, BST],
        "category": "cross_kp",
    },
    {
        "question": "进程和线程有什么区别？",
        "expected_ids": [PROC1, PROC2],
        "category": "cross_kp",
    },
    {
        "question": "常见的排序算法有哪些？",
        "expected_ids": [SORT1, SORT2, QUICK],
        "category": "cross_kp",
    },
    {
        "question": "HTTP 和 HTTPS 有什么区别？",
        "expected_ids": [HTTP404, HTTPS],
        "category": "cross_kp",
    },
    {
        "question": "TCP 三次握手每一阶段发什么？",
        "expected_ids": [TCP],
        "category": "cross_kp",
    },
]

