import streamlit as st
import time
import re
from agents import build_search_agent, build_search_agent, writer_chain, critic_chain, build_reader_agent


# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeepLens — AI Research System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }

    /* ── Hero Header ── */
    .hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
    }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero p {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        max-width: 640px;
        margin: 0 auto;
    }

    /* ── Agent Cards ── */
    .agent-card {
        background: linear-gradient(145deg, rgba(30,30,46,0.85), rgba(24,24,37,0.95));
        border: 1px solid rgba(99,102,241,0.18);
        border-radius: 16px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(10px);
        transition: border-color 0.3s ease;
    }
    .agent-card:hover {
        border-color: rgba(99,102,241,0.45);
    }
    .agent-card h3 {
        margin: 0 0 0.8rem;
        font-size: 1.15rem;
        font-weight: 600;
    }
    .agent-card .content {
        font-size: 0.88rem;
        line-height: 1.7;
        color: #cbd5e1;
        white-space: pre-wrap;
        max-height: 420px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }

    /* ── Score Badge ── */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
        border-radius: 14px;
        margin: 0.5rem 0 1rem;
    }

    /* ── Step indicator pills ── */
    .step-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .step-active {
        background: rgba(99,102,241,0.2);
        color: #818cf8;
        border: 1px solid rgba(99,102,241,0.35);
    }
    .step-done {
        background: rgba(34,197,94,0.15);
        color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
    }
    .step-pending {
        background: rgba(100,116,139,0.12);
        color: #64748b;
        border: 1px solid rgba(100,116,139,0.2);
    }

    /* ── Input area ── */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        padding: 0.7rem 1rem !important;
        font-size: 1rem !important;
        background: rgba(15,15,25,0.6) !important;
        transition: border-color 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
    }

    /* ── Button ── */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.65rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: transform 0.15s ease, box-shadow 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99,102,241,0.35) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ── Divider ── */
    .styled-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), transparent);
        margin: 2rem 0;
        border: none;
    }

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Scrollbar styling for agent cards */
    .agent-card .content::-webkit-scrollbar {
        width: 5px;
    }
    .agent-card .content::-webkit-scrollbar-track {
        background: transparent;
    }
    .agent-card .content::-webkit-scrollbar-thumb {
        background: rgba(99,102,241,0.3);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper: render an agent card ─────────────────────────────────────────────
def agent_card(icon: str, title: str, body: str, color: str = "#818cf8"):
    st.markdown(f"""
    <div class="agent-card">
        <h3 style="color:{color}">{icon}&ensp;{title}</h3>
        <div class="content">{body}</div>
    </div>
    """, unsafe_allow_html=True)


# ─── Helper: parse critic score ───────────────────────────────────────────────
def parse_score(feedback: str) -> str | None:
    match = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback, re.IGNORECASE)
    return match.group(1) if match else None


# ─── Helper: step pills ──────────────────────────────────────────────────────
STEPS = [
    ("🔍", "Search"),
    ("📖", "Reader"),
    ("✍️", "Writer"),
    ("🧐", "Critic"),
]

def render_step_bar(active_index: int):
    pills = ""
    for i, (icon, name) in enumerate(STEPS):
        if i < active_index:
            cls = "step-done"
            indicator = "✓"
        elif i == active_index:
            cls = "step-active"
            indicator = "⟳"
        else:
            cls = "step-pending"
            indicator = "·"
        pills += f'<span class="step-pill {cls}">{indicator} {icon} {name}</span>'
    st.markdown(pills, unsafe_allow_html=True)


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🔬 DeepLens</h1>
    <p>Your autonomous AI research team — agents that search, read, write, and critique — so you don't have to.</p>
