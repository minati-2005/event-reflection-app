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

DATA_FILE = "reflections_v2.csv" # 構造が変わるため新ファイル名に
MASTER_FILE = "master_data.json"

try:
    API_KEY = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    API_KEY = ""

# ==========================================
# データ管理
# ==========================================
def load_master_data():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "events": ["あそびの日", "企画展示", "定例ミーティング"],
        "contents": ["シャボン玉", "会場設営", "集客・宣伝", "予算管理"],
        "members": ["自分"]
    }

def save_master_data(data):
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# CSVの初期化（新しい列構成）
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Timestamp", "Event", "Content", "Person", "Rating", "GoodPoints", "BadPoints"])
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

master_data = load_master_data()

if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0
def reset_inputs():
    st.session_state.reset_key += 1

# ==========================================
# アプリ画面
# ==========================================
st.set_page_config(page_title="イベント反省アプリ Pro", layout="wide")

with st.sidebar:
    st.header("⚙️ 設定")
    if st.button("選択肢の管理画面を開く"):
        st.info("サイドバーで項目削除ができる機能を維持しています")
    
    del_event = st.multiselect("🗑️ 削除するイベント", master_data["events"])
    del_person = st.multiselect("🗑️ 削除する記入者", master_data["members"])
    del_content = st.multiselect("🗑️ 削除する内容", master_data["contents"])
    
    if st.button("選択項目を削除", type="primary"):
        master_data["events"] = [e for e in master_data["events"] if e not in del_event]
        master_data["members"] = [m for m in master_data["members"] if m not in del_person]
        master_data["contents"] = [c for c in master_data["contents"] if c not in del_content]
        save_master_data(master_data)
        st.rerun()

st.title("💡 イベント反省＆分析アプリ Pro")
tab_input, tab_analysis = st.tabs(["📝 反省を入力", "📊 データを分析"])

# --- タブ1：入力 ---
with tab_input:
    k = st.session_state.reset_key
    st.header("今回の活動を振り返る")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_event = st.selectbox("📌 イベント名", master_data["events"] + ["+ 新規追加"], key=f"evt_{k}")
        new_event = st.text_input("🆕 新規イベント名", key=f"new_evt_{k}") if selected_event == "+ 新規追加" else ""
        selected_person = st.selectbox("👤 記入者", master_data["members"] + ["+ 新規追加"], key=f"psn_{k}")
        new_person = st.text_input("🆕 新規名前", key=f"new_psn_{k}") if selected_person == "+ 新規追加" else ""
    
    with col2:
        rating = st.select_slider("⭐ 自身の満足度", options=[1, 2, 3, 4, 5], value=3, key=f"rate_{k}")
        selected_contents = st.multiselect("🏷️ 実施した内容（複数選択可）", master_data["contents"], key=f"cnt_{k}")
        new_content_item = st.text_input("🆕 新しい内容を追加", key=f"new_cnt_{k}")

    st.divider()
    
    # 良かった点・改善点の入力エリア
    good_text_list = []
    bad_text_list = []

    if selected_contents:
        st.subheader("📋 項目ごとの振り返り")
        for content in selected_contents:
            with st.expander(f"【{content}】の詳細", expanded=True):
                c_good = st.text_area(f"👍 {content} で良かった点・成功要因", key=f"good_{content}_{k}")
                c_bad = st.text_area(f"🔧 {content} の課題・改善点", key=f"bad_{content}_{k}")
                if c_good: good_text_list.append(f"[{content}] {c_good}")
                if c_bad: bad_text_list.append(f"[{content}] {c_bad}")

    st.subheader("総括")
    overall_good = st.text_area("✨ 全体を通して良かった点", key=f"og_{k}")
    overall_bad = st.text_area("🤔 全体を通しての課題", key=f"ob_{k}")
    
    if overall_good: good_text_list.append(f"[全体] {overall_good}")
    if overall_bad: bad_text_list.append(f"[全体] {overall_bad}")

    if st.button("🚀 この内容を保存する", use_container_width=True, type="primary"):
        final_event = new_event if selected_event == "+ 新規追加" else selected_event
        final_person = new_person if selected_person == "+ 新規追加" else selected_person
        final_contents = selected_contents
        if new_content_item: final_contents.append(new_content_item)
        
        if not final_event or not final_person or not good_text_list:
            st.error("入力が不足しています（イベント名、名前、良かった点は必須です）")
        else:
            new_row = pd.DataFrame({
                "Timestamp": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "Event": [final_event],
                "Content": [", ".join(final_contents)],
                "Person": [final_person],
                "Rating": [rating],
                "GoodPoints": ["\n".join(good_text_list)],
                "BadPoints": ["\n".join(bad_text_list)]
            })
            new_row.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            # マスターデータ更新
            updated = False
            if final_event and final_event not in master_data["events"]:
                master_data["events"].append(final_event); updated = True
            if final_person and final_person not in master_data["members"]:
                master_data["members"].append(final_person); updated = True
            for c in final_contents:
                if c not in master_data["contents"]:
                    master_data["contents"].append(c); updated = True
            if updated: save_master_data(master_data)
            st.success("保存しました！")
            st.balloons()

