# auth.py

import streamlit as st
from db.supabase_client import supabase
from streamlit_javascript import st_javascript

def check_login():
    refresh_token = st_javascript("window.localStorage.getItem('refresh_token');", key="get_refresh")

    # JS評価前（初期ロード中）
    if refresh_token is None and "user" not in st.session_state:
        st.info("ログイン状態を確認中です…")
        st.stop()

    # refresh_token があるならセッション再取得
    if refresh_token and "access_token" not in st.session_state:
        try:
            res = supabase.auth.refresh_session(refresh_token)
            if res.session:
                st.session_state["user"] = {
                    "id": res.user.id,
                    "email": res.user.email
                }
                st.session_state["access_token"] = res.session.access_token
                st_javascript(f"""
                    window.localStorage.setItem('refresh_token', '{res.session.refresh_token}');
                """)
        except Exception:
            st.session_state.pop("user", None)
            st.session_state.pop("access_token", None)

    # 未ログインならフォーム表示
    if "user" not in st.session_state:
        # --- ログインフォームを中央寄せ + 幅制限 ---
        col1, col2, col3 = st.columns([1, 2, 1])  # 中央を狭めて表示

        with col2:
            with st.form("login_form"):
                st.markdown("##  ログイン")
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                submitted = st.form_submit_button("ログイン")

                if submitted:
                    try:
                        res = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        if res.session:
                            st.session_state["user"] = {
                                "id": res.user.id,
                                "email": res.user.email
                            }
                            st.session_state["access_token"] = res.session.access_token
                            st_javascript(f"""
                                window.localStorage.setItem('refresh_token', '{res.session.refresh_token}');
                            """)
                            st.success("ログイン成功！")
                            st.rerun()
                        else:
                            st.error("ログインに失敗しました。")
                    except Exception:
                        st.error("メールアドレスまたはパスワードが間違っています。")

        st.stop()

def logout():
    st_javascript("window.localStorage.removeItem('refresh_token');", key="remove_refresh")
    st.session_state.clear()
    st.success("ログアウトしました")
    st.rerun()
