"""Debug: inspect default stream_mode output format"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'backend')

from langchain_core.messages import HumanMessage
from services.agent import get_agent

agent = get_agent()
config = {"configurable": {"thread_id": "debug-test-002"}}

print("=== default stream_mode (updates) ===")
for i, chunk in enumerate(agent.stream(
    {"messages": [HumanMessage(content="hi")]},
    config=config,
)):
    print(f"\n--- chunk {i} ---")
    print(f"  keys: {list(chunk.keys())}")
    for key, val in chunk.items():
        print(f"  [{key}]:")
        if isinstance(val, dict) and 'messages' in val:
            for msg in val['messages']:
                print(f"    type: {type(msg).__name__}")
                content = getattr(msg, 'content', '')
                print(f"    content length: {len(content)}")
                print(f"    content preview: {repr(content[:200])}")
                print(f"    tool_calls: {getattr(msg, 'tool_calls', [])}")
        else:
            print(f"    {str(val)[:200]}")

print("\n=== DONE ===")
