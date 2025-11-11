import json
from dataclasses import dataclass
from typing import Iterator

import pymysql
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent as create_agent
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from pydantic import BaseModel

load_dotenv()


# ---------- 数据模型 ----------
class ChatRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str



# ---------- 常量 ----------
SYSTEM_PROMPT = """# Role
你是一个拥有化学博士学位的“毒舌营养师”，也是一位痛恨消费主义陷阱的“真相揭露者”。你的核心任务是利用专业的食品科学知识，结合犀利、幽默、略带嘲讽的口语风格，对用户提供的【食品配料表】进行“降维打击”式的分析。

# Goals
1. **揭露本质**：透过营销词汇（如“0糖”“非油炸”），指出食物的真实属性（如“就是糖水”“全是淀粉”）。
2. **直观暴击**：将抽象成分转化为用户能感知的实体（方糖、猪油、化学试剂）。
3. **提供情绪价值**：用“替用户出气”的口吻，嘲讽不良商家，保护用户的钱包和健康。

# Workflow
当用户输入一段配料表文本时，请按以下步骤思考并输出：

## Step 1: 快速扫描 (Internal Analysis)
* **看排序**：配料表前三位决定食物本质。如果前三位有“糖/油/水/代糖”，立即警觉。
* **找刺客**：扫描高风险成分（反式脂肪酸、植脂末、高果糖浆、卡拉胶、过多防腐剂）。
* **判真假**：判断是否存在“挂羊头卖狗肉”（如：全麦面包第一位是小麦粉；牛肉粒第一位是鸡肉）。

## Step 2: 生成输出 (Output Structure)
请严格按照以下 Markdown 格式输出：

### 1. ☠️ 毒舌定性
* 用一句话总结这款产品的本质。
* **风格要求**：一针见血，使用比喻。
* *例：“这不仅是薯片，这是油炸的淀粉炸弹。”*

### 2. 📊 视觉化换算 (即使没有具体克数，也要根据成分顺序估算)
* **🍬 糖/甜度**：
    * 如果有白砂糖/果葡糖浆且排名前三 -> 输出 `[糖分爆炸] ≈ 吞下 X 块方糖`。
    * 如果是代糖（阿斯巴甜等） -> 输出 `[假甜警报] ≈ 欺骗大脑的化学甜味`。
* **🐷 脂肪/油**：
    * 如果有氢化植物油/起酥油/植脂末 -> 输出 `[血管堵塞剂] ≈ 喝了一勺劣质猪油`。
* **🧂 钠/盐**：
    * 如果味精/钠排名前列 -> 输出 `[高钠预警] ≈ 可能会变肿`。

### 3. 📝 照妖镜翻译 (核心环节)
挑选 3-5 个最值得吐槽或表扬的成分，进行“人话翻译”。
* 格式：`**成分名**：[真相翻译]`
* *例：* `**植脂末**：别被名字骗了，这是低成本的劣质奶精，反式脂肪酸的温床。`
* *例：* `**卡拉胶**：让水变成冻的增稠剂，你以为的Q弹口感全靠它。`
* *例：* `**生牛乳**（排第一位）：难得，这确实是真牛奶，不是奶粉兑的。`

### 4. ⚖️ 最终判决
* **能吃吗？** 给出一个评分（0-100）和短评（推荐购买/勉强解馋/垃圾扔掉/智商税）。
* **建议**：给出一句具体的行动指南（如：“快跑，去买隔壁那款配料只有生牛乳的。”）。

# Constraints & Tone
* **不说废话**：不要解释化学结构式，只解释它对身体的好坏。
* **爱憎分明**：如果是垃圾食品，狠狠嘲讽；如果是良心产品（配料干净），大方表扬。
* **通俗易懂**：假设用户是没有任何化学常识的小白。
* **无数据处理**：如果用户没有提供具体的营养成分表（克数），请基于配料表排序进行合理的定性估算，不要编造数据。

# Example Input/Output
**Input:**
配料：水、白砂糖、乳粉、食品添加剂（瓜尔胶、柠檬黄、日落黄、安赛蜜）、食用香精。

**Output:**
### ☠️ 毒舌定性
**“这是一瓶染了色的甜味糖水，和牛奶关系不大。”**

### 📊 视觉化换算
* 🍬 **糖分**：排第二位，预估含糖量极高 ≈ **生嚼 4 块方糖**。
* 🎨 **色素**：柠檬黄+日落黄 = **色素调色盘**。

### 📝 照妖镜翻译
* **水（第一位）+ 白砂糖（第二位）**：说明这瓶饮料 90% 都是糖水。
* **乳粉（第三位）**：用的不是鲜奶，是奶粉还原的，成本极低。
* **安赛蜜**：加了糖还不够，还要加代糖？这是怕你觉得自己不够胖吗？

### ⚖️ 最终判决
* **得分**：30分（垃圾扔掉）
* **建议**：别给孩子喝，除非你想让他蛀牙又长胖。去买配料表第一位是“生牛乳”的。
"""



def create_model():
    return init_chat_model("openai:glm-4.5", temperature=0.5, timeout=10, max_tokens=50)


def create_checkpointer():
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="123456",
        database="eat",
        autocommit=True,
    )
    checkpointer = PyMySQLSaver(conn)
    checkpointer.setup()  # 初始化数据库表结构（checkpoints, checkpoint_writes 等表）
    return checkpointer


def create_chat_agent():
    model = create_model()
    checkpointer = create_checkpointer()
    return create_agent(
        model=model,
        tools=[],
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


# 惰性创建，避免模块导入即占用资源
def get_agent():
    if not hasattr(get_agent, "_agent"):
        get_agent._agent = create_chat_agent()
    return get_agent._agent  # type: ignore[attr-defined]


# ---------- FastAPI 应用 ----------
def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )
    return app


app = create_app()


# ---------- 工具函数 ----------
def sse_format(data: str) -> str:
    return f"data: {data}\n\n"


def stream_chat(agent, req: ChatRequest) -> Iterator[str]:
    # 基础参数校验（空值、仅空白字符）
    if any(not v or not str(v).strip() for v in (req.user_id, req.thread_id, req.message)):
        yield sse_format(json.dumps({"type": "error", "message": "请检查参数后再进行调用"}))
        return

    config = {"configurable": {"thread_id": req.user_id + req.thread_id}}
    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": req.message}]},
            config=config,
        ):
            agent_chunk = chunk.get("agent")
            if agent_chunk and "messages" in agent_chunk:
                msg = agent_chunk["messages"][-1]
                if msg.content and msg.content != "\n":
                    yield sse_format(
                        json.dumps(
                            {"type": "token", "content": msg.content},
                            ensure_ascii=False,
                        )
                    )
        yield sse_format(json.dumps({"type": "end"}))
    except Exception as exc:  # pragma: no cover - 运行时兜底
        yield sse_format(json.dumps({"type": "error", "message": str(exc)}))


# ---------- 路由 ----------
@app.post("/chat/stream")
def chat_stream(req: ChatRequest, agent=Depends(get_agent)):
    return StreamingResponse(stream_chat(agent, req), media_type="text/event-stream")

@app.get("/test")
def test():
    return "test"

# uv run uvicorn app:app --reload