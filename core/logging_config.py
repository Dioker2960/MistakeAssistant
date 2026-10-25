import logging
import os
from logging.handlers import TimedRotatingFileHandler

# 日志目录（绝对路径）
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

# 日志格式
_CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FILE_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """
    配置全局日志。
    应该在 main.py 启动时调用一次。
    """

    # 调高第三方库的日志级别，避免噪音
    for noisy in ["httpx", "httpcore", "openai", "sqlalchemy.engine", "watchfiles", "faiss"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # TODO 1: 获取根 logger（logging.getLogger()）
    root_logger = logging.getLogger()
    # TODO 2: 设置级别（logging.getLevelName(level) 或 logging.DEBUG）
    root_logger.setLevel(getattr(logging, level.upper()))
    # TODO 3: 清除已有 handler（避免重复添加）
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # TODO 4: 创建控制台 handler（StreamHandler）
    #         设置格式为 _CONSOLE_FORMAT
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))

    # TODO 5: 创建文件 handler（TimedRotatingFileHandler）
    #         参数：
    #           filename=os.path.join(_LOG_DIR, "app.log")
    #           when="midnight"（每天轮转）
    #           backupCount=7（保留 7 天）
    #           encoding="utf-8"
    #         设置格式为 _FILE_FORMAT
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(_LOG_DIR, "app.log"),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))

    # TODO 6: 把两个 handler 添加到根 logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