# --- タブ2：分析 ---
with tab_analysis:
    st.header("振り返りデータの分析")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        if not df.empty:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                e_filter = st.multiselect("イベント", df["Event"].unique())
            with col_f2:
                # 複数項目が入っているContent列をバラしてユニークなリストを作成
                all_contents = set()
                df["Content"].str.split(", ").apply(lambda x: all_contents.update(x) if isinstance(x, list) else None)
                c_filter = st.multiselect("内容", sorted(list(all_contents)))
            with col_f3:
                p_filter = st.multiselect("記入者", df["Person"].unique())
            
            filtered_df = df.copy()
            if e_filter: filtered_df = filtered_df[filtered_df["Event"].isin(e_filter)]
            if p_filter: filtered_df = filtered_df[filtered_df["Person"].isin(p_filter)]
            if c_filter:
                # コンテンツフィルタ：選択されたいずれかの内容が含まれる行を抽出
                filtered_df = filtered_df[filtered_df["Content"].apply(lambda x: any(c in str(x) for c in c_filter))]
            
            st.dataframe(filtered_df.sort_values("Timestamp", ascending=False), use_container_width=True)
            
            # 平均満足度の表示
            if not filtered_df.empty:
                avg_rate = filtered_df["Rating"].mean()
                st.metric("平均満足度", f"{avg_rate:.2f} / 5.0")

            if st.button("🤖 AIで多角的に分析する", type="primary"):
                if not API_KEY:
                    st.error("APIキーが設定されていません")
                else:
                    with st.spinner("⏳ 良かった点と改善点を整理中..."):
                        combined_text = ""
                        for _, row in filtered_df.iterrows():
                            combined_text += f"--- {row['Timestamp']} ---\n"
                            combined_text += f"満足度:{row['Rating']} / 内容:{row['Content']}\n"
                            combined_text += f"【良かった点】\n{row['GoodPoints']}\n"
                            combined_text += f"【課題・改善点】\n{row['BadPoints']}\n\n"
                        
                        prompt = f"""
                        以下のイベント反省データを分析してください。
                        1. 満足度と内容の相関関係（何が満足度を上げているか）
                        2. 複数の活動に共通する「成功パターン」の言語化
                        3. 繰り返し現れる「課題」と、それを解決するための具体的なネクストアクション
                        
                        データを元に、論理的かつ前向きなアドバイスを日本語で回答してください。
                        
                        {combined_text}
                        """

                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                        payload = {"contents": [{"parts": [{"text": prompt}]}]}
                        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})

                        try:
                            with urllib.request.urlopen(req) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                answer = result['candidates'][0]['content']['parts'][0]['text']
                                st.markdown("### 📊 拡張AI分析レポート")
                                st.write(answer)
                        except Exception as e:
                            st.error(f"分析エラー: {str(e)}")
