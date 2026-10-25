import uuid
from datetime import datetime
from core.database import SessionLocal
from models.user import User
from models.wrong_question import WrongQuestion
from models.knowledge_point import QuestionKnowledge
from models.answer_record import AnswerRecord, KnowledgeMastery
from models.conversation import Conversation, Message
from repositories import answer_record_repo


def gen_id():
    return uuid.uuid4().hex


def generate_related_data():
    with SessionLocal() as session:
        users = session.query(User).filter(User.username.in_(["alice", "bob"])).all()
        if not users:
            print("❌ 请先运行之前的基础数据导入脚本，确保 alice 和 bob 存在。")
            return

        for user in users:
            print(f"\n正在为用户 [{user.username}] 生成联动数据...")

            # 1. 生成会话与消息
            conv = Conversation(
                id=gen_id(),
                user_id=user.id,
                title=f"{user.username}的测试会话",
                summary="用户询问了关于二叉树和Redis的错题。"
            )
            session.add(conv)
            session.flush()

            for seq in range(1, 5):
                role = "user" if seq % 2 != 0 else "assistant"
                content = "帮我分析一下这道错题" if role == "user" else "好的，这道题考察了..."
                session.add(Message(
                    id=gen_id(), conversation_id=conv.id, seq=seq,
                    role=role, content=content, references_json="[]"
                ))

            # 2. 查该用户所有的错题
            questions = session.query(WrongQuestion).filter(WrongQuestion.user_id == user.id).all()

            for q in questions:
                # 3. 模拟历史答题记录 (随机答对/答错 2-4 次)
                # 假设某个特定题目多错几次，让数据看起来更真实
                times = 3 if "二叉树" in q.question_content else 2
                for i in range(times):
                    is_correct = 1 if (i == times - 1 and times == 3) else 0  # 最后一次可能答对

                    ar = AnswerRecord(
                        id=gen_id(), user_id=user.id, question_id=q.id,
                        user_answer=q.correct_answer if is_correct else q.user_answer,
                        is_correct=is_correct,
                        source_type="PRACTICE",
                        created_at=datetime.now()
                    )
                    session.add(ar)

                    # 4. 联动更新知识点掌握度
                    # 查找这道题关联的知识点
                    qks = session.query(QuestionKnowledge).filter(QuestionKnowledge.question_id == q.id).all()
                    for qk in qks:
                        # 这里我们手动调用 repo 里的聚合逻辑（模拟真实触发）
                        # 注意：在真实 API 中，这是通过 answer_record_repo.upsert_mastery 触发的
                        pass

            session.commit()

            # 为保证掌握度数据精准，我们直接利用已有的 Repo 逻辑批量重算一次
            _rebuild_mastery(session, user.id)

            print(f"✅ {user.username} 的会话、答题记录、掌握度已生成！")


def _rebuild_mastery(session, user_id):
    """辅助函数：根据答题记录重新计算知识点掌握度"""
    # 简单粗暴：先清空当前用户的掌握度表
    session.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user_id).delete()

    # 拉取所有答题记录
    records = session.query(AnswerRecord).filter(AnswerRecord.user_id == user_id).all()

    # 按知识点聚合
    kp_stats = {}  # kp_id -> {total, correct}

    for r in records:
        qks = session.query(QuestionKnowledge).filter(QuestionKnowledge.question_id == r.question_id).all()
        for qk in qks:
            if qk.knowledge_point_id not in kp_stats:
                kp_stats[qk.knowledge_point_id] = {"total": 0, "correct": 0}

            kp_stats[qk.knowledge_point_id]["total"] += 1
            if r.is_correct:
                kp_stats[qk.knowledge_point_id]["correct"] += 1

    # 写入表
    for kp_id, stat in kp_stats.items():
        total = stat["total"]
        correct = stat["correct"]
        accuracy = correct / total if total else 0
        mastery_status = "已掌握" if accuracy >= 0.8 else ("学习中" if accuracy >= 0.6 else "薄弱")

        km = KnowledgeMastery(
            id=gen_id(),
            user_id=user_id,
            knowledge_point_id=kp_id,
            total_count=total,
            correct_count=correct,
            wrong_count=total - correct,
            accuracy=accuracy,
            consecutive_correct=1,  # 测试数据简单赋值
            mastery_status=mastery_status,
            last_answer_time=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(km)
    session.commit()


if __name__ == "__main__":
    generate_related_data()