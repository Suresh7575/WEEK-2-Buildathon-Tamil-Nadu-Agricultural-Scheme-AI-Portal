import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
from pathlib import Path

# 1. Page Configuration
st.set_page_config(
    page_title="Tamil Nadu Agricultural Scheme AI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8000/ask"
VIDEO_DIR = Path(r"D:\Personal\GenAI Program\WEEK 2 · Buildathon Tamil Nadu Agricultural Scheme AI Portal\Agricultural_Scheme_AI\data\Videos")
BG_IMAGE_PATH = VIDEO_DIR / "backgroun.png"

# Helper: Encode local file to Base64 for CSS background & HTML5 video playlist
def get_base64_str(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Helper: Load video files dynamically
def get_local_videos(folder_path: Path):
    if not folder_path.exists():
        return []
    supported_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")
    return sorted([f for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() in supported_exts])

local_videos = get_local_videos(VIDEO_DIR)
bg_base64 = get_base64_str(BG_IMAGE_PATH)

# 2. Custom CSS: Full-Page Background Image + Bright High-Contrast Glass UI
bg_css = f"""
    background-image: linear-gradient(rgba(6, 20, 9, 0.74), rgba(6, 20, 9, 0.80)), url("data:image/png;base64,{bg_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
""" if bg_base64 else """
    background: linear-gradient(180deg, #0d2612 0%, #163a1e 100%);
"""

st.markdown(f"""
    <style>
    /* Full Page Agricultural Image Background */
    .stApp {{
        {bg_css}
        color: #ffffff !important;
    }}

    /* Make all standard Streamlit text bright & visible */
    .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
        color: #ffffff !important;
    }}

    /* Sidebar Glass Styling */
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 28, 14, 0.92) !important;
        border-right: 2px solid #66bb6a;
    }}
    [data-testid="stSidebar"] * {{
        color: #f1f8e9 !important;
    }}
    [data-testid="stSidebar"] .stButton button {{
        background-color: rgba(46, 125, 50, 0.85) !important;
        color: #ffffff !important;
        border: 1px solid #81c784 !important;
        border-radius: 8px;
        text-align: left;
    }}
    [data-testid="stSidebar"] .stButton button:hover {{
        background-color: #43a047 !important;
        border-color: #ffd54f !important;
    }}

    /* Main Hero Banner */
    .hero-banner {{
        background: linear-gradient(135deg, rgba(27, 94, 32, 0.92) 0%, rgba(46, 125, 50, 0.88) 60%, rgba(104, 159, 56, 0.88) 100%);
        padding: 1.5rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255, 255, 255, 0.35);
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(8px);
    }}
    .hero-banner h1 {{
        color: #ffffff !important;
        margin-bottom: 0.3rem;
        font-size: 2.1rem;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}
    .hero-banner p {{
        color: #e8f5e9 !important;
        font-size: 1.05rem;
        margin-bottom: 0;
    }}

    /* Highlighted Section Headers */
    .ai-spotlight-header {{
        background: linear-gradient(90deg, #1b5e20, #388e3c);
        color: #ffffff !important;
        padding: 0.85rem 1.3rem;
        border-radius: 12px 12px 0 0;
        font-size: 1.3rem;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.25);
        border-bottom: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .section-banner {{
        background: linear-gradient(90deg, rgba(27, 94, 32, 0.92), rgba(56, 142, 60, 0.88));
        color: #ffffff !important;
        padding: 0.75rem 1.3rem;
        border-radius: 10px;
        font-size: 1.25rem;
        font-weight: 700;
        margin-top: 1.6rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.25);
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    }}

    /* Frosted Dark Glass Containers for Chat & Inputs */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: rgba(12, 30, 16, 0.84) !important;
        border: 1px solid rgba(129, 199, 132, 0.45) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
    }}

    /* Chat Message Bubbles */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.10) !important;
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }}

    /* Search Input Box */
    .stTextInput input {{
        background-color: rgba(15, 38, 20, 0.90) !important;
        color: #ffffff !important;
        border: 1px solid #81c784 !important;
        border-radius: 8px;
    }}
    .stTextInput input::placeholder {{
        color: #c8e6c9 !important;
    }}

    /* Scheme Cards: Dark Translucent Glass with Bright High-Contrast Text */
    .scheme-card {{
        background-color: rgba(14, 36, 18, 0.88) !important;
        border-left: 6px solid #ffd54f;
        border-top: 1px solid rgba(165, 214, 167, 0.35);
        border-right: 1px solid rgba(165, 214, 167, 0.35);
        border-bottom: 1px solid rgba(165, 214, 167, 0.35);
        padding: 1.15rem 1.35rem;
        border-radius: 12px;
        margin-bottom: 0.95rem;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
    }}
    .scheme-card h4 {{
        color: #ffd54f !important;
        margin-top: 0.25rem;
        margin-bottom: 0.55rem;
        font-size: 1.14rem;
    }}
    .scheme-card p {{
        color: #f1f8e9 !important;
        font-size: 0.96rem;
        line-height: 1.55;
    }}
    .scheme-card b {{
        color: #a5d6a7 !important;
    }}
    .scheme-card .officer-text {{
        color: #dce775 !important;
        font-size: 0.9rem;
    }}
    .badge {{
        display: inline-block;
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        padding: 0.25rem 0.8rem;
        border-radius: 14px;
        font-size: 0.84rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
        border: 1px solid #81c784;
    }}

    /* Metric Cards Styling */
    [data-testid="stMetric"] {{
        background-color: rgba(14, 36, 18, 0.88) !important;
        padding: 0.85rem 1rem;
        border-radius: 12px;
        border-left: 5px solid #ffd54f;
        border: 1px solid rgba(129, 199, 132, 0.4);
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    }}
    [data-testid="stMetricLabel"] p {{
        color: #a5d6a7 !important;
        font-weight: 600;
    }}
    [data-testid="stMetricValue"] div {{
        color: #ffffff !important;
    }}
    [data-testid="stMetricDelta"] div {{
        color: #ffd54f !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quick_question" not in st.session_state:
    st.session_state.quick_question = None

# Helper function to query FastAPI
def ask_backend(question_text):
    st.session_state.messages.append({"role": "user", "content": question_text})
    chat_history = st.session_state.messages[:-1]

    try:
        response = requests.post(
            API_URL,
            json={"question": question_text, "chat_history": chat_history},
            timeout=120
        )
        response.raise_for_status()
        answer = response.json()["answer"]
        st.session_state.messages.append({"role": "assistant", "content": answer})
    except requests.exceptions.ConnectionError:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ **Connection Error:** Cannot connect to FastAPI (`127.0.0.1:8000`). Please ensure your backend server is running."
        })
    except requests.exceptions.RequestException as error:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ **API Request Failed:** {error}"
        })
    except (KeyError, ValueError):
        st.session_state.messages.append({
            "role": "assistant",
            "content": "⚠️ **Invalid Response:** The API returned an unexpected format."
        })

# 4. Sidebar: Quick Actions & Department Contact
with st.sidebar:
    st.markdown("### 🌱 Quick Scheme Prompts")
    st.caption("Click any question below to ask the AI immediately:")

    sample_questions = [
        "What is the subsidy for Tractors & Power Tillers?",
        "Tell me about Rain Water Harvesting grants for SC/ST farmers.",
        "Which districts are covered under NABARD Rain Water Harvesting?",
        "How do I apply for Soil Conservation in Tribal Areas?"
    ]

    for idx, q in enumerate(sample_questions):
        if st.button(q, key=f"sample_{idx}", use_container_width=True):
            st.session_state.quick_question = q

    st.divider()
    st.markdown("### 📞 Department Contact")
    st.markdown(
        "**Chief Engineer (AED)**\n\n"
        "Agricultural Engineering Department,\n"
        "Pammal, Chennai - 600 035\n\n"
        "☎️ `9840675759`"
    )
    st.markdown("[🔗 Official Portal](https://www.skool.com/@suresh-kumar-6294)")

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 5. Hero Banner
st.markdown("""
    <div class="hero-banner">
        <h1>🌾 Tamil Nadu Agricultural Engineering Scheme AI</h1>
        <p>Your intelligent assistant for Tamil Nadu Government subsidies, farm mechanization, soil conservation, and water management schemes.</p>
    </div>
""", unsafe_allow_html=True)

# 6. Top KPI / Quick Highlights Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total AED Schemes", "15 Major", "TNAU Reference")
col2.metric("Mechanization Subsidy", "25% Cost", "Or GoI Ceiling")
col3.metric("Rainwater Harvesting", "90–100%", "Patta & Community")
col4.metric("Tribal Area Subsidy", "100%", "Grant 7 Hill Districts")

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# PRIORITY #1 (MOST HIGHLIGHTED): 💬 AI SCHEME ASSISTANT
# ==============================================================================
st.markdown('<div class="ai-spotlight-header">💬 AI Assistant — Ask Details About Agricultural Scheme Eligibility & Subsidies</div>', unsafe_allow_html=True)

with st.container(border=True):
    if st.session_state.quick_question:
        q_to_run = st.session_state.quick_question
        st.session_state.quick_question = None
        with st.spinner("Searching agricultural documents..."):
            ask_backend(q_to_run)
        st.rerun()

    chat_container = st.container(height=200)
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                "👋 **Vanakkam!** Ask any question below about Tamil Nadu agricultural schemes, machinery subsidies, "
                "or rainwater harvesting—or pick a quick prompt from the left sidebar."
            )
        for message in st.session_state.messages:
            avatar = "🧑‍🌾" if message["role"] == "user" else "🌾"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    user_input = st.chat_input("Ask your question about Tamil Nadu agricultural schemes here...")
    if user_input:
        with chat_container:
            with st.chat_message("user", avatar="🧑‍🌾"):
                st.markdown(user_input)
            with st.chat_message("assistant", avatar="🌾"):
                with st.spinner("Searching agricultural documents..."):
                    ask_backend(user_input)
                    st.markdown(st.session_state.messages[-1]["content"])

# ==============================================================================
# PRIORITY #2 (SECOND HIGHLIGHTED): 🎥 SINGLE CONTINUOUS LOOPING VIDEO SHOWCASE
# ==============================================================================
st.markdown('<div class="section-banner">🎥 Featured Agricultural Scheme & Mechanization Videos</div>', unsafe_allow_html=True)

if not local_videos:
    st.warning(f"No video files found in `{VIDEO_DIR}`. Please verify `.mp4` files are placed in that directory.")
else:
    featured_videos = local_videos[:3]
    video_items_js = []

    for vf in featured_videos:
        b64_vid = get_base64_str(vf)
        ext = vf.suffix.lower().lstrip(".")
        mime = "video/mp4" if ext == "mp4" else f"video/{ext}"
        title = vf.stem.replace("_", " ").replace("-", " ").title()
        video_items_js.append(f'{{ title: "{title}", src: "data:{mime};base64,{b64_vid}" }}')

    playlist_array_str = ",\n".join(video_items_js)

    loop_player_html = f"""
    <div style="
        background: rgba(12, 32, 16, 0.90);
        border: 2px solid #ffd54f;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        font-family: sans-serif;
        color: #ffffff;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
            <div>
                <span style="background: #2e7d32; color: #ffd54f; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; border: 1px solid #81c784;">
                    🔁 (<span id="vidCounter">1 / {len(featured_videos)}</span>)
                </span>
                <span id="vidTitle" style="font-size: 18px; font-weight: bold; margin-left: 10px; color: #ffffff;"></span>
            </div>
            <div>
                <button onclick="prevVideo()" style="background:#2e7d32; color:#fff; border:1px solid #81c784; padding:6px 14px; border-radius:8px; cursor:pointer; font-weight:bold; margin-right:6px;">⏮ Prev</button>
                <button onclick="nextVideo()" style="background:#2e7d32; color:#fff; border:1px solid #81c784; padding:6px 14px; border-radius:8px; cursor:pointer; font-weight:bold;">Next ⏭</button>
            </div>
        </div>

        <video id="agriLoopPlayer" width="100%" height="440" controls autoplay muted playsinline
            style="border-radius: 10px; background: #000; object-fit: contain; border: 1px solid rgba(255,255,255,0.2);">
        </video>
    </div>

    <script>
        const playlist = [
            {playlist_array_str}
        ];
        let currentIndex = 0;
        const player = document.getElementById("agriLoopPlayer");
        const titleEl = document.getElementById("vidTitle");
        const counterEl = document.getElementById("vidCounter");

        function loadVideo(idx) {{
            if (playlist.length === 0) return;
            currentIndex = (idx + playlist.length) % playlist.length;
            player.src = playlist[currentIndex].src;
            titleEl.textContent = "🎬 " + playlist[currentIndex].title;
            counterEl.textContent = (currentIndex + 1) + " / " + playlist.length;
            player.play().catch(() => {{}});
        }}

        function nextVideo() {{
            loadVideo(currentIndex + 1);
        }}

        function prevVideo() {{
            loadVideo(currentIndex - 1);
        }}

        player.addEventListener("ended", () => {{
            nextVideo();
        }});

        loadVideo(0);
    </script>
    """
    components.html(loop_player_html, height=530)

# ==============================================================================
# PRIORITY #3: 📋 TNAU AGRICULTURAL ENGINEERING SCHEMES DIRECTORY
# ==============================================================================
st.markdown('<div class="section-banner">📋 TNAU Agricultural Engineering Schemes Quick Reference</div>', unsafe_allow_html=True)

search_filter = st.text_input("🔍 Filter schemes by keyword (e.g., Tractor, Rain, Tribal, River, Pumpset):").lower()

schemes_data = [
    {
        "no": "Scheme 1",
        "title": "Soil and Water Conservation in Catchments of River Valley Project",
        "subsidy": "25% Subsidy + 75% Loan (2-yr moratorium)",
        "area": "Vellore, Thiruvannamalai, Dharmapuri, Krishnagiri & Salem (South Pennaiyar & Mettur Catchments)",
        "details": "Contour bunding, horticultural plantations, drainage line treatment, farm ponds, agro-forestry, and silt detention structures.",
        "officer": "Assistant Executive Engineer (River Valley Project) in Krishnagiri, Harur, Dharmapuri, Mettur, or Chengam."
    },
    {
        "no": "Scheme 2",
        "title": "Agricultural Mechanisation Programme",
        "subsidy": "25% of Machinery Cost (or GoI ceiling limit)",
        "area": "All Districts (Except Chennai)",
        "details": "Subsidy assistance for Tractors, Power Tillers, Self-propelled Paddy Transplanters, Paddy Reapers, Rotavators, Cultivators, Disc & Chisel Ploughs.",
        "officer": "Assistant Executive Engineer (AED) in the Revenue Division / Executive Engineer (AED) in the District."
    },
    {
        "no": "Scheme 3",
        "title": "Command Area Development and Water Management Programme",
        "subsidy": "Centre-State Grant + Rs. 540/ha for Farmers Council",
        "area": "Cauvery Command (Thanjavur, Tiruvarur, Nagapattinam, Trichy, Cuddalore) & Reservoir Projects (Villupuram, Erode, Tirunelveli, Dharmapuri)",
        "details": "Construction of field channels and drains, rotational water supply works, and formation of Water Users Associations.",
        "officer": "Assistant Executive Engineer, Command Area Development Programme."
    },
    {
        "no": "Scheme 4 & 5",
        "title": "Demonstration & Farmer Training in Agricultural Machinery",
        "subsidy": "Free Field Demonstrations & Refresher Training",
        "area": "All Districts (Except Chennai)",
        "details": "Field demonstrations of newly developed farm implements and refresher maintenance training for farmers & rural youth (ages 18–40).",
        "officer": "Assistant Executive Engineer (AED) in the Revenue Division."
    },
    {
        "no": "Scheme 6",
        "title": "Rain Water Harvesting and Runoff Management Programme",
        "subsidy": "100% Grant (Community) | 90% Subsidy (Patta Land; 95% for SC/ST)",
        "area": "All Districts (Except Chennai and Nilgiris)",
        "details": "Percolation ponds, major/medium/minor check dams, farm ponds, rejuvenation of unused wells, and village tanks/ooranies.",
        "officer": "Assistant Executive Engineer (AED) in the Revenue Division."
    },
    {
        "no": "Scheme 7",
        "title": "NABARD Assisted Rain Water Harvesting Programme",
        "subsidy": "100% Grant (Community) | 75% Subsidy (Patta Land)",
        "area": "19 Districts including Kanchipuram, Vellore, Salem, Erode, Trichy, Dindigul, Madurai/Theni belt, Ramnad, Coimbatore & Nilgiris",
        "details": "Construction of percolation ponds, check dams, farm ponds, and rejuvenation of unused wells in priority watersheds.",
        "officer": "Assistant Executive Engineer (AED) in the Revenue Division."
    },
    {
        "no": "Scheme 8 & 9",
        "title": "Hill Area (Nilgiris) & Western Ghats Soil/Water Conservation",
        "subsidy": "100% Grant (10% beneficiary share; 5% for SC/ST & community)",
        "area": "Nilgiris (HADP) & Coimbatore, Erode, Madurai, Theni, Dindigul, Virudhunagar, Tirunelveli, Kanyakumari (WGDP)",
        "details": "Bench terracing, landslide treatment, staggered contour trenching, gabion structures, contour rubble bunds, and check dams.",
        "officer": "Assistant Executive Engineer (AED), Udagamandalam / Gudalur / Coonoor or respective Revenue Divisions."
    },
    {
        "no": "Scheme 10",
        "title": "Soil Conservation in Tribal Areas (ITDP)",
        "subsidy": "100% Subsidy for Land-Owning Scheduled Tribal Farmers",
        "area": "Kalrayan, Jawadhu, Shervarayan, Kolli, Sitheri & Patchai Hills (7 Districts)",
        "details": "Contour stone walls, land shaping, pipe laying, disc ploughing, and irrigation check dams.",
        "officer": "Assistant Executive Engineer (AED) in the respective Revenue Division."
    },
    {
        "no": "Scheme 11–15",
        "title": "Pumpset Replacement, TN IAMWARM, Minor Irrigation, Land Dev & NADP",
        "subsidy": "Scheme-specific State/World Bank/NADP Subsidies",
        "area": "Tamil Nadu State-wide (varies by project sub-basin)",
        "details": "Replacement of old inefficient pumpsets, World Bank aided irrigation modernization (TN IAMWARM), minor irrigation, and land development.",
        "officer": "Executive Engineer (AED) in the District / Chief Engineer (AED), Chennai."
    }
]

filtered_schemes = [
    item for item in schemes_data
    if search_filter in f"{item['title']} {item['area']} {item['details']}".lower()
]

scheme_cols = st.columns(2)
for idx, item in enumerate(filtered_schemes):
    with scheme_cols[idx % 2]:
        st.markdown(f"""
            <div class="scheme-card">
                <span class="badge">{item['no']} • {item['subsidy']}</span>
                <h4>{item['title']}</h4>
                <p style="margin-bottom:6px;"><b>📍 Coverage:</b> {item['area']}</p>
                <p style="margin-bottom:6px;"><b>🛠️ Works & Benefits:</b> {item['details']}</p>
                <p class="officer-text" style="margin-bottom:0;"><b>🏢 Contact Officer:</b> {item['officer']}</p>
            </div>
        """, unsafe_allow_html=True)