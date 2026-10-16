import streamlit as st
import requests
import base64
import json
import io
from PIL import Image

# ==========================================
# 1. 配置 API Key（本地测试时改成真实Key，测试完改回占位符）
# ==========================================
API_KEY = "sk-你的key"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL_NAME = "qwen3.8-flash"


# ==========================================
# 2. 定义切片函数
# ==========================================
def split_image(img, tile_size=512):
    tiles = []
    for i in range(0, img.width, tile_size):
        for j in range(0, img.height, tile_size):
            box = (i, j, min(i + tile_size, img.width), min(j + tile_size, img.height))
            tiles.append(img.crop(box))
    return tiles


# ==========================================
# 3. 封装调用大模型的函数
# ==========================================
def call_qwen_vl(image_bytes, prompt_text):
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
                        {"text": prompt_text}
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
# 4. Streamlit 网页界面（核心改造区）
# ==========================================
st.title("🛰️ 遥感影像看图说话助手")
st.write("上传一张遥感影像，AI将自动切图并识别其中的地物。")

uploaded_file = st.file_uploader("请上传遥感图片", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="上传的遥感图", use_container_width=True)

    if st.button("开始识别"):
        with st.spinner("正在切片并调用大模型识别中，请稍候..."):
            # 1. 读取上传的图片
            img_bytes = uploaded_file.getvalue()
            img = Image.open(io.BytesIO(img_bytes))

            # 2. 切图（把大图切成512x512的小块）
            tiles = split_image(img, tile_size=512)

            results = []
            # 3. 循环遍历每个切片，发给大模型
            for i, tile in enumerate(tiles):
                # 把切片转成字节流
                tile_bytes = io.BytesIO()
                tile.save(tile_bytes, format='JPEG')

                # 构造提示词（后面加时空特征时可以在这里改）
                prompt_text = "你是一位遥感解译专家。请识别这张遥感切片中的主要地物，用一句话简洁描述。"

                # 调用模型
                result_text = call_qwen_vl(tile_bytes.getvalue(), prompt_text)
                results.append(f"**切片 {i + 1}:** {result_text}")

            # 4. 在网页上展示所有切片的结果
            st.success(f"✅ 识别完成！共切分并识别了 {len(tiles)} 个切片。")
            for res in results:
                st.info(res)