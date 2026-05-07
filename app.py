import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ==================== 页面配置 ====================
st.set_page_config(page_title="送花数据分析看板", page_icon="🌸", layout="wide")

# ==================== 自动刷新（每300秒 = 5分钟） ====================
st.markdown('<meta http-equiv="refresh" content="300">', unsafe_allow_html=True)

# ==================== 全屏平铺水印 ====================
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
    opacity: 0.22;
    transform: rotate(-20deg);
}}
.watermark-item {{
    font-size: 22px;
    font-weight: bold;
    color: #aaa;
    font-family: 'Microsoft YaHei', sans-serif;
    white-space: nowrap;
    text-align: center;
    padding: 30px 0;
    user-select: none;
}}
</style>
<div class="watermark-layer"></div>
<script>
    (function() {{
        const layer = document.querySelector('.watermark-layer');
        if (!layer) return;
        const itemWidth = 240;
        const itemHeight = 80;
        const cols = Math.ceil(window.innerWidth / itemWidth) + 1;
        const rows = Math.ceil(window.innerHeight / itemHeight) + 1;
        const total = cols * rows;
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

# ==================== 数据加载函数（返回df和获取时间） ====================
@st.cache_data(ttl=300)
def load_data():
    """
    获取数据，返回 (DataFrame, 数据获取时间)
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(API_URL, timeout=10, headers=headers)
        resp.raise_for_status()
        raw = resp.json()

        # 提取列表数据
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

        # 字段映射
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

        # 记录数据获取的时间（即数据“生成”时间）
        data_time = datetime.now()

        return df, data_time

    except Exception as e:
        st.error(f"❌ 数据加载失败：{e}")
        return pd.DataFrame(), None

# ==================== UI 布局 ====================
st.title("🌸 百度送花数据实时看板")
# 隐藏了数据接口显示
st.caption(f"缓存：5分钟 | 全屏水印：“{watermark_text}”")

# 手动刷新按钮（已注释，若需要可取消注释）
# col1, col2, col3 = st.columns([1, 4, 1])
# with col1:
#     if st.button("🔄 手动刷新数据", use_container_width=True):
#         st.cache_data.clear()
#         st.rerun()

with st.spinner("加载中..."):
    df, data_time = load_data()

if df.empty:
    st.stop()

# 显示数据时间（数据实际获取的时间，与缓存一致）
if data_time:
    st.info(f"📅 数据时间：{data_time.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.info("数据时间无法获取")

# ==================== 排名表格（隐藏行索引列） ====================
st.subheader("🏆 送花排行榜（按今日送花降序）")
df_display = df.copy()
df_display.insert(0, "排名", range(1, len(df_display) + 1))
display_cols = ["排名", "姓名", "今日送花"]
if "历史总数" in df_display.columns:
    display_cols.append("历史总数")
if "今日人数" in df_display.columns:
    display_cols.append("今日人数")
if "增量送花" in df_display.columns:
    display_cols.append("增量送花")

# 关键：index=False 去掉左侧默认的0,1,2...列
st.dataframe(df_display[display_cols], use_container_width=True, height=400, index=False)

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
        gifts_by_date = {}
        for item in trend_list:
            date = item.get("date")
            gift = item.get("giftNum") or item.get("gift_num")
            if date and gift is not None:
                gifts_by_date[date] = gift
                all_dates.add(date)
        if gifts_by_date:
            star_trends[name] = gifts_by_date

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
        st.info("暂无有效的趋势数据")
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
st.caption("💡 页面每5分钟自动刷新，数据同步更新。")