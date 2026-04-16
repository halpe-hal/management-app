# modules/sales_tables.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from db.all_sales import get_sales, add_sale, delete_sale, update_sales_total
from db.income_sources import get_income_sources
from db.supabase_client import supabase


def show_all_sales_tables(year: int, month: int, top_category: str):
    show_sales_table(year, month, top_category)


def show_sales_table(year: int, month: int, top_category: str):
    st.markdown(f"### 入金明細")

    key_prefix = f"sales_{top_category.replace(' ', '_')}"
    last_month_key = f"{key_prefix}_last_month"
    data_key = f"{key_prefix}_data"

    if last_month_key not in st.session_state:
        st.session_state[last_month_key] = f"{year}-{month:02d}"

    current_key = f"{year}-{month:02d}"
    if st.session_state[last_month_key] != current_key:
        st.session_state.pop(data_key, None)
        st.session_state[last_month_key] = current_key

    existing = get_sales(year, month, top_category)
    existing_df = pd.DataFrame([
        {
            "id": row["id"],
            "入金元": row["partner"],
            "詳細": row.get("detail", ""),
            "入金予定額": row.get("expected_amount", 0),
            "入金済額": row.get("received_amount", 0),
            "入金手段": row.get("payment", ""),
            "請求書": row.get("invoice_issued", False),
            "税区分": row.get("tax_rate", ""),
            "操作": "（なし）"
        }
        for row in existing
    ])

    default_data = get_income_sources()
    default_rows = [
        {
            "入金元": row["partner"],
            "詳細": row.get("detail", ""),
            "入金予定額": row.get("expected_amount", 0),
            "入金済額": row.get("received_amount", 0),
            "入金手段": row.get("payment", ""),
            "請求書": row.get("invoice_issued", False),
            "税区分": row.get("tax_rate", ""),
            "操作": "（なし）",
            "id": None
        }
        for row in default_data if row["top_category"] == top_category
    ]

    if data_key not in st.session_state:
        st.session_state[data_key] = existing_df if not existing_df.empty else pd.DataFrame(default_rows)

    df = st.session_state[data_key]

    # if df.empty:
    #     st.info("この月の入金データが存在しません。")
    #     return

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)
    gb.configure_column("入金手段", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["現金", "銀行振込", "クレジット", "paygent", "paypal", "その他"]})
    gb.configure_column("請求書", cellEditor="agSelectCellEditor", cellEditorParams={"values": [True, False]})
    gb.configure_column("税区分", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["売上10%", "売上8%", "その他売上10%", "その他売上8%"]})
    gb.configure_column("操作", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["（なし）", "削除"]})
    gb.configure_column("入金予定額", type=["numericColumn"], precision=0)
    gb.configure_column("入金済額", type=["numericColumn"], precision=0)
    gb.configure_column("id", hide=True)

    grid_options = gb.build()
    table_height = len(df) * 35 + 40
    response = AgGrid(df, gridOptions=grid_options, update_mode=GridUpdateMode.MODEL_CHANGED, fit_columns_on_grid_load=True, height=table_height)
    updated_df = response["data"]

    col1, col2, col3 = st.columns([6, 2, 2])
    with col1:
        if st.button("＋ 行を追加", key=f"add_{key_prefix}_row"):
            new_row = {"入金元": "", "詳細": "", "入金予定額": 0, "入金済額": 0, "入金手段": "", "請求書": False, "税区分": "売上10%", "操作": "（なし）", "id": None}
            st.session_state[data_key] = pd.concat([updated_df, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            if st.button("登録", key=f"register_{key_prefix}"):
                inserted = 0
                for _, row in updated_df.iterrows():
                    if pd.isna(row.get("id")) and row["入金元"] and row["入金手段"]:
                        success = add_sale(
                            year, month,
                            row["入金元"],
                            row["詳細"],
                            row["入金予定額"],
                            row["入金済額"],
                            row["入金手段"],
                            top_category,
                            row["請求書"],
                            row["税区分"]
                        )
                        if success:
                            inserted += 1
                if inserted:
                    update_sales_total(year, month, top_category)
                    st.success(f"{inserted} 件を登録しました")
                    st.session_state.pop(data_key, None)
                    st.rerun()
                else:
                    st.warning("登録対象がありません")

        with col3b:
            if st.button("更新", key=f"update_{key_prefix}"):
                updated = 0
                deleted = 0
                for _, row in updated_df.iterrows():
                    if row["操作"] == "削除" and not pd.isna(row.get("id")):
                        delete_sale(int(row["id"]))
                        deleted += 1
                    elif row["操作"] != "削除" and not pd.isna(row.get("id")):
                        old = existing_df[existing_df["id"] == row["id"]]
                        if not old.empty:
                            ex = old.iloc[0]
                            if any([
                                row["入金元"] != ex["入金元"],
                                row["詳細"] != ex["詳細"],
                                row["入金予定額"] != ex["入金予定額"],
                                row["入金済額"] != ex["入金済額"],
                                row["入金手段"] != ex["入金手段"],
                                row["請求書"] != ex["請求書"],
                                row["税区分"] != ex["税区分"]
                            ]):
                                supabase.table("all_sales").update({
                                    "partner": row["入金元"],
                                    "detail": row["詳細"],
                                    "expected_amount": row["入金予定額"],
                                    "received_amount": row["入金済額"],
                                    "payment": row["入金手段"],
                                    "invoice_issued": row["請求書"],
                                    "tax_rate": row["税区分"]
                                }).eq("id", int(row["id"])).execute()
                                updated += 1

                if deleted or updated:
                    update_sales_total(year, month, top_category)
                    if deleted: st.success(f"{deleted} 件を削除しました")
                    if updated: st.success(f"{updated} 件を更新しました")
                    st.session_state.pop(data_key, None)
                    st.rerun()
                else:
                    st.info("更新または削除対象がありませんでした")
