import streamlit as st
import requests
import base64
import json

# ==========================================
# 1. 配置 API Key（先写占位符，本地测试时再改真实的）
# ==========================================
API_KEY = "sk-你的key"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL_NAME = "qwen3.8-flash"


# ==========================================
# 2. 封装调用 API 的函数（把你昨天跑通的代码搬进来）
# ==========================================
def call_qwen_vl(image_bytes):
    img_base64 = base64.b64encode(image_bytes).decode("utf-8")
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
                        {"image": f"data:image/jpeg;base64,{img_base64}"},
                        {"text": "你是一位遥感解译专家。请识别这张遥感图片中的主要地物，用一句话简洁描述。"}
                    ]
                }
            ]
        },
        "parameters": {}
    }
    try:
        response = requests.post(URL, headers=headers, json=data)
        result = response.json()
        if response.status_code == 200 and "output" in result:
            return result["output"]["choices"][0]["message"]["content"][0]["text"]
        else:
            return f"API返回错误：{json.dumps(result, ensure_ascii=False)}"
    except Exception as e:
        return f"网络请求失败：{e}"


# ==========================================
# 3. Streamlit 网页界面
# ==========================================
st.title("🛰️ 遥感影像看图说话助手")
st.write("上传一张遥感影像，AI将自动识别其中的地物并生成描述。")

# 文件上传组件
uploaded_file = st.file_uploader("请上传遥感图片", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="上传的遥感图", use_container_width=True)

    if st.button("开始识别"):
        with st.spinner("正在调用大模型识别中，请稍候..."):
            # 获取图片的字节流，并调用函数
            result_text = call_qwen_vl(uploaded_file.getvalue())
            st.success("✅ 识别完成！")
            st.info(f"**识别结果：**\n\n{result_text}")