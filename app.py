import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
from PIL import Image

# Import your existing backend
from extract import extract_website_data
from rag import GeminiTestGenerator

# Page config
st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Professional Design
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom color scheme */
    :root {
        --primary-color: #2C3E50;
        --secondary-color: #34495E;
        --accent-color: #3498DB;
        --text-color: #2C3E50;
        --bg-color: #ECF0F1;
    }
    
    /* Main container */
    .main {
        background-color: #ffffff;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
        text-align: center;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
        margin-top: 0.5rem;
        text-align: center;
    }
    
    /* Logo container */
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
        
    }
    
    /* Section headers */
    .section-header {
        color: #2C3E50;
        font-size: 1.4rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498DB;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3498DB;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #3498DB;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        border-radius: 6px;
        border: 2px solid #E8E8E8;
        padding: 0.75rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #3498DB;
        box-shadow: 0 0 0 0.2rem rgba(52, 152, 219, 0.25);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #E8E8E8;
        border-radius: 6px;
        padding: 1rem;
        background: #F8F9FA;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #F8F9FA;
        border-radius: 6px;
        font-weight: 600;
        color: #2C3E50;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #F8F9FA;
        border-radius: 6px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #2C3E50;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #D4EDDA;
        color: #155724;
        border-left: 4px solid #28A745;
        border-radius: 6px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #F8D7DA;
        color: #721C24;
        border-left: 4px solid #DC3545;
        border-radius: 6px;
        padding: 1rem;
    }
    
    /* Download button */
    .stDownloadButton>button {
        background-color: white;
        color: #3498DB;
        border: 2px solid #3498DB;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    
    .stDownloadButton>button:hover {
        background-color: #3498DB;
        color: white;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1E83B;
    }
    
    /* DataFrame styling */
    .dataframe {
        border: none !important;
    }
    
    .dataframe thead tr th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        font-weight: 600;
        text-align: left;
        padding: 0.75rem;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #F8F9FA;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Logo Section (Put your logo here)
logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
with logo_col2:
    # Uncomment and modify this when you have a logo
    if os.path.exists("logo.png"):
        logo = Image.open("logo.png")
        st.image(logo, width=500)
   
# Header
st.markdown("""
    <div class='header-container'>
        <h1 class='header-title'>Automated Test Case Generator</h1>
        <p class='header-subtitle'>Generate comprehensive test cases and test suites using AI</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("<h3 style='color: #2C3E50;'>Configuration</h3>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #7F8C8D; font-size: 0.9rem;'>PDF Documentation</p>", unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader(
        "Upload PDF (optional)",
        type=['pdf'],
        help="Upload testing documentation or leave empty to use default",
        label_visibility="collapsed"
    )
    
    if uploaded_pdf:
        pdf_path = f"temp_{uploaded_pdf.name}"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        st.success(f"Loaded: {uploaded_pdf.name}")
    else:
        if os.path.exists("blackbox-07.pdf"):
            st.info("Using default documentation")
    
    st.markdown("---")
    
    st.markdown("<p style='color: #7F8C8D; font-size: 0.9rem;'>Crawling Settings</p>", unsafe_allow_html=True)
    max_pages = st.slider("Maximum pages", 1, 20, 6, label_visibility="collapsed")
    
    if st.session_state.results:
        st.markdown("---")
        st.success("Tests generated successfully")

# Main Content
st.markdown("<h2 class='section-header'>Website Information</h2>", unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])

with col1:
    url = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        help="Enter the full URL of the website to test"
    )

# User Stories Section
with st.expander("Add User Stories (Optional)"):
    user_stories_text = st.text_area(
        "Enter user stories, one per line",
        value="As a user, I want to authenticate securely\nAs a user, I want to navigate intuitively\nAs a user, I want forms to validate properly\nAs a user, I want responsive design on all devices",
        height=120,
        label_visibility="collapsed"
    )

user_stories = [s.strip() for s in user_stories_text.split('\n') if s.strip()]

st.markdown("<br>", unsafe_allow_html=True)

# Generate Button
if st.button("Generate Test Cases", use_container_width=True):
    if not url:
        st.error("Please enter a website URL")
    elif not url.startswith(('http://', 'https://')):
        st.error("URL must start with http:// or https://")
    else:
        try:
            # Step 1: Extract
            st.markdown("<h2 class='section-header'>Step 1: Extracting Website Data</h2>", unsafe_allow_html=True)
            with st.spinner("Analyzing website structure..."):
                web_data = extract_website_data(url, max_pages)
            
            st.success(f"Successfully extracted data from {web_data['basic_info']['pages_crawled']} pages")
            
            # Step 2: Initialize AI
            st.markdown("<h2 class='section-header'>Step 2: Initializing AI Engine</h2>", unsafe_allow_html=True)
            with st.spinner("Loading AI model..."):
                pdf_files = [pdf_path] if uploaded_pdf and os.path.exists(pdf_path) else None
                generator = GeminiTestGenerator(pdf_paths=pdf_files)
            
            st.success("AI engine initialized successfully")
            
            # Step 3: Generate
            st.markdown("<h2 class='section-header'>Step 3: Generating Test Cases</h2>", unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Generating main test cases...")
            progress_bar.progress(30)
            
            with st.spinner("AI is analyzing and generating tests..."):
                results = generator.generate_all_tests(web_data, user_stories)
            
            progress_bar.progress(100)
            status_text.text("Generation complete!")
            
            st.session_state.results = results
            
            # Cleanup
            if uploaded_pdf and os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            st.success("All test cases and suites generated successfully")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Display Results
if st.session_state.results:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-header'>Generated Results</h2>", unsafe_allow_html=True)
    
    results = st.session_state.results
    main_tests = results['main_test_cases'].get('test_cases', [])
    suites = results['test_suites']
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-value'>{len(main_tests)}</p>
                <p class='metric-label'>Total Tests</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        positive = len([tc for tc in main_tests if tc.get('type') == 'positive'])
        st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-value'>{positive}</p>
                <p class='metric-label'>Positive Tests</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        negative = len([tc for tc in main_tests if tc.get('type') == 'negative'])
        st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-value'>{negative}</p>
                <p class='metric-label'>Negative Tests</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_suites = sum(len(suite) for suite in suites.values())
        st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-value'>{total_suites}</p>
                <p class='metric-label'>Suite Tests</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Main Test Cases", "Test Suites", "Download"])
    
    # TAB 1: Main Tests
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        search = st.text_input("Search test cases", "", placeholder="Search by ID or name...")
        
        for tc in main_tests:
            if search and search.lower() not in tc.get('name', '').lower() and search.lower() not in tc.get('id', '').lower():
                continue
            
            with st.expander(f"{tc.get('id')}: {tc.get('name')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Type:** {tc.get('type', 'N/A')}")
                with col2:
                    st.write(f"**Priority:** {tc.get('priority', 'N/A')}")
                with col3:
                    st.write(f"**Technique:** {tc.get('test_technique', 'N/A')}")
                
                st.write("**Test Steps:**")
                for step in tc.get('steps', []):
                    st.write(f"• {step}")
                
                st.write(f"**Expected Result:** {tc.get('expected_result', 'N/A')}")
    
    # TAB 2: Suites
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        suite_tabs = st.tabs(["Performance", "Cross-Browser", "Responsive Design", "Stress Testing"])
        
        suite_names = ['performance', 'cross_browser', 'responsive_design', 'stress']
        suite_titles = ['Performance Tests', 'Cross-Browser Tests', 'Responsive Design Tests', 'Stress Tests']
        
        for idx, (suite_name, suite_title) in enumerate(zip(suite_names, suite_titles)):
            with suite_tabs[idx]:
                suite_tests = suites.get(suite_name, [])
                st.write(f"**Total Tests:** {len(suite_tests)}")
                st.markdown("<br>", unsafe_allow_html=True)
                
                for test in suite_tests:
                    with st.expander(f"{test.get('id')}: {test.get('name')}"):
                        st.write(f"**Description:** {test.get('description', 'N/A')}")
                        st.write(f"**Priority:** {test.get('priority', 'N/A')}")
                        
                        st.write("**Test Steps:**")
                        for step in test.get('steps', []):
                            st.write(f"• {step}")
                        
                        st.write(f"**Expected Result:** {test.get('expected_result', 'N/A')}")
    
    # TAB 3: Download
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Main Test Cases")
            
            json_data = json.dumps(results['main_test_cases'], indent=2)
            st.download_button(
                "Download JSON",
                json_data,
                "main_test_cases.json",
                "application/json",
                use_container_width=True
            )
            
            df = pd.DataFrame(main_tests)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "main_test_cases.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            st.subheader("Test Suites")
            
            all_suites = json.dumps(suites, indent=2)
            st.download_button(
                "Download All Suites",
                all_suites,
                "all_suites.json",
                "application/json",
                use_container_width=True
            )
            
            for suite_name in suite_names:
                suite_data = json.dumps({
                    "suite_name": suite_name,
                    "tests": suites.get(suite_name, [])
                }, indent=2)
                
                st.download_button(
                    f"{suite_name.replace('_', ' ').title()}",
                    suite_data,
                    f"{suite_name}_suite.json",
                    "application/json",
                    key=f"dl_{suite_name}",
                    use_container_width=True
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("Complete Package")
        complete = json.dumps(results, indent=2)
        st.download_button(
            "Download Everything (JSON)",
            complete,
            f"complete_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )

# Footer
st.markdown("""
<div class="intro-container">
    <h2 class="intro-title">Platform Overview</h2>
    <p class="intro-text">
        This platform automatically generates structured, professional-grade test cases
        by analyzing website structure, UI components, navigation flows, and optional
        documentation using advanced AI reasoning.
    </p>
    <div class="feature-list">
        <strong>Core Capabilities:</strong><br>
        • Intelligent website crawling and UI analysis<br>
        • Functional positive and negative test coverage<br>
        • Performance, cross-browser, responsive, and stress test suites<br>
        • AI-powered contextual understanding via PDF documentation<br>
        • Export-ready testing artifacts for QA workflows
    </div>
</div>
""", unsafe_allow_html=True)

# ================= FOOTER =================
st.markdown("""
<div class="footer-container">
    <p class="creators">Developed by Wissem Ben Khalifa & Yassin Ayedi</p>
    <p class="footer-text">Automated Test Case Generator © 2026</p>
</div>
""", unsafe_allow_html=True)