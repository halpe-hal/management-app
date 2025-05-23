# modules/default_partners_setting.py

import streamlit as st
from db.default_partners import (
    get_default_partners,
    save_default_partner,
    update_default_partner,
    delete_default_partner
)
from db.account_items import get_account_items
from db.divisions import get_divisions
from db.expense_categories import get_variable_expense_categories


def handle_default_partners_setting():

    # --- 事業部タブ ---
    top_category_options = get_divisions()
    if not top_category_options:
        st.warning("事業部が未登録です。先に『事業部設定』から登録してください。")
        return

    top_tabs = st.tabs(top_category_options)

    for i, top_category in enumerate(top_category_options):
        with top_tabs[i]:
            selected_top_category = top_category

            # --- 費目カテゴリタブ（second_category） ---
            second_category_options = get_variable_expense_categories()
            if not second_category_options:
                st.warning("費目カテゴリが未登録です。先に『費目カテゴリ設定』から登録してください。")
                continue

            second_category_tabs = st.tabs(second_category_options)

            for j, selected_second_category in enumerate(second_category_options):
                with second_category_tabs[j]:

                    # --- 勘定科目リスト ---
                    account_options = get_account_items()
                    account_names = ["選択してください"] + [item["name"] for item in account_options]

                    # --- 支払方法リスト ---
                    payment_methods = ["選択してください", "現金", "クレジット", "銀行振込", "銀行引落", "その他"]


                    # --- データ取得 ---
                    all_data = get_default_partners()
                    filtered_rows = [
                        row for row in all_data
                        if row.get("top_category") == selected_top_category and row.get("second_category") == selected_second_category
                    ]

                    # --- 新規登録フォーム ---
                    st.markdown(f"#### {selected_second_category}カテゴリに新規登録")
                    with st.form(f"new_default_partner_{selected_top_category}_{selected_second_category}", clear_on_submit=True):
                        col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
                        with col1:
                            partner = st.text_input("取引先", placeholder="例：三和", key=f"partner_input_{selected_top_category}_{selected_second_category}")
                        with col2:
                            account = st.selectbox("勘定科目", account_names, key=f"account_select_{selected_top_category}_{selected_second_category}")
                        with col3:
                            detail = st.text_input("詳細", placeholder="例：厨房仕入", key=f"detail_input_{selected_top_category}_{selected_second_category}")
                        with col4:
                            payment = st.selectbox("支払方法", payment_methods, key=f"payment_select_{selected_top_category}_{selected_second_category}")

                        submitted = st.form_submit_button("登録")

                        if submitted:
                            if not partner:
                                st.warning("必須項目が未入力です。")
                            else:
                                status = save_default_partner(
                                    selected_second_category, partner, account, detail, payment, selected_top_category
                                )
                                if status == "success":
                                    st.success("登録しました。")
                                    st.rerun()
                                elif status == "duplicate":
                                    st.info("同じ内容がすでに登録されています。")
                                else:
                                    st.error("登録に失敗しました。")

                    # --- 表示：登録済み行 ---
                    if filtered_rows:
                        st.markdown("#### 登録済みデフォルト行")
                        for row in filtered_rows:
                            row_id = row["id"]
                            cols = st.columns([2, 2, 3, 2, 1, 1])
                            with cols[0]:
                                st.text_input("取引先", value=row["partner"], key=f"readonly_partner_{row_id}", disabled=True)
                            with cols[1]:
                                st.text_input("勘定科目", value=row["account"], key=f"readonly_account_{row_id}", disabled=True)
                            with cols[2]:
                                st.text_input("詳細", value=row["detail"], key=f"readonly_detail_{row_id}", disabled=True)
                            with cols[3]:
                                st.text_input("支払方法", value=row["payment"], key=f"readonly_payment_{row_id}", disabled=True)
                            with cols[4]:
                                if st.button("編集", key=f"edit_btn_{row_id}"):
                                    st.session_state[f"edit_mode_{row_id}"] = True
                            with cols[5]:
                                if st.button("削除", key=f"delete_btn_{row_id}"):
                                    delete_default_partner(row_id)
                                    st.success("削除しました。")
                                    st.rerun()

                            # --- 編集モード表示 ---
                            if st.session_state.get(f"edit_mode_{row_id}", False):
                                with st.expander("編集フォーム", expanded=True):
                                    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 2, 1])
                                    with col1:
                                        partner = st.text_input("取引先", value=row["partner"], key=f"edit_partner_{row_id}")
                                    with col2:
                                        account = st.selectbox(
                                            "勘定科目", account_names,
                                            index=account_names.index(row["account"]) if row["account"] in account_names else 0,
                                            key=f"edit_account_{row_id}"
                                        )
                                    with col3:
                                        detail = st.text_input("詳細", value=row["detail"], key=f"edit_detail_{row_id}")
                                    with col4:
                                        payment = st.selectbox(
                                            "支払方法", payment_methods,
                                            index=payment_methods.index(row["payment"]) if row["payment"] in payment_methods else 0,
                                            key=f"edit_payment_{row_id}"
                                        )
                                    with col5:
                                        if st.button("更新", key=f"update_btn_{row_id}"):
                                            update_default_partner(row_id, "partner", partner)
                                            update_default_partner(row_id, "account", account)
                                            update_default_partner(row_id, "detail", detail)
                                            update_default_partner(row_id, "payment", payment)
                                            st.success("更新しました。")
                                            st.session_state[f"edit_mode_{row_id}"] = False
                                            st.rerun()
                    else:
                        st.info("このカテゴリにはまだ登録がありません。")