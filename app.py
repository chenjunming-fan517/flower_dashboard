import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ==================== 页面配置 ====================
st.set_page_config(page_title="送花数据分析看板", page_icon="🌸", layout="wide")

# ==================== 全屏平铺水印（高可见度版） ====================
watermark_text = "陈浚铭四代第一门面"
watermark_css = f"""
<style>
.watermark-layer {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 9999;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 260px));
    justify-content: center;
    align-items: center;
    opacity: 0.35;           /* 提高透明度，更明显 */
    transform: rotate(-20deg);
    background-color: transparent;
}}
.watermark-item {{
    font-size: 26px;         /* 稍大一点 */
    font-weight: bold;
    color: #6c6c6c;          /* 深灰色，更清晰 */
    font-family: 'Microsoft YaHei', sans-serif;
    white-space: nowrap;
    text-align: center;
    padding: 30px 0;
    user-select: none;
    text-shadow: 1px 1px 0 rgba(255,255,255,0.5);
}}
</style>
<div class="watermark-layer" id="watermark-layer"></div>
<script>
    (function() {{
        const layer = document.getElementById('watermark-layer');
        if (!layer) return;
        // 清空已有内容，避免重复添加（Streamlit 热重载可能导致重复）
        layer.innerHTML = '';
        const itemWidth = 240;
        const itemHeight = 90;
        const cols = Math.ceil(window.innerWidth / itemWidth) + 1;
        const rows = Math.ceil(window.innerHeight / itemHeight) + 1;
        const total = Math.max(cols * rows, 30); // 至少30个
        for (let i = 0; i < total; i++) {{
            const div = document.createElement('div');
            div.className = 'watermark-item';
            div.innerText = '{watermark_text}';
            layer.appendChild(div);
        }}
    }})();
</script>
"""
st.markdown(watermark_css, unsafe_allow_html=True)

# ==================== 明星专属颜色映射 ====================
COLOR_MAP = {
    "王橹杰": "#06B6D4",
    "张函瑞": "#10B981",
    "张桂源": "#F59E0B",
    "杨博文": "#EC4899",
    "左奇函": "#3B82F6",
    "陈奕恒": "#8B5CF6",
    "陈浚铭": "#EF4444",
}
DEFAULT_COLOR = "#888888"

# ==================== 数据接口 ====================
API_URL = "http://47.109.181.0/api/data"

# ==================== 数据加载 ====================
@st.cache_data(ttl=300)
def load_data():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(API_URL, timeout=10, headers=headers)
        resp.raise_for_status()
        raw = resp.json()

        data_list = None
        if isinstance(raw, list):
            data_list = raw
        elif isinstance(raw, dict):
            for key in ["data_list", "data", "list", "result", "records", "items"]:
                if key in raw and isinstance(raw[key], list):
                    data_list = raw[key]
                    break
            if data_list is None:
                for v in raw.values():
                    if isinstance(v, list):
                        data_list = v
                        break

        if not isinstance(data_list, list):
            raise ValueError(f"未找到列表数据，返回结构: {str(raw)[:200]}")

        df = pd.DataFrame(data_list)

        column_mapping = {
            "name": "姓名",
            "today_gift": "今日送花",
            "total_gift": "历史总数",
            "today_users": "今日人数",
            "delta_gift": "增量送花",
            "delta_users": "增量人数",
            "trend": "趋势"
        }
        df.rename(columns=column_mapping, inplace=True)

        if "姓名" not in df.columns:
            df["姓名"] = [f"明星{i}" for i in range(len(df))]
        if "今日送花" not in df.columns:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                df["今日送花"] = df[numeric_cols[0]]
            else:
                df["今日送花"] = 0

        df = df.sort_values("今日送花", ascending=False).reset_index(drop=True)
        return df

    except Exception as e:
        st.error(f"❌ 数据加载失败：{e}")
        return pd.DataFrame()

# ==================== UI 布局 ====================
st.title("🌸 百度送花数据实时看板")
st.caption(f"数据接口：`{API_URL}` | 缓存：5分钟 | 全屏水印：“{watermark_text}”")

col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    if st.button("🔄 手动刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("加载中..."):
    df = load_data()

if df.empty:
    st.stop()

st.info(f"📅 数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==================== 排名表格（排名从1开始） ====================
st.subheader("🏆 送花排行榜（按今日送花降序）")
df_display = df.copy()
df_display.insert(0, "排名", range(1, len(df_display) + 1))   # 排名从1开始，不是0
display_cols = ["排名", "姓名", "今日送花"]
if "历史总数" in df_display.columns:
    display_cols.append("历史总数")
if "今日人数" in df_display.columns:
    display_cols.append("今日人数")
if "增量送花" in df_display.columns:
    display_cols.append("增量送花")

st.dataframe(df_display[display_cols], use_container_width=True, height=400)

# ==================== 折线图 ====================
st.subheader("📈 近7日送花趋势（所有明星）")
trend_col = "趋势" if "趋势" in df.columns else ("trend" if "trend" in df.columns else None)

if trend_col:
    star_trends = {}
    all_dates = set()
    for _, row in df.iterrows():
        name = row["姓名"]
        trend_list = row.get(trend_col)
        if not trend_list or not isinstance(trend_list, list):
            continue
        gifts = {}
        for item in trend_list:
            date = item.get("date")
            gift = item.get("giftNum") or item.get("gift_num")
            if date and gift is not None:
                gifts[date] = gift
                all_dates.add(date)
        if gifts:
            star_trends[name] = gifts

    if star_trends and all_dates:
        sorted_dates = sorted(all_dates, key=lambda x: (int(x.split(".")[0]), int(x.split(".")[1])))
        fig, ax = plt.subplots(figsize=(12, 6))
        for name, gifts in star_trends.items():
            color = COLOR_MAP.get(name, DEFAULT_COLOR)
            values = [gifts.get(d) for d in sorted_dates]
            ax.plot(sorted_dates, values, marker='o', label=name, linewidth=2, color=color, markersize=4)
        ax.set_xlabel("日期")
        ax.set_ylabel("送花数量")
        ax.set_title("近7日送花趋势对比")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("暂无有效趋势数据")
else:
    st.info("当前数据不含趋势字段")

# ==================== 柱状图 ====================
st.subheader("📊 今日送花排行柱状图（按送花数量排序）")
df_chart = df.sort_values("今日送花", ascending=False).reset_index(drop=True)
bar_colors = [COLOR_MAP.get(name, DEFAULT_COLOR) for name in df_chart["姓名"]]
fig_width = max(8, len(df_chart) * 0.6)
fig, ax = plt.subplots(figsize=(fig_width, 6))
bars = ax.bar(df_chart["姓名"], df_chart["今日送花"], color=bar_colors)
ax.bar_label(bars, fmt='%d', label_type='edge', padding=2, fontsize=9)
ax.set_xticks(range(len(df_chart)))
ax.set_xticklabels(df_chart["姓名"], rotation=45, ha='right', fontsize=10)
ax.set_xlabel("明星")
ax.set_ylabel("送花数量")
ax.set_title("今日送花排行榜（专属颜色）")
plt.tight_layout()
st.pyplot(fig)

st.markdown("---")
st.caption("💡 手动刷新按钮可立即获取最新数据。水印文字：“陈浚铭四代第一门面”")