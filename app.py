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

# ==================== 智能解析数据 ====================
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
    """
    智能映射列名，区分总人数和增量人数。
    标准列名及优先级关键词：
    - 姓名: name, 姓名, star_name
    - 今日送花: today_gift, today, 今日送花, gift_today
    - 历史总数: total_gift, total, 历史总数, total_flowers
    - 今日总人数: today_users, total_users, people, user_count, 今日人数
    - 今日增量人数: delta_users, new_users, increase_users
    - 今日增量送花: delta_gift, delta, 增量送花
    - 趋势: trend, 趋势
    """
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
    
    # 去除可能因重名导致的重复列（保留第一个）
    for std_name in mapping_rules.keys():
        if std_name in df_renamed.columns:
            matching = [c for c in df_renamed.columns if c == std_name]
            if len(matching) > 1:
                keep_cols = [matching[0]] + [c for c in df_renamed.columns if c not in matching[1:]]
                df_renamed = df_renamed[keep_cols]
    return df_renamed

# ==================== 数据加载 ====================
@st.cache_data(ttl=300)
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

        # 必要列兜底
        if "姓名" not in df.columns:
            df["姓名"] = [f"明星{i}" for i in range(len(df))]
        if "今日送花" not in df.columns:
            num_cols = df.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                df["今日送花"] = df[num_cols[0]]
            else:
                df["今日送花"] = 0
        if "今日总人数" not in df.columns:
            # 尝试找任意数字列作为总人数（如果缺失则设为0）
            df["今日总人数"] = 0

        # 确保数值类型
        df["今日送花"] = pd.to_numeric(df["今日送花"], errors='coerce').fillna(0)
        df["今日总人数"] = pd.to_numeric(df["今日总人数"], errors='coerce').fillna(0)
        if "今日增量人数" in df.columns:
            df["今日增量人数"] = pd.to_numeric(df["今日增量人数"], errors='coerce').fillna(0)

        df = df.sort_values("今日送花", ascending=False).reset_index(drop=True)
        return df, data_time, time_source, None

    except Exception as e:
        return pd.DataFrame(), None, None, str(e)

# ==================== UI ====================
st.title("🌸 百度送花数据实时看板")
st.caption(f"缓存：5分钟 | 全屏水印：“{watermark_text}”")

with st.spinner("加载中..."):
    df, data_time, time_source, error = load_data()

if error:
    st.error(f"数据加载失败：{error}")
    st.stop()
if df.empty:
    st.warning("未获取到有效数据")
    st.stop()

# 显示更新时间
if data_time:
    if time_source == "api":
        st.info(f"📅 数据最后更新时间（接口提供）：{data_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info(f"📅 数据获取时间（本地）：{data_time.strftime('%Y-%m-%d %H:%M:%S')}")

# ==================== 表格 ====================
st.subheader("🏆 送花排行榜（按今日送花降序）")
df_display = df.copy()
df_display.insert(0, "排名", range(1, len(df_display) + 1))

display_cols = ["排名", "姓名", "今日送花", "今日总人数"]
if "历史总数" in df_display.columns:
    display_cols.append("历史总数")
if "今日增量人数" in df_display.columns:
    display_cols.append("今日增量人数")
if "今日增量送花" in df_display.columns:
    display_cols.append("今日增量送花")

html_table = df_display[display_cols].to_html(index=False)
st.markdown(html_table, unsafe_allow_html=True)

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
        try:
            sorted_dates = sorted(all_dates, key=lambda x: (int(x.split(".")[0]), int(x.split(".")[1])))
        except:
            sorted_dates = sorted(all_dates)
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
        st.info("暂无趋势数据")
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
st.caption("💡 页面每5分钟自动刷新，数据同步更新。表格中「今日总人数」为当日送花参与总人数。")

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