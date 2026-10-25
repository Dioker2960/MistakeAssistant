import requests

BASE_URL = "http://127.0.0.1:8080"

WRONG_QUESTIONS = [
    # ========== 数据结构 ==========
    {
        "question_content": "下列关于二叉树的说法正确的是？",
        "question_type": "single_choice",
        "options": ["A. 二叉树是线性结构", "B. 二叉树每个节点最多有两个子节点", "C. 二叉树不能为空", "D. 二叉树必须完全填满"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "二叉树是非线性结构，每个节点最多有两个子节点，可以为空。",
        "error_type": "概念理解错误",
        "difficulty": 3,
    },
    {
        "question_content": "哈希表在最坏情况下的查找时间复杂度是？",
        "question_type": "single_choice",
        "options": ["A. O(1)", "B. O(log n)", "C. O(n)", "D. O(n²)"],
        "user_answer": "A",
        "correct_answer": "C",
        "analysis": "哈希表平均 O(1)，但所有 key 冲突时会退化成链表，最坏 O(n)。",
        "error_type": "概念理解错误",
        "difficulty": 3,
    },
    {
        "question_content": "栈的特点是？",
        "question_type": "single_choice",
        "options": ["A. 先进先出", "B. 先进后出", "C. 随机存取", "D. 双端操作"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "栈是后进先出（LIFO），队列才是先进先出（FIFO）。",
        "error_type": "概念混淆",
        "difficulty": 1,
    },
    {
        "question_content": "在单链表中删除某个节点，需要知道什么？",
        "question_type": "single_choice",
        "options": ["A. 只需要该节点本身", "B. 需要该节点的前驱节点", "C. 需要头节点", "D. 需要尾节点"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "单链表删除节点需要前驱节点的指针，否则无法修改前驱的 next。",
        "error_type": "知识点遗忘",
        "difficulty": 2,
    },
    {
        "question_content": "二叉搜索树的中序遍历结果是？",
        "question_type": "single_choice",
        "options": ["A. 无序", "B. 降序", "C. 升序", "D. 随机"],
        "user_answer": "A",
        "correct_answer": "C",
        "analysis": "二叉搜索树中序遍历得到升序序列，这是它的重要性质。",
        "error_type": "知识点遗忘",
        "difficulty": 2,
    },

    # ========== 算法 ==========
    {
        "question_content": "时间复杂度为 O(n log n) 的排序算法是？",
        "question_type": "single_choice",
        "options": ["A. 冒泡排序", "B. 快速排序", "C. 插入排序", "D. 选择排序"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "快排平均 O(n log n)，冒泡/插入/选择都是 O(n²)。",
        "error_type": "知识点遗忘",
        "difficulty": 2,
    },
    {
        "question_content": "快速排序在最坏情况下的时间复杂度是？",
        "question_type": "single_choice",
        "options": ["A. O(n log n)", "B. O(n²)", "C. O(n)", "D. O(log n)"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "快排最坏情况（如已排序数组选第一个为基准）退化为 O(n²)。",
        "error_type": "概念理解错误",
        "difficulty": 3,
    },
    {
        "question_content": "二分查找的前提条件是？",
        "question_type": "single_choice",
        "options": ["A. 数组无序", "B. 数组有序", "C. 数组长度为偶数", "D. 数组元素唯一"],
        "user_answer": "C",
        "correct_answer": "B",
        "analysis": "二分查找要求数组有序，每次比较中间元素后缩小一半范围。",
        "error_type": "概念理解错误",
        "difficulty": 1,
    },
    {
        "question_content": "动态规划与分治法的核心区别是？",
        "question_type": "single_choice",
        "options": ["A. 没有区别", "B. 动态规划有重叠子问题", "C. 分治法更快", "D. 动态规划不用递归"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "动态规划的关键特征是重叠子问题，通过记忆化避免重复计算。",
        "error_type": "概念混淆",
        "difficulty": 4,
    },

    # ========== 计算机网络 ==========
    {
        "question_content": "HTTP 状态码 404 表示？",
        "question_type": "single_choice",
        "options": ["A. 服务器内部错误", "B. 资源未找到", "C. 权限不足", "D. 请求超时"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "404 Not Found 表示请求的资源不存在，500 才是服务器内部错误。",
        "error_type": "概念混淆",
        "difficulty": 1,
    },
    {
        "question_content": "TCP 三次握手的第二次，客户端发送的标志位是？",
        "question_type": "single_choice",
        "options": ["A. SYN", "B. ACK", "C. SYN+ACK", "D. FIN"],
        "user_answer": "B",
        "correct_answer": "C",
        "analysis": "三次握手：客户端 SYN → 服务端 SYN+ACK → 客户端 ACK。",
        "error_type": "知识点遗忘",
        "difficulty": 3,
    },
    {
        "question_content": "HTTPS 使用的默认端口是？",
        "question_type": "single_choice",
        "options": ["A. 80", "B. 443", "C. 8080", "D. 22"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "HTTP 默认 80，HTTPS 默认 443，SSH 是 22。",
        "error_type": "知识点遗忘",
        "difficulty": 1,
    },

    # ========== 操作系统 ==========
    {
        "question_content": "进程和线程的主要区别是？",
        "question_type": "single_choice",
        "options": ["A. 没有区别", "B. 进程是资源分配单位，线程是CPU调度单位", "C. 进程比线程轻量", "D. 线程有独立地址空间"],
        "user_answer": "C",
        "correct_answer": "B",
        "analysis": "进程有独立地址空间，是资源分配单位；线程共享进程地址空间，是CPU调度单位。",
        "error_type": "概念混淆",
        "difficulty": 3,
    },
    {
        "question_content": "死锁产生的四个必要条件不包括？",
        "question_type": "single_choice",
        "options": ["A. 互斥", "B. 请求与保持", "C. 可剥夺", "D. 循环等待"],
        "user_answer": "C",
        "correct_answer": "C",
        "analysis": "死锁四个条件：互斥、请求与保持、不可剥夺、循环等待。C 说反了。",
        "error_type": "审题错误",
        "difficulty": 3,
    },

    # ========== 数据库 ==========
    {
        "question_content": "MySQL 中 InnoDB 的默认隔离级别是？",
        "question_type": "single_choice",
        "options": ["A. 读未提交", "B. 读已提交", "C. 可重复读", "D. 串行化"],
        "user_answer": "B",
        "correct_answer": "C",
        "analysis": "InnoDB 默认是可重复读（RR），通过 MVCC + 间隙锁避免幻读。",
        "error_type": "知识点遗忘",
        "difficulty": 3,
    },
    {
        "question_content": "数据库索引的主要作用是？",
        "question_type": "single_choice",
        "options": ["A. 节省存储空间", "B. 加快查询速度", "C. 保证数据一致性", "D. 防止SQL注入"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "索引本质是用空间换时间，加快查询速度。",
        "error_type": "概念理解错误",
        "difficulty": 1,
    },

    # ========== Java 基础 ==========
    {
        "question_content": "Java 中 == 和 equals 的区别是？",
        "question_type": "single_choice",
        "options": ["A. 没有区别", "B. == 比较地址，equals 可重写比较内容", "C. == 比较内容", "D. equals 比较地址"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "== 比较引用地址，equals 默认也是比较地址但可被重写为比较内容。",
        "error_type": "概念理解错误",
        "difficulty": 2,
    },
    {
        "question_content": "HashMap 和 Hashtable 的主要区别不包括？",
        "question_type": "single_choice",
        "options": ["A. HashMap 线程不安全", "B. HashMap 允许 null 键", "C. Hashtable 效率更高", "D. Hashtable 是遗留类"],
        "user_answer": "C",
        "correct_answer": "C",
        "analysis": "Hashtable 用 synchronized 方法，效率反而更低。",
        "error_type": "审题错误",
        "difficulty": 3,
    },
]


def seed():
    success = 0
    fail = 0
    for i, q in enumerate(WRONG_QUESTIONS, 1):
        try:
            resp = requests.post(f"{BASE_URL}/wrong-questions", json=q, timeout=10)
            if resp.status_code == 201:
                success += 1
                print(f"[{i}/{len(WRONG_QUESTIONS)}] ✅ {q['question_content'][:30]}...")
            else:
                fail += 1
                print(f"[{i}/{len(WRONG_QUESTIONS)}] ❌ {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            fail += 1
            print(f"[{i}/{len(WRONG_QUESTIONS)}] ❌ 异常: {e}")

    print(f"\n成功: {success}, 失败: {fail}")


if __name__ == "__main__":
    seed()