# Internal Support Ticketing Tool — Setup

## 1. Supabase (2 min)
1. Go to supabase.com, sign in with GitHub, create a new project.
2. Open SQL Editor → New query → paste the contents of `schema.sql` → Run.
3. Go to Project Settings → API → copy the **Project URL** and the **anon public key**.

## 2. Groq API key (1 min)
1. Go to console.groq.com → API Keys → create a key (free tier is fine for this prototype).

## 3. Local setup (3 min)
```bash
cd ticketing-tool
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# paste your real SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY into secrets.toml
streamlit run app.py
```

## 4. Try it end to end
1. In the sidebar pick **Employee** → fill in name, title, description → leave
   "let AI suggest" checked → Submit. Watch it get auto-routed to a department.
2. Switch to **Agent** in the sidebar → see the ticket in the queue → change
   status → click "Generate suggested response" to see the AI draft → add
   resolution notes → Save.
3. Submit a second, similar ticket as Employee and expand "Check similar past
   tickets" — it should surface the first one once it's marked Resolved.
4. Check the **Analytics** tab under Agent for the department/status/urgency charts.

## 5. Deploy (optional, 5 min)
Push this folder to a GitHub repo → share.streamlit.io → New app → point at
the repo → in "Advanced settings", paste the same secrets → Deploy.

## Notes for your write-up
- Architecture: Streamlit (frontend + app logic) → Supabase/Postgres (storage)
  → Llama 3.3 70B via Groq API (categorization + draft responses) →
  scikit-learn TF-IDF + cosine similarity (similar-ticket search, no extra
  API calls needed for this part).
- Known simplifications made for the 2-hour build: no authentication (name/
  email is self-reported), no email notifications (status changes are visible
  in the "My Tickets" tab on refresh), no RLS policies yet (commented in
  schema.sql as a next step).
