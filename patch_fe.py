import re

file_path = 'frontend_v2/src/store/chat.ts'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Add logging
code = code.replace(
    "const data = JSON.parse(line.replace('data: ', ''));",
    "const data = JSON.parse(line.replace('data: ', ''));\n              console.log('【DEBUG SSE event】', data);"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)
