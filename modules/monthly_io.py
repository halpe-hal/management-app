# modules/monthly_io.py

import streamlit as st
from datetime import datetime, date
import calendar
from modules.header import render_styled_table
from db.all_expense_total import get_expense_totals
from modules.expense_tables import show_expense_tables_by_select
from db.fixed_categories import apply_fixed_expenses
from db.all_expense import update_expense_totals_by_category
from db.all_expense_depreciation import update_expense_totals_depreciation_by_category
from db.divisions import get_divisions
from db.expense_categories import get_fixed_expense_categories, get_variable_expense_categories
from modules.sales_tables import show_all_sales_tables
from db.all_sales import get_sales
from db.all_sales_total import get_sales_totals

# --- 年度・月管理ユーティリティ ---
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

# --- 入金管理 ---
def handle_all_income(year: int, month: int, top_category: str):
    st.markdown("<h3 class='nyukin-h3'>入金集計</h3>", unsafe_allow_html=True)

    # tax_rateごとに合計を取得
    tax_rates = ["売上10%", "売上8%", "その他売上10%", "その他売上8%"]
    totals = {rate: get_sales_totals(year, month, top_category, rate) for rate in tax_rates}

    # 全体合計も計算
    total_amount = sum(totals.values())

    if total_amount > 0:
        totals["入金合計"] = total_amount
        st.markdown("#### 【入金明細】")
        render_styled_table(totals)
    else:
        st.info("この月の入金データがまだ登録されていません。")

    # 入金入力テーブルを表示
    show_all_sales_tables(year, month, top_category)

# --- 出金管理 ---
def handle_all_expense(year: int, month: int, top_category: str):
    st.markdown("<h3 class='syukkin-h3'>出金集計</h3>", unsafe_allow_html=True)

    totals = get_expense_totals(year, month, top_category)

    # カテゴリ一覧をDBから取得
    variable_categories = get_variable_expense_categories()
    fixed_categories = get_fixed_expense_categories()

    if totals:
        variable_summary = {}
        fixed_summary = {}
        variable_total = 0
        fixed_total = 0

        # ✅ カテゴリ登録順で変動費集計
        for cat in variable_categories:
            if cat in totals:
                variable_summary[cat] = totals[cat]
                variable_total += totals[cat]

        # ✅ カテゴリ登録順で固定費集計
        for cat in fixed_categories:
            if cat in totals:
                fixed_summary[cat] = totals[cat]
                fixed_total += totals[cat]

        variable_summary["合計（変動費）"] = variable_total
        fixed_summary["合計（固定費）"] = fixed_total

        st.markdown("#### 【変動費】")
        render_styled_table(variable_summary)

        st.markdown("#### 【固定費】")
        render_styled_table(fixed_summary)
    else:
        st.info("この月の出金データがまだ登録されていません。")

    # 出金入力テーブルを表示
    show_expense_tables_by_select(year, month, top_category)

    # 固定費手動反映ボタン
    if st.button("この月に固定費を反映する", key=f"apply_fixed_{year}_{month}_{top_category}"):
        success, failed_expense, failed_depreciation = apply_fixed_expenses(year, month, top_category)
        if success:
            for second_category in fixed_categories:
                update_expense_totals_by_category(year, month, second_category, top_category)
                update_expense_totals_depreciation_by_category(year, month, second_category, top_category)

                # 👇 表示キャッシュを破棄（AgGridを再表示させる）
                key_prefix = second_category.replace(" ", "_").replace("(", "").replace(")", "")
                st.session_state.pop(f"{key_prefix}_{top_category}_table_data", None)
                st.session_state.pop(f"{key_prefix}_{top_category}_last_month", None)

            st.success("固定費を反映しました。")
            st.rerun()
        else:
            if failed_expense > 0 and failed_depreciation == 0:
                st.error("出金テーブルへの登録に失敗しました")
            elif failed_expense == 0 and failed_depreciation > 0:
                st.error("減価償却テーブルへの登録に失敗しました")
            elif failed_expense > 0 and failed_depreciation > 0:
                st.error("両方の登録に失敗しました")
            else:
                st.error("固定費の反映処理で例外が発生しました")

    # 月末日なら自動反映
    today = date.today()
    last_day = calendar.monthrange(year, month)[1]

    if today == date(year, month, last_day):
        key = f"auto_fixed_{year}_{month}_{top_category}"
        if not st.session_state.get(key):
            success = apply_fixed_expenses(year, month, top_category)
            if success:
                for second_category in fixed_categories:
                    update_expense_totals_by_category(year, month, second_category, top_category)
                st.success("固定費を月末に自動反映しました。")
            st.session_state[key] = True

# --- メイン表示関数 ---
def show_monthly_io():
    st.markdown("## 月別入出金管理")

    terms = generate_terms()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        term_labels = [term["label"] for term in terms]
        selected_label = st.selectbox("期を選択", term_labels, index=len(term_labels)-1)

    with col2:
        division_options = get_divisions()
        if not division_options:
            st.warning("事業部が未登録です。先に『事業部設定』から登録してください。")
            return
        top_category = st.selectbox("事業部を選択", division_options)

    with col3:
        io_type = st.selectbox("表示タイプを選択", ["入金", "出金"])

    with col4:
        selected_term = next(t for t in terms if t["label"] == selected_label)
        months = get_months_in_term(selected_term)
        today = datetime.today()
        prev_month = f"{today.year - 1}-12" if today.month == 1 else f"{today.year}-{today.month - 1:02d}"
        default_index = months.index(prev_month) if prev_month in months else len(months) - 1
        selected_month = st.selectbox("月を選択", months, index=default_index)

    year, month = map(int, selected_month.split("-"))

    # --- 表示分岐 ---
    if io_type == "入金":
        handle_all_income(year, month, top_category)
    elif io_type == "出金":
        handle_all_expense(year, month, top_category)

