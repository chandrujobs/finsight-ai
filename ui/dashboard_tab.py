import streamlit as st
from modules.visualization import create_financial_dashboard
from modules.qa_chain import create_qa_chain, generate_financial_insights  # Already imported here

def render_dashboard_tab():
    """Render the financial dashboard tab"""
    st.header("Financial Dashboard")
    
    if st.session_state.extracted_data:
        # Create comprehensive dashboard from all extracted data
        create_financial_dashboard(st.session_state.extracted_data)
        
        # Add AI-powered insights
        st.subheader("Dashboard Insights")
        
        if st.button("Generate Dashboard Insights"):
            with st.spinner("Generating AI-powered insights..."):
                # Combine all extracted data for analysis
                current_doc_data = st.session_state.processed_docs[st.session_state.current_doc]
                # The error is happening here - we already imported create_qa_chain at the top
                qa_chain = create_qa_chain(current_doc_data['vectorstore'])
                insights = generate_financial_insights(qa_chain, st.session_state.extracted_data)
                
                st.markdown(insights)
    else:
        st.info("Extract data in the Data Extraction tab to populate the dashboard.")
        
        if st.button("Extract Data for Dashboard"):
            with st.spinner("Extracting standardized financial data..."):
                # Already imported at the top level, no need to import here
                # from modules.qa_chain import create_qa_chain  <- REMOVE THIS LINE
                from modules.data_extraction import extract_standardized_financials
                
                current_doc_data = st.session_state.processed_docs[st.session_state.current_doc]
                qa_chain = create_qa_chain(current_doc_data['vectorstore'])
                extracted_data = extract_standardized_financials(qa_chain, current_doc_data['info']['type'])
                
                # Store for future use
                if st.session_state.current_doc not in st.session_state.extracted_data:
                    st.session_state.extracted_data[st.session_state.current_doc] = extracted_data
                    st.success("Data extracted! Refresh the dashboard to view.")