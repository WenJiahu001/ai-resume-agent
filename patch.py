import re

with open('backend/services/agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add logging
code = code.replace('chunk = item', 'chunk = item\n            logger.info(f"【DEBUG chunk】: {chunk}")')
code = code.replace('def _run_stream():\n        """在子线程中运行同步 agent.stream()，把结果逐个放入队列"""\n        try:', 'def _run_stream():\n        """在子线程中运行同步 agent.stream()，把结果逐个放入队列"""\n        try:\n            logger.info("【DEBUG stream start】")')

with open('backend/services/agent.py', 'w', encoding='utf-8') as f:
    f.write(code)
