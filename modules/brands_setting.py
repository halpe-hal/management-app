# modules/brands_setting.py

import streamlit as st
from db.brands import (
    get_brand_records,
    add_brand,
    delete_brand,
    update_brand_order
)

def handle_brand_setting():

    # --- 新規ブランドの登録フォーム ---
    st.markdown("#### ブランドの新規登録")
    st.caption("ダッシュボードのセレクタに「ブランド名合計」として表示され、そのブランド名を含む全事業部の合計を集計します。")
    with st.form("brand_form", clear_on_submit=True):
        new_brand = st.text_input("ブランド名", placeholder="例：H.A.L. cafe")
        submitted = st.form_submit_button("登録")

        if submitted:
            if new_brand.strip() == "":
                st.warning("空欄では登録できません。")
            else:
                result = add_brand(new_brand.strip())
                if result == "success":
                    st.success("ブランドを登録しました。")
                    st.session_state.pop("brand_order", None)
                    st.rerun()
                elif result == "duplicate":
                    st.info("同じブランドがすでに登録されています。")
                else:
                    st.error("登録中にエラーが発生しました。")

    # --- 並び順のセッション保存（初期化） ---
    if "brand_order" not in st.session_state:
        brands = get_brand_records()
        st.session_state.brand_order = brands.copy()
    else:
        brands = st.session_state.brand_order

    # --- 並び替えアクションの記録と実行 ---
    move_key = st.session_state.get("move_brand_action", None)
    if move_key:
        action, idx = move_key.split("_")
        idx = int(idx)
        if action == "up" and idx > 0:
            brands[idx - 1], brands[idx] = brands[idx], brands[idx - 1]
            update_brand_order(brands)
        elif action == "down" and idx < len(brands) - 1:
            brands[idx + 1], brands[idx] = brands[idx], brands[idx + 1]
            update_brand_order(brands)
        del st.session_state["move_brand_action"]
        st.rerun()

    # --- 登録済みのブランド一覧（並び替え＆削除） ---
    if brands:
        st.markdown("#### 登録済みのブランド（並び替え＆削除）")
        for i, row in enumerate(brands):
            col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 2, 1])
            with col1:
                st.write(row["name"])
            with col2:
                if i > 0 and st.button("↑", key=f"up_brand_{i}_{row['id']}"):
                    st.session_state["move_brand_action"] = f"up_{i}"
                    st.rerun()
            with col3:
                if i < len(brands) - 1 and st.button("↓", key=f"down_brand_{i}_{row['id']}"):
                    st.session_state["move_brand_action"] = f"down_{i}"
                    st.rerun()
            with col4:
                confirm = st.checkbox("削除確認", key=f"confirm_brand_{i}_{row['id']}")
            with col5:
                if st.button("削除", key=f"del_brand_{i}_{row['id']}"):
                    if confirm:
                        delete_brand(row["id"])
                        st.success("削除しました。")
                        st.session_state.brand_order = [b for b in st.session_state.brand_order if b["id"] != row["id"]]
                        update_brand_order(st.session_state.brand_order)
                        st.rerun()
                    else:
                        st.warning("削除確認にチェックを入れてください。")

        if st.button("並び順を初期状態に戻す", key="reset_brand_order"):
            st.session_state.brand_order = get_brand_records()
            update_brand_order(st.session_state.brand_order)
            st.success("現在のデータベースの順序に戻しました。")
            st.rerun()
    else:
        st.info("まだブランドが登録されていません。")
