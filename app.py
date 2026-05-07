import streamlit as st
import pandas as pd
import time
import random

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="送花数据实时监控看板",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 模拟数据生成 (修复了语法错误)
# ==========================================
def get_data():
    """
    模拟从API获取数据。
    注意：实际使用时请删除此函数，改为 requests.get 请求您的API。
    """
    # 这里补全了所有数字，确保代码不报错
    data = {
        "姓名": ["王橹杰", "张函瑞", "陈浚铭", "左奇函", "杨博文", "张桂源"],
        "今日送花": [12580, 9800, 8500, 6200, 4300, 3100],
        "今日总人数": [450, 320, 280, 210, 150, 110],
        "历史总数": [1250000, 980000, 850000, 620000, 430000, 310000],
        "今日增量送花": [120, 80, 150, 60, 40, 30],
        "今日增量人数": [12, 8, 15, 6, 4, 3]
    }
    df = pd.DataFrame(data)
    # 计算人均
    df["人均送花"] = (df["今日送花"] / df["今日总人数"]).round(2)
    return df

# ==========================================
# 3. 获取数据
# ==========================================
try:
    df = get_data()
    # 按今日送花降序排列
    df = df.sort_values(by="今日送花", ascending=False).reset_index(drop=True)
    last_update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
except Exception as e:
    st.error(f"数据加载失败: {e}")
    st.stop()

# ==========================================
# 4. 自定义 CSS 样式 (实现精准对齐)
# ==========================================
st.markdown("""
<style>
    /* 卡片整体布局：三列网格 */
    .rank-card {
        display: grid;
        grid-template-columns: 130px 1fr 1fr; /* 左侧固定宽度，右侧自适应 */
        gap: 15px;
        background: white;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #f0f2f6;
        align-items: center;
    }

    /* 左侧区域：姓名 + 历史总数 (垂直居中) */
    .col-name {
        grid-column: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-right: 2px solid #f0f2f6;
        padding-right: 15px;
    }

    /* 中间区域：今日送花 + 增量 */
    .col-flowers {
        grid-column: 2;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-right: 2px solid #f0f2f6;
        padding-right: 15px;
    }

    /* 右侧区域：今日人数 + 增量 */
    .col-people {
        grid-column: 3;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* 文本样式微调 */
    .main-value { font-size: 24px; font-weight: bold; color: #333; }
    .sub-label { font-size: 12px; color: #888; margin-top: 2px; }
    .sub-value { font-size: 13px; color: #d32f2f; font-weight: 600; }
    .history-value { font-size: 14px; color: #555; margin-top: 5px; }
    .avatar { width: 40px; height: 40px; border-radius: 50%; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. 页面主体渲染
# ==========================================

# 标题区
st.title("🌸 送花数据实时监控看板")
st.caption(f"最后更新时间: {last_update_time} (每30秒自动刷新)")
st.markdown("---")

# 循环渲染每一行卡片
for index, row in df.iterrows():
    # 颜色逻辑 (示例)
    color = "#d32f2f" if index == 0 else "#1976d2"

    # 构建 HTML 卡片
    # 结构：
    # [ 姓名 ] [ 今日送花 ] [ 今日人数 ]
    # [ 历史 ] [ 增量送花 ] [ 增量人数 ]

    card_html = f"""
    <div class="rank-card">
        <!-- 第一列：姓名与历史 -->
        <div class="col-name">
            <div style="font-size: 18px; font-weight: bold; color: {color};">{row['姓名']}</div>
            <div class="history-value">历史: {row['历史总数']:,}</div>
        </div>

        <!-- 第二列：送花数据 -->
        <div class="col-flowers">
            <div class="main-value">{row['今日送花']:,}</div>
            <div class="sub-value">+ {row['今日增量送花']:,} 朵</div>
        </div>

        <!-- 第三列：人数数据 -->
        <div class="col-people">
            <div class="main-value">{row['今日总人数']:,}</div>
            <div class="sub-value">+ {row['今日增量人数']:,} 人</div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# 6. 自动刷新逻辑
# ==========================================
# 如果需要自动刷新，取消下面的注释（注意：streamlit 原生自动刷新需要配合浏览器插件或实验性功能，
# 或者使用 st.rerun() 在脚本末尾控制，但在云托管环境可能受限）

# time.sleep(30)
# st.rerun()