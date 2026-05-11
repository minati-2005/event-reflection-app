import streamlit as st
import pandas as pd
import os
import datetime
import json
import sys
import io

# 🌟 強制的に日本語(UTF-8)で処理させる設定（おまじない）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
# データ読み込み・保存関数（日本語対応を徹底）
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
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig') # 🌟 encodingを追加

master_data = load_master_data()

# --- リセット用の機能 ---
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0

def reset_inputs():
    st.session_state.reset_key += 1

# ==========================================
# アプリ画面の構築
# ==========================================
st.set_page_config(page_title="イベント反省アプリ", layout="wide")

# サイドバー：選択肢の削除
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

# ==========================================
# タブ1：反省の入力画面
# ==========================================
with tab_input:
    st.header("新しい反省を記録")
    k = st.session_state.reset_key
    
    col1, col2 = st.columns(2)
    with col1:
        selected_event = st.selectbox("📌 イベント名を選択", master_data["events"] + ["+ 新規追加"], key=f"evt_{k}")
        new_event = st.text_input("🆕 新しいイベント名を入力", key=f"new_evt_{k}") if selected_event == "+ 新規追加" else ""
        
        selected_person = st.selectbox("👤 記入者を選択", master_data["members"] + ["+ 新規追加"], key=f"psn_{k}")
        new_person = st.text_input("🆕 新しい名前を入力", key=f"new_psn_{k}") if selected_person == "+ 新規追加" else ""

    with col2:
        selected_contents = st.multiselect("🏷️ イベント内容（タグ付け）", master_data["contents"], key=f"cnt_{k}")
        new_content_item = st.text_input("🆕 リストにない内容を追加", key=f"new_cnt_{k}")

    reflection_text = st.text_area("✍️ 反省・気付き・課題などを入力", height=200, key=f"txt_{k}")
    
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        save_btn = st.button("🚀 この内容を保存する", use_container_width=True)
    with btn_col2:
        st.button("🔄 入力をリセット", on_click=reset_inputs, use_container_width=True)

    if save_btn:
        final_event = new_event if selected_event == "+ 新規追加" else selected_event
        final_person = new_person if selected_person == "+ 新規追加" else selected_person
        
        final_contents = selected_contents
        if new_content_item:
            final_contents.append(new_content_item)
        
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
            # 🌟 保存時の日本語設定を強化
            new_row.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            updated = False
            if final_event and final_event not in master_data["events"]:
                master_data["events"].append(final_event)
                updated = True
            if final_person and final_person not in master_data["members"]:
                master_data["members"].append(final_person)
                updated = True
            for c in final_contents:
                if c not in master_data["contents"]:
                    master_data["contents"].append(c)
                    updated = True
            
            if updated:
                save_master_data(master_data)
            st.success(f"保存しました！")
            st.balloons()

# ==========================================
# タブ2：蓄積データの分析画面
# ==========================================
with tab_analysis:
    st.header("これまでの反省を振り返る")
    
    try:
        # 🌟 読み込み時の日本語設定を強化
        df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        if df.empty:
            st.info("データがありません。")
        else:
            st.subheader("🔍 絞り込みと並び替え")
            
            all_contents = set()
            for c_str in df["Content"].dropna():
                for c in str(c_str).split(", "):
                    if c: all_contents.add(c)
            
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                event_filter = st.multiselect("イベント", df["Event"].unique())
            with f_col2:
                person_filter = st.multiselect("記入者", df["Person"].unique())
            with f_col3:
                content_filter = st.multiselect("内容", list(all_contents))
            
            sort_order = st.selectbox("順序", ["新しい順", "古い順"])
            
            filtered_df = df.copy()
            if event_filter: filtered_df = filtered_df[filtered_df["Event"].isin(event_filter)]
            if person_filter: filtered_df = filtered_df[filtered_df["Person"].isin(person_filter)]
            if content_filter:
                filtered_df = filtered_df[filtered_df["Content"].apply(lambda x: any(c in str(x) for c in content_filter))]
                
            if sort_order == "新しい順":
                filtered_df = filtered_df.sort_values("Timestamp", ascending=False)
            else:
                filtered_df = filtered_df.sort_values("Timestamp", ascending=True)
                
            st.dataframe(filtered_df, use_container_width=True)
            
            if st.button("🤖 AIで分析する", type="primary"):
                if not API_KEY:
                    st.error("APIキーが設定されていません")
                elif filtered_df.empty:
                    st.warning("分析するデータがありません。")
                else:
                    with st.spinner("⏳ AIがデータを分析中..."):
                        combined_text = ""
                        for _, row in filtered_df.iterrows():
                            combined_text += f"\n【{row['Event']} / {row['Person']}】\n内容: {row['Content']}\n反省: {row['Reflection']}\n"
                        
                        # 🌟 送信するプロンプト自体もUTF-8として扱う
                        prompt = f"以下のイベント反省データを分析し、共通の課題と具体的な対策をまとめてください。\n{combined_text}"
                        
                        try:
                            from google import genai
                            client = genai.Client(api_key=API_KEY)
                            # 🌟 モデル名は最新の gemini-2.0-flash を使用
                            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                            st.markdown("### 📊 AI分析レポート")
                            st.write(response.text)
                        except Exception as e:
                            # 🌟 エラー内容を詳しく表示
                            st.error(f"分析エラー: {str(e)}")
                        
    except Exception as e:
        st.error(f"読み込みエラー: {str(e)}")
