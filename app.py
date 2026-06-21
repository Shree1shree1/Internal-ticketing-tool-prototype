import pandas as pd
import streamlit as st

import ai_utils
import db

st.set_page_config(page_title="Internal Ticketing Tool", layout="wide")
st.title("🎫 Internal Support Ticketing Tool")

DEPARTMENTS = ["IT", "HR", "Finance", "Admin"]
URGENCY_LEVELS = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

role = st.sidebar.radio("I am a:", ["Employee", "Agent"])


if role == "Employee":
    tab_new, tab_mine = st.tabs(["📝 Raise a Ticket", "📋 My Tickets"])

    with tab_new:
        employee_name = st.text_input("Your name / email")
        title = st.text_input("Ticket title")
        description = st.text_area("Describe your issue", height=120)

        col1, col2 = st.columns(2)
        with col1:
            unsure = st.checkbox("Not sure which department — let AI suggest", value=True)
            category = None if unsure else st.selectbox("Category", DEPARTMENTS)
        with col2:
            urgency = st.selectbox("Urgency", URGENCY_LEVELS, index=1)

        if description and len(description) > 15:
            with st.expander("🔍 Check similar past tickets before submitting"):
                past = db.get_resolved_tickets()
                similar = ai_utils.find_similar_tickets(description, past)
                if similar:
                    for t, score in similar:
                        st.markdown(f"**{t['title']}**  ·  {t['category']}  ·  similarity {score:.0%}")
                        if t.get("resolution_notes"):
                            st.caption(f"Resolution: {t['resolution_notes']}")
                else:
                    st.caption("No closely matching past tickets found.")
        
        if st.button("Submit Ticket", type="primary"):
            if not (employee_name and title and description):
                st.error("Please fill in your name, title, and description.")
            else:
                final_category, ai_suggested = category, None
                if unsure or not category:
                    with st.spinner("AI is categorizing your ticket..."):
                        ai_suggested = ai_utils.categorize_ticket(description)
                        final_category = ai_suggested
                db.create_ticket(title, description, final_category, urgency, employee_name, ai_suggested)
                st.success(f"Ticket submitted and routed to **{final_category}**.")
                st.rerun()

    with tab_mine:
        lookup_name = st.text_input("Enter your name/email to view your tickets", key="emp_lookup")
        if lookup_name:
            my_tickets = db.get_tickets({"created_by": lookup_name})
            if my_tickets:
                df = pd.DataFrame(my_tickets)[["title", "category", "urgency", "status", "created_at"]]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No tickets found for this name/email.")


else:
    tab_queue, tab_analytics = st.tabs(["📥 Ticket Queue", "📊 Analytics"])

    with tab_queue:
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("Department queue", ["All"] + DEPARTMENTS)
        with col2:
            status_filter = st.selectbox("Status filter", ["All"] + STATUSES)

        filters = {}
        if dept_filter != "All":
            filters["category"] = dept_filter
        if status_filter != "All":
            filters["status"] = status_filter

        tickets = db.get_tickets(filters)

        if not tickets:
            st.info("No tickets match this filter.")

        for t in tickets:
            with st.container(border=True):
                left, right = st.columns([3, 1])

                with left:
                    st.markdown(f"**{t['title']}**  \n{t['description']}")
                    st.caption(
                        f"From: {t['created_by']}  |  Category: {t['category']}  |  "
                        f"Urgency: {t['urgency']}  |  Created: {t['created_at']}"
                    )
                    if t.get("ai_suggested_category"):
                        st.caption(f"🤖 AI suggested category: {t['ai_suggested_category']}")

                with right:
                    new_status = st.selectbox(
                        "Status", STATUSES, index=STATUSES.index(t["status"]), key=f"status_{t['id']}"
                    )
                    if new_status != t["status"] and st.button("Update", key=f"update_{t['id']}"):
                        db.update_ticket(t["id"], {"status": new_status})
                        st.success("Status updated.")
                        st.rerun()

                with st.expander("AI-suggested first response & resolution notes"):
                    if st.button("Generate suggested response", key=f"draft_{t['id']}"):
                        with st.spinner("Drafting..."):
                            past = db.get_resolved_tickets(category=t["category"])
                            similar = ai_utils.find_similar_tickets(t["description"], past)
                            st.session_state[f"draft_text_{t['id']}"] = ai_utils.draft_response(
                                t["description"], similar
                            )

                    draft_text = st.session_state.get(f"draft_text_{t['id']}", t.get("ai_suggested_response") or "")
                    st.text_area("Suggested response", value=draft_text, key=f"draft_area_{t['id']}", height=100)

                    resolution_notes = st.text_area(
                        "Resolution notes (feeds future similar-ticket matching)",
                        value=t.get("resolution_notes") or "",
                        key=f"notes_{t['id']}",
                    )
                    if st.button("Save notes", key=f"save_notes_{t['id']}"):
                        db.update_ticket(t["id"], {"resolution_notes": resolution_notes})
                        st.success("Notes saved.")

    with tab_analytics:
        all_tickets = db.get_tickets()
        if all_tickets:
            df = pd.DataFrame(all_tickets)

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Tickets by Department")
                st.bar_chart(df["category"].value_counts())
            with c2:
                st.subheader("Tickets by Status")
                st.bar_chart(df["status"].value_counts())

            st.subheader("Tickets by Urgency")
            st.bar_chart(df["urgency"].value_counts())

            st.subheader("All Tickets")
            st.dataframe(
                df[["title", "category", "urgency", "status", "created_by", "created_at"]],
                use_container_width=True,
            )
        else:
            st.info("No tickets yet.")
