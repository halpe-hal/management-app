# db/income_sources.py

from db.supabase_client import supabase
import logging
from datetime import datetime

def get_income_sources() -> list:
    try:
        res = supabase.table("income_sources").select("*").order("id").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_income_sources error: {e}")
        return []

def add_income_source(data: dict) -> str:
    try:
        supabase.table("income_sources").insert({
            "top_category": data["top_category"],
            "partner": data["partner"],
            "expected_amount": data["expected_amount"],
            "received_amount": data["received_amount"],
            "payment": data["payment"],
            "detail": data.get("detail", ""),
            "tax_rate": data.get("tax_rate", ""),
            "updated_at": datetime.now().isoformat()
        }).execute()
        return "success"
    except Exception as e:
        logging.error(f"add_income_source error: {e}")
        return "error"

def update_income_source(id: int, field: str, value) -> bool:
    try:
        supabase.table("income_sources").update({
            field: value,
            "updated_at": datetime.now().isoformat()
        }).eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"update_income_source error: {e}")
        return False

def delete_income_source(id: int) -> bool:
    try:
        supabase.table("income_sources").delete().eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_income_source error: {e}")
        return False
