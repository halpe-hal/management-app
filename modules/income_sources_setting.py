# modules/income_sources_setting.py

import streamlit as st
from db.income_sources import get_income_sources, add_income_source, delete_income_source, update_income_source
from db.divisions import get_divisions
import pandas as pd

def handle_income_sources_setting():
    top_categories = get_divisions()
    if not top_categories:
        st.warning("事業部が未登録です。先に『事業部設定』から登録してください。")
        return

    tax_rate_options = ["売上10%", "売上8%", "その他売上10%", "その他売上8%"]
    payment_methods = ["選択してください", "現金", "銀行振込", "クレジット", "paygent", "paypal", "その他"]

    top_tabs = st.tabs(top_categories)

    for i, top_category in enumerate(top_categories):
        tab_key = top_category.replace(" ", "_")
        with top_tabs[i]:
            st.markdown(f"#### {top_category} の入金元を新規登録")

            with st.form(f"income_source_form_{tab_key}", clear_on_submit=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    partner = st.text_input("入金元", placeholder="例：Uber", key=f"partner_{tab_key}")
                with col2:
                    expected_amount = st.number_input("入金予定額", min_value=0, step=1000, key=f"expected_{tab_key}")
                with col3:
                    received_amount = st.number_input("入金済額", min_value=0, step=1000, key=f"received_{tab_key}")
                with col4:
                    payment = st.selectbox("入金手段", payment_methods, key=f"payment_{tab_key}")
                col5 = st.columns(1)[0]
                with col5:
                    tax_rate = st.selectbox("税率", tax_rate_options, key=f"tax_rate_{tab_key}")

                detail = st.text_input("詳細（任意）", key=f"detail_{tab_key}")
                submitted = st.form_submit_button("登録")

                if submitted:
                    if not partner:
                        st.warning("入金元を入力してください。")
                    else:
                        status = add_income_source({
                            "top_category": top_category,
                            "partner": partner,
                            "expected_amount": expected_amount,
                            "received_amount": received_amount,
                            "payment": payment,
                            "tax_rate": tax_rate,
                            "detail": detail,
                        })
                        if status == "success":
                            st.success("入金元を登録しました。")
                            st.rerun()
                        else:
                            st.error("登録に失敗しました。")

            all_data = get_income_sources()
            filtered_rows = [row for row in all_data if row["top_category"] == top_category]

            if filtered_rows:
                st.markdown("#### 登録済み入金元")
                for row in filtered_rows:
                    row_id = row["id"]
                    prefix = tab_key
                    cols = st.columns([2, 2, 1.5, 1.5, 2, 2, 1])
                    with cols[0]:
                        st.text_input("入金元", value=row["partner"], key=f"{prefix}_readonly_partner_{row_id}", disabled=True)
                    with cols[1]:
                        st.text_input("詳細", value=row["detail"], key=f"{prefix}_readonly_detail_{row_id}", disabled=True)
                    with cols[2]:
                        st.number_input("予定額", value=row["expected_amount"], step=1000, key=f"{prefix}_readonly_expected_{row_id}", disabled=True)
                    with cols[3]:
                        st.number_input("済額", value=row["received_amount"], step=1000, key=f"{prefix}_readonly_received_{row_id}", disabled=True)
                    with cols[4]:
                        st.text_input("入金手段", value=row["payment"], key=f"{prefix}_readonly_payment_{row_id}", disabled=True)
                    with cols[5]:
                        st.text_input("税率", value=row["tax_rate"], key=f"{prefix}_readonly_tax_rate_{row_id}", disabled=True)
                    with cols[6]:
                        if st.button("編集", key=f"{prefix}_edit_btn_{row_id}"):
                            st.session_state[f"{prefix}_edit_mode_{row_id}"] = True
                        if st.button("削除", key=f"{prefix}_delete_btn_{row_id}"):
                            delete_income_source(row_id)
                            st.success("削除しました。")
                            st.rerun()

                    if st.session_state.get(f"{prefix}_edit_mode_{row_id}", False):
                        with st.expander("編集フォーム", expanded=True):
                            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
                            with col1:
                                partner = st.text_input("入金元", value=row["partner"], key=f"{prefix}_edit_partner_{row_id}")
                            with col2:
                                detail = st.text_input("詳細", value=row["detail"], key=f"{prefix}_edit_detail_{row_id}")
                            with col3:
                                expected_amount = st.number_input("予定額", value=row["expected_amount"], step=1000, key=f"{prefix}_edit_expected_{row_id}")
                            with col4:
                                received_amount = st.number_input("済額", value=row["received_amount"], step=1000, key=f"{prefix}_edit_received_{row_id}")
                            with col5:
                                payment = st.selectbox(
                                    "入金手段", payment_methods,
                                    index=payment_methods.index(row["payment"]) if row["payment"] in payment_methods else 0,
                                    key=f"{prefix}_edit_payment_{row_id}"
                                )
                            with col6:
                                tax_rate = st.selectbox(
                                    "税率", tax_rate_options,
                                    index=tax_rate_options.index(row["tax_rate"]) if row["tax_rate"] in tax_rate_options else 0,
                                    key=f"{prefix}_edit_tax_rate_{row_id}"
                                )
                            if st.button("更新", key=f"{prefix}_update_btn_{row_id}"):
                                update_income_source(row_id, "partner", partner)
                                update_income_source(row_id, "detail", detail)
                                update_income_source(row_id, "expected_amount", expected_amount)
                                update_income_source(row_id, "received_amount", received_amount)
                                update_income_source(row_id, "payment", payment)
                                update_income_source(row_id, "tax_rate", tax_rate)
                                st.success("更新しました。")
                                st.session_state[f"{prefix}_edit_mode_{row_id}"] = False
                                st.rerun()
            else:
                st.info(f"{top_category} の入金元はまだ登録されていません。")