</div>
""", unsafe_allow_html=True)

# ─── Agent One-Liners ─────────────────────────────────────────────────────────
a1, a2, a3, a4 = st.columns(4)
with a1:
    st.markdown("🔍 **Search Agent**")
    st.caption("Scours the live web for the latest, most reliable sources.")
with a2:
    st.markdown("📖 **Reader Agent**")
    st.caption("Scrapes top links and extracts the important details.")
with a3:
    st.markdown("✍️ **Writer Agent**")
    st.caption("Synthesizes everything into a polished research report.")
with a4:
    st.markdown("🧐 **Critic Agent**")
    st.caption("Reviews the report for accuracy, depth, and clarity.")

st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)


# ─── Sample Topics ─────────────────────────────────────────────────────────────
SAMPLE_TOPICS = [
    "Latest breakthroughs in quantum computing 2026",
    "How AI is transforming drug discovery",
    "The future of renewable energy storage",
    "Impact of large language models on education",
    "Space debris removal technologies",
    "CRISPR gene editing recent advances",
    "Global semiconductor chip shortage analysis",
    "Rise of autonomous vehicles in urban transport",
]

# Use session state to hold the selected sample topic
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = ""

with st.expander("💡 **Need inspiration? Browse sample topics**", expanded=False):
    cols = st.columns(2)
    for idx, sample in enumerate(SAMPLE_TOPICS):
        with cols[idx % 2]:
            if st.button(sample, key=f"sample_{idx}", use_container_width=True):
                st.session_state.selected_topic = sample


# ─── Input ─────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1], vertical_alignment="bottom")
with col_input:
    topic = st.text_input(
        "Research Topic",
        value=st.session_state.selected_topic,
        placeholder="e.g.  Latest breakthroughs in quantum computing 2026",
        label_visibility="collapsed",
    )
with col_btn:
    run_clicked = st.button("🚀  Research", use_container_width=True)


# ─── Pipeline Execution ───────────────────────────────────────────────────────
if run_clicked and topic.strip():
    state = {}

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # ── Step 1: Search Agent ──────────────────────────────────────────────
    render_step_bar(0)
    with st.status("🔍  **Search Agent** is finding relevant information…", expanded=True) as status:
        st.caption("Querying the live web via Tavily for recent, reliable sources…")
        search_agent = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        state["search_results"] = search_result["messages"][-1].content
        status.update(label="🔍  **Search Agent** — done!", state="complete", expanded=False)

    agent_card("🔍", "Search Results", state["search_results"], "#60a5fa")

    # ── Step 2: Reader Agent ──────────────────────────────────────────────
    render_step_bar(1)
    with st.status("📖  **Reader Agent** is scraping top resources…", expanded=True) as status:
        st.caption("Picking the most relevant URL and extracting deeper content…")
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "messages": [("user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )]
        })
        state["scraped_content"] = reader_result["messages"][-1].content
        status.update(label="📖  **Reader Agent** — done!", state="complete", expanded=False)

    agent_card("📖", "Scraped Content", state["scraped_content"], "#34d399")

    # ── Step 3: Writer Chain ──────────────────────────────────────────────
    render_step_bar(2)
    with st.status("✍️  **Writer Agent** is drafting the report…", expanded=True) as status:
        st.caption("Synthesizing all research into a structured, professional report…")
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined,
        })
        status.update(label="✍️  **Writer Agent** — done!", state="complete", expanded=False)

    agent_card("✍️", "Research Report", state["report"], "#a78bfa")

    # ── Step 4: Critic Chain ──────────────────────────────────────────────
    render_step_bar(3)
    with st.status("🧐  **Critic Agent** is reviewing the report…", expanded=True) as status:
        st.caption("Evaluating accuracy, depth, and clarity of the report…")
        state["feedback"] = critic_chain.invoke({
            "report": state["report"],
        })
        status.update(label="🧐  **Critic Agent** — done!", state="complete", expanded=False)

    # ── Final Results ─────────────────────────────────────────────────────
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)
    render_step_bar(4)  # all done

    st.markdown("""
    <div class="hero" style="padding: 1.2rem 0 0.5rem;">
        <h1 style="font-size:1.8rem;">📋 Final Results</h1>
    </div>
    """, unsafe_allow_html=True)

    # Score badge
    score = parse_score(state["feedback"])
    if score:
        st.markdown(f'<div style="text-align:center"><span class="score-badge">⭐ {score} / 10</span></div>', unsafe_allow_html=True)

    col_report, col_critic = st.columns([3, 2])

    with col_report:
        agent_card("✍️", "Final Report", state["report"], "#a78bfa")

    with col_critic:
        agent_card("🧐", "Critic Review", state["feedback"], "#fb923c")

    # Download button for the report
    st.download_button(
        label="📥  Download Report as Text",
        data=f"# Research Report: {topic}\n\n{state['report']}\n\n---\n\n# Critic Review\n\n{state['feedback']}",
        file_name=f"research_report_{topic[:40].replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True,
    )

elif run_clicked and not topic.strip():
    st.warning("⚠️  Please enter a research topic to begin.")


# ─── Sidebar Info ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧩 How It Works")
    st.markdown("""
    This system uses **4 specialized AI agents** working in sequence:

    **1. 🔍 Search Agent**
    Queries the live web via Tavily API to find the most recent and reliable sources.

    **2. 📖 Reader Agent**
    Scrapes the most relevant URLs using BeautifulSoup to extract deeper content.

    **3. ✍️ Writer Agent**
    Synthesizes all gathered research into a well-structured, professional report.

    **4. 🧐 Critic Agent**
    Reviews the final report for accuracy, depth, and clarity — providing a score and feedback.

    ---
    *Powered by LangChain LCEL & Google Gemini*
    """)
