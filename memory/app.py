import streamlit as st
from retrieval import get_combined_logs
from generate_response import generate_response
from datetime import datetime
import re
import string
import plotly.graph_objects as go

# ------------------------- Stopwords + Keyword Tools -------------------------

STOPWORDS = {
    "the", "was", "in", "of", "and", "to", "for", "on", "at", "a", "an", "is", "are", "it", "as", "by",
    "that", "with", "be", "or", "from", "this", "which", "can", "but", "not", "if", "then", "do", "so",
    "about", "into", "we", "our", "their", "your"
}

def extract_keywords(query):
    query = query.translate(str.maketrans('', '', string.punctuation))  # remove punctuation
    return [kw for kw in query.lower().split() if kw not in STOPWORDS and len(kw) > 2]

def highlight_keywords(text, keywords):
    for kw in keywords:
        pattern = re.compile(rf"\b\w*{re.escape(kw)}\w*\b", re.IGNORECASE)
        text = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)
    return text

# ------------------------- Streamlit UI -------------------------

st.set_page_config(page_title="Memory Assistant Demo", page_icon="🧠")

st.markdown("""
    <style>
    .big-title {
        font-size: 2.2em;
        font-weight: bold;
    }
    .stButton > button {
        background-color: transparent;
        color: white;
        border: 2px solid #3B82F6;
        padding: 0.5rem 1.5rem;
        border-radius: 0.5rem;
        font-size: 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #3B82F6;
        color: white;
        border-color: #3B82F6;
    }
    .tag {
        display: inline-block;
        padding: 2px 10px;
        font-size: 0.75em;
        font-weight: 600;
        border-radius: 999px;
        margin-left: 10px;
        text-transform: capitalize;
    }
    .ticket     { background-color: #2563eb; color: white; }
    .summary    { background-color: #16a34a; color: white; }
    .decision   { background-color: #7e22ce; color: white; }
    .question   { background-color: #f97316; color: white; }
    .feedback   { background-color: #dc2626; color: white; }
    .milestone  { background-color: #6b7280; color: white; }
    .general    { background-color: #9ca3af; color: white; }
    .source-tag {
        background-color: #e5e7eb;
        color: #111827;
        font-size: 0.70em;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 500;
        margin-left: 8px;
        text-transform: uppercase;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🧠 Memory-Enhanced AI Assistant</div>', unsafe_allow_html=True)
st.markdown("Improve LLM responses by grounding them in long-term memory (Semantic + Temporal + Relational)")

# ------------------------- Input + Trigger -------------------------

query = st.text_input("📨 Ask a question", placeholder="e.g., Why was the feature rollout delayed in March?")
keywords = []
submit = st.button("🔍 Retrieve & Respond")

if submit and query:
    keywords = extract_keywords(query)
    st.markdown(f"**Extracted Keywords:** {keywords}")

    with st.spinner("Fetching memory and generating answer..."):
        retained_logs, discarded_logs = get_combined_logs(query, return_discarded=True)

        # Add parsed time
        for log in retained_logs:
            try:
                log["parsed_time"] = datetime.fromisoformat(log.get("timestamp", ""))
            except:
                log["parsed_time"] = datetime.min
        retained_logs.sort(key=lambda x: x["parsed_time"], reverse=True)

        raw_response, memory_response = generate_response(query)

        st.session_state["raw"] = raw_response
        st.session_state["memory"] = memory_response
        st.session_state["logs"] = retained_logs
        st.session_state["discarded"] = discarded_logs
        st.session_state["keywords"] = keywords

# ------------------------- Log Display + LLM Result -------------------------

if "logs" in st.session_state:
    logs = st.session_state["logs"]
    discarded_logs = st.session_state.get("discarded", [])
    keywords = st.session_state.get("keywords", [])

    st.markdown("### 📚 Retrieved Memory Logs")
    if not logs:
        st.info("No memory found for this query.")
    else:
        for log in logs:
            timestamp = log.get("timestamp", "Unknown time")
            speaker = log.get("user", "Unknown")
            raw_content = log.get("content", "No content available.")
            project = log.get("project", "Unknown")
            memory_type = log.get("type", "general")
            memory_source = log.get("source", "unknown")

            content = highlight_keywords(raw_content, keywords) if keywords else raw_content

            header = f"{timestamp} | {speaker} | Project: {project}"
            default_expanded = False if log.get("type") == "summary" else True
            with st.expander(header, expanded=default_expanded):
    
                st.markdown(
                    f"<span class='tag {memory_type}'>{memory_type.capitalize()}</span> "
                    f"<span class='source-tag'>{memory_source}</span>",
                    unsafe_allow_html=True
                )
                st.markdown(f"**Speaker:** {speaker}")
                st.markdown(f"**Timestamp:** {timestamp}")
                st.markdown(f"**Content:** {content}", unsafe_allow_html=True)
                st.markdown(f"**Project:** {project}")

        # ------------------------- Plotly Score Chart -------------------------

        st.markdown("### 📈 Log Relevance Scores")
        fig = go.Figure()
        for log in logs:
            score = log.get("score", 0)
            label = f"{log.get('source', 'Log')} | {log.get('user', '')[:6]} | {log.get('timestamp', '')[:10]}"
            fig.add_trace(go.Bar(
                x=[label],
                y=[score],
                name=label,
                hovertext=log.get("content", "")[:120] + "...",
                marker=dict(color="skyblue")
            ))
        fig.update_layout(
            height=400,
            margin=dict(l=30, r=30, t=30, b=30),
            xaxis_title="Logs",
            yaxis_title="Relevance Score",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # ------------------------- Discarded Logs Section -------------------------

        if discarded_logs:
            with st.expander("🗑️ Discarded Logs (Below Relevance Threshold)", expanded=False):
                for log in discarded_logs:
                    score = round(log.get("score", 0), 4)
                    st.markdown(f"**{log.get('timestamp', '')} | {log.get('user', 'Unknown')}**")
                    st.markdown(f"*Score:* {score}")
                    st.markdown(f"> {log.get('content', '')}")
                    st.markdown("---")

    # ------------------------- Final LLM Answer -------------------------

    st.markdown("### 🤖 Final LLM Response")
    mode = st.radio("Choose response type:", ["LLM + Memory", "LLM Only"], horizontal=True)
    if mode == "LLM Only" and "raw" in st.session_state:
        st.success(st.session_state["raw"])
    elif mode == "LLM + Memory" and "memory" in st.session_state:
        st.success(st.session_state["memory"])
