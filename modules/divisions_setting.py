# modules/divisions_setting.py

import streamlit as st
from db.divisions import (
    get_division_records,
    add_division,
    delete_division,
    update_division_order
)

def handle_division_setting():

    # --- 新規事業部の登録フォーム ---
    st.markdown("#### 事業部・店舗の新規登録")
    with st.form("division_form", clear_on_submit=True):
        new_div = st.text_input("事業部・店舗名", placeholder="例：新規開発事業部")
        submitted = st.form_submit_button("登録")

        if submitted:
            if new_div.strip() == "":
                st.warning("空欄では登録できません。")
            else:
                result = add_division(new_div.strip())
                if result == "success":
                    st.success("事業部・店舗を登録しました。")
                    st.session_state.pop("division_order", None)  # 順番のキャッシュをリセット
                    st.rerun()
                elif result == "duplicate":
                    st.info("同じ事業部・店舗がすでに登録されています。")
                else:
                    st.error("登録中にエラーが発生しました。")

    # --- 並び順のセッション保存（初期化） ---
    if "division_order" not in st.session_state:
        divisions = get_division_records()
        st.session_state.division_order = divisions.copy()
    else:
        divisions = st.session_state.division_order

    # --- 並び替えアクションの記録と実行 ---
    move_key = st.session_state.get("move_div_action", None)
    if move_key:
        action, idx = move_key.split("_")
        idx = int(idx)
        if action == "up" and idx > 0:
            divisions[idx - 1], divisions[idx] = divisions[idx], divisions[idx - 1]
            update_division_order(divisions)
        elif action == "down" and idx < len(divisions) - 1:
            divisions[idx + 1], divisions[idx] = divisions[idx], divisions[idx + 1]
            update_division_order(divisions)
        del st.session_state["move_div_action"]
        st.rerun()

    # --- 登録済みの事業部一覧（並び替え＆削除） ---
    if divisions:
        st.markdown("#### 登録済みの事業部・店舗（並び替え＆削除）")
        for i, row in enumerate(divisions):
            # 費目設定の画面レイアウトに合わせてカラム幅を調整しています
            col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 2, 1])
            with col1:
                st.write(row["name"])
            with col2:
                if i > 0 and st.button("↑", key=f"up_div_{i}_{row['id']}"):
                    st.session_state["move_div_action"] = f"up_{i}"
                    st.rerun()
            with col3:
                if i < len(divisions) - 1 and st.button("↓", key=f"down_div_{i}_{row['id']}"):
                    st.session_state["move_div_action"] = f"down_{i}"
                    st.rerun()
            with col4:
                confirm = st.checkbox("削除確認", key=f"confirm_div_{i}_{row['id']}")
            with col5:
                if st.button("削除", key=f"del_div_{i}_{row['id']}"):
                    if confirm:
                        delete_division(row["id"])
                        st.success("削除しました。")
                        # 削除した事業部をセッションからも除外し、並び順を再更新
                        st.session_state.division_order = [d for d in st.session_state.division_order if d["id"] != row["id"]]
                        update_division_order(st.session_state.division_order)
                        st.rerun()
                    else:
                        st.warning("削除確認にチェックを入れてください。")
        
        # 万が一セッションがズレたときのためのリセットボタン
        if st.button("並び順を初期状態に戻す", key="reset_div_order"):
            st.session_state.division_order = get_division_records()
            update_division_order(st.session_state.division_order)
            st.success("現在のデータベースの順序に戻しました。")
            st.rerun()
    else:
        st.info("まだ事業部・店舗が登録されていません。")