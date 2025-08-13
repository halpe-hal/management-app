# modules/dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime
from collections import defaultdict
from db.all_sales_total import get_sales_totals_batch, get_sales_totals_all
from db.all_expense_total import get_expense_totals_batch, get_expense_totals_all
from db.expense_targets import get_expense_target_by_top_category
from db.divisions import get_divisions
from modules.header import render_pl_table

# 年度生成
def generate_terms(start_year=2020):
    today = datetime.today()
    current_term = (today.year - start_year) + (1 if today.month >= 8 else 0)
    terms = []
    for i in range(1, current_term + 1):
        begin_year = start_year + i - 1
        end_year = begin_year + 1
        terms.append({
            "label": f"{i}期目",
            "value": i,
            "start": f"{begin_year}-08",
            "end": f"{end_year}-07"
        })
    return terms

def get_months_in_term(term):
    start_year, start_month = map(int, term["start"].split("-"))
    end_year, end_month = map(int, term["end"].split("-"))
    months = []
    for m in range(start_month, 13):
        months.append(f"{start_year}-{m:02d}")
    for m in range(1, end_month + 1):
        months.append(f"{end_year}-{m:02d}")
    return months

def show_dashboard():
    st.markdown("## ダッシュボード")

    # --- UI選択 ---
    terms = generate_terms()
    term_labels = [term["label"] for term in terms]
    selected_label = st.selectbox("期を選択", term_labels, index=len(term_labels)-1)
    selected_term = next(t for t in terms if t["label"] == selected_label)
    months = get_months_in_term(selected_term)
    years = sorted(set(int(m.split("-")[0]) for m in months))

    divisions = get_divisions()
    selected_div = st.selectbox("事業部を選択", divisions)

    # --- データ取得 ---
    if selected_div == "事業本部":
        sales_data = get_sales_totals_all(years)
        expense_data = get_expense_totals_all(years)

        # 合算処理
        sales_agg = defaultdict(float)
        for d in sales_data:
            key = (d["year"], d["month"], d["tax_rate"])
            sales_agg[key] += d.get("total_amount", 0)

        expense_agg = defaultdict(float)
        for d in expense_data:
            key = (d["year"], d["month"], d["second_category"])
            expense_agg[key] += d.get("total_cost", 0)

        sales_dict = dict(sales_agg)
        expense_dict = dict(expense_agg)

    else:
        sales_data = get_sales_totals_batch(years, selected_div)
        expense_data = get_expense_totals_batch(years, selected_div)
        sales_dict = {(d["year"], d["month"], d["tax_rate"]): d["total_amount"] for d in sales_data}
        expense_dict = {(d["year"], d["month"], d["second_category"]): d["total_cost"] for d in expense_data}

    # --- PL構築 ---
    pl_dict = {
        "売上（税率10%）": {}, "売上（税率8%）": {}, "その他売上（税率10%）": {}, "その他売上（税率8%）": {},
        "総売上": {}, "原価": {}, "売上総利益": {}, "人件費": {}, "水道光熱費": {}, "消耗品費・その他諸経費": {}, "臨時諸経費": {},
        "その他固定費": {}, "家賃": {}, "広告費": {}, "融資返済利息": {}, "営業利益": {},
        "消費税額": {}, "法人税額": {}, "融資返済元金": {}, "内部留保": {}
    }

    for ym in months:
        year, month = map(int, ym.split("-"))
        u10 = sales_dict.get((year, month, "売上10%"), 0)
        u8 = sales_dict.get((year, month, "売上8%"), 0)
        o10 = sales_dict.get((year, month, "その他売上10%"), 0)
        o8 = sales_dict.get((year, month, "その他売上8%"), 0)
        原価 = expense_dict.get((year, month, "原価（仕入れ高）"), 0)
        人件費 = expense_dict.get((year, month, "人件費"), 0)
        水道光熱費 = expense_dict.get((year, month, "水道光熱費"), 0)
        消耗品 = expense_dict.get((year, month, "消耗品費・その他諸経費"), 0)
        臨時 = expense_dict.get((year, month, "臨時諸経費"), 0)
        その他固定費 = expense_dict.get((year, month, "その他固定費"), 0)
        家賃 = expense_dict.get((year, month, "家賃"), 0)
        広告費 = expense_dict.get((year, month, "広告費"), 0)
        融資利息 = expense_dict.get((year, month, "融資返済利息"), 0)
        融資元金 = expense_dict.get((year, month, "融資返済元金"), 0)

        総売上 = u10 + u8 + o10 + o8
        売上総利益 = 総売上 - 原価
        営業利益 = 売上総利益 - 人件費 - 水道光熱費 - 消耗品 - 臨時 - その他固定費 - 家賃 - 広告費 - 融資利息
        消費税額 = (
            (u10 + o10) - (u10 + o10) / 1.1 +
            (u8 + o8) - (u8 + o8) / 1.08 -
            (原価 - 原価 / 1.08) -
            ((水道光熱費 + 消耗品 + 臨時 + その他固定費 + 家賃 + 広告費) -
             (水道光熱費 + 消耗品 + 臨時 + その他固定費 + 家賃 + 広告費) / 1.1)
        )
        法人税額 = 営業利益 * 0.3358 if 営業利益 > 0 else 0
        内部留保 = 営業利益 - 消費税額 - 法人税額 - 融資元金

        for key, value in zip(pl_dict.keys(), [u10, u8, o10, o8, 総売上, 原価, 売上総利益, 人件費, 水道光熱費, 消耗品, 臨時,
                                               その他固定費, 家賃, 広告費, 融資利息, 営業利益,
                                               消費税額, 法人税額, 融資元金, 内部留保]):
            pl_dict[key][ym] = value

        # 格納
        pl_dict["売上（税率10%）"][ym] = u10
        pl_dict["売上（税率8%）"][ym] = u8
        pl_dict["その他売上（税率10%）"][ym] = o10
        pl_dict["その他売上（税率8%）"][ym] = o8
        pl_dict["総売上"][ym] = 総売上
        pl_dict["原価"][ym] = 原価
        pl_dict["売上総利益"][ym] = 売上総利益
        pl_dict["人件費"][ym] = 人件費
        pl_dict["水道光熱費"][ym] = 水道光熱費
        pl_dict["消耗品費・その他諸経費"][ym] = 消耗品
        pl_dict["臨時諸経費"][ym] = 臨時
        pl_dict["その他固定費"][ym] = その他固定費
        pl_dict["家賃"][ym] = 家賃
        pl_dict["広告費"][ym] = 広告費
        pl_dict["融資返済利息"][ym] = 融資利息
        pl_dict["営業利益"][ym] = 営業利益
        pl_dict["消費税額"][ym] = 消費税額
        pl_dict["法人税額"][ym] = 法人税額
        pl_dict["融資返済元金"][ym] = 融資元金
        pl_dict["内部留保"][ym] = 内部留保


    # --- DataFrame化 ---
    df = pd.DataFrame(pl_dict).T
    df["合計"] = df.sum(axis=1)
    df = df[["合計"] + months]

    # --- 比率行挿入 ---
    def pct_row(numerator_row):
        return {
            col: (numerator_row[col] / df.loc["総売上", col]) if df.loc["総売上", col] else 0
            for col in df.columns
        }

    def insert_after(df, target, label, values):
        idx = df.index.tolist()
        i = idx.index(target) + 1
        upper = df.iloc[:i]
        lower = df.iloc[i:]
        insert = pd.DataFrame([values], index=[label])
        return pd.concat([upper, insert, lower])

    df = insert_after(df, "原価", "原価率", pct_row(df.loc["原価"]))
    df = insert_after(df, "人件費", "人件費率", pct_row(df.loc["人件費"]))
    df = insert_after(df, "人件費率", "FL比率", pct_row(df.loc["原価"] + df.loc["人件費"]))
    df = insert_after(df, "水道光熱費", "水道光熱費率", pct_row(df.loc["水道光熱費"]))
    df = insert_after(df, "消耗品費・その他諸経費", "消耗品・その他諸経費率", pct_row(df.loc["消耗品費・その他諸経費"]))
    df = insert_after(df, "その他固定費", "その他固定費率", pct_row(df.loc["その他固定費"]))
    df = insert_after(df, "家賃", "家賃率", pct_row(df.loc["家賃"]))
    df = insert_after(df, "家賃率", "FLR比率", pct_row(df.loc["原価"] + df.loc["人件費"]+ df.loc["家賃"]))
    df = insert_after(df, "営業利益", "営業利益率", pct_row(df.loc["営業利益"]))

    # --- 表示用変換 ---
    def format_val(val, row_label):
        try:
            if isinstance(val, (int, float)):
                if "率" in str(row_label) and "税率" not in str(row_label):
                    return f"{val:.1%}"
                return f"¥{val:,.0f}"
        except:
            pass
        return val

    df_display = df.copy()
    df_display["項目"] = df_display.index
    df_display = df_display[["項目", "合計"] + months]

    for i, row in df_display.iterrows():
        row_label = row["項目"]
        for col in df_display.columns[1:]:
            df_display.at[i, col] = format_val(row[col], row_label)

    # --- 目標比率取得（※「事業本部」では空に）

    target = get_expense_target_by_top_category(selected_div)
    targets = {
        "原価率": target["cost_rate"],
        "人件費率": target["labor_rate"],
        "FL比率": target["fl_rate"],
        "水道光熱費率": target["utility_rate"],
        "消耗品・その他諸経費率": target["misc_rate"],
        "その他固定費率": target["other_fixed_rate"],
        "家賃率": target["rent_rate"],
        "FLR比率": target["flr_rate"],
        "営業利益率": target["op_profit_rate"]
    }

    # --- 表示 ---
    st.markdown("### 月別PL")
    render_pl_table(df_display, targets)
