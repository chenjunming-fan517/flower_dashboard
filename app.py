import streamlit as st
import pandas as pd
import time

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="送花数据实时监控看板",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 模拟数据生成 (实际使用时可替换为API请求)
# ==========================================
def get_data():
    # 这里模拟了API返回的数据结构
    # 如果您有真实API，请替换此函数内容
    data = {
        "姓名": ["王橹杰", "张函瑞", "陈浚铭", "左奇函", "杨博文", "其他艺人"],
        "今日送花": ,
        "今日总人数": ,
        "历史总数": ,
        "今日增量送花": , # 模拟增量
        "今日增量人数":    # 模拟增量
    }
    df = pd.DataFrame(data)
    # 计算人均
    df["人均送花"] = (df["今日送花"] / df["今日总人数"]).round(2)
    return df<websource>source_group_web_1</websource>

# ==========================================
# 3. 核心样式与布局 (CSS Grid 实现精准对齐)
# ==========================================

# 定义颜色映射
COLOR_MAP = {
    "王橹杰": "#06B6D4", # 青色
    "张函瑞": "#10B981", # 绿色
    "陈浚铭": "#F59E0B", # 橙色
    "左奇函": "#8B5CF6", # 紫色
    "杨博文": "#EC4899", # 粉色
}
DEFAULT_COLOR = "#94A3B8" # 默认灰色

# 注入CSS样式
st.markdown("""
<style>
/* 隐藏Streamlit默认的菜单和页脚，让看板更干净 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* 卡片容器：使用Grid布局分为三列 */
.rank-card {
    display: grid;
    grid-template-columns: 140px 1fr 1fr; /* 左列固定宽度(姓名)，中右列自动平分 */
    gap: 15px;
    background: white;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0;
    transition: transform 0.2s;
}

.rank-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

/* --- 左列：姓名与历史总数 --- */
.name-section {
    grid-column: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-right: 2px dashed #e2e8f0; /* 分隔线 */
    padding-right: 15px;
}

.rank-name {
    font-size: 1.5rem;
    font-weight: 800;
    color: #1e2a3a;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
}

.history-badge {
    background: #f1f5f9;
    color: #475569;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    white-space: nowrap;
}

/* --- 中列与右列：数据组 --- */
.data-column {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

/* 数据行样式 */
.data-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    border-radius: 8px;
    background: #f8fafc;
    border-left: 5px solid #cbd5e1; /* 默认边框色 */
}

.data-label {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
}

.data-value {
    font-size: 1.1rem;
    font-family: 'Courier New', monospace; /* 等宽字体，数字对齐更好看 */
    font-weight: 700;
    color: #0f172a;
}

/* 增量数据的特殊样式 */
.data-row.increment {
    background: #ffffff;
    border: 1px solid #f1f5f9;
    border-left: 5px solid #cbd5e1;
}
.data-row.increment .data-label { color: #94a3b8; font-size: 0.85rem; }
.data-row.increment .data-value { color: #64748b; font-size: 1rem; }

/* 移动端适配 */
@media (max-width: 600px) {
    .rank-card { grid-template-columns: 1fr; gap: 10px; }
    .name-section { border-right: none; border-bottom: 2px dashed #e2e8f0; padding-bottom: 10px; flex-direction: row; justify-content: space-between; }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主程序逻辑
# ==========================================

st.title("🌸 送花数据实时监控看板")
st.caption("数据每 5 秒自动刷新 | 仅展示核心指标")

# 占位符，用于动态刷新
placeholder = st.empty()

while True:
    with placeholder.container():
        # 1. 获取数据
        try:
            df = get_data()
            # 按今日送花降序排列
            df = df.sort_values(by="今日送花", ascending=False).reset_index(drop=True)
        except Exception as e:
            st.error(f"数据加载失败: {e}")
            df = pd.DataFrame()

        # 2. 渲染卡片
        if not df.empty:
            for i, row in df.iterrows():
                name = row["姓名"]
                color = COLOR_MAP.get(name, DEFAULT_COLOR)
                
                # 格式化数字
                today_fmt = f"{int(row['今日送花']):,}"
                people_fmt = f"{int(row['今日总人数']):,}"
                total_fmt = f"{int(row['历史总数']):,}"
                delta_gift_fmt = f"+{int(row['今日增量送花']):,}"
                delta_people_fmt = f"+{int(row['今日增量人数']):,}"

                # HTML 结构
                # 逻辑：
                # Grid Col 1: 姓名 + 历史总数 (垂直对齐)
                # Grid Col 2: 今日送花 + 增量送花 (垂直对齐)
                # Grid Col 3: 今日人数 + 增量人数 (垂直对齐)
                card_html = f"""
                <div class="rank-card">
                    <!-- 左列：姓名与历史 -->
                    <div class="name-section">
                        <div class="rank-name" style="color: {color};">{name}</div>
                        <div class="history-badge">📜 历史总数：{total_fmt}</div>
                    </div>

                    <!-- 中列：送花数据 -->
                    <div class="data-column">
                        <div class="data-row" style="border-left-color: {color};">
                            <span class="data-label">🌸 今日送花</span>
                            <span class="data-value">{today_fmt}</span>
                        </div>
                        <div class="data-row increment" style="border-left-color: {color};">
                            <span class="data-label">📈 较上轮增量</span>
                            <span class="data-value">{delta_gift_fmt}</span>
                        </div>
                    </div>

                    <!-- 右列：人数数据 -->
                    <div class="data-column">
                        <div class="data-row" style="border-left-color: {color};">
                            <span class="data-label">👥 今日人数</span>
                            <span class="data-value">{people_fmt}</span>
                        </div>
                        <div class="data-row increment" style="border-left-color: {color};">
                            <span class="data-label">👤 较上轮增量</span>
                            <span class="data-value">{delta_people_fmt}</span>
                        </div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        
        # 3. 模拟自动刷新 (实际部署时请配合 st.autorun 或前端刷新)
        time.sleep(5) 
        # 注意：在真实Streamlit Cloud环境中，通常使用 st.rerun() 或前端meta刷新
        # 这里为了演示循环效果使用了while True，本地运行按 Ctrl+C 停止
        st.rerun()