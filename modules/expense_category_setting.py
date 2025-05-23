# modules/expense_category_setting.py

import streamlit as st
from db.expense_categories import (
    get_expense_categories,
    add_expense_category,
    delete_expense_category,
    update_expense_category_order
)

def handle_expense_category_setting():
    st.markdown("### 費目カテゴリの新規登録", unsafe_allow_html=True)

    # --- 新規登録フォーム ---
    with st.form("add_expense_category_form", clear_on_submit=True):
        new_cat = st.text_input("カテゴリ名", placeholder="例：外注費、雑費 など")
        is_fixed = st.checkbox("固定費として登録")
        submitted = st.form_submit_button("登録")

        if submitted:
            if not new_cat.strip():
                st.warning("カテゴリ名を入力してください。")
            else:
                result = add_expense_category(new_cat.strip(), is_fixed)
                if result == "success":
                    st.success("カテゴリを登録しました。")
                    st.session_state.pop("category_order", None)  # ← 表示リセット
                    st.rerun()
                elif result == "duplicate":
                    st.info("同じカテゴリがすでに登録されています。")
                else:
                    st.error("登録中にエラーが発生しました。")

    # --- 並び順のセッション保存（初期化） ---
    if "category_order" not in st.session_state:
        categories = get_expense_categories()
        st.session_state.category_order = categories.copy()
    else:
        categories = st.session_state.category_order

    # --- 並び替えアクションの記録と実行 ---
    move_key = st.session_state.get("move_action", None)
    if move_key:
        action, idx = move_key.split("_")
        idx = int(idx)
        if action == "up" and idx > 0:
            categories[idx - 1], categories[idx] = categories[idx], categories[idx - 1]
            update_expense_category_order(categories)
        elif action == "down" and idx < len(categories) - 1:
            categories[idx + 1], categories[idx] = categories[idx], categories[idx + 1]
            update_expense_category_order(categories)
        del st.session_state["move_action"]
        st.rerun()

    # --- 並び替え・削除UI表示 ---
    if categories:
        st.markdown("#### 登録済みの費目カテゴリ（並び替え＆削除）")
        for i, cat in enumerate(categories):
            col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 2, 1])
            with col1:
                st.write(cat)
            with col2:
                if i > 0 and st.button("↑", key=f"up_btn_{i}_{cat}"):
                    st.session_state["move_action"] = f"up_{i}"
                    st.rerun()
            with col3:
                if i < len(categories) - 1 and st.button("↓", key=f"down_btn_{i}_{cat}"):
                    st.session_state["move_action"] = f"down_{i}"
                    st.rerun()
            with col4:
                confirm = st.checkbox("削除確認", key=f"confirm_del_{i}_{cat}")
            with col5:
                if st.button("削除", key=f"del_btn_{i}_{cat}"):
                    if confirm:
                        delete_expense_category(cat)
                        st.success("削除しました。")
                        st.session_state.category_order.remove(cat)
                        update_expense_category_order(st.session_state.category_order)
                        st.rerun()
                    else:
                        st.warning("削除確認にチェックを入れてください。")

        if st.button("並び順を初期状態に戻す"):
            st.session_state.category_order = get_expense_categories()
            update_expense_category_order(st.session_state.category_order)
            st.success("初期順に戻しました。")
    else:
        st.info("まだ費目カテゴリが登録されていません。")
