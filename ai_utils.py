import streamlit as st
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CATEGORIES = ["IT", "HR", "Finance", "Admin"]
MODEL = "llama-3.3-70b-versatile"  # fast + free-tier friendly on Groq, good enough for routing/drafting


@st.cache_resource
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


def categorize_ticket(description: str) -> str:
    """Classify a ticket description into one of CATEGORIES using Groq."""
    client = get_groq_client()
    prompt = (
        "You are routing internal employee support tickets for an organization.\n"
        f"Classify the ticket description below into exactly ONE of these categories: "
        f"{', '.join(CATEGORIES)}.\n\n"
        f'Ticket description: "{description}"\n\n'
        "Respond with ONLY the category name, nothing else."
    )
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}],
    )
    category = response.choices[0].message.content.strip()
    return category if category in CATEGORIES else "Admin"


def find_similar_tickets(description: str, past_tickets: list, top_n: int = 3, min_score: float = 0.1):
    """
    Rank past_tickets by TF-IDF cosine similarity to `description`.
    Returns a list of (ticket_dict, similarity_score) tuples, highest first.
    """
    if not past_tickets:
        return []

    corpus = [t["description"] for t in past_tickets] + [description]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    sims = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    ranked = sorted(zip(past_tickets, sims), key=lambda pair: pair[1], reverse=True)
    return [(t, score) for t, score in ranked[:top_n] if score > min_score]


def draft_response(description: str, similar_tickets: list) -> str:
    """Draft a short first response for the agent, using similar past resolutions as grounding context."""
    client = get_groq_client()

    context = ""
    for t, _score in similar_tickets:
        if t.get("resolution_notes"):
            context += f'- Similar past ticket "{t["title"]}" was resolved with: {t["resolution_notes"]}\n'

    prompt = (
        "You are an internal support-desk assistant. Draft a brief, professional first response "
        "to the employee who raised this ticket.\n\n"
        f'Ticket description: "{description}"\n\n'
        f"Relevant past resolutions for context:\n{context if context else 'None available.'}\n\n"
        "Write a 2-4 sentence first response: acknowledge the issue, and outline next steps. "
        "Do not promise a specific resolution time unless the past tickets give a clear basis for it."
    )
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
