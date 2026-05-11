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
# データ管理
# ==========================================
def load_master_data():
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "events" not in data: data["events"] = []
                if "contents" not in data: data["contents"] = []
                if "members" not in data: data["members"] = []
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

# セッション状態でのリセット管理
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

# ==========================================
# アプリ画面の構築
# ==========================================
st.set_page_config(page_title="イベント反省アプリ Pro V3", layout="wide")

# サイドバー：項目管理
with st.sidebar:
    st.header("⚙️ 選択肢の管理")
    st.write("不要になった項目を削除できます。")
    del_event = st.multiselect("🗑️ イベント名の削除", master_data["events"])
    del_person = st.multiselect("🗑️ 記入者の削除", master_data["members"])
    del_content = st.multiselect("🗑️ 内容の削除", master_data["contents"])
    
    if st.button("選択した項目を削除", type="primary"):
        master_data["events"] = [e for e in master_data["events"] if e not in del_event]
        master_data["members"] = [m for m in master_data["members"] if m not in del_person]
        master_data["contents"] = [c for c in master_data["contents"] if c not in del_content]
        save_master_data(master_data)
        st.rerun()

st.title("💡 イベント反省＆分析アプリ Pro")
tab_input, tab_analysis = st.tabs(["📝 反省を入力", "📊 データを分析"])

# --- タブ1：入力画面 ---
with tab_input:
    # リセット用のユニークキーを生成
    reset_key = st.session_state.reset_counter
    
    st.header("今回の活動を振り返る")
    
    # 1. 基本情報
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_event = st.selectbox("📌 イベント名", master_data["events"] + ["+ 新規追加"], key=f"evt_{reset_key}")
        new_event = st.text_input("🆕 新規イベント名を入力", key=f"new_evt_{reset_key}") if selected_event == "+ 新規追加" else ""
    with col2:
        selected_person = st.selectbox("👤 記入者", master_data["members"] + ["+ 新規追加"], key=f"psn_{reset_key}")
        new_person = st.text_input("🆕 新規名前を入力", key=f"new_psn_{reset_key}") if selected_person == "+ 新規追加" else ""
    with col3:
        rating = st.select_slider("⭐ 満足度", options=[1, 2, 3, 4, 5], value=3, key=f"rate_{reset_key}")

    # 2. イベント内容の入力（改善：既存選択と新規入力を並列化）
    st.markdown("---")
    st.subheader("🏷️ 実施した内容")
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        current_contents = st.multiselect("リストから選択", master_data["contents"], key=f"cnt_{reset_key}")
    with col_c2:
        new_content_raw = st.text_input("🆕 新しい内容を追加（カンマ区切り可）", key=f"new_cnt_{reset_key}", help="例: スライム作り, 備品購入")

    # 全ての選択された内容（既存 + 新規）を統合して詳細入力欄を作成
    all_selected_contents = current_contents.copy()
    new_content_list = [c.strip() for c in new_content_raw.split(",") if c.strip()]
    all_selected_contents.extend(new_content_list)
    # 重複除去して整理
    all_selected_contents = sorted(list(set(all_selected_contents)))

    st.markdown("---")
    
    # 3. 項目ごとの詳細入力
    good_text_list = []
    bad_text_list = []

    if all_selected_contents:
        st.info("選択・追加した各内容について詳細を記入してください。")
        for content in all_selected_contents:
            with st.expander(f"【{content}】の振り返り", expanded=True):
                c_col1, c_col2 = st.columns(2)
                c_good = c_col1.text_area(f"👍 {content} で良かった点", key=f"good_{content}_{reset_key}")
                c_bad = c_col2.text_area(f"🔧 {content} の改善点", key=f"bad_{content}_{reset_key}")
                if c_good: good_text_list.append(f"[{content}] {c_good}")
                if c_bad: bad_text_list.append(f"[{content}] {c_bad}")

    # 4. 全体の振り返り
    st.subheader("📋 総括")
    col_og, col_ob = st.columns(2)
    overall_good = col_og.text_area("✨ 全体を通して良かった点", key=f"og_{reset_key}")
    overall_bad = col_ob.text_area("🤔 全体を通しての課題", key=f"ob_{reset_key}")
    
    if overall_good: good_text_list.append(f"[全体] {overall_good}")
    if overall_bad: bad_text_list.append(f"[全体] {overall_bad}")

    # 5. 操作ボタン
    st.markdown("<br>", unsafe_allow_url=True)
    btn_col1, btn_col2 = st.columns([2, 1])
    
    if btn_col1.button("🚀 この内容を保存する", use_container_width=True, type="primary"):
        final_event = new_event if selected_event == "+ 新規追加" else selected_event
        final_person = new_person if selected_person == "+ 新規追加" else selected_person
        
        if not final_event or not final_person or not all_selected_contents:
            st.error("入力が不足しています。イベント名、名前、実施内容は必須です。")
        else:
            # CSVデータの保存
            new_row = pd.DataFrame({
                "Timestamp": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "Event": [final_event],
                "Content": [", ".join(all_selected_contents)],
                "Person": [final_person],
                "Rating": [rating],
                "GoodPoints": ["\n".join(good_text_list)],
                "BadPoints": ["\n".join(bad_text_list)]
            })
            new_row.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            # マスターデータの更新（保存と同時に選択肢を更新）
            updated = False
            if final_event and final_event not in master_data["events"]:
                master_data["events"].append(final_event); updated = True
            if final_person and final_person not in master_data["members"]:
                master_data["members"].append(final_person); updated = True
            for c in all_selected_contents:
                if c not in master_data["contents"]:
                    master_data["contents"].append(c); updated = True
            
            if updated:
                save_master_data(master_data)
            
            st.success("保存しました！新しい項目も選択肢に追加されました。")
            st.balloons()
            # 画面を更新して新しい選択肢を反映し、入力をリセット
            st.session_state.reset_counter += 1
            st.rerun()

    # 🔄 リセットボタンの復活
    if btn_col2.button("🔄 入力をリセット", use_container_width=True):
        st.session_state.reset_counter += 1
        st.rerun()

