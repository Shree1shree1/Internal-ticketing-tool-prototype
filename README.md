# Internal Support Ticketing Tool

An internal web app that lets employees raise support tickets for IT, HR, Finance, or Admin, and lets agents track them through their full lifecycle — with an AI layer that auto-categorizes new tickets, surfaces similar past tickets to reduce duplicates, and drafts a first response for agents.

Built for The/Nudge Institute's AI Product Engineer internship assignment (Option A).

## Features

- **Full ticket lifecycle**: Open → In Progress → Resolved → Closed, with department-based routing.
- **Employee view**: submit a ticket with title, description, category, and urgency; check similar past tickets before submitting; view status of your own past tickets.
- **Agent view**: department-filtered ticket queue, status updates, AI-drafted first response, resolution notes, and an analytics dashboard.
- **AI layer**:
  - Auto-categorization of new tickets from their description, so employees don't have to guess the right department.
  - Similar-ticket search using TF-IDF + cosine similarity, surfaced before submission to cut down on duplicates.
  - Auto-drafted first response for agents, grounded in resolution notes from similar past tickets.
- **Analytics**: ticket counts by department, status, and urgency.

## Architecture

```
Employee/Agent (browser)
        |
   Streamlit (app.py)   <-- UI + page logic
        |
   +----+-----------------------+
   |                            |
db.py                      ai_utils.py
   |                            |
Supabase (Postgres)        Groq API (Llama 3.3 70B)
   |                       + scikit-learn (TF-IDF / cosine similarity,
tickets table                runs locally, no API call)
```

- **Frontend + app logic**: Streamlit (`app.py`) — single-page app with role selection (Employee / Agent) in the sidebar.
- **Storage**: Supabase (hosted Postgres), accessed through `db.py`. All reads/writes go through this one file so the rest of the app never talks to the database directly.
- **AI layer**: `ai_utils.py`, using two different techniques deliberately:
  - LLM calls (Groq, Llama 3.3 70B) for categorization and response drafting — tasks that need language understanding.
  - TF-IDF + cosine similarity (scikit-learn, no API call) for similar-ticket matching — a deterministic, free, low-latency technique that doesn't need an LLM for this kind of short-text matching.

## File structure

```
ticketing-tool/
├── app.py                         
├── db.py                          
├── ai_utils.py                     
├── schema.sql                      
├── requirements.txt                
├── .streamlit/
│   └── secrets.toml.example        
├── .gitignore                     
└── README.md
```

## Setup

### 1. Supabase (2 min)
1. Go to supabase.com, sign in, create a new project.
2. Open SQL Editor → New query → paste the contents of `schema.sql` → Run.
3. Go to Project Settings → Data API → copy the **Project URL**.
4. Go to Project Settings → API Keys → copy the **secret key** (`sb_secret_...`), or the **service_role** key if using the legacy tab.

### 2. Groq API key (1 min)
Go to console.groq.com → API Keys → create a key (free tier is enough for this prototype).

### 3. Local setup (3 min)
```bash
cd ticketing-tool
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

### 4. Try it end to end
1. Sidebar → **Employee** → fill in name, title, description → leave "let AI suggest" checked → Submit. It should auto-route to a department.
2. Sidebar → **Agent** → find the ticket → change status to Resolved → add resolution notes → Save.
3. Back to **Employee** → submit a second, related ticket → expand "Check similar past tickets" → the first ticket should appear with a similarity score.
4. Back to **Agent** → open the second ticket → click "Generate suggested response" → should produce a short drafted reply.
5. **Agent → Analytics** tab → charts by department, status, urgency.

### 5. Deploy (optional)
Push to a GitHub repo (with `.gitignore` excluding `secrets.toml`) → share.streamlit.io → New app → point at the repo → in "Advanced settings", paste the same three secrets directly into the Streamlit Cloud secrets box → Deploy.

## Design decisions and trade-offs

- **TF-IDF over embeddings for similar-ticket matching**: chosen for zero extra latency/cost and because ticket descriptions are short, making TF-IDF's keyword-overlap approach effective enough without the complexity of a vector database.
- **Two different AI techniques used deliberately**: classification and drafting genuinely need an LLM's language understanding; similarity search doesn't, so it stays local and fast.
- **No authentication**: employees self-report their name/email rather than logging in, to keep the prototype buildable in the time available. A production version would add Supabase Auth and Row Level Security policies so employees only see their own tickets and agents only see their department's queue.
- **No email notifications**: status changes are visible by refreshing the "My Tickets" tab rather than pushed via email, to avoid needing SMTP credentials for the prototype.
- **Groq (Llama 3.3 70B) over a hosted/paid LLM API**: free tier and low latency made it a practical choice for a fast build and live demo.

## Possible next steps
- Add Supabase Auth + Row Level Security for proper per-user/per-department access control.
- Add email or in-app push notifications on ticket status changes.
- Swap TF-IDF for sentence embeddings if ticket volume grows large enough that keyword overlap stops being a reliable similarity signal.
- Add an assigned-agent field and basic workload balancing across agents within a department.
