# db/supabase_client.py

from supabase import create_client
import streamlit as st

@st.cache_resource
def get_supabase_client():
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_API_KEY = st.secrets["SUPABASE_API_KEY"]
    return create_client(SUPABASE_URL, SUPABASE_API_KEY)

supabase = get_supabase_client()
