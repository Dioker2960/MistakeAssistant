"""
意图评测集——验证 Router 判断意图的准确率。
"""

INTENT_EVAL_SET = [
    # ========== knowledge ==========
    {"question": "什么是二叉树？", "expected_intent": "knowledge"},
    {"question": "哈希表的原理是什么？", "expected_intent": "knowledge"},
    {"question": "解释一下动态规划", "expected_intent": "knowledge"},
    {"question": "栈和队列有什么区别？", "expected_intent": "knowledge"},
    {"question": "HTTP 和 HTTPS 有什么区别？", "expected_intent": "knowledge"},

    # ========== diagnosis ==========
    {"question": "二叉树那道题为什么选B？", "expected_intent": "diagnosis"},
    {"question": "我为什么选错了哈希表那题？", "expected_intent": "diagnosis"},
    {"question": "二分查找那道题错在哪？", "expected_intent": "diagnosis"},
    {"question": "帮我分析一下这道错题", "expected_intent": "diagnosis"},
    {"question": "TCP 三次握手那题我错在哪里？", "expected_intent": "diagnosis"},

    # ========== recommendation ==========
    {"question": "有什么和二叉树类似的题？", "expected_intent": "recommendation"},
    {"question": "推荐几道排序的题", "expected_intent": "recommendation"},
    {"question": "给我找几道相似的题", "expected_intent": "recommendation"},
    {"question": "还有类似的题吗？", "expected_intent": "recommendation"},

    # ========== stats ==========
    {"question": "我一共有多少错题？", "expected_intent": "stats"},
    {"question": "我概念理解错误的题有哪些？", "expected_intent": "stats"},
    {"question": "我哪个错误类型错得最多？", "expected_intent": "stats"},
    {"question": "我的错题总数是多少？", "expected_intent": "stats"},

    # ========== list_by_kp ==========
    {"question": "我数据结构有哪些错题？", "expected_intent": "list_by_kp"},
    {"question": "二叉树相关的题有哪些？", "expected_intent": "list_by_kp"},
    {"question": "列一下我网络相关的错题", "expected_intent": "list_by_kp"},
    {"question": "我排序相关的错题都有哪些？", "expected_intent": "list_by_kp"},
]