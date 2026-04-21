# modules/header.py

import pandas as pd
import streamlit as st

def show():
    st.markdown(
        """
        <style>
        .custom-header {
            background-color: #006a38;
            color: #ffffff;
            padding: 12px 24px;
            font-size: 20px;
            font-weight: bold;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 999999;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }

        .main > div:first-child {
            padding-top: 70px !important;
        }

        /* メイン画面の最大幅を強制的に広げる */
        section.stMain > div { 
            max-width: 1000px !important;
            padding-top: 60px;
        }

        /* サイドバーの幅を調整 */
        section[data-testid="stSidebar"] {
            width: 220px !important;     /* サイドバー全体の幅 */
            min-width: 220px !important;
            max-width: 220px !important;
        }
        /* サイドバー内のコンテンツの余白も調整（必要なら） */
        .css-1d391kg.e1fqkh3o5 {  
            padding-left: 10px;
            padding-right: 10px;
        }

        .st-emotion-cache-kgpedg {
            padding-bottom: 0;
        }

        .st-emotion-cache-1f3w014 {
            margin-top: 35px;
        }

        h2 {
            position: relative;
            font-size: 24px !important;
            font-weight: bold;
            padding: 2% !important;
            margin-bottom: 3% !important;
            }

        h2::before {
            position: absolute;
            content: '';
            left: 0;
            bottom: 0;
            width: 100px;
            height: 5px;
            background: #006a38;
            z-index: 1;
        }
        
        h2::after {
            position: absolute;
            content: '';
            left: 0;
            bottom: 0;
            width: 100%;
            height: 5px;
            background: #efefef;
        }

        h3 {
            border-bottom: 1px solid #006a38;
            padding: 0 0 1% 1% !important;
            font-size: 20px !important;
            margin-bottom: 1% !important;
        }

        .nyukin-h3 {
            border: none;
            background-color: #00a497;
            font-weight: bold;
            color: #ffffff !important;
            padding: 1% !important;
            border-radius: 10px;
        }

        .syukkin-h3 {
            border: none;
            background-color: #c2302a;
            font-weight: bold;
            color: #ffffff !important;
            padding: 1% !important;
            border-radius: 10px;
        }

        h4 {
            margin-top: 20px !important;
        }
        </style>
        <div class="custom-header">
            株式会社Lia 管理会計
        </div>
        """,
        unsafe_allow_html=True
    )

def render_styled_table(data: dict):
    """カテゴリと金額の辞書を装飾付きテーブルとして描画（DataFrame経由）"""

    # 金額をフォーマット（例：¥1,234円）
    formatted_data = {k: f"¥{int(v):,}円" for k, v in data.items()}
    df = pd.DataFrame(formatted_data.items(), columns=["カテゴリ", "金額"])

    styled_html = df.to_html(escape=False, index=False)

    st.markdown(
        f"""
        <div style="overflow-x: auto; overflow-y: auto; height: 100%;">
            <style>
                table {{
                    border-collapse: separate;
                    border-spacing: 0;
                    table-layout: fixed;
                    width: 100%;
                }}
                th {{
                    position: sticky;
                    top: 0;
                    z-index: 2;
                    white-space: nowrap;
                    text-align :center !important;
                    background-color: #006a38 !important;
                    color: #ffffff;
                    padding: 8px;
                }}
                td {{
                    white-space: nowrap;
                    text-align: right;
                    height: 50px;
                    padding: 8px;
                    font-weight: bold;
                }}
                th:first-child, td:first-child {{
                    text-align: left;
                    position: sticky;
                    left: 0;
                    background-color: #f0f2f6;
                    z-index: 1;
                }}
            </style>
            {styled_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_pl_table(df: pd.DataFrame, targets: dict = {}):
    def css_class(row_label):
        if row_label in ["総売上", "実質営業利益", "実質営業利益率", "最終営業利益", "最終営業利益率"]:
            return "blue-bg bold"
        elif row_label in ["原価率", "人件費率", "FL比率", "水道光熱費率",
                           "消耗品・その他諸経費率", "その他固定費率", "家賃率", "FLR比率", "広告費率"]:
            return "red-bg bold"
        else:
            return ""

    # --- HTML化 ---
    rows_html = []
    for _, row in df.iterrows():
        row_label = row["項目"]
        row_css = css_class(row_label)
        row_html = f'<tr class="{row_css}"><td>{row_label}</td>'

        for col in df.columns[1:]:
            val = row[col]
            style = ""

            # 🔴 比率が目標未達 または 超過で赤文字
            if row_label in targets and isinstance(val, str) and "%" in val:
                try:
                    # 改行タグを取り除き、実績の%部分だけを抽出
                    base_val = val.split("<br>")[0] 
                    pct_val = float(base_val.replace("%", "").replace(",", ""))
                    
                    threshold = targets[row_label]
                    if threshold > 0:
                        # 利益率（実質営業利益率など）は、目標を下回った場合に赤字
                        if "利益率" in row_label:
                            if pct_val < threshold:
                                style = ' style="color:red;"'
                        # それ以外のコスト（原価率など）は、目標を上回った場合に赤字
                        else:
                            if pct_val > threshold:
                                style = ' style="color:red;"'
                except:
                    pass

            # 🔴 金額がマイナス
            elif isinstance(val, str) and "¥" in val:
                try:
                    amount = int(val.replace("¥", "").replace(",", ""))
                    if amount < 0:
                        style = ' style="color:red;"'
                except:
                    pass

            row_html += f'<td{style}>{val}</td>'

        row_html += '</tr>'
        rows_html.append(row_html)

    table_html = f"""
    <div style="overflow-x: auto;">
    <style>
        table {{
            border-collapse: separate;
            border-spacing: 0;
            table-layout: auto;
            width: max-content;
            min-width: 100%;
        }}
        th {{
            position: sticky;
            top: 0;
            z-index: 1;
            white-space: nowrap;
            text-align: center !important;
            background-color: #006a38 !important;
            color: #ffffff;
            padding: 8px;
        }}
        td {{
            white-space: nowrap;
            text-align: right;
            padding: 8px;
        }}
        th:first-child, td:first-child {{
            text-align: left;
            position: sticky;
            left: 0;
            background-color: #f0f2f6;
            z-index: 2;
        }}
        .bold td {{
            font-weight: bold;
        }}
        .blue-bg td {{
            background-color: #e0f0ff;
        }}
        .red-bg td {{
            background-color: #ffecec;
        }}
    </style>
    <table>
        <thead><tr><th>項目</th>""" + "".join(
        [f"<th>{col}</th>" for col in df.columns[1:]]
    ) + "</tr></thead><tbody>" + "".join(rows_html) + "</tbody></table></div>"

    st.markdown(table_html, unsafe_allow_html=True)
