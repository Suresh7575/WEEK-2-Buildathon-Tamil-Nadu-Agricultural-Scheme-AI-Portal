import base64
import json
from pathlib import Path
import requests
import streamlit as st


# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="Tamil Nadu Agricultural Scheme AI Portal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paths for local videos and background image.
# Resolve paths from this script so the app works regardless of the terminal's
# current working directory.
PROJECT_DIR = Path(__file__).resolve().parent
VIDEO_DIR_CANDIDATES = [
    PROJECT_DIR / "data" / "Videos",
    PROJECT_DIR / "Videos",
    Path.cwd() / "data" / "Videos",
]
VIDEO_DIR = next(
    (folder for folder in VIDEO_DIR_CANDIDATES if folder.is_dir()),
    PROJECT_DIR / "data" / "Videos",
)

# Accept both the corrected filename and the original filename used earlier.
BG_IMAGE_CANDIDATES = [
    VIDEO_DIR / "background.png",
    VIDEO_DIR / "backgroun.png",
    PROJECT_DIR / "background.png",
    PROJECT_DIR / "backgroun.png",
]
BG_IMAGE_PATH = next(
    (path for path in BG_IMAGE_CANDIDATES if path.is_file()),
    BG_IMAGE_CANDIDATES[0],
)


def get_base64_str(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def format_api_error(response: requests.Response) -> str:
    """Return a useful FastAPI error message without hiding the HTTP status."""
    try:
        payload = response.json()
        detail = payload.get("detail", payload)
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("reason") or str(detail)
        else:
            message = str(detail)
    except ValueError:
        message = response.text.strip() or response.reason
    return f"HTTP {response.status_code}: {message}"


def get_local_videos(folder_path: Path):
    supported_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")
    if folder_path.exists():
        files = sorted(
            [f for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() in supported_exts]
        )
        if files:
            return files
    return sorted(
        [f for f in Path(".").iterdir() if f.is_file() and f.suffix.lower() in supported_exts]
    )


local_videos = get_local_videos(VIDEO_DIR)
bg_base64 = get_base64_str(BG_IMAGE_PATH)

# 2. Bilingual Text Dictionary
TEXT = {
    "English": {
        "title": "Tamil Nadu Agricultural Engineering Scheme AI Portal",
        "subtitle": "Simple, reliable guidance about Tamil Nadu Government agricultural schemes, subsidies, and machinery—based on uploaded government PDFs.",
        "language": "Language / மொழி",
        "upload_title": "📄 Add Scheme Documents",
        "upload_help": "Upload one or more government scheme PDFs. New documents are processed and added to the search index automatically.",
        "choose_pdf": "Choose PDF files",
        "index_button": "Upload and Index PDFs",
        "upload_success": "Document processing completed.",
        "ask_header": "💬 AI Scheme Assistant — Ask About Eligibility, Subsidies & District Offices",
        "ask_hint": "Ask your question about Tamil Nadu agricultural schemes here (e.g., What documents are needed?)...",
        "quick": "🌱 Suggested Quick Prompts",
        "welcome": "👋 **Vanakkam!** Ask any question below about Tamil Nadu agricultural schemes, machinery subsidies, or rainwater harvesting. I will explain the answer in simple language using the uploaded government documents.",
        "clear": "🗑️ Clear Conversation",
        "disclaimer": "Important: This assistant summarizes uploaded government documents. Scheme rules may change. Confirm eligibility, subsidy amounts, deadlines, and application steps with the relevant Agricultural Engineering Department (AED) office before applying.",
        "backend_error": "Could not connect to the FastAPI backend. Please start FastAPI and try again.",
        "processing": "Searching agricultural documents and updating index...",
        "indexed": "Indexed",
        "duplicate": "Already in search index",
        "failed": "Could not process",
        "pages": "pages",
        "chunks": "searchable sections",
        "video_banner": "🎥 Featured Agricultural Scheme & Mechanization Videos",
        "schemes_banner": "📋 TNAU Agricultural Engineering Schemes Quick Reference",
        "filter_hint": "🔍 Filter schemes by keyword (e.g., Tractor, Rain, Tribal, River, Pumpset):",
        "contact_header": "📞 Department Contact",
        "contact_body": (
            "**Chief Engineer (AED)**\n\n"
            "Agricultural Engineering Department,\n"
            "Nandanam, Chennai - 600 035\n\n"
            "☎️ `044-2435 2686` / `2435 2622`"
        ),
        "quick_questions": [
            "Who is eligible for this scheme?",
            "What subsidy amount is available for Tractors & Power Tillers?",
            "Tell me about Rain Water Harvesting grants for SC/ST farmers.",
            "Which districts are covered under NABARD Rain Water Harvesting?",
        ],
        "footer": "Designed to help Tamil Nadu farmers find scheme information—not to replace official government advice.",
    },
    "தமிழ்": {
        "title": "தமிழ்நாடு வேளாண்மைப் பொறியியல் திட்டங்கள் AI தளம்",
        "subtitle": "பதிவேற்றப்பட்ட அரசு PDF ஆவணங்களின் அடிப்படையில் வேளாண்மைத் திட்டங்கள் மற்றும் மானியங்களை எளிய தமிழில் அறியுங்கள்.",
        "language": "மொழி / Language",
        "upload_title": "📄 திட்ட ஆவணங்களைச் சேர்க்கவும்",
        "upload_help": "அரசுத் திட்டங்களின் PDF கோப்புகளைப் பதிவேற்றவும். புதிய ஆவணங்கள் தானாகப் படிக்கப்பட்டு தேடல் அமைப்பில் சேர்க்கப்படும்.",
        "choose_pdf": "PDF கோப்புகளைத் தேர்ந்தெடுக்கவும்",
        "index_button": "PDF பதிவேற்றி சேர்க்கவும்",
        "upload_success": "ஆவணச் செயலாக்கம் முடிந்தது.",
        "ask_header": "💬 AI திட்ட உதவியாளர் — தகுதி, மானியம் & விண்ணப்ப விவரங்களைக் கேளுங்கள்",
        "ask_hint": "தமிழ்நாடு வேளாண்மைத் திட்டம் குறித்து உங்கள் கேள்வியை இங்கே கேளுங்கள்...",
        "quick": "🌱 மாதிரி கேள்விகள்",
        "welcome": "👋 **வணக்கம்!** தமிழ்நாடு வேளாண்மைத் திட்டங்கள், இயந்திர மானியங்கள் மற்றும் மழைநீர் சேகரிப்பு குறித்து கீழே கேள்வி கேளுங்கள். பதிவேற்றிய ஆவணங்களைப் பயன்படுத்தி எளிய தமிழில் பதிலளிக்கிறேன்.",
        "clear": "🗑️ உரையாடலை நீக்கவும்",
        "disclaimer": "முக்கியம்: இந்த உதவியாளர் பதிவேற்றிய ஆவணங்களிலிருந்து தகவல்களைச் சுருக்குகிறது. விண்ணப்பிப்பதற்கு முன் தகுதி, மானியத் தொகை மற்றும் நடைமுறைகளை சம்பந்தப்பட்ட வேளாண்மைப் பொறியியல் துறையிடம் உறுதிப்படுத்தவும்.",
        "backend_error": "பின்புற சேவையகத்துடன் (FastAPI) இணைக்க முடியவில்லை. FastAPI இயங்குகிறதா எனச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
        "processing": "வேளாண்மை ஆவணங்கள் தேடப்படுகின்றன...",
        "indexed": "தேடல் அமைப்பில் சேர்க்கப்பட்டது",
        "duplicate": "ஏற்கனவே தேடல் அமைப்பில் உள்ளது",
        "failed": "செயலாக்க முடியவில்லை",
        "pages": "பக்கங்கள்",
        "chunks": "தேடக்கூடிய பகுதிகள்",
        "video_banner": "🎥 வேளாண்மைத் திட்டங்கள் & இயந்திரமயமாக்கல் விளக்க வீடியோக்கள்",
        "schemes_banner": "📋 TNAU வேளாண்மைப் பொறியியல் துறை திட்டங்கள் விரைவு வழிகாட்டி",
        "filter_hint": "🔍 திட்டங்களைத் தேடவும் (உதாரணம்: Tractor, Rain, Tribal, River, Pumpset):",
        "contact_header": "📞 துறை தொடர்பு விவரம்",
        "contact_body": (
            "**தலைமைப் பொறியாளர் (வே.பொ.து)**\n\n"
            "வேளாண்மைப் பொறியியல் துறை,\n"
            "நந்தனம், சென்னை - 600 035\n\n"
            "☎️ `044-2435 2686` / `2435 2622`"
        ),
        "quick_questions": [
            "இந்தத் திட்டத்திற்கு யார் தகுதியானவர்கள்?",
            "டிராக்டர் மற்றும் பவர் டில்லருக்கு எவ்வளவு மானியம் கிடைக்கும்?",
            "மழைநீர் சேகரிப்பு திட்டத்தில் SC/ST விவசாயிகளுக்கான மானியம் என்ன?",
            "எந்த மாவட்டங்கள் பயன்பெறும்?",
        ],
        "footer": "அரசு ஆலோசனைக்கு மாற்றாக அல்ல; விவசாயிகளுக்கு தகவல் அறிய உதவும் தளம்.",
    },
}

# 3. Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "English"

# 4. Base CSS: High-Contrast Glass UI + Balanced Card Heights
bg_css = (
    f"""
    background-image: linear-gradient(rgba(6, 20, 9, 0.74), rgba(6, 20, 9, 0.80)), url("data:image/png;base64,{bg_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
"""
    if bg_base64
    else """
    background: linear-gradient(180deg, #0d2612 0%, #163a1e 100%);
"""
)

st.markdown(
    f"""
    <style>
    /* Full Page Agricultural Image Background */
    .stApp {{
        {bg_css}
        color: #ffffff !important;
    }}

    /* Global Bright Text & Inline Code */
    .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp small {{
        color: #ffffff !important;
    }}
    code {{
        background-color: #1b4d24 !important;
        color: #ffd54f !important;
        padding: 0.18rem 0.45rem !important;
        border-radius: 6px !important;
        border: 1px solid #81c784 !important;
        font-weight: 700 !important;
        font-size: 0.90rem !important;
    }}

    /* Sidebar Glass Styling */
    [data-testid="stSidebar"] {{
        background-color: #0b2210 !important;
        border-right: 2px solid #66bb6a;
    }}
    [data-testid="stSidebar"] * {{
        color: #f1f8e9 !important;
    }}
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: #14381c !important;
        color: #ffffff !important;
        border: 1px solid #81c784 !important;
    }}

    /* Sidebar Quick Prompt & Clear Buttons */
    [data-testid="stSidebar"] .stButton button {{
        background-color: #1e5628 !important;
        color: #ffffff !important;
        border: 1px solid #81c784 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        line-height: 1.35 !important;
        padding: 0.45rem 0.65rem !important;
    }}
    [data-testid="stSidebar"] .stButton button:hover {{
        background-color: #2e7d32 !important;
        border-color: #ffd54f !important;
    }}
    [data-testid="stSidebar"] .stButton button:disabled {{
        background-color: #173d1e !important;
        color: #c8e6c9 !important;
        border: 1px dashed #81c784 !important;
        opacity: 0.95 !important;
    }}

    /* File Uploader Dropzone Fix */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: #13351a !important;
        border: 1.5px dashed #ffd54f !important;
        border-radius: 10px !important;
    }}
    [data-testid="stFileUploaderDropzone"] * {{
        color: #f1f8e9 !important;
    }}
    [data-testid="stFileUploaderDropzone"] small {{
        color: #ffd54f !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }}
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border: 1px solid #ffd54f !important;
        font-weight: 700 !important;
    }}

    /* Hero Banner */
    .hero-banner {{
        background: linear-gradient(135deg, rgba(27, 94, 32, 0.95) 0%, rgba(46, 125, 50, 0.92) 60%, rgba(104, 159, 56, 0.92) 100%);
        padding: 1.4rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 1.1rem;
        border: 1px solid rgba(255, 255, 255, 0.35);
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
    }}
    .hero-banner h1 {{
        color: #ffffff !important;
        margin-top: 0 !important;
        margin-bottom: 0.35rem !important;
        font-size: 2.0rem !important;
        line-height: 1.25 !important;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}
    .hero-banner .hero-sub {{
        color: #f1f8e9 !important;
        font-size: 1.0rem !important;
        line-height: 1.45 !important;
        margin: 0 !important;
    }}

    /* Equal-Height High-Contrast KPI Cards */
    .kpi-card {{
        background-color: #0e2914 !important;
        padding: 0.95rem 1.1rem;
        border-radius: 12px;
        border: 1.5px solid #81c784;
        border-left: 6px solid #ffd54f;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
        min-height: 136px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }}
    .kpi-label {{
        color: #c8e6c9 !important;
        font-size: 0.90rem;
        font-weight: 700;
        line-height: 1.3;
    }}
    .kpi-value {{
        color: #ffffff !important;
        font-size: 1.75rem;
        font-weight: 800;
        line-height: 1.2;
        margin: 0.25rem 0;
    }}
    .kpi-delta {{
        display: inline-block;
        align-self: flex-start;
        background-color: rgba(255, 213, 79, 0.18);
        color: #ffd54f !important;
        border: 1px solid #ffd54f;
        padding: 0.15rem 0.6rem;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 700;
        line-height: 1.25;
    }}

    /* Highlighted AI Spotlight Header */
    .ai-spotlight-header {{
        background: linear-gradient(90deg, #1b5e20, #388e3c, #2e7d32);
        color: #ffd54f !important;
        padding: 0.85rem 1.4rem;
        border-radius: 14px 14px 0 0;
        font-size: 1.28rem;
        font-weight: 800;
        border: 2px solid #ffd54f;
        border-bottom: none;
        box-shadow: 0 0 20px rgba(255, 213, 79, 0.25);
    }}

    /* Highlighted Welcome Box inside AI Assistant */
    .welcome-highlight {{
        background: linear-gradient(90deg, rgba(46, 125, 50, 0.72), rgba(104, 159, 56, 0.62));
        border-left: 5px solid #ffd54f;
        padding: 0.85rem 1.1rem;
        border-radius: 10px;
        color: #ffffff !important;
        font-size: 1.0rem;
        line-height: 1.5;
        margin-bottom: 0.6rem;
    }}

    /* Chat Input Box Fix */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {{
        background-color: #0b2210 !important;
        border: 2px solid #ffd54f !important;
        border-radius: 12px !important;
        box-shadow: 0 0 16px rgba(255, 213, 79, 0.30) !important;
    }}
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"] {{
        background-color: #0b2210 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #ffd54f !important;
        font-size: 1.0rem !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stChatInputTextArea"]::placeholder {{
        color: #fff59d !important;
        -webkit-text-fill-color: #fff59d !important;
        opacity: 1 !important;
    }}
    [data-testid="stChatInput"] button {{
        background-color: #ffd54f !important;
        color: #0b2210 !important;
        border-radius: 8px !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: #0b2210 !important;
        color: #0b2210 !important;
    }}

    /* Section Banners */
    .section-banner {{
        background: linear-gradient(90deg, rgba(27, 94, 32, 0.94), rgba(56, 142, 60, 0.90));
        color: #ffffff !important;
        padding: 0.75rem 1.3rem;
        border-radius: 10px;
        font-size: 1.22rem;
        font-weight: 700;
        margin-top: 1.6rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.25);
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    }}

    /* Frosted Dark Glass Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: rgba(10, 28, 14, 0.92) !important;
        border: 2px solid #ffd54f !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45);
    }}

    /* Chat Message Bubbles */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.14) !important;
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }}

    /* Search Input Box */
    .stTextInput input {{
        background-color: #0e2914 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1.5px solid #81c784 !important;
        border-radius: 8px;
    }}
    .stTextInput input::placeholder {{
        color: #c8e6c9 !important;
        -webkit-text-fill-color: #c8e6c9 !important;
        opacity: 1 !important;
    }}

    /* Equal-Height Scheme Cards with Bright High-Contrast Text */
    .scheme-card {{
        background-color: rgba(12, 32, 16, 0.94) !important;
        border-left: 6px solid #ffd54f;
        border-top: 1px solid rgba(165, 214, 167, 0.4);
        border-right: 1px solid rgba(165, 214, 167, 0.4);
        border-bottom: 1px solid rgba(165, 214, 167, 0.4);
        padding: 1.15rem 1.35rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        min-height: 295px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45);
    }}
    .scheme-card h4 {{
        color: #ffd54f !important;
        margin-top: 0.35rem !important;
        margin-bottom: 0.55rem !important;
        font-size: 1.10rem !important;
        line-height: 1.35 !important;
    }}
    .scheme-card p {{
        color: #f1f8e9 !important;
        font-size: 0.94rem !important;
        line-height: 1.5 !important;
        margin-bottom: 0.45rem !important;
    }}
    .scheme-card b {{
        color: #a5d6a7 !important;
    }}
    .scheme-card .officer-text {{
        color: #dce775 !important;
        font-size: 0.88rem !important;
        margin-bottom: 0 !important;
        padding-top: 0.35rem;
        border-top: 1px dashed rgba(165, 214, 167, 0.25);
    }}
    .badge {{
        display: inline-block;
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        line-height: 1.3 !important;
        margin-bottom: 0.25rem;
        border: 1px solid #81c784;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# 5. Sidebar: Language, Backend API, PDF Upload & Quick Prompts
with st.sidebar:
    language = st.selectbox(
        "Language / மொழி",
        ["English", "தமிழ்"],
        index=0 if st.session_state.language == "English" else 1,
    )
    st.session_state.language = language
    t = TEXT[language]

    # Balanced Tamil typography & equalized heights when தமிழ் is selected
    if language == "தமிழ்":
        st.markdown(
            """
            <style>
            .hero-banner h1 { font-size: 1.48rem !important; line-height: 1.35 !important; }
            .hero-banner .hero-sub { font-size: 0.88rem !important; line-height: 1.45 !important; }
            .kpi-card { min-height: 148px !important; padding: 0.85rem 0.95rem !important; }
            .kpi-label { font-size: 0.78rem !important; line-height: 1.35 !important; }
            .kpi-value { font-size: 1.28rem !important; line-height: 1.25 !important; }
            .kpi-delta { font-size: 0.72rem !important; line-height: 1.3 !important; }
            .ai-spotlight-header { font-size: 1.02rem !important; }
            .welcome-highlight { font-size: 0.88rem !important; line-height: 1.55 !important; }
            .section-banner { font-size: 1.0rem !important; }
            .scheme-card { min-height: 365px !important; padding: 1.05rem 1.2rem !important; }
            .scheme-card h4 { font-size: 0.95rem !important; line-height: 1.4 !important; }
            .scheme-card p, .scheme-card b { font-size: 0.82rem !important; line-height: 1.52 !important; }
            .scheme-card .officer-text { font-size: 0.78rem !important; line-height: 1.45 !important; }
            .badge { font-size: 0.72rem !important; line-height: 1.35 !important; }
            [data-testid="stSidebar"] .stButton button { font-size: 0.80rem !important; line-height: 1.4 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    API_BASE = st.text_input(
        "Backend API",
        "http://127.0.0.1:8000",
        help="FastAPI server address",
    )

    st.divider()
    st.markdown(f"### {t['quick']}")
    for idx, sample in enumerate(t["quick_questions"]):
        if st.button(sample, key=f"quick_{language}_{idx}", use_container_width=True):
            st.session_state.pending_question = sample

    st.divider()
    st.markdown(f"### {t['upload_title']}")
    st.caption(t["upload_help"])
    uploaded_files = st.file_uploader(
        t["choose_pdf"],
        type=["pdf"],
        accept_multiple_files=True,
        help=t["upload_help"],
    )
    if st.button(
        t["index_button"],
        use_container_width=True,
        disabled=not uploaded_files,
    ):
        try:
            payload = [
                ("files", (file.name, file.getvalue(), "application/pdf"))
                for file in uploaded_files
            ]
            with st.spinner(t["processing"]):
                result = requests.post(
                    f"{API_BASE.rstrip('/')}/upload", files=payload, timeout=600
                )
            result.raise_for_status()
            data = result.json()
            st.success(t["upload_success"])
            for item in data.get("results", []):
                status = item.get("status")
                if status == "indexed":
                    st.success(
                        f"{item['filename']} — {t['indexed']} ({item.get('pages', 0)} {t['pages']}, {item.get('chunks', 0)} {t['chunks']})"
                    )
                elif status == "already_indexed":
                    st.info(f"{item['filename']} — {t['duplicate']}")
                else:
                    st.error(
                        f"{item.get('filename', 'PDF')}: {item.get('message', t['failed'])}"
                    )
        except requests.exceptions.HTTPError as exc:
            st.error(f"{t['backend_error']} ({format_api_error(exc.response)})")
        except requests.exceptions.RequestException as exc:
            st.error(f"{t['backend_error']} ({exc})")

    st.divider()
    st.markdown(f"### {t['contact_header']}")
    st.markdown(t["contact_body"])

    st.divider()
    if st.button(t["clear"], use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 6. Hero Banner & Bilingual Equal-Height KPIs
st.markdown(
    f"""
    <div class="hero-banner">
        <h1>🌾 {t['title']}</h1>
        <div class="hero-sub">{t['subtitle']}</div>
    </div>
""",
    unsafe_allow_html=True,
)

KPIS_BY_LANG = {
    "English": [
        ("Total AED Schemes", "15 Major", "TNAU Reference"),
        ("Mechanization Subsidy", "25% Cost", "Or GoI Ceiling"),
        ("Rainwater Harvesting", "90–100%", "Patta & Community"),
        ("Tribal Area Subsidy", "100% Grant", "7 Hill Districts"),
    ],
    "தமிழ்": [
        ("மொத்த AED திட்டங்கள்", "15 முக்கிய", "TNAU வழிகாட்டி"),
        ("இயந்திர மானியம்", "25% விலை", "அரசு உச்சவரம்பு"),
        ("மழைநீர் சேகரிப்பு", "90–100%", "பட்டா & சமுதாய நிலம்"),
        ("பழங்குடியினர் மானியம்", "100% மானியம்", "7 மலை மாவட்டங்கள்"),
    ],
}

kpi_cols = st.columns(4)
for col, (label, val, delta) in zip(kpi_cols, KPIS_BY_LANG[language]):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-delta">▲ {delta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# PRIORITY #1 (MOST HIGHLIGHTED & COMPACT): 💬 AI SCHEME ASSISTANT
# ==============================================================================
st.markdown(
    f'<div class="ai-spotlight-header">{t["ask_header"]}</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    if not st.session_state.messages:
        st.markdown(
            f'<div class="welcome-highlight">{t["welcome"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        chat_container = st.container(height=320)
        with chat_container:
            for message in st.session_state.messages:
                avatar = "🧑‍🌾" if message["role"] == "user" else "🌾"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

    question = st.chat_input(t["ask_hint"])
    if st.session_state.get("pending_question"):
        question = st.session_state.pop("pending_question")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        try:
            with st.spinner(t["processing"]):
                response = requests.post(
                    f"{API_BASE.rstrip('/')}/ask",
                    json={
                        "question": question,
                        "chat_history": st.session_state.messages[:-1],
                        "language": "Tamil" if language == "தமிழ்" else "English",
                    },
                    timeout=180,
                )
            response.raise_for_status()
            answer = response.json().get("answer", "")
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except requests.exceptions.HTTPError as exc:
            detail = format_api_error(exc.response)
            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠️ {t['backend_error']} ({detail})"}
            )
        except requests.exceptions.RequestException as exc:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠️ {t['backend_error']} ({exc})"}
            )
        st.rerun()

    st.caption(f"ℹ️ {t['disclaimer']}")

# ==============================================================================
# PRIORITY #2 (SECOND HIGHLIGHTED): 🎥 SINGLE CONTINUOUS LOOPING VIDEO SHOWCASE
# ==============================================================================
st.markdown(
    f'<div class="section-banner">{t["video_banner"]}</div>',
    unsafe_allow_html=True,
)

VIDEO_TITLE_MAP = {
    "video_1": "NADP: Agricultural Development & Conservation",
    "video_2": "Tamil Nadu Agricultural Engineering Department Schemes",
    "video_3": "Soil & Water Conservation, TN IAMWARM & Mechanisation",
}

if not local_videos:
    st.warning(
        f"No video files found in `{VIDEO_DIR}`. Please verify your `.mp4` files are in that directory."
    )
else:
    featured_videos = local_videos[:3]
    video_items_js = []

    for vf in featured_videos:
        b64_vid = get_base64_str(vf)
        ext = vf.suffix.lower().lstrip(".")
        mime = "video/mp4" if ext == "mp4" else f"video/{ext}"
        title = VIDEO_TITLE_MAP.get(
            vf.stem.lower(), vf.stem.replace("_", " ").replace("-", " ").title()
        )
        safe_title = json.dumps(title, ensure_ascii=False)
        video_items_js.append(
            f'{{ title: {safe_title}, src: "data:{mime};base64,{b64_vid}" }}'
        )

    playlist_array_str = ",\n".join(video_items_js)

    loop_player_html = f"""
    <div style="
        background: rgba(12, 32, 16, 0.92);
        border: 2px solid #ffd54f;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        font-family: sans-serif;
        color: #ffffff;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
            <div>
                <span id="vidTitle" style="font-size: 18px; font-weight: bold; color: #ffd54f;"></span>
            </div>
            <div>
                <button onclick="prevVideo()" style="background:#2e7d32; color:#fff; border:1px solid #ffd54f; padding:6px 14px; border-radius:8px; cursor:pointer; font-weight:bold; margin-right:6px;">⏮ Prev</button>
                <button onclick="nextVideo()" style="background:#2e7d32; color:#fff; border:1px solid #ffd54f; padding:6px 14px; border-radius:8px; cursor:pointer; font-weight:bold;">Next ⏭</button>
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

        function loadVideo(idx) {{
            if (playlist.length === 0) return;
            currentIndex = (idx + playlist.length) % playlist.length;
            player.src = playlist[currentIndex].src;
            titleEl.textContent = "🎬 " + playlist[currentIndex].title;
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
    st.html(loop_player_html, unsafe_allow_javascript=True)

# ==============================================================================
# PRIORITY #3: 📋 TNAU AGRICULTURAL ENGINEERING SCHEMES DIRECTORY (BILINGUAL)
# ==============================================================================
st.markdown(
    f'<div class="section-banner">{t["schemes_banner"]}</div>',
    unsafe_allow_html=True,
)

search_filter = st.text_input(t["filter_hint"]).lower()

CARD_LABELS = {
    "English": {
        "coverage": "📍 Coverage:",
        "works": "🛠️ Works & Benefits:",
        "officer": "🏢 Contact Officer:",
    },
    "தமிழ்": {
        "coverage": "📍 செயல்படுத்தப்படும் பகுதிகள்:",
        "works": "🛠️ பணிகள் மற்றும் மானியப் பலன்கள்:",
        "officer": "🏢 தொடர்பு கொள்ள வேண்டிய அலுவலர்:",
    },
}

SCHEMES_DATA = {
    "English": [
        {
            "no": "Scheme 1",
            "title": "Soil and Water Conservation in Catchments of River Valley Project",
            "subsidy": "25% Subsidy + 75% Loan (2-yr moratorium)",
            "area": "Vellore, Thiruvannamalai, Dharmapuri, Krishnagiri & Salem (South Pennaiyar & Mettur Catchments)",
            "details": "Contour bunding, horticultural plantations, drainage line treatment, farm ponds, agro-forestry, and silt detention structures.",
            "officer": "Assistant Executive Engineer (River Valley Project) in Krishnagiri, Harur, Dharmapuri, Mettur, or Chengam.",
        },
        {
            "no": "Scheme 2",
            "title": "Agricultural Mechanisation Programme",
            "subsidy": "25% of Machinery Cost (or GoI ceiling limit)",
            "area": "All Districts (Except Chennai)",
            "details": "Subsidy assistance for Tractors, Power Tillers, Self-propelled Paddy Transplanters, Paddy Reapers, Rotavators, Cultivators, Disc & Chisel Ploughs.",
            "officer": "Assistant Executive Engineer (AED) in the Revenue Division / Executive Engineer (AED) in the District.",
        },
        {
            "no": "Scheme 3",
            "title": "Command Area Development and Water Management Programme",
            "subsidy": "Centre-State Grant + Rs. 540/ha for Farmers Council",
            "area": "Cauvery Command (Thanjavur, Tiruvarur, Nagapattinam, Trichy, Cuddalore) & Reservoir Projects (Villupuram, Erode, Tirunelveli, Dharmapuri)",
            "details": "Construction of field channels and drains, rotational water supply works, and formation of Water Users Associations.",
            "officer": "Assistant Executive Engineer, Command Area Development Programme.",
        },
        {
            "no": "Scheme 4 & 5",
            "title": "Demonstration & Farmer Training in Agricultural Machinery",
            "subsidy": "Free Field Demonstrations & Refresher Training",
            "area": "All Districts (Except Chennai)",
            "details": "Field demonstrations of newly developed farm implements and refresher maintenance training for farmers & rural youth (ages 18–40).",
            "officer": "Assistant Executive Engineer (AED) in the Revenue Division.",
        },
        {
            "no": "Scheme 6",
            "title": "Rain Water Harvesting and Runoff Management Programme",
            "subsidy": "100% Grant (Community) | 90% Subsidy (Patta Land; 95% for SC/ST)",
            "area": "All Districts (Except Chennai and Nilgiris)",
            "details": "Percolation ponds, major/medium/minor check dams, farm ponds, rejuvenation of unused wells, and village tanks/ooranies.",
            "officer": "Assistant Executive Engineer (AED) in the Revenue Division.",
        },
        {
            "no": "Scheme 7",
            "title": "NABARD Assisted Rain Water Harvesting Programme",
            "subsidy": "100% Grant (Community) | 75% Subsidy (Patta Land)",
            "area": "19 Districts including Kanchipuram, Vellore, Salem, Erode, Trichy, Dindigul, Madurai/Theni belt, Ramnad, Coimbatore & Nilgiris",
            "details": "Construction of percolation ponds, check dams, farm ponds, and rejuvenation of unused wells in priority watersheds.",
            "officer": "Assistant Executive Engineer (AED) in the Revenue Division.",
        },
        {
            "no": "Scheme 8 & 9",
            "title": "Hill Area (Nilgiris) & Western Ghats Soil/Water Conservation",
            "subsidy": "100% Grant (10% beneficiary share; 5% for SC/ST & community)",
            "area": "Nilgiris (HADP) & Coimbatore, Erode, Madurai, Theni, Dindigul, Virudhunagar, Tirunelveli, Kanyakumari (WGDP)",
            "details": "Bench terracing, landslide treatment, staggered contour trenching, gabion structures, contour rubble bunds, and check dams.",
            "officer": "Assistant Executive Engineer (AED), Udagamandalam / Gudalur / Coonoor or respective Revenue Divisions.",
        },
        {
            "no": "Scheme 10",
            "title": "Soil Conservation in Tribal Areas (ITDP)",
            "subsidy": "100% Subsidy for Land-Owning Scheduled Tribal Farmers",
            "area": "Kalrayan, Jawadhu, Shervarayan, Kolli, Sitheri & Patchai Hills (7 Districts)",
            "details": "Contour stone walls, land shaping, pipe laying, disc ploughing, and irrigation check dams.",
            "officer": "Assistant Executive Engineer (AED) in the respective Revenue Division.",
        },
        {
            "no": "Scheme 11–15",
            "title": "Pumpset Replacement, TN IAMWARM, Minor Irrigation, Land Dev & NADP",
            "subsidy": "Scheme-specific State/World Bank/NADP Subsidies",
            "area": "Tamil Nadu State-wide (varies by project sub-basin)",
            "details": "Replacement of old inefficient pumpsets, World Bank aided irrigation modernization (TN IAMWARM), minor irrigation, and land development.",
            "officer": "Executive Engineer (AED) in the District / Chief Engineer (AED), Chennai.",
        },
    ],
    "தமிழ்": [
        {
            "no": "திட்டம் 1",
            "title": "நதிப் பள்ளத்தாக்குத் திட்ட நீர்ப்பிடிப்புப் பகுதிகளில் மண் மற்றும் நீர் வளப் பாதுகாப்பு",
            "subsidy": "25% மானியம் + 75% கடன் (2 ஆண்டுகள் சலுகைக் காலம்)",
            "area": "வேலூர், திருவண்ணாமலை, தருமபுரி, கிருஷ்ணகிரி & சேலம் (தென்பெண்ணை மற்றும் மேட்டூர் நீர்ப்பிடிப்புப் பகுதிகள்)",
            "details": "சமமட்ட வரப்புகள் அமைத்தல், தோட்டக்கலைப் பயிர்கள், வடிகால் பாதை சீரமைப்பு, பண்ணைக் குட்டைகள், வேளாண் காடுகள் மற்றும் வண்டல் தடுப்பு அமைப்புகள்.",
            "officer": "உதவி செயற்பொறியாளர் (நதிப் பள்ளத்தாக்குத் திட்டம்), கிருஷ்ணகிரி, அரூர், தருமபுரி, மேட்டூர் அல்லது செங்கம்.",
        },
        {
            "no": "திட்டம் 2",
            "title": "வேளாண்மை இயந்திரமயமாக்கும் திட்டம்",
            "subsidy": "இயந்திர விலையில் 25% மானியம் (அல்லது இந்திய அரசு உச்சவரம்பு)",
            "area": "சென்னை நீங்கலாக அனைத்து மாவட்டங்களும்",
            "details": "டிராக்டர்கள், பவர் டில்லர்கள், நெல் நடவு இயந்திரங்கள், நெல் அறுவடை இயந்திரங்கள், ரோட்டவேட்டர், கல்டிவேட்டர், தட்டுக் கலப்பை மற்றும் உளிக் கலப்பை வாங்க மானியம்.",
            "officer": "வருவாய் கோட்ட உதவி செயற்பொறியாளர் (வே.பொ.து) / மாவட்ட செயற்பொறியாளர் (வே.பொ.து).",
        },
        {
            "no": "திட்டம் 3",
            "title": "பாசனப் பகுதி மேம்பாடு மற்றும் நீர் மேலாண்மைத் திட்டம் (CADWM)",
            "subsidy": "மத்திய-மாநில அரசு மானியம் + விவசாயிகள் மன்றத்திற்கு ஹெக்டேருக்கு ரூ. 540",
            "area": "காவிரி டெல்டா (தஞ்சாவூர், திருவாரூர், நாகப்பட்டினம், திருச்சி, கடலூர்) & அணைத் திட்டங்கள் (விழுப்புரம், ஈரோடு, திருநெல்வேலி, தருமபுரி)",
            "details": "வயல் வாய்க்கால்கள் மற்றும் வடிகால்கள் அமைத்தல், சுழற்சி முறை நீர் விநியோகப் பணிகள் மற்றும் நீர் பயன்படுத்துவோர் சங்கங்கள் அமைத்தல்.",
            "officer": "உதவி செயற்பொறியாளர், பாசனப் பகுதி மேம்பாட்டுத் திட்டம் (CADP).",
        },
        {
            "no": "திட்டம் 4 & 5",
            "title": "வேளாண் இயந்திரங்கள் செயல்விளக்கம் மற்றும் விவசாயிகள் பயிற்சித் திட்டம்",
            "subsidy": "இலவச வயல்வெளி செயல்விளக்கம் & புத்தாக்கப் பயிற்சி",
            "area": "சென்னை நீங்கலாக அனைத்து மாவட்டங்களும்",
            "details": "புதிதாக உருவாக்கப்பட்ட வேளாண் கருவிகளின் வயல்வெளி செயல்விளக்கம் மற்றும் 18–40 வயதுடைய விவசாயிகள், கிராமப்புற இளைஞர்களுக்கு இயந்திரப் பராமரிப்புப் பயிற்சி.",
            "officer": "வருவாய் கோட்ட உதவி செயற்பொறியாளர் (வேளாண்மைப் பொறியியல் துறை).",
        },
        {
            "no": "திட்டம் 6",
            "title": "மழைநீர் சேகரிப்பு மற்றும் வழிந்தோடும் நீர் மேலாண்மைத் திட்டம்",
            "subsidy": "சமுதாய நிலங்களுக்கு 100% மானியம் | பட்டா நிலங்களுக்கு 90% மானியம் (SC/ST 95%)",
            "area": "சென்னை மற்றும் நீலகிரி நீங்கலாக அனைத்து மாவட்டங்களும்",
            "details": "நீர் உறிஞ்சும் குட்டைகள், பெரிய/நடுத்தர/சிறிய தடுப்பணைகள், பண்ணைக் குட்டைகள், பயன்பாடற்ற கிணறுகளைப் புதுப்பித்தல் மற்றும் ஊரணிகள் சீரமைப்பு.",
            "officer": "வருவாய் கோட்ட உதவி செயற்பொறியாளர் (வேளாண்மைப் பொறியியல் துறை).",
        },
        {
            "no": "திட்டம் 7",
            "title": "நபார்டு (NABARD) உதவியுடன் கூடிய மழைநீர் சேகரிப்புத் திட்டம்",
            "subsidy": "சமுதாய நிலங்களுக்கு 100% மானியம் | பட்டா நிலங்களுக்கு 75% மானியம்",
            "area": "காஞ்சிபுரம், வேலூர், சேலம், ஈரோடு, திருச்சி, திண்டுக்கல், மதுரை, தேனி, இராமநாதபுரம், கோயம்புத்தூர் & நீலகிரி உள்ளிட்ட 19 மாவட்டங்கள்",
            "details": "தேர்ந்தெடுக்கப்பட்ட நீர்வடிப் பகுதிகளில் நீர் உறிஞ்சும் குட்டைகள், தடுப்பணைகள், பண்ணைக் குட்டைகள் அமைத்தல் மற்றும் பழைய கிணறுகளைப் புதுப்பித்தல்.",
            "officer": "வருவாய் கோட்ட உதவி செயற்பொறியாளர் (வேளாண்மைப் பொறியியல் துறை).",
        },
        {
            "no": "திட்டம் 8 & 9",
            "title": "மலைப் பகுதி (நீலகிரி) & மேற்குத் தொடர்ச்சி மலை மண்/நீர் வளப் பாதுகாப்புத் திட்டம்",
            "subsidy": "100% மானியம் (தனிநபர் பங்கு 10%; SC/ST & சமுதாயப் பணிகளுக்கு 5%)",
            "area": "நீலகிரி (HADP) மற்றும் கோயம்புத்தூர், ஈரோடு, மதுரை, தேனி, திண்டுக்கல், விருதுநகர், திருநெல்வேலி, கன்னியாகுமரி (WGDP)",
            "details": "படிநிலை வரப்புகள், நிலச்சரிவு தடுப்புப் பணிகள், சமமட்ட அகழிகள், கம்பி வலை தடுப்புச் சுவர்கள் (Gabion), கல் வரப்புகள் மற்றும் தடுப்பணைகள்.",
            "officer": "உதவி செயற்பொறியாளர் (வே.பொ.து), உதகமண்டலம் / கூடலூர் / குன்னூர் அல்லது அந்தந்த வருவாய் கோட்ட அலுவலகம்.",
        },
        {
            "no": "திட்டம் 10",
            "title": "பழங்குடியினர் பகுதிகளில் மண் வளப் பாதுகாப்புத் திட்டம் (ITDP)",
            "subsidy": "நிலம் வைத்துள்ள பழங்குடியின விவசாயிகளுக்கு 100% முழு மானியம்",
            "area": "கல்வராயன், ஜவ்வாது, சேர்வராயன், கொல்லி, சித்தேரி மற்றும் பச்சை மலைப் பகுதிகள் (7 மாவட்டங்கள்)",
            "details": "சமமட்டக் கல் வரப்புகள், நிலம் சமன் செய்தல், குழாய் பதித்தல், தட்டுக் கலப்பை உழவு மற்றும் பாசனத் தடுப்பணைகள் அமைத்தல்.",
            "officer": "சம்பந்தப்பட்ட வருவாய் கோட்ட உதவி செயற்பொறியாளர் (வேளாண்மைப் பொறியியல் துறை).",
        },
        {
            "no": "திட்டம் 11–15",
            "title": "பழைய பம்ப்செட் மாற்றுதல், TN IAMWARM, சிறுபாசனம், நில மேம்பாடு & NADP",
            "subsidy": "திட்டத்திற்கு ஏற்ற மாநில அரசு / உலக வங்கி / NADP மானியங்கள்",
            "area": "தமிழ்நாடு முழுவதும் (திட்ட உப-வடிநிலப் பகுதிகளுக்கு ஏற்ப)",
            "details": "பழைய திறனற்ற பம்ப்செட்டுகளை மாற்றுதல், உலக வங்கி உதவியுடன் நீர்வள நிலவளத் திட்டம் (TN IAMWARM), சிறுபாசனம் மற்றும் நில மேம்பாட்டுப் பணிகள்.",
            "officer": "மாவட்ட செயற்பொறியாளர் (வே.பொ.து) / தலைமைப் பொறியாளர் (வே.பொ.து), சென்னை.",
        },
    ],
}

active_schemes = SCHEMES_DATA.get(language, SCHEMES_DATA["English"])
labels = CARD_LABELS.get(language, CARD_LABELS["English"])

filtered_schemes = [
    item
    for item in active_schemes
    if search_filter in f"{item['no']} {item['title']} {item['area']} {item['details']} {item['subsidy']}".lower()
]

# Render cards row-by-row in pairs so both columns stay evenly aligned
for row_start in range(0, len(filtered_schemes), 2):
    row_items = filtered_schemes[row_start : row_start + 2]
    row_cols = st.columns(2)
    for col, item in zip(row_cols, row_items):
        with col:
            st.markdown(
                f"""
                <div class="scheme-card">
                    <div>
                        <span class="badge">{item['no']} • {item['subsidy']}</span>
                        <h4>{item['title']}</h4>
                        <p><b>{labels['coverage']}</b> {item['area']}</p>
                        <p><b>{labels['works']}</b> {item['details']}</p>
                    </div>
                    <p class="officer-text"><b>{labels['officer']}</b> {item['officer']}</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

st.divider()
st.caption(t["footer"])