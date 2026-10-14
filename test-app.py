import requests
import base64
import json
import os

# ==========================================
# 1. 配置 API Key（替换成你的真实 Key）
# ==========================================
API_KEY = "sk-你的key"
# 通义千问多模态API的固定请求地址
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

# 这里填你选择的模型名称（根据你百炼控制台里的实际名字填写）
MODEL_NAME = "qwen3.8-flash"

# 要测试的本地图片路径（改成你自己的）
IMAGE_PATH = "test.jpg" 

# ==========================================
# 2. 检查图片并转 Base64 编码
# ==========================================
if not os.path.exists(IMAGE_PATH):
    print(f"❌ 找不到图片：{IMAGE_PATH}，请确认路径是否正确！")
else:
    print("🔄 正在读取图片并发送请求，请稍等...")
    
    with open(IMAGE_PATH, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    # ==========================================
    # 3. 构造请求头和请求体（JSON格式）
    # ==========================================
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        # 图片必须是 data:image/jpeg;base64, 开头的格式
                        {"image": f"data:image/jpeg;base64,{img_base64}"},
                        # 这里就是你的 Prompt Engineering（提示词工程）
                        {"text": "你是一位遥感解译专家。请识别这张遥感图片中的主要地物，用一句话简洁描述。"}
                    ]
                }
            ]
        },
        "parameters": {}
    }

    # ==========================================
    # 4. 发送 POST 请求并解析结果
    # ==========================================
    try:
        response = requests.post(URL, headers=headers, json=data)
        result = response.json()

        # 检查是否有报错
        if response.status_code == 200 and "output" in result:
            print("\n✅ 识别成功！结果如下：")
            # 提取大模型返回的文字
            output_text = result["output"]["choices"][0]["message"]["content"][0]["text"]
            print(output_text)
        else:
            print("\n❌ API返回了错误：")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
    except Exception as e:
        print(f"\n❌ 网络请求失败，错误信息：{e}")