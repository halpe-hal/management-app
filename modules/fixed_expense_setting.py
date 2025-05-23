# modules/fixed_expense_setting.py

import streamlit as st
from db.fixed_categories import (
    get_fixed_categories,
    save_fixed_category,
    delete_fixed_category
)
from db.account_items import get_account_items
from db.fixed_categories import update_fixed_category
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
from db.divisions import get_divisions
from db.expense_categories import get_fixed_expense_categories

def handle_fixed_expense_setting():
    st.markdown("## 固定費の管理", unsafe_allow_html=True)

    top_category_options = get_divisions()
    if not top_category_options:
        st.warning("事業部が未登録です。先に『事業部設定』から登録してください。")
        return

    # --- タブ切り替えで事業部を表示 ---
    top_tabs = st.tabs(top_category_options)

    for i, selected_top_category in enumerate(top_category_options):
        with top_tabs[i]:
            account_options = get_account_items()
            account_names = ["選択してください"] + [item["name"] for item in account_options]

            fixed_second_categories = get_fixed_expense_categories()
            second_category_options = ["選択してください"] + fixed_second_categories

            st.markdown(f"#### {selected_top_category}カテゴリの固定費を新規登録")
            with st.form(f"fixed_expense_form_{selected_top_category}", clear_on_submit=True):
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    second_category = st.selectbox("費目（必須）", second_category_options, key=f"second_category_{selected_top_category}")
                with col2:
                    partner = st.text_input("支払先", placeholder="例：ビル管理会社", key=f"partner_{selected_top_category}")
                with col3:
                    account = st.selectbox("勘定科目", account_names, key=f"account_{selected_top_category}")

                col4, col5, col6 = st.columns([2, 2, 2])
                with col4:
                    detail = st.text_input("内容詳細", placeholder="例：1階テナント", key=f"detail_{selected_top_category}")
                with col5:
                    payment = st.selectbox("支払方法", ["現金", "クレジットカード", "銀行振込", "銀行引落", "その他"], key=f"payment_{selected_top_category}")
                with col6:
                    cost_input = st.text_input("金額（円）", placeholder="例：50000", key=f"cost_{selected_top_category}")

                submitted = st.form_submit_button("登録")

                if submitted:
                    if not partner:
                        st.error("支払先を入力してください。")
                    elif account == "選択してください":
                        st.error("勘定科目を選択してください。")
                    elif second_category == "選択してください":
                        st.error("費目を選択してください。")
                    elif not cost_input:
                        st.error("金額を入力してください。")
                    elif not cost_input.replace(",", "").isdigit():
                        st.error("金額は数字で入力してください。")
                    else:
                        cost = float(cost_input.replace(",", ""))
                        status = save_fixed_category(
                            partner=partner,
                            account=account,
                            detail=detail,
                            payment=payment,
                            cost=cost,
                            top_category=selected_top_category,
                            second_category=second_category
                        )
                        if status == "success":
                            st.success("固定費を登録しました。")
                            st.rerun()
                        elif status == "duplicate":
                            st.info("同じ内容の固定費がすでに登録されています。")
                        else:
                            st.error("登録中に予期せぬエラーが発生しました。")

            # --- 一覧表示 ---
            fixed = get_fixed_categories()
            filtered = [f for f in fixed if f["top_category"] == selected_top_category]

            if filtered:
                st.markdown(f"#### {selected_top_category}カテゴリの固定費一覧")

                df = pd.DataFrame([
                    {
                        "id": row["id"],
                        "費目": row["second_category"],
                        "支払先": row["partner"],
                        "勘定科目": row["account"],
                        "詳細": row["detail"] or "",
                        "支払方法": row["payment"],
                        "金額": row["cost"],
                        "操作": "（なし）"
                    }
                    for row in filtered
                ])

                payment_methods = ["現金", "クレジットカード", "銀行振込", "銀行引落", "その他"]

                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True)
                gb.configure_column("費目", cellEditor="agSelectCellEditor", cellEditorParams={"values": second_category_options})
                gb.configure_column("勘定科目", cellEditor="agSelectCellEditor", cellEditorParams={"values": account_names[1:]})
                gb.configure_column("支払方法", cellEditor="agSelectCellEditor", cellEditorParams={"values": payment_methods})
                gb.configure_column("操作", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["（なし）", "編集", "削除"]})
                gb.configure_column("id", hide=True)

                grid_options = gb.build()

                response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    fit_columns_on_grid_load=True,
                    height=35 * len(df) + 40,
                    key=f"aggrid_{selected_top_category}"  # ← keyを一意に
                )

                updated_df = response["data"]

                if st.button("一覧を更新する", key=f"update_button_{selected_top_category}"):
                    updated = 0
                    deleted = 0
                    for _, row in updated_df.iterrows():
                        id_ = int(row["id"])
                        action = row["操作"]
                        if action == "削除":
                            delete_fixed_category(id_)
                            deleted += 1
                        elif action == "編集":
                            update_fixed_category(id_, "partner", row["支払先"])
                            update_fixed_category(id_, "second_category", row["費目"])
                            update_fixed_category(id_, "account", row["勘定科目"])
                            update_fixed_category(id_, "detail", row["詳細"])
                            update_fixed_category(id_, "payment", row["支払方法"])
                            update_fixed_category(id_, "cost", str(row["金額"]))
                            updated += 1

                    if updated > 0:
                        st.success(f"{updated} 件を更新しました")
                    if deleted > 0:
                        st.success(f"{deleted} 件を削除しました")
                    if updated == 0 and deleted == 0:
                        st.info("更新・削除された行はありませんでした")
                    st.rerun()
            else:
                st.info(f"{selected_top_category}カテゴリの固定費はまだ登録されていません。")
