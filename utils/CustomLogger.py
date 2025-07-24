from loguru import logger

# 添加文件处理器，但不要重新赋值给logger
logger.add("logs/app.log", rotation="100 MB", retention="10 days")
