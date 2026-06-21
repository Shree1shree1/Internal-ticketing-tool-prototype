"""
Supabase data-access layer for the Internal Ticketing Tool.
All Streamlit pages talk to the database only through these functions.
"""

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def create_ticket(title, description, category, urgency, created_by, ai_suggested_category=None):
    """Insert a new ticket. Status always starts as 'Open'."""
    client = get_client()
    data = {
        "title": title,
        "description": description,
        "category": category,
        "urgency": urgency,
        "created_by": created_by,
        "status": "Open",
        "ai_suggested_category": ai_suggested_category,
    }
    return client.table("tickets").insert(data).execute()


def get_tickets(filters: dict | None = None):
    """Fetch tickets, optionally filtered by exact-match columns (e.g. category, status, created_by)."""
    client = get_client()
    query = client.table("tickets").select("*").order("created_at", desc=True)
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    return query.execute().data


def update_ticket(ticket_id, updates: dict):
    """Update one or more fields on a ticket (status, resolution_notes, ai_suggested_response, ...)."""
    client = get_client()
    return client.table("tickets").update(updates).eq("id", ticket_id).execute()


def get_resolved_tickets(category: str | None = None):
    """Fetch previously Resolved/Closed tickets, used as the knowledge base for the AI layer."""
    client = get_client()
    query = client.table("tickets").select("*").in_("status", ["Resolved", "Closed"])
    if category:
        query = query.eq("category", category)
    return query.execute().data
