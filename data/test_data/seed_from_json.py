import json
import uuid
from datetime import datetime

from core.database import SessionLocal
from models.user import User
from models.wrong_question import WrongQuestion
from models.knowledge_point import KnowledgePoint, QuestionKnowledge
from core.security import hash_password  # 确保路径正确


def gen_id():
    return uuid.uuid4().hex


def seed_from_json(file_path: str):
    # 1. 读取 JSON 文件
    with open(file_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    with SessionLocal() as session:
        # 2. 创建/获取测试用户 alice
        user = session.query(User).filter(User.username == "alice").first()
        if not user:
            user = User(
                id=gen_id(),
                username="alice",
                password_hash=hash_password("123456"),
                role="user"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"✅ 创建测试用户成功: alice / 123456")
        else:
            print(f"✅ 使用已存在的测试用户: alice")

        # 3. 收集所有唯一的知识点
        kp_names = set(item["knowledge_point"] for item in questions_data)

        # 4. 创建知识点（自动归入“计算机基础”大类下）
        parent_kp = session.query(KnowledgePoint).filter(KnowledgePoint.name == "计算机基础").first()
        if not parent_kp:
            parent_kp = KnowledgePoint(id=gen_id(), name="计算机基础", description="根知识点")
            session.add(parent_kp)
            session.commit()
            session.refresh(parent_kp)

        kp_map = {}  # 用于快速查找知识点 ID
        for name in kp_names:
            kp = session.query(KnowledgePoint).filter(KnowledgePoint.name == name).first()
            if not kp:
                kp = KnowledgePoint(
                    id=gen_id(),
                    name=name,
                    parent_id=parent_kp.id,
                    description=f"这是关于{name}的知识点"
                )
                session.add(kp)
                session.commit()
                session.refresh(kp)
            kp_map[name] = kp.id
        print(f"✅ 创建/检查了 {len(kp_names)} 个知识点")

        # 5. 批量插入错题
        count = 0
        for item in questions_data:
            q = WrongQuestion(
                id=gen_id(),
                user_id=user.id,
                question_content=item["question_content"],
                question_type=item["question_type"],
                options=item.get("options"),
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

            # 建立题目-知识点关联
            kp_id = kp_map[item["knowledge_point"]]
            qk = QuestionKnowledge(
                id=gen_id(),
                question_id=q.id,
                knowledge_point_id=kp_id,
                created_at=datetime.now()
            )
            session.add(qk)
            count += 1

        session.commit()
        print(f"✅ 成功导入 {count} 道错题！")
        print("提示：如果你启动着 FastAPI 服务，重启一下服务，FAISS 向量库会自动重新构建。")


if __name__ == "__main__":
    seed_from_json("questions.json")