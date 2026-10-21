import streamlit as st
import requests
import base64
import json
import io
from PIL import Image

# ==========================================
# 0. 配置
# ==========================================
API_KEY = "sk-你的key"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL_NAME = "qwen3.8-flash"


def call_qwen_vl(image_bytes, prompt_text):
    img_base64 = base64.b64encode(image_bytes).decode("utf-8")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "input": {"messages": [{"role": "user", "content": [
            {"image": f"data:image/jpeg;base64,{img_base64}"},
            {"text": prompt_text}
        ]}]},
        "parameters": {}
    }
    try:
        response = requests.post(URL, headers=headers, json=data)
        result = response.json()
        if response.status_code == 200 and "output" in result:
            return result["output"]["choices"][0]["message"]["content"][0]["text"]
        else:
            return f"API错误：{json.dumps(result, ensure_ascii=False)}"
    except Exception as e:
        return f"网络失败：{e}"


# ==========================================
# 1. 界面与模式选择
# ==========================================
st.title("🛰️ 遥感影像时空智能分析系统")

analysis_mode = st.radio(
    "请选择分析模式",
    ["模式一：单时单像解析 (空间特征)", "模式二：多时相变化检测 (时间特征)"]
)
st.divider()

# ------------------ 模式一：单时单像（切片） ------------------
if analysis_mode == "模式一：单时单像解析 (空间特征)":
    st.subheader("单幅影像切片解析")
    col1, col2 = st.columns(2)
    with col1:
        location = st.text_input("拍摄地点", "北京", key="loc1")
    with col2:
        capture_time = st.text_input("拍摄时间", "2026年10月", key="time1")

    file_single = st.file_uploader("上传影像", type=["jpg", "png"], key="single")

    if file_single is not None:
        st.image(file_single, caption="上传的影像", use_container_width=True)
        if st.button("开始切片识别", key="btn_single"):
            with st.spinner("正在切片并识别中..."):
                img = Image.open(file_single).convert("RGB")
                results = []
                tile_index = 1
                tile_size = 512

                # 循环切片（上限设为 1024，最多切4块，防止卡死）
                for i in range(0, min(img.width, 1024), tile_size):
                    for j in range(0, min(img.height, 1024), tile_size):
                        tile = img.crop((i, j, min(i + tile_size, img.width), min(j + tile_size, img.height)))
                        bytes_io = io.BytesIO();
                        tile.save(bytes_io, format='JPEG')

                        prompt = f"""你是一位资深遥感解译专家。这是{location}在{capture_time}的第{tile_index}个切片，坐标为[X:{i}, Y:{j}]。
                        请严格按照以下格式输出：
                        1. 【主要地物】：（列出识别到的地物，如建筑、水体、农田）
                        2. 【空间分布】：（描述这些地物在切片中的位置关系）
                        3. 【时空推断】：（结合{capture_time}的季节和{location}的地理特点，推测地物当前的状态，如农作物长势、水体丰枯）"""
                        res = call_qwen_vl(bytes_io.getvalue(), prompt)
                        results.append(f"**切片 {tile_index} [X:{i},Y:{j}]:** {res}")
                        tile_index += 1

                st.success(f"✅ 识别完成！共识别 {tile_index - 1} 个切片。")
                for r in results: st.info(r)

# ------------------ 模式二：多时相变化检测 ------------------
else:
    st.subheader("同一地点、不同时间的影像变化检测")
    location = st.text_input("拍摄地点", "北京", key="loc2")

    colA, colB = st.columns(2)
    with colA:
        time_A = st.text_input("时间A (前期)", "2026年7月", key="timeA")
        file_A = st.file_uploader("上传时间A影像", type=["jpg", "png"], key="fileA")
    with colB:
        time_B = st.text_input("时间B (后期)", "2026年12月", key="timeB")
        file_B = st.file_uploader("上传时间B影像", type=["jpg", "png"], key="fileB")

    if file_A is not None and file_B is not None:
        st.image([file_A, file_B], caption=["前期影像", "后期影像"], width=300)
        if st.button("开始变化检测", key="btn_time"):
            with st.spinner("正在拼接切片并检测变化..."):
                img_A = Image.open(file_A).convert("RGB")
                img_B = Image.open(file_B).convert("RGB")
                results = []
                tile_index = 1
                tile_size = 512

                # 限制只切前4块进行对比
                for i in range(0, min(img_A.width, 1024), tile_size):
                    for j in range(0, min(img_A.height, 1024), tile_size):
                        tile_A = img_A.crop((i, j, min(i + tile_size, img_A.width), min(j + tile_size, img_A.height)))
                        tile_B = img_B.crop((i, j, min(i + tile_size, img_B.width), min(j + tile_size, img_B.height)))

                        # 左右拼接当前切片
                        combined_img = Image.new('RGB', (tile_size * 2, tile_size))
                        combined_img.paste(tile_A, (0, 0))
                        combined_img.paste(tile_B, (tile_size, 0))
                        bytes_io = io.BytesIO();
                        combined_img.save(bytes_io, format='JPEG')

                        prompt = f"""你是一位专业的遥感变化检测专家。
                        这是一张左右拼接的对比图。左侧影像拍摄于【{time_A}】，右侧影像拍摄于【{time_B}】，地点在【{location}】。

                        请仔细观察左右两张图的差异，严格按照以下格式输出你的发现：
                        1. 【水体变化】：对比左右两侧，水体（河流、湖泊）的面积、边界或颜色是否发生变化？
                        2. 【植被/农田变化】：对比左右两侧，植被的颜色（如由绿变黄）或农田的纹理是否发生变化？结合季节因素推断原因。
                        3. 【建筑/人造地物】：是否有新增的道路、建筑或施工区域？
                        4. 【综合结论】：用一句话总结该区域在这段时间内的主要变化。

                        注意：如果某项没有变化，请直接回答“无明显变化”。不要写废话，直接给出专业分析。"""
                        res = call_qwen_vl(bytes_io.getvalue(), prompt)
                        results.append(f"**切片 {tile_index} [X:{i},Y:{j}] 变化:** {res}")
                        tile_index += 1

                st.success(f"✅ 检测完成！共对比了 {tile_index - 1} 个切片。")
                for r in results: st.info(r)