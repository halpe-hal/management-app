# modules/account_items_setting.py

import streamlit as st
from db.account_items import (
    get_account_items,
    save_account_item,
    delete_account_item
)

def handle_account_items_setting():

    # --- 勘定科目の新規登録 ---
    st.markdown("#### 勘定科目の新規登録")
    with st.form("account_item_form", clear_on_submit=True):
        name = st.text_input("勘定科目名", placeholder="例：地代家賃、光熱費など")
        submitted = st.form_submit_button("登録")

        if submitted:
            if name.strip() == "":
                st.warning("空欄では登録できません。")
            else:
                status = save_account_item(name.strip())
                if status == "success":
                    st.success("勘定科目を登録しました。")
                    st.rerun()
                elif status == "duplicate":
                    st.info("同じ勘定科目がすでに登録されています。")
                else:
                    st.error("登録中にエラーが発生しました。")

    # --- 登録済み勘定科目一覧（削除確認付き） ---
    items = get_account_items()
    if items:
        st.markdown("#### 登録済みの勘定科目")
        for i, row in enumerate(items):
            cols = st.columns([6, 2, 2])
            with cols[0]:
                st.write(row["name"])
            with cols[1]:
                confirm_key = f"confirm_{row.get('id', 'none')}_{i}"
                confirm = st.checkbox("削除確認", key=confirm_key)
            with cols[2]:
                delete_key = f"delete_account_item_{row.get('id', 'none')}_{i}"
                if st.button("削除", key=delete_key):
                    if confirm:
                        delete_account_item(row["id"])
                        st.success("削除しました。")
                        st.rerun()
                    else:
                        st.warning("削除確認にチェックを入れてください。")
    else:
        st.info("まだ勘定科目が登録されていません。")
