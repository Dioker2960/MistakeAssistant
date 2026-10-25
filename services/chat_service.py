from repositories import conversation_repo
import json

from ai import prompts, retriever
from ai.langchain_llm import get_llm
from ai.rewrite import rewrite_question
from repositories import conversation_repo
from schemas.chat import ChatRequest

llm = get_llm()


def ask(request: ChatRequest) -> str:
    """
    处理用户提问，返回模型回答。

    步骤:
    1. 把 request.message 包装成 messages 列表
    2. 调用 llm_client.chat
    3. 返回结果
    """
    # TODO: 构造 messages 列表
    # 提示：至少要有 [{"role": "user", "content": request.message}]
    messages = [
        {"role": "user", "content": request.message}
    ]
    # TODO: 调用 llm_client.chat(messages)
    answer = llm.invoke(messages)
    # TODO: 返回结果
    return answer.content


# def ask_with_rag(question: str, top_k: int = 3) -> dict:
def ask_with_rag(question: str, user_id: str, conversation_id: str | None = None, top_k: int = 3) -> dict:
    """
    基于错题知识库回答问题。

    返回:
        {
            "reply": "模型回答",
            "references": [{"question_id": ..., "score": ...}, ...],
        }
    """
    # 查询redis中conversation_id的会话数据
    history = []
    if conversation_id:
        history = conversation_repo.get_messages(user_id, conversation_id)
    # 新增：改写问题
    search_query = rewrite_question(question, history)
    # TODO 1: 检索相关错题，限定当前用户
    contexts = retriever.search(search_query, top_k, user_id=user_id)
    # TODO 2: 拼 Prompt user_prompt = prompts.build_rag_prompt(question, contexts)
    messages = prompts.build_rag_messages(question, contexts, history)
    # # TODO 3: 构造 messages = [{"role": "system", "content": prompts.SYSTEM_PROMPT},
    # #                          {历史会话数据}
    # #                          {"role": "user", "content": user_prompt}]
    # messages = [{"role": "system", "content": prompts.SYSTEM_PROMPT}, ]
    # messages.extend(history)
    # messages.append({"role": "user", "content": user_prompt}, )
    # TODO 4: reply = llm_client.chat(messages)
    reply = llm.invoke(messages)
    # 写回历史（注意：存原始 question，不是 user_prompt）
    if conversation_id:
        conversation_repo.append_messages(user_id, conversation_id, [
            {"role": "user", "content": question},  # ← 原始问题
            {"role": "assistant", "content": reply.content},
        ])

    result = {
        "reply": reply.content,
        "references": [
            {"question_id": context["question_id"], "score": context["score"]}
            for context in contexts
        ],
    }
    return result


def ask_with_rag_stream(question: str, user_id: str, conversation_id: str | None = None, top_k: int = 3):
    """流式版本：逐段 yield SSE 事件内容。"""
    # 1. 读历史
    history = []
    if conversation_id:
        history = conversation_repo.get_messages(user_id, conversation_id)
    # 多轮对话改写问题
    search_query = rewrite_question(question, history)
    # 2. 检索，限定当前用户
    contexts = retriever.search(search_query, top_k, user_id=user_id)
    # 3. 拼 Prompt
    messages = prompts.build_rag_messages(question, contexts, history)
    # 5. 先 yield 一个特殊事件，告诉客户端 references
    references = [
        {"question_id": ctx["question_id"], "score": ctx["score"]}
        for ctx in contexts
    ]
    yield f"event: references\ndata: {json.dumps({'references': references}, ensure_ascii=False)}\n\n"
    # 6. 流式 yield 模型回答
    full_reply = ""
    for chunk in llm.stream(messages):
        piece = chunk.content
        if not piece:
            continue
        full_reply += piece
        yield f"data: {json.dumps({'text': piece}, ensure_ascii=False)}\n\n"
    # 7. 写回历史
    if conversation_id:
        conversation_repo.append_messages(user_id, conversation_id, [
            {"role": "user", "content": question},
            {"role": "assistant", "content": full_reply},
        ])
    # 8. 发送结束事件
    yield "event: done\ndata: {}\n\n"


# def _rewrite_question(question: str, history: list[dict]) -> str:
#     """
#     结合历史，把当前问题改写为完整问题。
#     没有历史时，直接返回原问题。
#     """
#     if not history:
#         return question
#
#     # TODO 1: 调用 prompts.build_rewrite_prompt(question, history) 拼 Prompt
#     rewrite_prompt = prompts.build_rewrite_messages(question, history)
#     # TODO 3: 用 llm_client.chat(messages) 拿到改写结果
#     rewrite_question = llm.invoke(rewrite_prompt).content.strip()
#     # TODO 4: 用 .strip() 去掉首尾空白，返回
#     print(f"[改写] 原问题: {question}")
#     print(f"[改写] 改写后: {rewrite_question}")
#     return rewrite_question.strip("")