# --- タブ2：分析画面 ---
with tab_analysis:
    st.header("振り返りデータの分析")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        if not df.empty:
            st.subheader("🔍 データの絞り込み")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                e_filter = st.multiselect("イベント名", df["Event"].unique())
            with col_f2:
                # Content列をバラして絞り込みの選択肢を作成
                all_c_set = set()
                df["Content"].dropna().str.split(", ").apply(lambda x: all_c_set.update(x))
                c_filter = st.multiselect("実施内容", sorted(list(all_c_set)))
            with col_f3:
                p_filter = st.multiselect("記入者", df["Person"].unique())
            
            filtered_df = df.copy()
            if e_filter: filtered_df = filtered_df[filtered_df["Event"].isin(e_filter)]
            if p_filter: filtered_df = filtered_df[filtered_df["Person"].isin(p_filter)]
            if c_filter:
                filtered_df = filtered_df[filtered_df["Content"].apply(lambda x: any(c in str(x) for c in c_filter))]
            
            st.dataframe(filtered_df.sort_values("Timestamp", ascending=False), use_container_width=True)
            
            if not filtered_df.empty:
                st.metric("平均満足度", f"{filtered_df['Rating'].mean():.2f} / 5.0")

            if st.button("🤖 AIで多角的に分析する", type="primary"):
                if not API_KEY:
                    st.error("APIキーが設定されていません")
                else:
                    with st.spinner("⏳ 成功パターンを分析中..."):
                        combined_text = ""
                        for _, row in filtered_df.iterrows():
                            combined_text += f"--- {row['Timestamp']} ---\n満足度:{row['Rating']} / 内容:{row['Content']}\n"
                            combined_text += f"【良】{row['GoodPoints']}\n【改】{row['BadPoints']}\n\n"
                        
                        prompt = f"以下の活動反省データを分析し、満足度向上のための成功要因と、具体的な次の一手を提案してください。\n\n{combined_text}"
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                        payload = {"contents": [{"parts": [{"text": prompt}]}]}
                        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})

                        try:
                            with urllib.request.urlopen(req) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                st.markdown("### 📊 AI分析レポート")
                                st.write(result['candidates'][0]['content']['parts'][0]['text'])
                        except Exception as e:
                            st.error(f"分析エラー: {str(e)}")
    else:
        st.info("データがありません。")
