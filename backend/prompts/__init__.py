# -*- coding: utf-8 -*-
"""
提示词模块

按场景管理不同的系统提示词。
"""
from .nutritionist import NUTRITIONIST_PROMPT
from .resume_assistant import RESUME_ASSISTANT_PROMPT

# 默认使用简历助手提示词（当前活跃功能）
SYSTEM_PROMPT = RESUME_ASSISTANT_PROMPT

__all__ = [
    "NUTRITIONIST_PROMPT",
    "RESUME_ASSISTANT_PROMPT", 
    "SYSTEM_PROMPT"
]
