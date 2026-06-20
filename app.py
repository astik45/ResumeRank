import streamlit as st
import os

from utils.ingest_single import ingest_resume
from utils.pinecone_utils import delete_all_vectors
from query_engine import search_resumes

st.set_page_config(
    page_title="ResumeRank | AI-Powered Resume Ranking",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: -1.5px;
        background: linear-gradient(135deg, #a78bfa 0%, #f472b6 50%, #fbbf24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .category-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        letter-spacing: 0.5px;
    }
    .badge-cloud { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-frontend { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-backend { background-color: #fae8ff; color: #7c3aed; border: 1px solid #f0abfc; }
    .badge-ai_ml { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }
    .badge-general { background-color: #f5f5f4; color: #57534e; border: 1px solid #e7e5e4; }

    .candidate-card {
        background: white;
        border: 1px solid #e7e5e4;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
    }
    .candidate-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border-color: #d6d3d1;
    }

    .candidate-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .candidate-source {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1c1917;
    }

    .candidate-score {
        font-weight: 600;
        color: #0f766e;
        background: #ccfbf1;
        border: 1px solid #99f6e4;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
    }

    .candidate-body {
        font-size: 0.9rem;
        color: #57534e;
        background: #fafaf9;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #f5f5f4;
        line-height: 1.6;
    }

    .summary-box {
        background: linear-gradient(135deg, #faf5ff 0%, #fdf2f8 100%);
        border: 1px solid #e9d5ff;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 24px;
        color: #292524;
        position: relative;
    }
    .summary-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(to bottom, #a78bfa, #f472b6);
        border-radius: 4px 0 0 4px;
    }

    .trace-step-card {
        background: #fafaf9;
        border: 1px solid #e7e5e4;
        border-left: 4px solid #a78bfa;
        padding: 16px;
        margin-bottom: 14px;
        border-radius: 0 10px 10px 0;
    }

    .trace-step-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #7c3aed;
        margin-bottom: 8px;
    }

    .sidebar-doc-item {
        background: #fafaf9;
        border: 1px solid #e7e5e4;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        font-size: 0.8rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .sidebar-doc-item:hover {
        border-color: #d6d3d1;
        background: white;
    }
    .sidebar-doc-item span {
        margin-left: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .status-dot {
        height: 7px;
        width: 7px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
    }

    .sidebar-box {
        background: #fafaf9;
        border: 1px solid #e7e5e4;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>ResumeRank | AI-Powered Resume Ranking</div>", unsafe_allow_html=True)

st.sidebar.markdown("### System Dashboard")

st.sidebar.markdown(
    """
    <div class="sidebar-box">
        <div style="font-weight: 700; margin-bottom: 8px; font-size: 0.95rem; color: #1c1917;">RAG Engine Status</div>
        <div style="font-size: 0.85rem; margin-bottom: 6px;"><span class="status-dot"></span><strong>LLM Engine</strong>: gemini-2.5-flash</div>
        <div style="font-size: 0.85rem; margin-bottom: 6px;"><span class="status-dot"></span><strong>Embeddings</strong>: gemini-embedding-2 (384d)</div>
        <div style="font-size: 0.85rem; margin-bottom: 6px;"><span class="status-dot"></span><strong>Vector DB</strong>: Pinecone (Serverless)</div>
        <div style="font-size: 0.85rem;"><span class="status-dot"></span><strong>Metadata Filter</strong>: Category Match</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.subheader("Indexed Documents")

os.makedirs("data/resumes", exist_ok=True)
resume_files = os.listdir("data/resumes")

if resume_files:
    for file in resume_files:
        st.sidebar.markdown(
            f"""
            <div class="sidebar-doc-item">
                📄 <span title="{file}">{file}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.sidebar.write("No resumes uploaded yet.")

st.sidebar.markdown("---")
st.sidebar.subheader("Ingest New Resume")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

uploaded_file = st.sidebar.file_uploader(
    "Upload PDF Resume",
    type=["pdf"],
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    save_path = os.path.join("data/resumes", uploaded_file.name)
    
    with st.sidebar.spinner("Uploading and indexing..."):
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            category = ingest_resume(save_path, uploaded_file.name)
            st.sidebar.success(f"Successfully Indexed!")
            st.sidebar.markdown(f"Category: **{category.upper()}**")
            st.session_state.uploader_key += 1
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error during ingestion: {e}")
            st.session_state.uploader_key += 1

st.sidebar.markdown("---")
if st.sidebar.button("Clear Vector DB & Resumes", use_container_width=True):
    with st.sidebar.spinner("Clearing storage..."):
        for file in os.listdir("data/resumes"):
            try:
                os.remove(os.path.join("data/resumes", file))
            except Exception:
                pass
        try:
            delete_all_vectors()
            st.sidebar.success("Database and local storage cleared!")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
        st.rerun()

query = st.text_input(
    "Search Candidate Profiles",
    placeholder="Enter search requirements (e.g. Python backend engineer, machine learning specialist, React developer)",
    label_visibility="collapsed"
)

generate_summary = st.checkbox(
    "Generate AI Analysis & Summary (uses Gemini text generation quota)",
    value=True,
    help="Uncheck this to run semantic matching only, which uses fast embeddings and saves your Gemini daily text generation quota."
)

if "results" not in st.session_state:
    st.session_state.results = None
if "query" not in st.session_state:
    st.session_state.query = ""
if "generate_summary" not in st.session_state:
    st.session_state.generate_summary = True

col1, col2 = st.columns([1, 5])
with col1:
    search_triggered = st.button("Search Candidates", use_container_width=True, type="primary")

query_changed = (query and query != st.session_state.query)
toggle_changed = (generate_summary != st.session_state.generate_summary)

if (search_triggered or query_changed or toggle_changed) and query:
    spinner_text = "Executing RAG Pipeline..." if generate_summary else "Retrieving Candidates from Pinecone..."
    with st.spinner(spinner_text):
        st.session_state.results = search_resumes(query, generate_summary=generate_summary)
        st.session_state.query = query
        st.session_state.generate_summary = generate_summary

if st.session_state.results is not None:
    results = st.session_state.results
    cat = results["category"]
    
    st.markdown("### AI Analysis & Summary")
    st.markdown(f"""
    <div class='summary-box'>
        <div class='category-badge badge-{cat}'>{cat}</div>
        <div style='margin-top: 10px; line-height: 1.7;'>{results["answer"]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Top Ranked Candidates")
    if not results["matches"]:
        st.info("No matching candidate segments found for this category.")
    else:
        for i, match in enumerate(results["matches"], start=1):
            metadata = match["metadata"]
            score = round(match["score"], 3)
            source_name = metadata.get('source', 'Unknown').replace('.pdf', '')
            
            st.markdown(f"""
            <div class='candidate-card'>
                <div class='candidate-header'>
                    <div class='candidate-source'>📄 Rank #{i} — {source_name}</div>
                    <div class='candidate-score'>Match Score: {score}</div>
                </div>
                <div class='candidate-body'>
                    {metadata.get('text', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
with st.expander("🛠️ Pipeline Trace (Reviewer Panel)", expanded=True):
    if st.session_state.results:
        trace = st.session_state.results["trace"]
        
        st.write("Shows what the pipeline did step by step.")
        
        st.markdown(f"""
        <div class='trace-step-card'>
            <div class='trace-step-title'>Step 1: Query Category Classification</div>
            <div>Predicted Category: <span class='category-badge badge-{trace['classification']['category']}'>{trace['classification']['category']}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Classification System Prompt:")
        st.code(trace["classification"]["prompt"], language="text")
        st.caption("LLM Raw Classification Response:")
        st.code(trace["classification"]["raw_response"], language="text")
        
        st.markdown(f"""
        <div class='trace-step-card'>
            <div class='trace-step-title'>Step 2: Query Embedding Generation</div>
            <div>Model: <code>{trace['embedding']['model']}</code> | Dimensions requested: <code>{trace['embedding']['dimensions']}</code></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Query Vector Sample (First 10 Dimensions):")
        st.code(str(trace["embedding"]["vector_sample"]), language="json")
        
        search_trace = trace['search']
        fallback_label = "✅ Yes (unfiltered search used)" if search_trace.get('fallback_used') else "❌ No (filter was sufficient)"
        st.markdown(f"""
        <div class='trace-step-card'>
            <div class='trace-step-title'>Step 3: Pinecone Vector Search with Source Deduplication</div>
            <div>Filter Payload: <code>{str(search_trace['filter'])}</code></div>
            <div>Filtered Chunks Retrieved: <code>{search_trace.get('filtered_chunks_retrieved', 'N/A')}</code></div>
            <div>Unique Resume Sources After Dedup: <code>{search_trace.get('unique_sources_after_dedup', 'N/A')}</code></div>
            <div>Fallback (Unfiltered) Search Used: <code>{fallback_label}</code></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Deduplicated Matches (Best chunk per resume):")
        st.json(search_trace["raw_matches"])
        
        st.markdown(f"""
        <div class='trace-step-card'>
            <div class='trace-step-title'>Step 4: Readable Q&A Answer Generation</div>
            <div>Model: <code>gemini-2.5-flash</code></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("System Instruction Prompt:")
        st.code(trace["generation"]["system_instruction"], language="text")
        st.caption("LLM Prompt Context:")
        st.code(trace["generation"]["prompt"], language="text")
        st.caption("LLM Generated Summary:")
        st.code(trace["generation"]["raw_response"], language="text")
    else:
        st.info("Submit a search query to inspect the detailed pipeline trace steps.")
