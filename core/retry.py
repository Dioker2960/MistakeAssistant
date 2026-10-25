import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器。捕获异常后等待一段时间重试。

    参数:
        max_attempts: 最大尝试次数（含第一次）
        delay: 首次重试前的等待秒数
        backoff: 每次重试的等待倍数（指数退避）
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exc = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt == max_attempts:
                        logger.error(
                            "%s 重试 %d 次后仍失败: %s",
                            func.__name__, max_attempts, e,
                        )
                        raise
                    logger.warning(
                        "%s 第 %d 次失败，%.1fs 后重试: %s",
                        func.__name__, attempt, current_delay, e,
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exc  # 理论上到不了这，为了类型检查

        return wrapper

    return decorator