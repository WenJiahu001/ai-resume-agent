# -*- coding: utf-8 -*-
import pymysql
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='123456',
    database='eat',
    autocommit=True,
    cursorclass=pymysql.cursors.DictCursor
)

checkpointer = PyMySQLSaver(conn)

# 获取所有 thread_id
with conn.cursor() as cur:
    cur.execute('SELECT DISTINCT thread_id FROM checkpoints')
    threads = cur.fetchall()
    print("=== 所有会话 ===")
    for t in threads:
        print(f"  - {t['thread_id']}")

# 获取指定 thread 的消息
config = {'configurable': {'thread_id': 'wenjiahu1'}}
ct = checkpointer.get_tuple(config)
if ct:
    messages = ct.checkpoint.get('channel_values', {}).get('messages', [])
    print(f"\n=== 消息历史 ({len(messages)} 条) ===")
    for i, msg in enumerate(messages):
        role = msg.type if hasattr(msg, 'type') else '?'
        content = msg.content if hasattr(msg, 'content') else str(msg)
        preview = content[:80] + '...' if len(content) > 80 else content
        print(f"[{i}] {role}: {preview}")

conn.close()
