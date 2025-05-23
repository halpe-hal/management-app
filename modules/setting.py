# modules/setting.py

import streamlit as st
from modules.account_items_setting import handle_account_items_setting
from modules.default_partners_setting import handle_default_partners_setting
from modules.divisions_setting import handle_division_setting
from modules.expense_category_setting import handle_expense_category_setting
from modules.income_sources_setting import handle_income_sources_setting
from modules.expense_targets_setting import handle_expense_targets_setting

def show_setting_menu():
    st.markdown("## 設定")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["事業部設定", "勘定科目設定", "費目設定", "目標比率設定", "取引先デフォルト設定", "入金元デフォルト設定"])
    with tab1:
        handle_division_setting()
    with tab2:
        handle_account_items_setting()
    with tab3:
        handle_expense_category_setting()
    with tab4:
        handle_expense_targets_setting()
    with tab5:
        handle_default_partners_setting()
    with tab6:
        handle_income_sources_setting()
