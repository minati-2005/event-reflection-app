import streamlit as st
import pandas as pd
import os
import datetime
import json
import urllib.request
import urllib.error

# ==========================================
# 🌟 環境設定
# ==========================================
os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["PYTHONIOENCODING"] = "utf-8"

DATA_FILE = "reflections_v2.csv" 
MASTER_FILE = "master_data.json"

try:
    API_KEY = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    API_KEY = ""

# ==========================================
# データ管理関数
# ==========================================
def load_master_data():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in ["events", "contents", "members"]:
                    if key not in data: data[key] = []
                return data
        except:
            pass
    return {
        "events": ["あそびの日", "企画展示", "定例ミーティング"],
        "contents": ["シャボン玉", "会場設営", "集客・宣伝", "予算管理"],
        "members": ["上野 湊"]
    }

def save_master_data(data):
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Timestamp", "Event", "Content", "Person", "Rating", "GoodPoints", "BadPoints"])
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

master_data = load_master_data()

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

# ==========================================
# アプリ画面の構築
# ==========================================
st.set_page_config(page_title="イベント反省アプリ Pro V7", layout="wide")

st.title("💡 イベント反省＆分析アプリ Pro")
tab_input, tab_analysis = st.tabs(["📝 反省を入力", "📊 データを管理・分析"])

# --- タブ1：入力画面 ---
with tab_input:
    reset_key = st.session_state.reset_counter
    st.header("今回の活動を振り返る")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_event = st.selectbox("📌 イベント名", master_data["events"] + ["+ 新規追加"], key=f"evt_{reset_key}")
        new_event = st.text_input("🆕 新規イベント名を入力", key=f"new_evt_{reset_key}") if selected_event == "+ 新規追加" else ""
    with col2:
        selected_person = st.selectbox("👤 記入者", master_data["members"] + ["+ 新規追加"], key=f"psn_{reset_key}")
        new_person = st.text_input("🆕 新規名前を入力", key=f"new_psn_{reset_key}") if selected_person == "+ 新規追加" else ""
    with col3:
        rating = st.select_slider("⭐ 満足度", options=[1, 2, 3, 4, 5], value=3, key=f"rate_{reset_key}")

    st.markdown("---")
    st.subheader("🏷️ 実施した内容")
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        current_contents = st.multiselect("リストから選択", master_data["contents"], key=f"cnt_{reset_key}")
    with col_c2:
        new_content_raw = st.text_input("🆕 新しい内容を追加（カンマ区切り可）", key=f"new_cnt_{reset_key}")

    all_selected_contents = current_contents.copy()
    new_content_list = [c.strip() for c in new_content_raw.split(",") if c.strip()]
    all_selected_contents.extend(new_content_list)
    all_selected_contents = sorted(list(set(all_selected_contents)))

    st.markdown("---")
    
    # 🌟 修正：ブースごとに独立してデータを保持するためのリスト
    feedback_data = []

    if all_selected_contents:
        for content in all_selected_contents:
            with st.expander(f"【{content}】の振り返り", expanded=True):
                c_col1, c_col2 = st.columns(2)
                c_good = c_col1.text_area(f"👍 {content} で良かった点", key=f"good_{content}_{reset_key}")
                c_bad = c_col2.text_area(f"🔧 {content} の改善点", key=f
