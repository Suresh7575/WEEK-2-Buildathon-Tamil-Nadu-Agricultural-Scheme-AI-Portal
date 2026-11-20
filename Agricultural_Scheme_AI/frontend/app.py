import base64
import json
import time
from pathlib import Path
import requests
import streamlit as st


# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="Tamil Nadu Agricultural Scheme AI Portal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Paths for local videos and background image
PROJECT_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR_CANDIDATES = [
    PROJECT_DIR / "data" / "Videos",
    PROJECT_DIR / "Videos",
    Path.cwd() / "data" / "Videos",
]
VIDEO_DIR = next(
    (folder for folder in VIDEO_DIR_CANDIDATES if folder.is_dir()),
    PROJECT_DIR / "data" / "Videos",
)

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


def stream_words(text: str):
    """Generator to stream AI reply word-by-word while preserving newlines."""
    for line in text.splitlines(keepends=True):
        words = line.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            time.sleep(0.025)


local_videos = get_local_videos(VIDEO_DIR)
bg_base64 = get_base64_str(BG_IMAGE_PATH)

# 2. Bilingual Text Dictionary
TEXT = {
    "English": {
        "title": "Tamil Nadu Agricultural Engineering Scheme AI Portal",
        "subtitle": "Simple, reliable guidance about Tamil Nadu Government agricultural schemes, subsidies, and machinery—based on uploaded government PDFs.",
        "language": "Language / மொழி",
        "upload_title": "📄 Add Scheme Documents",
        "upload_help": "Upload government scheme PDFs. New files are indexed automatically.",
        "choose_pdf": "Choose PDF files",
        "index_button": "Upload & Index PDFs",
        "upload_success": "Document processing completed.",
        "ask_header": "💬 AI Scheme Assistant — Eligibility, Subsidies & Offices",
        "ask_hint": "Ask about Tamil Nadu agricultural schemes...",
        "send_btn": "Ask 🚀",
        "quick": "🌱 Suggested Quick Prompts",
        "welcome": "👋 **Vanakkam!** Ask any question below about Tamil Nadu agricultural schemes, machinery subsidies, or rainwater harvesting using the uploaded government documents.",
        "clear": "🗑️ Clear",
        "disclaimer": "Confirm eligibility & subsidies with AED office before applying.",
        "backend_error": "Could not connect to FastAPI backend. Start FastAPI and retry.",
        "processing": "Searching agricultural documents...",
        "indexed": "Indexed",
        "duplicate": "Already indexed",
        "failed": "Could not process",
        "pages": "pages",
        "video_banner": "🎥 Scheme Videos",
        "schemes_banner": "📋 TNAU Schemes Directory",
        "filter_hint": "🔍 Filter schemes (Tractor, Rain, Tribal...)",
        "contact_footer": "📞 Chief Engineer (AED), Nandanam, Chennai - 600 035 | ☎️ 044-2435 2686 / 2435 2622",
        "quick_questions": [
            "Who is eligible for this scheme?",
            "What subsidy is available for Tractors & Power Tillers?",
            "Rain Water Harvesting grants for SC/ST farmers?",
            "Districts covered under NABARD Rain Water Harvesting?",
        ],
    },
    "தமிழ்": {
        "title": "தமிழ்நாடு வேளாண்மைப் பொறியியல் திட்டங்கள் AI தளம்",
        "subtitle": "பதிவேற்றப்பட்ட அரசு PDF ஆவணங்களின் அடிப்படையில் வேளாண்மைத் திட்டங்கள் மற்றும் மானியங்களை எளிய தமிழில் அறியுங்கள்.",
        "language": "Language / மொழி",
        "upload_title": "📄 திட்ட ஆவணங்களைச் சேர்க்கவும்",
        "upload_help": "அரசுத் திட்ட PDF கோப்புகளைப் பதிவேற்றவும். தானாகத் தேடல் அமைப்பில் சேர்க்கப்படும்.",
        "choose_pdf": "PDF கோப்புகளைத் தேர்ந்தெடுக்கவும்",
        "index_button": "PDF பதிவேற்றி சேர்க்கவும்",
        "upload_success": "ஆவணச் செயலாக்கம் முடிந்தது.",
        "ask_header": "💬 AI திட்ட உதவியாளர் — தகுதி & மானிய விவரங்கள்",
        "ask_hint": "வேளாண்மைத் திட்டம் குறித்து கேள்வி கேளுங்கள்...",
        "send_btn": "கேள் 🚀",
        "quick": "🌱 மாதிரி கேள்விகள்",
        "welcome": "👋 **வணக்கம்!** தமிழ்நாடு வேளாண்மைத் திட்டங்கள், இயந்திர மானியங்கள் மற்றும் மழைநீர் சேகரிப்பு குறித்து கீழே கேள்வி கேளுங்கள்.",
        "clear": "🗑️ நீக்கு",
        "disclaimer": "விண்ணப்பிப்பதற்கு முன் வேளாண்மைப் பொறியியல் துறையிடம் உறுதிப்படுத்தவும்.",
        "backend_error": "FastAPI சேவையகத்துடன் இணைக்க முடியவில்லை.",
        "processing": "ஆவணங்கள் தேடப்படுகின்றன...",
        "indexed": "சேர்க்கப்பட்டது",
        "duplicate": "ஏற்கனவே உள்ளது",
        "failed": "செயலாக்க முடியவில்லை",
        "pages": "பக்கங்கள்",
        "video_banner": "🎥 விளக்க வீடியோக்கள்",
        "schemes_banner": "📋 TNAU திட்டங்கள் பட்டியல்",
        "filter_hint": "🔍 திட்டங்களைத் தேடவும் (Tractor, Rain, Tribal...)",
        "contact_footer": "📞 தலைமைப் பொறியாளர் (வே.பொ.து), நந்தனம், சென்னை | ☎️ 044-2435 2686",
        "quick_questions": [
            "இந்தத் திட்டத்திற்கு யார் தகுதியானவர்கள்?",
            "டிராக்டர் மற்றும் பவர் டில்லருக்கு எவ்வளவு மானியம்?",
            "மழைநீர் சேகரிப்பு திட்டத்தில் SC/ST மானியம் என்ன?",
            "எந்த மாவட்டங்கள் பயன்பெறும்?",
        ],
    },
}

