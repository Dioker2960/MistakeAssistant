import json
import logging

from langchain.tools import tool
from pydantic import BaseModel, Field

from ai import langchain_store
from ai.context import current_user_id
from repositories import wrong_question_repo, knowledge_point_repo, answer_record_repo

logger = logging.getLogger(__name__)


@tool
def get_wrong_question_stats() -> str:
    """
    查询用户的错题统计信息。包括错题总数、按错误类型的分布。
    当用户问"我有多少错题""哪些类型错得最多"这类统计问题时使用。
    本工具不需要任何参数。
    """
    logger.info("执行工具: get_wrong_question_stats")
    user_id = current_user_id.get()
    if not user_id:
        return "缺少用户信息。"
    questions = wrong_question_repo.list_all(user_id)
    if not questions:
        return "当前没有错题记录。"

    total = len(questions)
    logger.info("查询到 %d 条错题", len(questions))

    # 按错误类型统计
    type_count: dict[str, int] = {}
    for q in questions:
        et = q.get("error_type") or "未分类"
        type_count[et] = type_count.get(et, 0) + 1

    lines = [f"错题总数：{total}"]
    lines.append("按错误类型分布：")
    for et, cnt in sorted(type_count.items(), key=lambda x: -x[1]):
        lines.append(f"  - {et}: {cnt} 道")

    return "\n".join(lines)


class SearchInput(BaseModel):
    query: str = Field(description="用户的完整问题，包含主题信息")


@tool
def search_wrong_questions(query: str) -> str:
    """
    根据问题检索相关的错题。
    用于回答关于错题内容、解析、知识点的问题。
    当用户问"为什么选X""这道题考什么""有没有类似的题"时使用。
    """
    user_id = current_user_id.get()
    if not user_id:
        return json.dumps({"context": "缺少用户信息，无法检索。", "references": []}, ensure_ascii=False)

    results = langchain_store.search(query, top_k=3, min_score=0.5, user_id=user_id)
    if not results:
        return json.dumps({"context": "没有找到相关错题。", "references": []}, ensure_ascii=False)

    refs = [
        {
            "question_id": r["question_id"],
            "score": r["score"],
            "title": r["text"][:40].replace("\n", " "),
        }
        for r in results
    ]

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"【错题 {i}】\n{r['text']}")

    return json.dumps({
        "context": "\n\n".join(parts),
        "references": refs,
    }, ensure_ascii=False)


@tool
def recommend_similar_questions(question_content: str) -> str:
    """
    根据题目内容推荐相似的练习题。
    当用户问"有没有类似的题""给我推荐几道相似的题"时使用。
    和 search_wrong_questions 的区别：search 是查已有的错题解析，
    本工具是推荐相似的练习题供用户继续练习。
    """
    user_id = current_user_id.get()
    if not user_id:
        return "缺少用户信息。"


    results = langchain_store.search(question_content, top_k=3, min_score=0.3, user_id=user_id)
    # 排除完全相同的，返回前 3 条
    if not results:
        return "没有找到相关错题。"

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"【错题 {i}】\n{r['text']}")
    return "\n\n".join(parts)


@tool
def get_questions_by_error_type(error_type: str) -> str:
    """
    按错误类型查询错题列表。
    用于回答"我概念理解错误的题有哪些""知识点遗忘的题有几道"这类问题。
    """
    user_id = current_user_id.get()
    if not user_id:
        return "缺少用户信息。"
    questions = wrong_question_repo.list_all(user_id)
    matched = [q for q in questions if q.get("error_type") == error_type]

    if not matched:
        return f"没有找到错误类型为「{error_type}」的错题。"

    lines = [f"错误类型「{error_type}」的错题共 {len(matched)} 道："]
    for i, q in enumerate(matched, 1):
        lines.append(f"{i}. {q['question_content'][:50]}...")
    return "\n".join(lines)


@tool
def list_questions_by_knowledge_point(kp_name: str) -> str:
    """
    按知识点名称列出当前用户的所有错题。
    当用户问"我XX知识点有哪些错题""XX相关的题有哪些"时使用。
    只在用户想"看清单"时使用；如果用户问"为什么""是什么"，用 search_wrong_questions。
    """
    user_id = current_user_id.get()
    if not user_id:
        return "缺少用户信息。"

    # 1. 按名字查知识点
    kp = knowledge_point_repo.get_by_name(kp_name)
    if kp is None:
        return f"没有找到知识点「{kp_name}」。"

    # 2. 递归拿该知识点及其所有子孙知识点
    kp_ids = knowledge_point_repo.get_descendant_ids(kp["id"])

    # 3. 查这些知识点下的题目 ID
    question_ids: set[str] = set()
    for kid in kp_ids:
        question_ids.update(knowledge_point_repo.list_question_ids_for_kp(kid))

    # 4. 过滤出当前用户的
    questions = []
    for qid in question_ids:
        q = wrong_question_repo.get_by_id(qid)
        if q and q["user_id"] == user_id:
            questions.append(q)

    # 5. 格式化返回
    if not questions:
        return f"「{kp_name}」下暂无错题。"

    lines = [f"「{kp_name}」下共 {len(questions)} 道错题："]
    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q['question_content'][:60]}")
    return "\n".join(lines)


@tool
def get_knowledge_point_mastery(kp_name: str) -> str:
    """
    查询当前用户在某个知识点上的掌握度。
    当用户问"我XX掌握得怎么样""XX的正确率是多少""我XX薄弱吗"时使用。
    参数 kp_name 是知识点名称，如"二叉树""动态规划"。
    """
    user_id = current_user_id.get()
    if not user_id:
        return "缺少用户信息。"

    mastery = answer_record_repo.get_mastery_by_name(user_id, kp_name)
    if mastery is None:
        return f"没有找到知识点「{kp_name}」。"

    if mastery["total_count"] == 0:
        return f"「{kp_name}」还没有答题记录。"

    lines = [
        f"「{kp_name}」掌握度统计：",
        f"  - 掌握状态：{mastery['mastery_status']}",
        f"  - 答题总数：{mastery['total_count']} 次",
        f"  - 正确次数：{mastery['correct_count']} 次",
        f"  - 错误次数：{mastery['wrong_count']} 次",
        f"  - 正确率：{mastery['accuracy']:.1%}",
        f"  - 连续答对：{mastery['consecutive_correct']} 次",
    ]
    return "\n".join(lines)


TOOLS = [get_wrong_question_stats, search_wrong_questions,
         recommend_similar_questions, get_questions_by_error_type,
         list_questions_by_knowledge_point, get_knowledge_point_mastery,]

# ========== 工具分组 ==========
KNOWLEDGE_TOOLS = [search_wrong_questions]
DIAGNOSIS_TOOLS = [search_wrong_questions, get_wrong_question_stats]
RECOMMENDATION_TOOLS = [recommend_similar_questions]
STATS_TOOLS = [get_wrong_question_stats, get_questions_by_error_type,
               list_questions_by_knowledge_point, get_knowledge_point_mastery,]

INTENT_TOOLS = {
    "knowledge": KNOWLEDGE_TOOLS,
    "diagnosis": DIAGNOSIS_TOOLS,
    "recommendation": RECOMMENDATION_TOOLS,
    "stats": STATS_TOOLS,
}

# 工具名 → 函数的映射，用于执行
TOOL_MAP = {t.name: t for t in TOOLS}
