import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Import UI modules
from ui.document_management import render_document_management
from ui.analysis_tab import render_analysis_tab
from ui.extraction_tab import render_extraction_tab
from ui.comparison_tab import render_comparison_tab
from ui.dashboard_tab import render_dashboard_tab

# Import config
from config import APP_TITLE, APP_DESCRIPTION

# Load environment variables
load_dotenv()

def init_session_state():
    """Initialize session state variables"""
    if 'processed_docs' not in st.session_state:
        st.session_state.processed_docs = {}
    if 'current_doc' not in st.session_state:
        st.session_state.current_doc = None
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = False
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = {}

def setup_page():
    """Setup page configuration"""
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

def handle_api_key():
    """Handle API key management"""
    # Sidebar for configuration
    st.sidebar.header("Configuration")

    # API Key handling - try .env first, then allow manual input
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        GOOGLE_API_KEY = st.sidebar.text_input("Enter Gemini API Key", type="password")
        if GOOGLE_API_KEY:
            # Set the API key in environment for the session
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
            st.sidebar.success("API Key set for this session!")
            return GOOGLE_API_KEY
        else:
            st.warning("Please enter your Gemini API Key to continue.")
            return None
    return GOOGLE_API_KEY

def render_sidebar():
    """Render the sidebar components"""
    # Add instructions to sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("How to use this app")
    st.sidebar.markdown("""
    1. Upload a single PDF or a folder of PDFs
    2. Process the documents to enable analysis
    3. Use the Financial Analysis tab to ask questions
    4. Extract standardized data for comparison and prediction
    5. Generate a dynamic financial dashboard
    6. Compare metrics across multiple documents
    7. Generate future financial projections
    """)

    # Display Gemini model information
    st.sidebar.markdown("---")
    st.sidebar.subheader("Model Information")
    st.sidebar.info("Using Gemini 1.5 Flash model for analysis")

    # Required dependencies footer
    st.sidebar.markdown("---")
    st.sidebar.subheader("Required Dependencies")
    st.sidebar.code("""
    pip install streamlit langchain faiss-cpu
    pip install PyMuPDF pandas plotly
    pip install google-generativeai
    pip install python-dotenv matplotlib seaborn
    pip install langchain-google-genai
    """)

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Setup page
    setup_page()
    
    # Handle API key
    api_key = handle_api_key()
    
    # Only proceed if we have an API key
    if api_key:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Create tabs for the main interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Document Management", 
            "Financial Analysis", 
            "Data Extraction", 
            "Comparison & Prediction", 
            "Financial Dashboard"
        ])
        
        # Render each tab
        with tab1:
            render_document_management()
        
        # Only show the other tabs if we have processed documents
        if st.session_state.processed_docs and st.session_state.current_doc:
            with tab2:
                render_analysis_tab()
            
            with tab3:
                render_extraction_tab()
            
            with tab4:
                render_comparison_tab()
            
            with tab5:
                render_dashboard_tab()
    
    # Render sidebar
    render_sidebar()

if __name__ == "__main__":
    main()