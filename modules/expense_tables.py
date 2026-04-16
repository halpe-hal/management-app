# modules/expense_tables.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from db.account_items import get_account_items
from db.all_expense import get_expenses, add_expense, delete_expense, update_expense_totals_by_category
from db.all_expense_depreciation import get_expenses_depreciation, add_expense_depreciation, delete_expense_depreciation, update_expense_totals_depreciation_by_category
from db.default_partners import get_default_partners_by_category
from db.supabase_client import supabase
from db.expense_categories import get_expense_categories

# ✅ すべての費目カテゴリを対象に表示

def show_expense_tables_by_select(year: int, month: int, top_category: str):
    st.markdown("### 出金カテゴリを選択")

    # --- 変動費カテゴリ一覧を取得 ---
    second_categories = get_expense_categories()
    selected_category = st.selectbox("費目カテゴリを選択", second_categories, key=f"select_{top_category}")

    show_single_expense_table(year, month, selected_category, top_category)


def show_single_expense_table(year: int, month: int, second_category: str, top_category: str):
    st.markdown(f"### {second_category}")

    key_prefix = f"aggrid_{second_category}_{top_category}".replace(" ", "_").replace("(", "").replace(")", "")
    last_month_key = f"{key_prefix}_last_month"
    data_key = f"{key_prefix}_table_data"

    # 月切り替え時にセッション初期化
    if last_month_key not in st.session_state:
        st.session_state[last_month_key] = f"{year}-{month:02d}"

    current_key = f"{year}-{month:02d}"
    if st.session_state[last_month_key] != current_key:
        st.session_state.pop(data_key, None)
        st.session_state[last_month_key] = current_key

    # Supabaseから既存データ取得
    existing = get_expenses(year, month, top_category)
    existing_df = pd.DataFrame([
        {
            "id": row["id"],
            "取引先": row["partner"],
            "勘定項目": row["account"],
            "詳細": row["detail"],
            "支払方法": row["payment"],
            "金額": row["cost"],
            "操作": "（なし）"
        }
        for row in existing if row["second_category"] == second_category and row["top_category"] == top_category
    ])

    # デフォルト行取得
    default_data = get_default_partners_by_category(second_category, top_category)
    default_rows = [
        {
            "取引先": row["partner"],
            "勘定項目": row["account"],
            "詳細": row.get("detail") or "",
            "支払方法": row["payment"],
            "金額": 0,
            "操作": "（なし）",
            "id": None
        }
        for row in default_data
    ]

    # セッションに初期表示
    if data_key not in st.session_state:
        st.session_state[data_key] = existing_df if not existing_df.empty else pd.DataFrame(default_rows)
    df = st.session_state[data_key]

    # 👇 追加：空のデータフレームはスキップ
    # if df.empty:
    #     st.info(f"{second_category} のデータが存在しません。")
    #     return

    # AgGrid設定
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)
    gb.configure_column("取引先", width=120)
    gb.configure_column("詳細", width=300)
    gb.configure_column("支払方法", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["選択してください", "現金", "クレジット", "銀行振込", "銀行引落", "その他"]}, width=120)
    gb.configure_column("操作", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["（なし）", "削除"]}, width=90)
    gb.configure_column("勘定項目", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["選択してください"] + [i["name"] for i in get_account_items()]}, width=120)
    gb.configure_column("金額", type=["numericColumn"], precision=0, width=100)
    gb.configure_column("id", hide=True)
    grid_options = gb.build()

    table_height = len(df) * 35 + 20
    response = AgGrid(df, gridOptions=grid_options, update_mode=GridUpdateMode.MODEL_CHANGED, fit_columns_on_grid_load=True, height=table_height)
    updated_df = response["data"]

    col1, col2, col3 = st.columns([6, 2, 2])
    with col1:
        if st.button("＋ 行を追加", key=f"add_{key_prefix}_row"):
            new_row = {"取引先": "", "勘定項目": "", "詳細": "", "支払方法": "", "金額": 0, "操作": "（なし）", "id": None}
            st.session_state[data_key] = pd.concat([updated_df, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            if st.button("登録", key=f"register_{key_prefix}"):

                # --- 登録対象抽出 ---
                targets = []
                for _, row in updated_df.iterrows():
                    if (
                        pd.isna(row.get("id")) and
                        str(row.get("取引先") or "").strip() and
                        row.get("勘定項目") != "選択してください" and
                        row.get("支払方法") != "選択してください"
                    ):
                        targets.append(row)

                # --- 登録対象なし（ここで止めない！） ---
                if not targets:
                    st.warning("登録対象がありません")
                else:
                    inserted = 0
                    failed_expense = 0
                    failed_depreciation = 0

                    for row in targets:
                        ok_expense = add_expense(
                            year, month,
                            row["取引先"], row["勘定項目"], row["詳細"],
                            row["支払方法"], row["金額"],
                            second_category, top_category
                        )

                        ok_depreciation = add_expense_depreciation(
                            year, month,
                            row["取引先"], row["勘定項目"], row["詳細"],
                            row["支払方法"], row["金額"],
                            second_category, top_category
                        )

                        if ok_expense and ok_depreciation:
                            inserted += 1
                        else:
                            if not ok_expense:
                                failed_expense += 1
                            if not ok_depreciation:
                                failed_depreciation += 1

                    if inserted > 0:
                        update_expense_totals_by_category(year, month, second_category, top_category)
                        update_expense_totals_depreciation_by_category(year, month, second_category, top_category)
                        st.success(f"{inserted} 件を登録しました")
                        st.session_state.pop(data_key, None)
                        st.rerun()
                    else:
                        if failed_expense > 0 and failed_depreciation == 0:
                            st.error("出金テーブルへの登録に失敗しました")
                        elif failed_expense == 0 and failed_depreciation > 0:
                            st.error("減価償却テーブルへの登録に失敗しました")
                        else:
                            st.error("両方の登録に失敗しました")

        with col3b:
            if st.button("更新", key=f"update_{key_prefix}"):
                updated = 0
                deleted = 0
                for _, row in updated_df.iterrows():
                    if row["操作"] == "削除" and not pd.isna(row.get("id")):
                        ok1 = delete_expense(int(row["id"]))
                        ok2 = delete_expense_depreciation(int(row["id"]))

                        if ok1 and ok2:
                            deleted += 1
                        else:
                            st.error(f"id={int(row['id'])} の削除が失敗しました（expense={ok1}, depreciation={ok2}）")
                    elif row["操作"] != "削除" and not pd.isna(row.get("id")):
                        old = existing_df[existing_df["id"] == row["id"]]
                        if not old.empty:
                            ex = old.iloc[0]
                            if any([
                                row["取引先"] != ex["取引先"],
                                row["勘定項目"] != ex["勘定項目"],
                                row["詳細"] != ex["詳細"],
                                row["支払方法"] != ex["支払方法"],
                                row["金額"] != ex["金額"]
                            ]):
                                r1 = supabase.table("all_expense").update({
                                    "partner": row["取引先"],
                                    "account": row["勘定項目"],
                                    "detail": row["詳細"],
                                    "payment": row["支払方法"],
                                    "cost": row["金額"]
                                }).eq("id", int(row["id"])).execute()
                                r2 = supabase.table("all_expense_depreciation").update({
                                    "partner": row["取引先"],
                                    "account": row["勘定項目"],
                                    "detail": row["詳細"],
                                    "payment": row["支払方法"],
                                    "cost": row["金額"]
                                }).eq("id", int(row["id"])).execute()
                                ok1 = bool(getattr(r1, "data", None))
                                ok2 = bool(getattr(r2, "data", None))

                                if ok1 and ok2:
                                    updated += 1
                                else:
                                    st.error(f"id={int(row['id'])} の更新が失敗しました（expense={ok1}, depreciation={ok2}）")

                if deleted or updated:
                    update_expense_totals_by_category(year, month, second_category, top_category)
                    update_expense_totals_depreciation_by_category(year, month, second_category, top_category)
                    if deleted: st.success(f"{deleted} 件を削除しました")
                    if updated: st.success(f"{updated} 件を更新しました")
                    st.session_state.pop(data_key, None)
                    st.rerun()
                else:
                    st.info("更新または削除対象がありませんでした")


# def show_all_expense_tables(year: int, month: int, top_category: str):
#     for second_category in get_expense_categories():
#         show_expense_table(year, month, second_category, top_category)


# def show_expense_table(year: int, month: int, second_category: str, top_category:str):
#     st.markdown(f"### {second_category}")

#     key_prefix = f"aggrid_{second_category}_{top_category}".replace(" ", "_").replace("(", "").replace(")", "")
#     last_month_key = f"{key_prefix}_last_month"
#     data_key = f"{key_prefix}_table_data"

#     # 月切り替え時にセッション初期化
#     if last_month_key not in st.session_state:
#         st.session_state[last_month_key] = f"{year}-{month:02d}"

#     current_key = f"{year}-{month:02d}"
#     if st.session_state[last_month_key] != current_key:
#         st.session_state.pop(data_key, None)
#         st.session_state[last_month_key] = current_key

#     # Supabaseから既存データ取得
#     existing = get_expenses(year, month, top_category)
#     existing_df = pd.DataFrame([
#         {
#             "id": row["id"],
#             "取引先": row["partner"],
#             "勘定項目": row["account"],
#             "詳細": row["detail"],
#             "支払方法": row["payment"],
#             "金額": row["cost"],
#             "操作": "（なし）"
#         }
#         for row in existing if row["second_category"] == second_category and row["top_category"] == top_category
#     ])

#     # デフォルト行取得
#     default_data = get_default_partners_by_category(second_category, top_category)
#     default_rows = [
#         {
#             "取引先": row["partner"],
#             "勘定項目": row["account"],
#             "詳細": row.get("detail") or "",
#             "支払方法": row["payment"],
#             "金額": 0,
#             "操作": "（なし）",
#             "id": None
#         }
#         for row in default_data
#     ]

#     # セッションに初期表示
#     if data_key not in st.session_state:
#         st.session_state[data_key] = existing_df if not existing_df.empty else pd.DataFrame(default_rows)
#     df = st.session_state[data_key]

#     # 👇 追加：空のデータフレームはスキップ
#     if df.empty:
#         st.info(f"{second_category} のデータが存在しません。")
#         return

#     # AgGrid設定
#     gb = GridOptionsBuilder.from_dataframe(df)
#     gb.configure_default_column(editable=True)
#     gb.configure_column("取引先", width=120)
#     gb.configure_column("詳細", width=300)
#     gb.configure_column("支払方法", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["選択してください", "現金", "クレジット", "銀行振込", "銀行引落", "その他"]}, width=120)
#     gb.configure_column("操作", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["（なし）", "削除"]}, width=90)
#     gb.configure_column("勘定項目", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["選択してください"] + [i["name"] for i in get_account_items()]}, width=120)
#     gb.configure_column("金額", type=["numericColumn"], precision=0, width=100)
#     gb.configure_column("id", hide=True)
#     grid_options = gb.build()

#     table_height = len(df) * 35 + 40
#     response = AgGrid(df, gridOptions=grid_options, update_mode=GridUpdateMode.MODEL_CHANGED, fit_columns_on_grid_load=True, height=table_height, key=key_prefix)
#     updated_df = response["data"]

#     col1, col2, col3 = st.columns([6, 2, 2])
#     with col1:
#         if st.button("＋ 行を追加", key=f"add_{key_prefix}_row"):
#             new_row = {"取引先": "", "勘定項目": "", "詳細": "", "支払方法": "", "金額": 0, "操作": "（なし）", "id": None}
#             st.session_state[data_key] = pd.concat([updated_df, pd.DataFrame([new_row])], ignore_index=True)
#             st.rerun()

#     with col3:
#         col3a, col3b = st.columns(2)
#         with col3a:
#             if st.button("登録", key=f"register_{key_prefix}"):
#                 inserted = 0
#                 for _, row in updated_df.iterrows():
#                     if (
#                         pd.isna(row.get("id")) and
#                         row["取引先"] and
#                         row["勘定項目"] != "選択してください" and
#                         row["支払方法"] != "選択してください"
#                     ):
#                         success = add_expense(
#                             year, month,
#                             row["取引先"], row["勘定項目"], row["詳細"], row["支払方法"], row["金額"], second_category, top_category
#                         )
#                         if success:
#                             inserted += 1
#                 if inserted:
#                     update_expense_totals_by_category(year, month, second_category, top_category)
#                     st.success(f"{inserted} 件を登録しました")
#                     st.session_state.pop(data_key, None)
#                     st.rerun()
#                 else:
#                     st.warning("登録対象がありません")

#         with col3b:
#             if st.button("更新", key=f"update_{key_prefix}"):
#                 updated = 0
#                 deleted = 0
#                 for _, row in updated_df.iterrows():
#                     if row["操作"] == "削除" and not pd.isna(row.get("id")):
#                         delete_expense(int(row["id"]))
#                         deleted += 1
#                     elif row["操作"] != "削除" and not pd.isna(row.get("id")):
#                         old = existing_df[existing_df["id"] == row["id"]]
#                         if not old.empty:
#                             ex = old.iloc[0]
#                             if any([
#                                 row["取引先"] != ex["取引先"],
#                                 row["勘定項目"] != ex["勘定項目"],
#                                 row["詳細"] != ex["詳細"],
#                                 row["支払方法"] != ex["支払方法"],
#                                 row["金額"] != ex["金額"]
#                             ]):
#                                 supabase.table("all_expense").update({
#                                     "partner": row["取引先"],
#                                     "account": row["勘定項目"],
#                                     "detail": row["詳細"],
#                                     "payment": row["支払方法"],
#                                     "cost": row["金額"]
#                                 }).eq("id", int(row["id"])).execute()
#                                 updated += 1

#                 if deleted or updated:
#                     update_expense_totals_by_category(year, month, second_category, top_category)
#                     if deleted: st.success(f"{deleted} 件を削除しました")
#                     if updated: st.success(f"{updated} 件を更新しました")
#                     st.session_state.pop(data_key, None)
#                     st.rerun()
#                 else:
#                     st.info("更新または削除対象がありませんでした")