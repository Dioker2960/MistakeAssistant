class AppError(Exception):
    """应用基础异常。"""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class BusinessError(AppError):
    """业务逻辑错误，比如资源不存在、状态不合法。"""
    def __init__(self, message: str):
        super().__init__(message, code="BUSINESS_ERROR")


class LLMError(AppError):
    """LLM 调用失败。"""
    def __init__(self, message: str):
        super().__init__(message, code="LLM_ERROR")


class RetrievalError(AppError):
    """检索失败。"""
    def __init__(self, message: str):
        super().__init__(message, code="RETRIEVAL_ERROR")