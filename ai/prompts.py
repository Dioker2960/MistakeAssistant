from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = """你是一个错题分析助手。用户会提供他做错的题目和相关解析，
你需要根据这些信息回答用户的问题。

要求：
1. 只根据提供的错题信息回答，不要编造。
2. 如果提供的错题信息不足以回答，就说"根据现有错题信息无法回答"。
3. 回答要简洁、清晰、有针对性。
"""

_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("history"),
    ("user", "以下是相关的错题信息：\n\n{contexts}\n\n用户问题：{question}"),
])


def build_rag_messages(question: str, contexts: list[dict], history: list[dict]) -> list[BaseMessage]:
    # 返回消息列表（含历史）
    """
    构造 RAG 问答的消息列表。

    参数:
        question: 用户问题
        contexts: retriever.search 返回的结果列表

    返回:
        可直接喂给 llm.invoke() 的消息列表
    """
    context_test = "\n".join(f"【错题 {i}】\n{ctx['text']}\n" for i, ctx in enumerate(contexts, 1))
    return _RAG_PROMPT.invoke({
        "history": history,
        "contexts": context_test,
        "question": question,
    }).to_messages()


REWRITE_SYSTEM_PROMPT = """你是一个问题改写助手。用户在多轮对话中提问，
有些问题会省略上下文（比如"那 A 呢"、"为什么"）。

你需要结合对话历史，把用户当前问题改写成一个完整的、独立的问题。

要求：
1. 只输出改写后的问题，不要任何解释、前缀或标点装饰。
2. 保留用户的原意，不要添加历史中没有的信息。
3. 如果当前问题本身已经完整，就原样输出。
"""

_REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", REWRITE_SYSTEM_PROMPT),
    ("user", "以下是对话历史：\n\n{history_text}\n\n当前问题：{question}\n\n请把当前问题改写成一个完整的、独立的问题："),
])


def build_rewrite_messages(question: str, history: list[dict]) -> list[BaseMessage]:
    """
    把历史和当前问题拼成改写 Prompt。

    参数:
        question: 用户当前问题
        history: 历史消息列表 [{"role": "user", "content": "..."}, ...]

    返回:
        改写 Prompt 字符串
    """
    history_text = "\n".join(
        f"{'用户' if msg['role'] == 'user' else '助手'}：{msg['content']}"
        for msg in history
    )

    return _REWRITE_PROMPT.invoke({
        "history_text":history_text,
        "question": question,
    }).to_messages()


# ========== 每个 Agent 的 System Prompt ==========
INTENT_PROMPTS = {
    "knowledge": """你是知识问答助手。用户问的是某个知识点、概念、原理。
先调用 search_wrong_questions 检索用户的错题，如果找到相关错题，基于错题回答；
如果没有相关错题，用你自己的知识回答。
回答要简洁、准确、有条理。""",

    "diagnosis": """你是错因分析助手。用户想知道某道题为什么错、错在哪里、怎么改。
先用 search_wrong_questions 检索相关错题，再分析：
1. 题目考察什么知识点
2. 用户为什么错（概念混淆/知识点遗忘/审题错误）
3. 正确的解题思路
回答要具体、有针对性。""",

    "recommendation": """你是题目推荐助手。用户想找相似的练习题。
调用 recommend_similar_questions 检索相似题，返回推荐列表。
如果用户提到了具体的题目内容，把它作为参数传进去。""",

    "stats": """你是学习统计助手。用户想了解自己的错题情况。
调用 get_wrong_question_stats 或 get_questions_by_error_type 获取统计信息。
回答时用清晰的数字和列表呈现。""",

    "list_by_kp": """你是错题列表助手。用户想看某个分类下的所有错题。
调用 list_questions_by_knowledge_point 列出相关错题。
如果用户说的知识点不存在，告诉用户没有找到。
回答时用清晰的列表呈现。""",
}


ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是意图分类器。根据用户问题判断意图，返回以下之一：

- knowledge: 知识问答。问某个概念、原理、定义。
  例："什么是二叉树"、"哈希表的原理"

- diagnosis: 错因分析。问某道题为什么错、错在哪里。
  例："二叉树那道题为什么选B"、"我错在哪了"

- recommendation: 相似题推荐。想找类似的题练习。
  例："有什么类似的题"、"推荐几道"

- stats: 统计查询。问错题数量、分布。
  例："我有多少错题"、"哪类错得多"
  
- list_by_kp: 按知识点列出错题。用户想看某个分类下的所有错题。
  例："我数据结构有哪些错题"、"二叉树相关的题有哪些"

只返回分类结果，不要解释。"""),
    MessagesPlaceholder("history"),
    ("user", "{question}"),
])
