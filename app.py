import streamlit as st
import pandas as pd
import os
import datetime
import json

# ==========================================
# 🌟 強制日本語設定（環境レベルでエラーを防ぐ）
# ==========================================
os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["PYTHONIOENCODING"] = "utf-8"

# ==========================================
# 🌟 設定
# ==========================================
DATA_FILE = "reflections.csv"
MASTER_FILE = "master_data.json"

# APIキーを金庫から取り出す
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = ""

# ==========================================
# データ読み込み・保存関数
# ==========================================
def load_master_data():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "events": ["新歓コンパ", "企画展示", "定例ミーティング"],
        "contents": ["会場設営", "集客・宣伝", "当日の進行", "予算管理", "片付け"],
        "members": ["自分"]
    }

def save_master_data(data):
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Timestamp", "Event", "Content", "Person", "Reflection"])
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

master_data = load_master_data()

# --- リセット用 ---
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0
def reset_inputs():
    st.session_state.reset_key += 1

# ==========================================
# アプリ画面の構築
# ==========================================
st.set_page_config(page_title="イベント反省アプリ", layout="wide")

with st.sidebar:
    st.header("⚙️ 選択肢の削除")
    del_event = st.multiselect("🗑️ 削除するイベント", master_data["events"])
    del_person = st.multiselect("🗑️ 削除する記入者", master_data["members"])
    del_content = st.multiselect("🗑️ 削除する内容", master_data["contents"])
    
    if st.button("選択した項目を完全に削除", type="primary"):
        master_data["events"] = [e for e in master_data["events"] if e not in del_event]
        master_data["members"] = [m for m in master_data["members"] if m not in del_person]
        master_data["contents"] = [c for c in master_data["contents"] if c not in del_content]
        save_master_data(master_data)
        st.success("削除しました！")
        st.rerun()

st.title("💡 イベント反省＆分析アプリ")
tab_input, tab_analysis = st.tabs(["📝 反省を入力", "📊 データを分析"])

# タブ1：入力
with tab_input:
    st.header("新しい反省を記録")
    k = st.session_state.reset_key
    col1, col2 = st.columns(2)
    with col1:
        selected_event = st.selectbox("📌 イベント名", master_data["events"] + ["+ 新規追加"], key=f"evt_{k}")
        new_event = st.text_input("🆕 新規イベント名", key=f"new_evt_{k}") if selected_event == "+ 新規追加" else ""
        selected_person = st.selectbox("👤 記入者", master_data["members"] + ["+ 新規追加"], key=f"psn_{k}")
        new_person = st.text_input("🆕 新規名前", key=f"new_psn_{k}") if selected_person == "+ 新規追加" else ""
    with col2:
        selected_contents = st.multiselect("🏷️ イベント内容", master_data["contents"], key=f"cnt_{k}")
        new_content_item = st.text_input("🆕 新規内容追加", key=f"new_cnt_{k}")
    reflection_text = st.text_area("✍️ 反省内容", height=200, key=f"txt_{k}")
    
    c1, c2 = st.columns(2)
    if c1.button("🚀 この内容を保存する", use_container_width=True):
        final_event = new_event if selected_event == "+ 新規追加" else selected_event
        final_person = new_person if selected_person == "+ 新規追加" else selected_person
        final_contents = selected_contents
        if new_content_item: final_contents.append(new_content_item)
        
        if not final_event or not reflection_text or not final_person:
            st.error("入力が不足しています")
        else:
            new_row = pd.DataFrame({
                "Timestamp": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "Event": [final_event],
                "Content": [", ".join(final_contents)],
                "Person": [final_person],
                "Reflection": [reflection_text]
            })
            new_row.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            # マスターデータ更新
            updated = False
            if final_event and final_event not in master_data["events"]:
                master_data["events"].append(final_event)
                updated = True
            if final_person and final_person not in master_data["members"]:
                master_data["members"].append(final_person)
                updated = True
            for c in final_contents:
                if c not in master_data["contents"]:
                    master_data["contents"].append(c); updated = True
            if updated: save_master_data(master_data)
            st.success("保存しました！")
            st.balloons()
    c2.button("🔄 入力をリセット", on_click=reset_inputs, use_container_width=True)

# タブ2：分析
with tab_analysis:
    st.header("これまでの反省を振り返る")
    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        if df.empty:
            st.info("データがありません。")
        else:
            st.subheader("🔍 絞り込み")
            f1, f2 = st.columns(2)
            event_filter = f1.multiselect("イベント", df["Event"].unique())
            person_filter = f2.multiselect("記入者", df["Person"].unique())
            
            filtered_df = df.copy()
            if event_filter: filtered_df = filtered_df[filtered_df["Event"].isin(event_filter)]
            if person_filter: filtered_df = filtered_df[filtered_df["Person"].isin(person_filter)]
            
            st.dataframe(filtered_df.sort_values("Timestamp", ascending=False), use_container_width=True)
            
if st.button("🤖 AIで分析する", type="primary"):
                if not API_KEY:
                    st.error("APIキーが設定されていません")
                else:
                    with st.spinner("⏳ AIが分析中..."):
                        # 🌟 送信データを徹底的にお掃除する
                        combined_text = ""
                        for _, row in filtered_df.iterrows():
                            # 各項目から改行や変な文字を除去して1行にまとめる
                            e = str(row['Event']).replace('\n', ' ')
                            p = str(row['Person']).replace('\n', ' ')
                            c = str(row['Content']).replace('\n', ' ')
                            r = str(row['Reflection']).replace('\n', ' ')
                            combined_text += f"イベント:{e} / 人:{p} / 内容:{c} / 反省:{r}\n"
                        
                        # 文字列をきれいに掃除（念のため）
                        combined_text = "".join(ch for ch in combined_text if ch.isprintable() or ch == '\n')

                        try:
                            import google.generativeai as genai
                            genai.configure(api_key=API_KEY)
                            
                            # 🌟 モデルを一番軽量な「flash-8b」に変えてみる（さらに高速化）
                            model = genai.GenerativeModel('gemini-1.5-flash-8b')
                            
                            prompt = f"以下のイベント反省データを分析し、共通の課題と対策を日本語で短くまとめてください。\n\n{combined_text}"
                            
                            # タイムアウト対策：一気に取得する
                            response = model.generate_content(prompt)
                            
                            if response.text:
                                st.markdown("### 📊 AI分析レポート")
                                st.write(response.text)
                            else:
                                st.warning("AIから有効な返答が得られませんでした。")

                        except Exception as e:
                            # エラー内容をより詳しく出すように変更
                            st.error(f"分析エラーが発生しました。詳細: {str(e)}")
