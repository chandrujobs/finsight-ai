import streamlit as st
from utils.pdf_utils import display_pdf_page

def display_confidence(score):
    """Display a visual confidence indicator"""
    try:
        score = float(score)
        if score >= 4:
            return st.success(f"High confidence: {score}/5")
        elif score >= 3:
            return st.info(f"Medium confidence: {score}/5")
        else:
            return st.warning(f"Low confidence: {score}/5")
    except:
        return st.error("Invalid confidence score")

def display_source_page(pdf_path, mentioned_pages):
    """Display source page from the PDF"""
    st.write("### Source Verification")
    selected_page = st.selectbox("View source page:", options=[int(p) for p in set(mentioned_pages)])
    if selected_page:
        st.markdown(display_pdf_page(pdf_path, selected_page), unsafe_allow_html=True)

def display_data_table(data_df):
    """Display a DataFrame with enhanced styling"""
    st.dataframe(data_df, use_container_width=True)

def create_metric_card(title, value, delta=None, help_text=None):
    """Create a metric card with optional delta value"""
    if delta:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            help=help_text
        )
    else:
        st.metric(
            label=title,
            value=value,
            help=help_text
        )

def create_expandable_text(title, content):
    """Create expandable text section"""
    with st.expander(title):
        st.write(content)

def create_file_uploader(label, accepted_types=None):
    """Create a file uploader with standard configuration"""
    if accepted_types is None:
        accepted_types = ["pdf"]
    
    return st.file_uploader(
        label=label,
        type=accepted_types,
        accept_multiple_files=False,
        help="Upload a PDF document for analysis"
    )

def create_warning_box(message):
    """Create a warning box with standardized styling"""
    st.warning(message)

def create_success_box(message):
    """Create a success box with standardized styling"""
    st.success(message)

def create_info_box(message):
    """Create an info box with standardized styling"""
    st.info(message)

def create_error_box(message):
    """Create an error box with standardized styling"""
    st.error(message)

def create_page_navigator(pdf_path, total_pages):
    """Create a page navigator for browsing PDF pages"""
    st.subheader("Document Browser")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        page_num = st.slider("Select page:", min_value=1, max_value=total_pages, value=1)
    
    with col2:
        prev_button = st.button("Previous Page")
        next_button = st.button("Next Page")
    
    # Handle navigation
    if prev_button and page_num > 1:
        page_num -= 1
    elif next_button and page_num < total_pages:
        page_num += 1
    
    # Display the selected page
    st.markdown("### Document Page")
    st.markdown(display_pdf_page(pdf_path, page_num), unsafe_allow_html=True)
    
    return page_num