# 3. Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "English"
if "api_base" not in st.session_state:
    st.session_state.api_base = "http://127.0.0.1:8000"

# 4. CSS: Clean High-Contrast Glass UI (No Sidebar)
bg_css = (
    f"""
    background-image: linear-gradient(rgba(6, 20, 9, 0.78), rgba(6, 20, 9, 0.84)), url("data:image/png;base64,{bg_base64}");
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
    /* Hide Sidebar & Top Chrome */
    [data-testid="stSidebar"], [data-testid="collapsedControl"], header[data-testid="stHeader"] {{
        display: none !important;
    }}

    /* Background & Global Text */
    .stApp {{
        {bg_css}
        color: #ffffff !important;
    }}

    .block-container {{
        padding-top: 0.7rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
        max-width: 100% !important;
    }}

    .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp small {{
        color: #ffffff !important;
    }}

    /* Hero Banner */
    .hero-banner {{
        background: linear-gradient(135deg, rgba(27, 94, 32, 0.95) 0%, rgba(46, 125, 50, 0.92) 60%, rgba(104, 159, 56, 0.92) 100%);
        padding: 0.65rem 1.4rem;
        border-radius: 12px;
        margin-bottom: 0.6rem;
        border: 1px solid rgba(255, 255, 255, 0.35);
    }}
    .hero-banner h1 {{
        color: #ffffff !important;
        margin: 0 0 0.15rem 0 !important;
        font-size: 1.45rem !important;
        line-height: 1.2 !important;
    }}
    .hero-banner .hero-sub {{
        color: #f1f8e9 !important;
        font-size: 0.86rem !important;
        line-height: 1.3 !important;
        margin: 0 !important;
    }}

    /* Compact KPI Cards */
    .kpi-card {{
        background-color: #0e2914 !important;
        padding: 0.45rem 0.85rem;
        border-radius: 10px;
        border: 1px solid #81c784;
        border-left: 5px solid #ffd54f;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
    }}
    .kpi-label {{
        color: #c8e6c9 !important;
        font-size: 0.78rem;
        font-weight: 700;
    }}
    .kpi-value {{
        color: #ffffff !important;
        font-size: 1.15rem;
        font-weight: 800;
    }}
    .kpi-delta {{
        background-color: rgba(255, 213, 79, 0.18);
        color: #ffd54f !important;
        border: 1px solid #ffd54f;
        padding: 0.1rem 0.45rem;
        border-radius: 8px;
        font-size: 0.72rem;
        font-weight: 700;
    }}

    /* Panel Headers */
    .panel-header {{
        background: linear-gradient(90deg, #1b5e20, #2e7d32);
        color: #ffd54f !important;
        padding: 0.5rem 0.9rem;
        border-radius: 10px 10px 0 0;
        font-size: 0.96rem;
        font-weight: 800;
        border: 1.5px solid #81c784;
        border-bottom: none;
    }}

    .ai-spotlight-header {{
        background: linear-gradient(90deg, #1b5e20, #388e3c, #2e7d32);
        color: #ffd54f !important;
        padding: 0.55rem 1rem;
        border-radius: 10px 10px 0 0;
        font-size: 1.05rem;
        font-weight: 800;
        border: 2px solid #ffd54f;
        border-bottom: none;
    }}

    /* Welcome Box */
    .welcome-highlight {{
        background: linear-gradient(90deg, rgba(46, 125, 50, 0.72), rgba(104, 159, 56, 0.62));
        border-left: 4px solid #ffd54f;
        padding: 0.65rem 0.9rem;
        border-radius: 8px;
        color: #ffffff !important;
        font-size: 0.92rem;
        line-height: 1.42;
        margin-bottom: 0.4rem;
    }}

    /* Frosted Glass Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: rgba(10, 28, 14, 0.92) !important;
        border: 1.5px solid #81c784 !important;
        border-radius: 0 0 10px 10px !important;
        padding: 0.55rem 0.75rem !important;
    }}

    /* Buttons Styling */
    .stButton button, [data-testid="stFormSubmitButton"] button {{
        background-color: #1e5628 !important;
        color: #ffffff !important;
        border: 1px solid #81c784 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0.35rem 0.6rem !important;
        line-height: 1.3 !important;
        text-align: left !important;
    }}
    .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {{
        background-color: #2e7d32 !important;
        border-color: #ffd54f !important;
    }}
    [data-testid="stFormSubmitButton"] button {{
        background-color: #ffd54f !important;
        color: #0b2210 !important;
        font-weight: 800 !important;
        text-align: center !important;
    }}

    /* Selectbox & Text Inputs */
    [data-baseweb="select"] > div, .stTextInput input {{
        background-color: #14381c !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1.5px solid #ffd54f !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
    }}
    .stTextInput input::placeholder {{
        color: #fff59d !important;
        -webkit-text-fill-color: #fff59d !important;
        opacity: 1 !important;
    }}

    /* Compact File Uploader Dropzone */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: #13351a !important;
        border: 1.5px dashed #ffd54f !important;
        border-radius: 8px !important;
        padding: 0.45rem 0.6rem !important;
    }}
    [data-testid="stFileUploaderDropzone"] small {{
        color: #ffd54f !important;
        font-weight: 600 !important;
        font-size: 0.74rem !important;
    }}
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border: 1px solid #ffd54f !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.76rem !important;
    }}

    /* Chat Message Bubbles */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 10px;
        padding: 0.55rem 0.8rem;
        margin-bottom: 0.45rem;
        font-size: 0.92rem !important;
    }}

    /* Scheme Cards */
    .scheme-card-mini {{
        background-color: rgba(16, 42, 21, 0.95) !important;
        border-left: 5px solid #ffd54f;
        border-top: 1px solid rgba(165, 214, 167, 0.35);
        border-right: 1px solid rgba(165, 214, 167, 0.35);
        border-bottom: 1px solid rgba(165, 214, 167, 0.35);
        padding: 0.7rem 0.9rem;
        border-radius: 10px;
        margin-bottom: 0.55rem;
    }}
    .scheme-card-mini h4 {{
        color: #ffd54f !important;
        margin: 0.25rem 0 0.35rem 0 !important;
        font-size: 0.95rem !important;
        line-height: 1.3 !important;
    }}
    .scheme-card-mini p {{
        font-size: 0.84rem !important;
        line-height: 1.4 !important;
        margin-bottom: 0.25rem !important;
    }}
    .badge {{
        display: inline-block;
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        padding: 0.15rem 0.55rem;
        border-radius: 8px;
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        border: 1px solid #81c784;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

t = TEXT[st.session_state.language]

# 5. Top Hero Banner & KPI Strip
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
        ("Total AED Schemes", "15 Major", "TNAU Ref"),
        ("Mechanization", "25% Cost", "GoI Limit"),
        ("Rainwater Harvesting", "90–100%", "Patta/Comm"),
        ("Tribal Subsidy", "100% Grant", "7 Districts"),
    ],
    "தமிழ்": [
        ("மொத்த திட்டங்கள்", "15 முக்கிய", "TNAU"),
        ("இயந்திர மானியம்", "25% விலை", "அரசு வரம்பு"),
        ("மழைநீர் சேகரிப்பு", "90–100%", "பட்டா/சமுதாய"),
        ("பழங்குடியினர்", "100% மானியம்", "7 மாவட்டங்கள்"),
    ],
}

kpi_cols = st.columns(4)
for col, (label, val, delta) in zip(kpi_cols, KPIS_BY_LANG[st.session_state.language]):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{val}</div>
                </div>
                <div class="kpi-delta">▲ {delta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# 6. LAYOUT:
#    [Left Panel: Language, Quick Prompts, PDF Upload]
#    [Single Main Column: AI Chat Box + Clear Button -> Videos & Schemes Below]
# ==============================================================================
col_left, col_main = st.columns([1.0, 2.75], gap="medium")

# ------------------------------------------------------------------------------
# LEFT PANEL: Language, Suggested Quick Prompts & Add Scheme Documents
# ------------------------------------------------------------------------------
with col_left:
    st.markdown(
        f'<div class="panel-header">⚙️ {t["language"]}</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        selected_lang = st.selectbox(
            "Language / மொழி",
            ["English", "தமிழ்"],
            index=0 if st.session_state.language == "English" else 1,
            label_visibility="collapsed",
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

        st.markdown(f"**{t['quick']}**")
        for idx, sample in enumerate(t["quick_questions"]):
            if st.button(
                sample,
                key=f"quick_{st.session_state.language}_{idx}",
                use_container_width=True,
            ):
                st.session_state.pending_question = sample

        st.markdown("---")
        st.markdown(f"**{t['upload_title']}**")
        st.caption(t["upload_help"])
        uploaded_files = st.file_uploader(
            t["choose_pdf"],
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
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
                        f"{st.session_state.api_base.rstrip('/')}/upload",
                        files=payload,
                        timeout=600,
                    )
                result.raise_for_status()
                data = result.json()
                st.success(t["upload_success"])
                for item in data.get("results", []):
                    status = item.get("status")
                    if status == "indexed":
                        st.success(
                            f"{item['filename']} — {t['indexed']} ({item.get('pages', 0)} {t['pages']})"
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


# ------------------------------------------------------------------------------
# SINGLE MAIN COLUMN:
#   1) AI Scheme Assistant + Question Input & Clear Button
#   2) Scheme Videos (Directly Below Chat Box, Edge-to-Edge No Black Bars)
#   3) TNAU Schemes Directory (Directly Below Videos)
# ------------------------------------------------------------------------------
with col_main:
    # === SECTION 1: AI SCHEME ASSISTANT ===
    st.markdown(
        f'<div class="ai-spotlight-header">{t["ask_header"]}</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        chat_box = st.container(height=275, border=False)
        with chat_box:
            if not st.session_state.messages:
                st.markdown(
                    f'<div class="welcome-highlight">{t["welcome"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                for message in st.session_state.messages:
                    avatar = "🧑‍🌾" if message["role"] == "user" else "🌾"
                    with st.chat_message(message["role"], avatar=avatar):
                        st.markdown(message["content"])

        # Question Input Box + Ask & Clear Conversation Buttons Side-by-Side
        with st.form("chat_ask_form", clear_on_submit=True):
            f_q, f_send, f_clear = st.columns([5.0, 1.1, 1.1], gap="small")
            with f_q:
                user_input = st.text_input(
                    "Question",
                    placeholder=t["ask_hint"],
                    label_visibility="collapsed",
                )
            with f_send:
                submitted = st.form_submit_button(
                    t["send_btn"], use_container_width=True
                )
            with f_clear:
                cleared = st.form_submit_button(
                    t["clear"], use_container_width=True
                )

        if cleared:
            st.session_state.messages = []
            st.rerun()

        question = user_input.strip() if submitted and user_input.strip() else None
        if st.session_state.get("pending_question"):
            question = st.session_state.pop("pending_question")

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with chat_box:
                with st.chat_message("user", avatar="🧑‍🌾"):
                    st.markdown(question)

                with st.chat_message("assistant", avatar="🌾"):
                    try:
                        with st.spinner(t["processing"]):
                            response = requests.post(
                                f"{st.session_state.api_base.rstrip('/')}/ask",
                                json={
                                    "question": question,
                                    "chat_history": st.session_state.messages[:-1],
                                    "language": (
                                        "Tamil"
                                        if st.session_state.language == "தமிழ்"
                                        else "English"
                                    ),
                                },
                                timeout=180,
                            )
                        response.raise_for_status()
                        answer = response.json().get("answer", "")
                    except requests.exceptions.HTTPError as exc:
                        detail = format_api_error(exc.response)
                        answer = f"⚠️ {t['backend_error']} ({detail})"
                    except requests.exceptions.RequestException as exc:
                        answer = f"⚠️ {t['backend_error']} ({exc})"

                    # Word-by-word streaming output
                    st.write_stream(stream_words(answer))

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
            st.rerun()

        st.caption(f"ℹ️ {t['disclaimer']}  |  {t['contact_footer']}")

    # === SECTION 2: SCHEME VIDEOS (DIRECTLY UNDER CHAT BOX, FULL-WIDTH FIT) ===
    st.markdown(
        f'<div class="panel-header" style="margin-top: 0.65rem;">{t["video_banner"]}</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        VIDEO_TITLE_MAP = {
            "video_1": "NADP: Agricultural Development & Conservation",
            "video_2": "Tamil Nadu Agricultural Engineering Department Schemes",
            "video_3": "Soil & Water Conservation, TN IAMWARM & Mechanisation",
        }

        if not local_videos:
            st.info(f"Add `.mp4` videos in `{VIDEO_DIR}`")
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
            <div style="font-family: sans-serif; color: #ffffff;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span id="vidTitle" style="font-size: 14px; font-weight: bold; color: #ffd54f;"></span>
                    <div>
                        <button onclick="prevVideo()" style="background:#2e7d32; color:#fff; border:1px solid #ffd54f; padding:4px 10px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:bold; margin-right:5px;">⏮ Prev</button>
                        <button onclick="nextVideo()" style="background:#2e7d32; color:#fff; border:1px solid #ffd54f; padding:4px 10px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:bold;">Next ⏭</button>
                    </div>
                </div>
                <video id="agriLoopPlayer" controls autoplay muted playsinline
                    style="width: 100%; height: 300px; border-radius: 8px; background: #0b2210; object-fit: cover; display: block;">
                </video>
            </div>
            <script>
                const playlist = [{playlist_array_str}];
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
                function nextVideo() {{ loadVideo(currentIndex + 1); }}
                function prevVideo() {{ loadVideo(currentIndex - 1); }}
                player.addEventListener("ended", () => {{ nextVideo(); }});
                loadVideo(0);
            </script>
            """
            st.html(loop_player_html, unsafe_allow_javascript=True)

    # === SECTION 3: TNAU SCHEMES DIRECTORY (DIRECTLY UNDER VIDEOS) ===
    st.markdown(
        f'<div class="panel-header" style="margin-top: 0.65rem;">{t["schemes_banner"]}</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        search_filter = st.text_input(
            "Filter",
            placeholder=t["filter_hint"],
            label_visibility="collapsed",
        ).lower()

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

        active_schemes = SCHEMES_DATA.get(st.session_state.language, SCHEMES_DATA["English"])
        labels = CARD_LABELS.get(st.session_state.language, CARD_LABELS["English"])
        filtered_schemes = [
            item
            for item in active_schemes
            if search_filter in f"{item['no']} {item['title']} {item['area']} {item['details']} {item['subsidy']}".lower()
        ]

        for item in filtered_schemes:
            st.markdown(
                f"""
                <div class="scheme-card-mini">
                    <span class="badge">{item['no']} • {item['subsidy']}</span>
                    <h4>{item['title']}</h4>
                    <p><b>{labels['coverage']}</b> {item['area']}</p>
                    <p><b>{labels['works']}</b> {item['details']}</p>
                    <p><b>{labels['officer']}</b> {item['officer']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )