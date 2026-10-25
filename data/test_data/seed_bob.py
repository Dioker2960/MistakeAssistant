import json
import uuid
from datetime import datetime

from core.database import SessionLocal
from models.user import User
from models.wrong_question import WrongQuestion
from models.knowledge_point import KnowledgePoint, QuestionKnowledge
from core.security import hash_password

def gen_id():
    return uuid.uuid4().hex

# BOB 的专属测试数据
BOB_QUESTIONS = [
    {
        "knowledge_point": "Redis",
        "question_content": "Redis的持久化机制中，AOF默认的刷盘策略是什么？",
        "question_type": "single_choice",
        "options": ["A. always", "B. everysec", "C. no", "D. 视情况而定"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "AOF默认是everysec（每秒刷盘一次），兼顾了性能和数据安全。",
        "error_type": "知识点遗忘",
        "difficulty": 3
    },
    {
        "knowledge_point": "Vue",
        "question_content": "Vue3中响应式数据基于什么机制实现？",
        "question_type": "single_choice",
        "options": ["A. Object.defineProperty", "B. Proxy", "C. Reflect", "D. Event Loop"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "Vue2使用Object.defineProperty，Vue3改用Proxy来实现响应式，可以监听数组和对象的新增/删除。",
        "error_type": "概念混淆",
        "difficulty": 3
    },
    {
        "knowledge_point": "计算机网络",
        "question_content": "DNS协议主要运行在哪一层？",
        "question_type": "single_choice",
        "options": ["A. 物理层", "B. 数据链路层", "C. 网络层", "D. 应用层"],
        "user_answer": "C",
        "correct_answer": "D",
        "analysis": "DNS（域名系统）是应用层协议，通常使用UDP进行传输。",
        "error_type": "概念理解错误",
        "difficulty": 2
    },
    {
        "knowledge_point": "Java基础",
        "question_content": "Java中的接口可以包含以下哪种实现？",
        "question_type": "single_choice",
        "options": ["A. 只能包含抽象方法", "B. 可以包含 default 和 static 方法", "C. 可以包含普通成员变量", "D. 可以包含构造方法"],
        "user_answer": "A",
        "correct_answer": "B",
        "analysis": "Java 8 之后接口支持 default 和 static 方法，Java 9 支持 private 方法；接口不能有构造器，成员变量默认是 public static final。",
        "error_type": "知识点遗忘",
        "difficulty": 2
    },
    {
        "knowledge_point": "操作系统基础",
        "question_content": "LRU（最近最少使用）页面置换算法的底层通常基于什么数据结构实现？",
        "question_type": "single_choice",
        "options": ["A. 数组", "B. 栈", "C. 哈希表 + 双向链表", "D. 红黑树"],
        "user_answer": "B",
        "correct_answer": "C",
        "analysis": "哈希表用于O(1)查找节点，双向链表用于维护访问顺序和O(1)移动节点。",
        "error_type": "概念理解错误",
        "difficulty": 4
    }
]

def seed_bob():
    with SessionLocal() as session:
        # 1. 创建/获取 BOB 用户
        bob = session.query(User).filter(User.username == "bob").first()
        if not bob:
            bob = User(
                id=gen_id(),
                username="bob",
                password_hash=hash_password("123456"),
                role="user"
            )
            session.add(bob)
            session.commit()
            session.refresh(bob)
            print("✅ 创建测试用户成功: bob / 123456")
        else:
            print("✅ 使用已存在的测试用户: bob")

        # 2. 提前处理知识点（确保不冲突）
        # 先拿父节点
        parent_kp = session.query(KnowledgePoint).filter(KnowledgePoint.name == "计算机基础").first()
        if not parent_kp:
            parent_kp = KnowledgePoint(id=gen_id(), name="计算机基础", description="根知识点")
            session.add(parent_kp)
            session.commit()
            session.refresh(parent_kp)

        kp_names = set(item["knowledge_point"] for item in BOB_QUESTIONS)
        kp_map = {}
        for name in kp_names:
            kp = session.query(KnowledgePoint).filter(KnowledgePoint.name == name).first()
            if not kp:
                kp = KnowledgePoint(id=gen_id(), name=name, parent_id=parent_kp.id)
                session.add(kp)
                session.commit()
                session.refresh(kp)
            kp_map[name] = kp.id

        # 3. 插入错题
        count = 0
        for item in BOB_QUESTIONS:
            q = WrongQuestion(
                id=gen_id(),
                user_id=bob.id,
                question_content=item["question_content"],
                question_type=item["question_type"],
                options=item["options"],
                user_answer=item["user_answer"],
                correct_answer=item["correct_answer"],
                analysis=item["analysis"],
                error_type=item["error_type"],
                difficulty=item["difficulty"],
                mastery_status="薄弱",
                wrong_count=1,
                last_wrong_time=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(q)
            session.flush()

            # 关联知识点
            qk = QuestionKnowledge(
                id=gen_id(),
                question_id=q.id,
                knowledge_point_id=kp_map[item["knowledge_point"]],
                created_at=datetime.now()
            )
            session.add(qk)
            count += 1

        session.commit()
        print(f"✅ 成功为 BOB 导入 {count} 道专属错题！")

if __name__ == "__main__":
    seed_bob()