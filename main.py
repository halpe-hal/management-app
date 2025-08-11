# main.py

import streamlit as st
st.set_page_config(page_title="管理会計", layout="wide")

from auth import check_login, logout
from modules import dashboard, monthly_io, header, dashboard_excluding_tax

# --- セッション初期化 ---
if "menu" not in st.session_state:
    st.session_state["menu"] = "ダッシュボード"

# --- ログイン処理 ---
check_login()

# --- ヘッダー表示 ---
header.show()

# --- サイドバー ---
with st.sidebar:
    st.markdown("<h4>メニューを選択</h4>", unsafe_allow_html=True)
    menus = ["ダッシュボード", "【税抜】ダッシュボード", "グラフ分析", "月別入出金管理", "固定費管理", "設定"]

    for menu_item in menus:
        if st.button(menu_item, key=f"menu_{menu_item}"):
            st.session_state["menu"] = menu_item

    st.markdown("---")
    if st.button("ログアウト", key="logout"):
        logout()

# --- メインコンテンツ切替 ---
if st.session_state["menu"] == "ダッシュボード":
    dashboard.show_dashboard()
elif st.session_state["menu"] == "【税抜】ダッシュボード":
    dashboard_excluding_tax.show_dashboard_excluding_tax()
elif st.session_state["menu"] == "グラフ分析":
    from modules.graph_analysis import show_graph_analysis
    show_graph_analysis()
elif st.session_state["menu"] == "月別入出金管理":
    monthly_io.show_monthly_io()
elif st.session_state["menu"] == "固定費管理":
    from modules.fixed_expense_setting import handle_fixed_expense_setting
    handle_fixed_expense_setting()
elif st.session_state["menu"] == "設定":
    from modules.setting import show_setting_menu
    show_setting_menu()

# --- CSSカスタマイズ ---
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        margin-bottom: -10px;
        border: none;
        background-color: transparent;
        color: #333;
        font-weight: bold;
        padding: 0.5em 1em;
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #006a38;
        color: #ffffff;
        border: none;
    }
    section[data-testid="stSidebar"] div.stButton > button:focus {
        background-color: #006a38 !important;
        color: white !important;
        border: 1px solid #006a38 !important;
    }

    h4 {
        margin-top: -5%;
    }
    </style>
    """,
    unsafe_allow_html=True
)
