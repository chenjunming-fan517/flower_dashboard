import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.graph_objects as go

# ==================== 配置区域 ====================
AUTO_REFRESH_SECONDS = 30
CACHE_TTL_SECONDS = 25
# ================================================

st.set_page_config(page_title="送花数据分析看板", page_icon="🌸", layout="wide")
st.markdown(f'<meta http-equiv="refresh" content="{AUTO_REFRESH_SECONDS}">', unsafe_allow_html=True)

# ==================== 水印 ====================
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

# 颜色映射（折线图、柱状图使用）
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
API_URL = "http://47.109.181.0/api/data"

# ---------- 数据解析函数（保持不变） ----------
def smart_find_list(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ["data_list", "data", "list", "result", "records", "items", "rows"]:
            if key in obj and isinstance(obj[key], list):
                return obj[key]
        for v in obj.values():
            if isinstance(v, list):
                return v
    return None

def smart_extract_time(obj):
    if isinstance(obj, dict):
        for key in ["update_time", "last_update", "data_time", "timestamp", "time"]:
            if key in obj:
                val = obj[key]
                if isinstance(val, str):
                    try:
                        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                    except:
                        pass
    return None

def auto_map_columns(df):
    mapping_rules = {
        "姓名": ["name", "姓名", "star_name"],
        "今日送花": ["today_gift", "today", "今日送花", "gift_today", "flower_today"],
        "历史总数": ["total_gift", "total", "历史总数", "total_flowers"],
        "今日总人数": ["today_users", "total_users", "people", "user_count", "today_people", "今日人数"],
        "今日增量人数": ["delta_users", "new_users", "increase_users", "增量人数"],
        "今日增量送花": ["delta_gift", "delta", "增量送花"],
        "趋势": ["trend", "趋势"]
    }
    rename_dict = {}
    used_cols = set()
    for std_name, keywords in mapping_rules.items():
        for col in df.columns:
            if col in used_cols:
                continue
            col_lower = col.lower()
            if any(kw in col_lower for kw in keywords):
                rename_dict[col] = std_name
                used_cols.add(col)
                break
    df_renamed = df.rename(columns=rename_dict)
    for std_name in mapping_rules.keys():
        if std_name in df_renamed.columns:
            matching = [c for c in df_renamed.columns if c == std_name]
            if len(matching) > 1:
                keep_cols = [matching[0]] + [c for c in df_renamed.columns if c not in matching[1:]]
                df_renamed = df_renamed[keep_cols]
    return df_renamed

@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_data():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(API_URL, timeout=10, headers=headers)
        resp.raise_for_status()
        raw = resp.json()
        data_time = smart_extract_time(raw)
        time_source = "api" if data_time else "local"
        if data_time is None:
            data_time = datetime.now()
        data_list = smart_find_list(raw)
        if not data_list:
            raise ValueError("未找到列表数据")
        df = pd.DataFrame(data_list)
        if df.empty:
            raise ValueError("列表为空")
        df = auto_map_columns(df)
        if "姓名" not in df.columns:
            df["姓名"] = [f"明星{i}" for i in range(len(df))]
        if "今日送花" not in df.columns:
            num_cols = df.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                df["今日送花"] = df[num_cols[0]]
            else:
                df["今日送花"] = 0
        if "今日总人数" not in df.columns:
            df["今日总人数"] = 0
        df["今日送花"] = pd.to_numeric(df["今日送花"], errors='coerce').fillna(0)
        df["今日总人数"] = pd.to_numeric(df["今日总人数"], errors='coerce').fillna(0)
        if "今日增量人数" in df.columns:
            df["今日增量人数"] = pd.to_numeric(df["今日增量人数"], errors='coerce').fillna(0)
        if "今日增量送花" in df.columns:
            df["今日增量送花"] = pd.to_numeric(df["今日增量送花"], errors='coerce').fillna(0)
        df["人均送花"] = df.apply(lambda row: round(row["今日送花"] / row["今日总人数"], 2) if row["今日总人数"] > 0 else 0, axis=1)
        df = df.sort_values("今日送花", ascending=False).reset_index(drop=True)
        return df, data_time, time_source, None
    except Exception as e:
        return pd.DataFrame(), None, None, str(e)

# ==================== 界面 ====================
st.title("🌸 百度送花数据实时看板")
st.caption(f"缓存：{CACHE_TTL_SECONDS}秒 | 自动刷新：{AUTO_REFRESH_SECONDS}秒 | 全屏水印：“{watermark_text}”")

with st.spinner("加载中..."):
    df, data_time, time_source, error = load_data()

if error:
    st.error(f"数据加载失败：{error}")
    st.stop()
if df.empty:
    st.warning("未获取到有效数据")
    st.stop()

if data_time:
    if time_source == "api":
        st.info(f"📅 数据最后更新时间（接口提供）：{data_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info(f"📅 数据获取时间（本地）：{data_time.strftime('%Y-%m-%d %H:%M:%S')}")

# ==================== 表格（两行结构，简单可靠） ====================
st.subheader("🏆 送花排行榜")

def fmt_num(n):
    return f"{int(n):,}"

table_html = """
<style>
.rank-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
}
.rank-table th, .rank-table td {
    border: 1px solid #d1d5db;
    padding: 8px;
    text-align: left;
    vertical-align: top;
}
.rank-table th {
    background-color: #f3f4f6;
    font-weight: 600;
}
.rank-table .main-row td {
    background-color: #ffffff;
}
.rank-table .sub-row td {
    background-color: #f9fafb;
    font-size: 12px;
    color: #4b5563;
}
.rank-table .delta {
    color: #10b981;
    font-weight: 500;
}
</style>
<table class="rank-table">
    <thead>
        <tr><th>名称</th><th>今日送花</th><th>今日人数</th><th>人均</th></tr>
    </thead>
    <tbody>
"""

for _, row in df.iterrows():
    name = row["姓名"]
    today = fmt_num(row["今日送花"])
    people = fmt_num(row["今日总人数"])
    avg = row["人均送花"]
    total_history = fmt_num(row["历史总数"]) if "历史总数" in row else "0"
    delta_gift = int(row["今日增量送花"]) if "今日增量送花" in row else 0
    delta_people = int(row["今日增量人数"]) if "今日增量人数" in row else 0

    # 主行
    table_html += f"""
        <tr class="main-row">
            <td>{name}</td>
            <td>{today}</td>
            <td>{people}</td>
            <td>{avg}</td>
        </tr>
    """
    # 副行
    gift_delta_html = f'<span class="delta">↑ {fmt_num(delta_gift)}</span>' if delta_gift > 0 else ''
    people_delta_html = f'<span class="delta">↑ {fmt_num(delta_people)}</span>' if delta_people > 0 else ''
    table_html += f"""
        <tr class="sub-row">
            <td>📜 历史总数 {total_history}</td>
            <td>{gift_delta_html}</td>
            <td>{people_delta_html}</td>
            <td><br/></td>
        </tr>
    """

table_html += """
    </tbody>
</table>
"""
st.markdown(table_html, unsafe_allow_html=True)

# ==================== 折线图 ====================
st.subheader("📈 近7日送花趋势对比")
trend_col = "趋势" if "趋势" in df.columns else ("trend" if "trend" in df.columns else None)

if trend_col:
    trend_data = []
    for _, row in df.iterrows():
        name = row["姓名"]
        trend_list = row.get(trend_col)
        if not trend_list or not isinstance(trend_list, list):
            continue
        for item in trend_list:
            date = item.get("date")
            gift = item.get("giftNum") or item.get("gift_num")
            if date and gift is not None:
                trend_data.append({"明星": name, "日期": date, "送花数量": gift})
    if trend_data:
        trend_df = pd.DataFrame(trend_data)
        try:
            trend_df["日期序"] = trend_df["日期"].apply(lambda x: (int(x.split(".")[0]), int(x.split(".")[1])))
            trend_df = trend_df.sort_values("日期序").drop("日期序", axis=1)
        except:
            trend_df = trend_df.sort_values("日期")
        all_dates = sorted(trend_df["日期"].unique())
        fig = go.Figure()
        for name in trend_df["明星"].unique():
            subset = trend_df[trend_df["明星"] == name].sort_values("日期")
            color = COLOR_MAP.get(name, DEFAULT_COLOR)
            fig.add_trace(go.Scatter(
                x=subset["日期"],
                y=subset["送花数量"],
                mode='lines+markers',
                name=name,
                line=dict(color=color, width=2),
                marker=dict(size=4)
            ))
        fig.update_xaxes(tickvals=all_dates, ticktext=all_dates, tickangle=0, fixedrange=True, showgrid=True, gridcolor='lightgray')
        fig.update_yaxes(fixedrange=True, showgrid=True, gridcolor='lightgray')
        fig.update_layout(
            autosize=True, margin=dict(l=20, r=20, t=40, b=40),
            legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(0,0,0,0)', title=None, font=dict(color='black', size=10), orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            xaxis_title="日期", yaxis_title="送花数量",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        config = {'displayModeBar': False, 'scrollZoom': False}
        st.plotly_chart(fig, use_container_width=True, config=config)
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
ax.set_title("今日送花排行榜")
plt.tight_layout()
st.pyplot(fig)

st.markdown("---")
st.caption(f"💡 页面每 {AUTO_REFRESH_SECONDS} 秒自动刷新，数据缓存 {CACHE_TTL_SECONDS} 秒。")