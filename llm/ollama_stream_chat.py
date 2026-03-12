# -*- coding: utf-8 -*-
import ollama

# 直接创建客户端
client = ollama.Client(host='http://127.0.0.1:11434')

# 调用模型，开启流式输出
stream = client.chat(
    model="deepseek-r1:latest",
    messages=[
        {"role": "system", "content": "你是一个翻译，内容与博彩相关，注重专用名词"},
        {"role": "user", "content": """请提供合适的俄语翻译或音译。
要求：
1. 按照顺序翻译每个文本2. 每行一个翻译结果，格式为：序号. 翻译结果3. 只返回俄语翻译，不要其他内容4. 如果某个文本无法翻译，返回空行待翻译文本：
1.Li, Bo 2.Osman, Ekber 3.Yufei, Jiang 4.Chaohui, Wang 请按以下格式返回（每行一个翻译结果）：
1. 翻译结果1 2. 翻译结果2 ..."""}
    ],
    # think=False,
    # think='low',
    stream=True,
    keep_alive=-1
)

resp = False
thingking = False
content = False

for chunk in stream:
    if not resp:
        print("-------- 开始回复 --------")
        resp = True

    if 'thinking' in chunk['message'] and chunk['message']['thinking']:
        if not thingking:
            print(">>>>>>>> 思考过程 >>>>>>>>")
            thingking = True
        print(chunk['message']['thinking'], end='', flush=True)

    if 'content' in chunk['message'] and chunk['message']['content']:
        if not content:
            if thingking:
                print(">>>>>>>> 思考完成 >>>>>>>>")
                print()
            print("########### 回复内容 ###########")
            content = True
        print(chunk['message']['content'], end='', flush=True)

print()
print("-------- 回复结束 --------")
