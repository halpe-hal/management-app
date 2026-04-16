#modules/graph_analysis.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from db.all_sales_total import get_sales_totals_all
from db.all_expense_total import get_expense_totals_all
from db.expense_targets import get_expense_target_by_top_category
from db.expense_categories import get_expense_categories
from db.divisions import get_divisions

# --- 期間オプションから日付範囲を返す ---
def get_filtered_period(option: str):
    today = datetime.today()
    if option == "今期":
        start = datetime(today.year if today.month >= 8 else today.year - 1, 8, 1)
        end = datetime(start.year + 1, 7, 31)
    elif option == "先期":
        start = datetime(today.year - 1 if today.month >= 8 else today.year - 2, 8, 1)
        end = datetime(start.year + 1, 7, 31)
    else:
        start = st.date_input("開始日", value=datetime(today.year, 1, 1))
        end = st.date_input("終了日", value=today)

        # ✅ 型をdatetimeに変換（これが必要！）
        from datetime import time
        start = datetime.combine(start, time.min)
        end = datetime.combine(end, time.max)

    return start, end

# --- 年月フィルター ---
def ym_filter(df, start: datetime, end: datetime):
    df["年月日"] = pd.to_datetime(df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01")
    return df[(df["年月日"] >= start) & (df["年月日"] <= end)]

# --- メイン表示関数 ---
def show_graph_analysis():
    st.markdown("## グラフ分析")

    # 期間選択
    period_option = st.selectbox("期間を選択", ["今期", "先期", "期間選択"])
    start_date, end_date = get_filtered_period(period_option)

    # データ取得
    divisions = get_divisions()
    sales_data = get_sales_totals_all(list(range(start_date.year - 1, end_date.year + 1)))
    expense_data = get_expense_totals_all(list(range(start_date.year - 1, end_date.year + 1)))

    df_sales = pd.DataFrame(sales_data)
    df_expense = pd.DataFrame(expense_data)

    if df_sales.empty or df_expense.empty:
        st.warning("データが存在しません。")
        return

    # 年月整形（YYYY / MM）
    df_sales["年月"] = df_sales["year"].astype(str) + " / " + df_sales["month"].astype(str).str.zfill(2)
    df_expense["年月"] = df_expense["year"].astype(str) + " / " + df_expense["month"].astype(str).str.zfill(2)

    # 事業部ごとのタブ
    tabs = st.tabs(divisions)

    for div_name, tab in zip(divisions, tabs):
        with tab:
            # --- 売上データ（事業本部は全体集計） ---
            df_sales_div = df_sales.copy() if div_name == "事業本部" else df_sales[df_sales["top_category"] == div_name].copy()
            df_sales_div = ym_filter(df_sales_div, start_date, end_date)
            df_sales_grouped = df_sales_div.groupby("年月")["total_amount"].sum().reset_index()

            if not df_sales_grouped.empty:
                st.markdown(f"### 売上推移")
                fig1 = px.bar(df_sales_grouped, x="年月", y="total_amount", title="月次売上",
                              labels={"total_amount": "売上金額"}, text_auto=True)
                fig1.update_layout(
                    yaxis=dict(tickformat=",", tickprefix="¥", separatethousands=True)
                )
                st.plotly_chart(fig1, use_container_width=True, key=f"{div_name}_sales")
            else:
                st.info("該当期間の売上データがありません。")

            # --- 支出データ（個別カテゴリ折れ線＋目標） ---
            df_expense_div = df_expense.copy() if div_name == "事業本部" else df_expense[df_expense["top_category"] == div_name].copy()
            df_expense_div = ym_filter(df_expense_div, start_date, end_date)
            df_expense_grouped = df_expense_div.groupby(["年月", "second_category"])["total_cost"].sum().reset_index()

            if not df_expense_grouped.empty:
                st.markdown(f"### 費目別支出推移")

                # ✅ 表示順：expense_categoriesテーブルの順
                category_order = get_expense_categories()

                # ✅ 目標率を取得
                target_row = get_expense_target_by_top_category(div_name)
                if target_row:
                    target_map = {
                        "原価（仕入れ高）": target_row.get("cost_rate", 0),
                        "人件費": target_row.get("labor_rate", 0),
                        "FL比率": target_row.get("fl_rate", 0),
                        "水道光熱費": target_row.get("utility_rate", 0),
                        "消耗品費・その他諸経費": target_row.get("misc_rate", 0),
                        "その他固定費": target_row.get("other_fixed_rate", 0),
                        "家賃": target_row.get("rent_rate", 0),
                        "営業利益": target_row.get("op_profit_rate", 0)
                    }
                else:
                    target_map = {}

                # ✅ 月別売上を辞書化（目標額算出用）
                sales_lookup = dict(zip(df_sales_grouped["年月"], df_sales_grouped["total_amount"]))

                for category in category_order:
                    if category not in df_expense_grouped["second_category"].unique():
                        continue  # データなしカテゴリはスキップ

                    df_cat = df_expense_grouped[df_expense_grouped["second_category"] == category].copy()

                    # ✅ 目標額を計算（%→小数に直すため /100）
                    target_rate = target_map.get(category, 0) / 100
                    df_cat["目標額"] = df_cat["年月"].map(lambda ym: sales_lookup.get(ym, 0) * target_rate)

                    fig = px.line(df_cat, x="年月", y="total_cost", markers=True,
                                  title=f"{category} の支出推移",
                                  labels={"total_cost": "支出金額"})
                    fig.update_traces(name="実績", line=dict(color="blue"))

                    # ✅ 赤点線で目標額表示
                    fig.add_scatter(x=df_cat["年月"], y=df_cat["目標額"], mode="lines+markers",
                                    name="目標額", line=dict(color="red", dash="dot"))

                    fig.update_layout(
                        yaxis=dict(
                            tickformat=",",
                            tickprefix="¥",
                            separatethousands=True
                        )
                    )
                    fig.update_yaxes(range=[0, max(df_cat["total_cost"].max(), df_cat["目標額"].max()) * 1.1])
                    st.plotly_chart(fig, use_container_width=True, key=f"{div_name}_{category}_expense")
            else:
                st.info("該当期間の支出データがありません。")
