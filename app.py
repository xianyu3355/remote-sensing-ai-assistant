import streamlit as st
import requests
import base64
import json
import io
from PIL import Image

# ==========================================
# 0. 全局配置
# ==========================================
# 设置网页标题和宽屏模式
st.set_page_config(page_title="遥感时空智能分析系统", layout="wide")

API_KEY = "sk-你的key"  # ⚠️ 测试时换成真实 Key
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL_NAME = "qwen3.8-flash"  # 如果你有权限，换成 qwen-vl-max 效果更好


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
# 1. 侧边栏（模式选择）
# ==========================================
with st.sidebar:
    st.header("⚙️ 控制面板")
    analysis_mode = st.radio(
        "请选择分析模式",
        ["模式一：单时单像解析 (空间)", "模式二：多时相变化检测 (时间)"]
    )
    st.info("💡 提示：上传影像后，系统将自动进行切片处理并调用大模型进行深度解析。")

# 网页主标题
st.title("🛰️ 遥感影像时空智能分析系统")
st.divider()

# ==========================================
# 2. 模式一：单时单像（空间切片）
# ==========================================
if analysis_mode == "模式一：单时单像解析 (空间)":
    st.subheader("单幅影像切片解析")

    col1, col2 = st.columns(2)
    with col1:
        location = st.text_input("拍摄地点", "北京", key="loc1")
    with col2:
        capture_time = st.text_input("拍摄时间", "2026年10月", key="time1")

    file_single = st.file_uploader("上传影像", type=["jpg", "png"], key="single")

    if file_single is not None:
        # 分左右两列：左边放图，右边放结果
        col_img, col_res = st.columns([1, 1.5])

        with col_img:
            st.image(file_single, caption="上传的影像", use_container_width=True)
            btn = st.button("开始切片识别", key="btn_single", use_container_width=True)

        with col_res:
            if btn:
                with st.spinner("正在切片并识别中，请稍候..."):
                    img = Image.open(file_single).convert("RGB")
                    tile_index = 1
                    tile_size = 512

                    # 限制只切前4块（防止太慢）
                    for i in range(0, min(img.width, 1024), tile_size):
                        for j in range(0, min(img.height, 1024), tile_size):
                            tile = img.crop((i, j, min(i + tile_size, img.width), min(j + tile_size, img.height)))
                            bytes_io = io.BytesIO();
                            tile.save(bytes_io, format='JPEG')

                            # 【高级 Prompt：强结构化输出】
                            prompt = f"""你是一位资深遥感解译专家。这是{location}在{capture_time}的第{tile_index}个切片，坐标为[X:{i}, Y:{j}]。
请严格按照以下格式输出你的分析：
1. 【主要地物】：（列出识别到的地物，如建筑、水体、农田等）
2. 【空间分布】：（描述这些地物在切片中的位置关系或纹理特征）
3. 【时空推断】：（结合{capture_time}的季节和{location}的地理特点，推测地物当前的状态，如农作物长势、水体丰枯等）
请保持语言专业简练，不要写废话。"""

                            res = call_qwen_vl(bytes_io.getvalue(), prompt)

                            # 结果放进折叠面板
                            with st.expander(f"切片 {tile_index} [X:{i},Y:{j}] 识别结果", expanded=True):
                                st.write(res)
                            tile_index += 1

# ==========================================
# 3. 模式二：多时相变化检测（时间）
# ==========================================
else:
    st.subheader("多时相变化检测")
    location = st.text_input("拍摄地点", "北京", key="loc2")

    # 两张图左右并排上传
    colA, colB = st.columns(2)
    with colA:
        time_A = st.text_input("时间A (前期)", "2026年7月", key="timeA")
        file_A = st.file_uploader("上传时间A影像", type=["jpg", "png"], key="fileA")
        if file_A: st.image(file_A, caption="前期影像", use_container_width=True)

    with colB:
        time_B = st.text_input("时间B (后期)", "2026年12月", key="timeB")
        file_B = st.file_uploader("上传时间B影像", type=["jpg", "png"], key="fileB")
        if file_B: st.image(file_B, caption="后期影像", use_container_width=True)

    st.divider()

    if file_A is not None and file_B is not None:
        if st.button("开始变化检测", key="btn_time", use_container_width=True):
            with st.spinner("正在拼接切片并检测变化..."):
                img_A = Image.open(file_A).convert("RGB")
                img_B = Image.open(file_B).convert("RGB")
                tile_index = 1
                tile_size = 512

                for i in range(0, min(img_A.width, 1024), tile_size):
                    for j in range(0, min(img_A.height, 1024), tile_size):
                        tile_A = img_A.crop((i, j, min(i + tile_size, img_A.width), min(j + tile_size, img_A.height)))
                        tile_B = img_B.crop((i, j, min(i + tile_size, img_B.width), min(j + tile_size, img_B.height)))

                        # 左右拼接
                        combined_img = Image.new('RGB', (tile_size * 2, tile_size))
                        combined_img.paste(tile_A, (0, 0))
                        combined_img.paste(tile_B, (tile_size, 0))
                        bytes_io = io.BytesIO();
                        combined_img.save(bytes_io, format='JPEG')

                        # 【高级 Prompt：强制找茬输出】
                        prompt = f"""你是一位专业的遥感变化检测专家。
这是一张左右拼接的对比图。左侧影像拍摄于【{time_A}】，右侧影像拍摄于【{time_B}】，地点在【{location}】。
请仔细观察左右两张图的差异，严格按照以下格式输出：
1. 【水体变化】：对比左右，水体面积、边界或颜色是否发生变化？
2. 【植被/农田变化】：对比左右，植被颜色或纹理是否变化？结合季节推断原因。
3. 【建筑/人造地物】：是否有新增的道路、建筑或施工区域？
4. 【综合结论】：用一句话总结该区域的主要变化。
注意：如果某项没有变化，请直接回答“无明显变化”。不要写废话。"""

                        res = call_qwen_vl(bytes_io.getvalue(), prompt)

                        with st.expander(f"切片 {tile_index} [X:{i},Y:{j}] 变化检测结果", expanded=True):
                            st.write(res)
                        tile_index += 1