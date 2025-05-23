# modules/divisions_setting.py

import streamlit as st
from db.supabase_client import supabase
from db.divisions import (
    get_division_records,
    delete_division
)

def handle_division_setting():

    # --- 新規事業部の登録フォーム ---
    st.markdown("#### 事業部の新規登録")
    with st.form("division_form", clear_on_submit=True):
        new_div = st.text_input("事業部名", placeholder="例：新規開発事業部")
        submitted = st.form_submit_button("登録")

        if submitted:
            if new_div.strip() == "":
                st.warning("空欄では登録できません。")
            else:
                try:
                    supabase.table("divisions").insert({"name": new_div.strip()}).execute()
                    st.success("登録しました。")
                    st.rerun()
                except Exception as e:
                    st.error(f"登録に失敗しました：{e}")

    # --- 登録済みの事業部一覧（削除確認付き） ---
    divisions = get_division_records()
    if divisions:
        st.markdown("#### 登録済みの事業部")
        for row in divisions:
            cols = st.columns([6, 2, 2])
            with cols[0]:
                st.write(row["name"])
            with cols[1]:
                confirm = st.checkbox("削除確認", key=f"confirm_{row['id']}")
            with cols[2]:
                if st.button("削除", key=f"delete_division_{row['id']}"):
                    if confirm:
                        delete_division(row["id"])
                        st.success("削除しました。")
                        st.rerun()
                    else:
                        st.warning("削除確認にチェックを入れてください。")
    else:
        st.info("まだ事業部が登録されていません。")
