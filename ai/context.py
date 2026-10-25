from contextvars import ContextVar

# 当前用户的 user_id，由 tool_node 在执行工具前设置
current_user_id: ContextVar[str] = ContextVar("current_user_id", default="")
last_references: ContextVar[list] = ContextVar("last_references", default=[])
