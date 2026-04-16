# modules/dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime
from collections import defaultdict
from db.all_sales_total import get_sales_totals_batch, get_sales_totals_all
from db.all_expense_total import get_expense_totals_batch, get_expense_totals_all
from db.expense_targets import get_expense_target_by_top_category
from db.divisions import get_divisions
from db.brands import get_brands
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
    brands = get_brands()

    # --- 仮想集計エントリを動的生成 ---
    # 「Lia全体合計」は DB 登録不要の動的エントリ
    # 「店舗合計」は [店舗] を名前に含む事業部が存在する場合に生成
    # 「〇〇合計」はブランド設定に登録されたブランド名ごとに生成
    virtual_entries = ["Lia全体合計"]

    store_divs = [d for d in divisions if "[店舗]" in d]
    if store_divs:
        virtual_entries.append("店舗合計")

    for brand in brands:
        brand_divs = [d for d in divisions if brand in d]
        if brand_divs:
            virtual_entries.append(f"{brand}合計")

    # DB に「Lia全体合計」が残っていても重複しないよう除外してセレクタ構築
    real_divisions = [d for d in divisions if d != "Lia全体合計"]
    divisions_for_select = virtual_entries + real_divisions

    selected_div = st.selectbox("事業部・店舗を選択", divisions_for_select)

    # --- 複数事業部を集計するヘルパー ---
    def aggregate_multi_divisions(div_list):
        s_agg = defaultdict(float)
        e_agg = defaultdict(float)
        for div in div_list:
            for d in get_sales_totals_batch(years, div):
                s_agg[(d["year"], d["month"], d["tax_rate"])] += d.get("total_amount", 0)
            for d in get_expense_totals_batch(years, div):
                e_agg[(d["year"], d["month"], d["second_category"])] += d.get("total_cost", 0)
        return dict(s_agg), dict(e_agg)

    # --- データ取得 ---
    if selected_div == "Lia全体合計":
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

    elif selected_div == "店舗合計":
        target_divs = [d for d in divisions if "[店舗]" in d]
        sales_dict, expense_dict = aggregate_multi_divisions(target_divs)

    elif selected_div.endswith("合計"):
        # 〇〇合計 → ブランド名を含む全事業部を集計
        brand_name = selected_div[:-2]
        target_divs = [d for d in divisions if brand_name in d]
        sales_dict, expense_dict = aggregate_multi_divisions(target_divs)

    else:
        sales_data = get_sales_totals_batch(years, selected_div)
        expense_data = get_expense_totals_batch(years, selected_div)
        sales_dict = {(d["year"], d["month"], d["tax_rate"]): d["total_amount"] for d in sales_data}
        expense_dict = {(d["year"], d["month"], d["second_category"]): d["total_cost"] for d in expense_data}

    # --- PL構築 ---
    pl_dict = {
        "売上（税率10%）": {}, "売上（税率8%）": {}, "その他売上（税率10%）": {}, "その他売上（税率8%）": {},
        "総売上": {}, "原価": {}, "売上総利益": {}, "人件費": {}, "源泉税・地方税・社会保険料": {}, "水道光熱費": {}, "消耗品費・その他諸経費": {},
        "その他固定費": {}, "家賃": {}, "広告費": {}, "融資返済利息": {}, "実質営業利益": {}, "臨時諸経費": {}, "（非課税）保険料・税金等": {}, "最終営業利益": {}, "インセンティブ支給総額": {}, "税額計算利益": {},
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
        非経費人件費 = expense_dict.get((year, month, "源泉税・地方税・社会保険料"), 0)
        水道光熱費 = expense_dict.get((year, month, "水道光熱費"), 0)
        消耗品 = expense_dict.get((year, month, "消耗品費・その他諸経費"), 0)
        その他固定費 = expense_dict.get((year, month, "その他固定費"), 0)
        家賃 = expense_dict.get((year, month, "家賃"), 0)
        広告費 = expense_dict.get((year, month, "広告費"), 0)
        融資利息 = expense_dict.get((year, month, "融資返済利息"), 0)
        臨時 = expense_dict.get((year, month, "臨時諸経費"), 0)
        税金等 = expense_dict.get((year, month, "（非課税）保険料・税金等"), 0)
        融資元金 = expense_dict.get((year, month, "融資返済元金"), 0)
        インセンティブ支給総額 = expense_dict.get((year, month, "インセンティブ支給総額"), 0)

        総売上 = u10 + u8 + o10 + o8
        売上総利益 = 総売上 - 原価
        実質営業利益 = 売上総利益 - 人件費 - 水道光熱費 - 消耗品 - その他固定費 - 家賃 - 広告費 - 融資利息
        最終営業利益 = 実質営業利益 - 臨時 - 税金等
        税額計算利益 = 最終営業利益 - インセンティブ支給総額
        消費税額 = (
            (u10 + o10) - (u10 + o10) / 1.1 +
            (u8 + o8) - (u8 + o8) / 1.08 -
            (原価 - 原価 / 1.08) -
            ((水道光熱費 + 消耗品 + 臨時 + その他固定費 + 家賃 + 広告費) -
             (水道光熱費 + 消耗品 + 臨時 + その他固定費 + 家賃 + 広告費) / 1.1)
        )
        法人税額 = 税額計算利益 * 0.3358 if 税額計算利益 > 0 else 0
        内部留保 = 税額計算利益 - 消費税額 - 法人税額 - 融資元金

        for key, value in zip(pl_dict.keys(), [u10, u8, o10, o8, 総売上, 原価, 売上総利益, 人件費, 非経費人件費, 水道光熱費, 消耗品,
                                               その他固定費, 家賃, 広告費, 融資利息, 実質営業利益, 臨時, 税金等, 最終営業利益, インセンティブ支給総額, 税額計算利益,
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
        pl_dict["源泉税・地方税・社会保険料"][ym] = 非経費人件費
        pl_dict["水道光熱費"][ym] = 水道光熱費
        pl_dict["消耗品費・その他諸経費"][ym] = 消耗品
        pl_dict["その他固定費"][ym] = その他固定費
        pl_dict["家賃"][ym] = 家賃
        pl_dict["広告費"][ym] = 広告費
        pl_dict["融資返済利息"][ym] = 融資利息
        pl_dict["実質営業利益"][ym] = 実質営業利益
        pl_dict["臨時諸経費"][ym] = 臨時
        pl_dict["（非課税）保険料・税金等"][ym] = 税金等
        pl_dict["最終営業利益"][ym] = 最終営業利益
        pl_dict["インセンティブ支給総額"][ym] = インセンティブ支給総額
        pl_dict["税額計算利益"][ym] = 税額計算利益
        pl_dict["消費税額"][ym] = 消費税額
        pl_dict["法人税額"][ym] = 法人税額
        pl_dict["融資返済元金"][ym] = 融資元金
        pl_dict["内部留保"][ym] = 内部留保


    # --- DataFrame化 ---
    df = pd.DataFrame(pl_dict).T
    df["合計"] = df.sum(axis=1)
    df = df[["合計"] + months]

    # 合計値を再計算して上書きする
    df.at["消費税額", "合計"] = ((df.at["売上（税率10%）", "合計"] + df.at["その他売上（税率10%）", "合計"]) - (df.at["売上（税率10%）", "合計"] + df.at["その他売上（税率10%）", "合計"]) / 1.1 + (df.at["売上（税率8%）", "合計"] + df.at["その他売上（税率8%）", "合計"]) - (df.at["売上（税率8%）", "合計"] + df.at["その他売上（税率8%）", "合計"]) / 1.08 - (df.at["原価", "合計"] - df.at["原価", "合計"] / 1.08) - ((df.at["水道光熱費", "合計"] + df.at["消耗品費・その他諸経費", "合計"] + df.at["臨時諸経費", "合計"] + df.at["その他固定費", "合計"] + df.at["家賃", "合計"] + df.at["広告費", "合計"]) - (df.at["水道光熱費", "合計"] + df.at["消耗品費・その他諸経費", "合計"] + df.at["臨時諸経費", "合計"] + df.at["その他固定費", "合計"] + df.at["家賃", "合計"] + df.at["広告費", "合計"]) / 1.1))
    df.at["法人税額", "合計"] = df.at["税額計算利益", "合計"] * 0.3358 if df.at["税額計算利益", "合計"] > 0 else 70000
    df.at["内部留保", "合計"] = df.at["税額計算利益", "合計"] - df.at["消費税額", "合計"] - df.at["法人税額", "合計"] - df.at["融資返済元金", "合計"]

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
    df = insert_after(df, "源泉税・地方税・社会保険料", "人件費率", pct_row(df.loc["人件費"] + df.loc["源泉税・地方税・社会保険料"]))
    df = insert_after(df, "人件費率", "FL比率", pct_row(df.loc["原価"] + df.loc["人件費"] + df.loc["源泉税・地方税・社会保険料"]))
    df = insert_after(df, "水道光熱費", "水道光熱費率", pct_row(df.loc["水道光熱費"]))
    df = insert_after(df, "消耗品費・その他諸経費", "消耗品・その他諸経費率", pct_row(df.loc["消耗品費・その他諸経費"]))
    df = insert_after(df, "その他固定費", "その他固定費率", pct_row(df.loc["その他固定費"]))
    df = insert_after(df, "家賃", "家賃率", pct_row(df.loc["家賃"]))
    df = insert_after(df, "家賃率", "FLR比率", pct_row(df.loc["原価"] + df.loc["人件費"] + df.loc["源泉税・地方税・社会保険料"] + df.loc["家賃"]))
    df = insert_after(df, "実質営業利益", "実質営業利益率", pct_row(df.loc["実質営業利益"]))
    df = insert_after(df, "最終営業利益", "最終営業利益率", pct_row(df.loc["最終営業利益"]))

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

    # --- 目標比率取得（※未設定や「Lia全体合計」の場合は空にするエラー回避） ---
    target = get_expense_target_by_top_category(selected_div)
    if target:
        targets = {
            "原価率": target.get("cost_rate", 0),
            "人件費率": target.get("labor_rate", 0),
            "FL比率": target.get("fl_rate", 0),
            "水道光熱費率": target.get("utility_rate", 0),
            "消耗品・その他諸経費率": target.get("misc_rate", 0),
            "その他固定費率": target.get("other_fixed_rate", 0),
            "家賃率": target.get("rent_rate", 0),
            "FLR比率": target.get("flr_rate", 0),
            "実質営業利益率": target.get("first_op_profit_rate", 0),
            "最終営業利益率": target.get("first_op_profit_rate", 0)
        }
    else:
        targets = {}

    # --- 表示用変換 ---
    def format_val(val, row_label):
        try:
            if isinstance(val, (int, float)):
                if "率" in str(row_label) and "税率" not in str(row_label):
                    actual_pct = val * 100
                    base_str = f"{actual_pct:.1f}%"
                    
                    # 目標比率との差分を計算して追加（HTMLの改行を使用）
                    if row_label in targets and targets[row_label] > 0:
                        diff = actual_pct - targets[row_label]
                        sign = "+" if diff > 0 else ""
                        return f"{base_str}<br><span style='font-size: 0.85em; color: gray;'>({sign}{diff:.1f}%)</span>"
                    
                    return base_str
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

    # --- 表示 ---
    st.markdown("### 月別PL")
    render_pl_table(df_display, targets)
