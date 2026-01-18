from openai import OpenAI

# 1. 初始化客户端
# 注意：api_key可以填任意非空字符串，base_url指向你的LM Studio服务地址
client = OpenAI(
    api_key="lm-studio",  # 可自定义，不能为空
    base_url="http://localhost:1234/v1",  # 默认地址
)

# 2. 定义对话历史
messages = [
    {"role": "system", "content": "你是一个乐于助人的助手。"},
    {"role": "user", "content": "你叫什么名字？"}
]

# 3. 发起API请求
stream = client.chat.completions.create(
    model="qwq-lcot-3b-instruct",  # 替换为你实际下载的模型名称
    messages=messages,
    temperature=0.7,        # 控制随机性 (0-1)，值越低输出越确定
    max_tokens=512,         # 控制回复的最大长度
    stream=True             # 启用流式输出，实现打字机效果
)

# 4. 处理流式响应
print("助手: ", end="", flush=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)