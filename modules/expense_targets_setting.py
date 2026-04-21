# modules/expense_targets_setting.py

import streamlit as st
from db.divisions import get_divisions, get_division_records
from db.expense_targets import get_expense_target_by_top_category, upsert_expense_target
from datetime import datetime

def handle_expense_targets_setting():
    st.markdown("## 目標比率の設定")

    division_records = get_division_records()
    divisions = [r["name"] for r in division_records]

    if not divisions:
        st.warning("事業部が未登録です。先に登録してください。")
        return

    # 業態・ブランドのグループを構築
    type_groups = {}
    brand_groups = {}
    for rec in division_records:
        if rec.get("type"):
            type_groups.setdefault(rec["type"], []).append(rec["name"])
        if rec.get("brand"):
            brand_groups.setdefault(rec["brand"], []).append(rec["name"])

    # 仮想集計エントリ
    virtual_entries = ["Lia全体合計", "全事業部合計（事業本部除く）"]
    for t, divs in type_groups.items():
        if len(divs) >= 2:
            virtual_entries.append(f"{t}合計")
    for b, divs in brand_groups.items():
        if len(divs) >= 2:
            virtual_entries.append(f"{b}合計")

    all_entries = virtual_entries + divisions

    tabs = st.tabs(all_entries)

    for i, div in enumerate(all_entries):
        with tabs[i]:
            if div == "Lia全体合計":
                label = div
            elif div in virtual_entries:
                label = f"{div}（合計）"
            else:
                label = div
            st.markdown(f"### 【{label}】の目標比率")

            data = get_expense_target_by_top_category(div)
            editing_key = f"{div}_editing"

            if not st.session_state.get(editing_key):
                # 初期表示（表のみ）
                if data:
                    st.markdown("""
                    <style>
                        .target-table td, .target-table th {
                            padding: 8px 12px;
                            border: 1px solid #ccc;
                        }
                        .target-table th {
                            background-color: #006a38;
                            color: white;
                            text-align: center;
                        }
                        .target-table td {
                            text-align: right;
                        }
                        .target-table td:first-child, .target-table th:first-child {
                            text-align: left;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <table class="target-table">
                        <tr><th>項目</th><th>目標比率（%）</th></tr>
                        <tr><td>原価率</td><td>{data.get("cost_rate", 0)}</td></tr>
                        <tr><td>人件費率</td><td>{data.get("labor_rate", 0)}</td></tr>
                        <tr><td>FL率</td><td>{data.get("fl_rate", 0)}</td></tr>
                        <tr><td>消耗品・諸経費率</td><td>{data.get("misc_rate", 0)}</td></tr>
                        <tr><td>水道光熱費率</td><td>{data.get("utility_rate", 0)}</td></tr>
                        <tr><td>その他固定費率</td><td>{data.get("other_fixed_rate", 0)}</td></tr>
                        <tr><td>家賃率</td><td>{data.get("rent_rate", 0)}</td></tr>
                        <tr><td>FLR率</td><td>{data.get("flr_rate", 0)}</td></tr>
                        <tr><td>広告費率</td><td>{data.get("ad_rate", 0)}</td></tr>
                        <tr><td>実質営業利益率</td><td>{data.get("first_op_profit_rate", 0)}</td></tr>
                    </table>
                    """, unsafe_allow_html=True)
                else:
                    st.info("まだ目標比率が登録されていません。")

                if st.button("編集", key=f"edit_btn_{div}"):
                    st.session_state[editing_key] = True
                    st.rerun()

            else:
                st.markdown(f"#### {div} の目標比率を編集")

                col1, col2 = st.columns(2)
                with col1:
                    cost_rate = st.number_input("原価率", value=float(data.get("cost_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_cost")
                    labor_rate = st.number_input("人件費率", value=float(data.get("labor_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_labor")
                    fl_rate = st.number_input("FL率", value=float(data.get("fl_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_fl")
                    misc_rate = st.number_input("消耗品・諸経費率", value=float(data.get("misc_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_misc")
                with col2:
                    utility_rate = st.number_input("水道光熱費率", value=float(data.get("utility_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_utility")
                    other_fixed_rate = st.number_input("その他固定費率", value=float(data.get("other_fixed_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_other_fixed")
                    rent_rate = st.number_input("家賃率", value=float(data.get("rent_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_rent")
                    flr_rate = st.number_input("FLR率", value=float(data.get("flr_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_flr")
                    ad_rate = st.number_input("広告費率", value=float(data.get("ad_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_ad")
                    first_op_profit_rate = st.number_input("実質営業利益率", value=float(data.get("first_op_profit_rate") or 0) if data else 0.0, step=0.1, key=f"{div}_op")
                if st.button("保存", key=f"save_btn_{div}"):
                    payload = {
                        "top_category": div,
                        "cost_rate": cost_rate,
                        "labor_rate": labor_rate,
                        "fl_rate": fl_rate,
                        "misc_rate": misc_rate,
                        "utility_rate": utility_rate,
                        "other_fixed_rate": other_fixed_rate,
                        "rent_rate": rent_rate,
                        "flr_rate": flr_rate,
                        "ad_rate": ad_rate,
                        "first_op_profit_rate": first_op_profit_rate
                    }
                    success = upsert_expense_target(payload)
                    if success:
                        st.success("保存しました")
                        st.session_state[editing_key] = False
                        st.rerun()
                    else:
                        st.error("保存に失敗しました")

                if st.button("キャンセル", key=f"cancel_btn_{div}"):
                    st.session_state[editing_key] = False
                    st.rerun()
