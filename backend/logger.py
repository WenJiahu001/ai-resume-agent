# -*- coding: utf-8 -*-
"""
日志配置模块

提供统一的日志配置，支持控制台和文件输出。
"""
import logging
import sys
from functools import lru_cache


def setup_logging(level: str = "INFO") -> None:
    """
    配置根日志器
    
    Args:
        level: 日志级别，默认为 INFO
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


@lru_cache
def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器
    
    Args:
        name: 日志器名称，通常使用 __name__
        
    Returns:
        配置好的日志器实例
    """
    return logging.getLogger(name)


# 应用启动时初始化日志配置
setup_logging()
