import streamlit as st
from modules.visualization import create_financial_dashboard
from modules.qa_chain import create_qa_chain, generate_financial_insights
from modules.data_extraction import extract_standardized_financials

def extract_text_from_response(response_obj):
    """Helper function to extract text from response object"""
    if isinstance(response_obj, dict):
        if 'result' in response_obj:
            return response_obj['result']
        else:
            return response_obj.get('answer',
                       response_obj.get('output_text',
                       response_obj.get('output',
                       str(response_obj))))
    else:
        return str(response_obj)

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
                qa_chain = create_qa_chain(current_doc_data['vectorstore'])
                
                # Updated to use invoke() and handle the response properly
                insights_obj = generate_financial_insights(qa_chain, st.session_state.extracted_data)
                insights = extract_text_from_response(insights_obj)
                
                st.markdown(insights)
    else:
        st.info("Extract data in the Data Extraction tab to populate the dashboard.")
        
        if st.button("Extract Data for Dashboard"):
            with st.spinner("Extracting standardized financial data..."):
                current_doc_data = st.session_state.processed_docs[st.session_state.current_doc]
                qa_chain = create_qa_chain(current_doc_data['vectorstore'])
                extracted_data = extract_standardized_financials(qa_chain, current_doc_data['info']['type'])
                
                # Store for future use
                if st.session_state.current_doc not in st.session_state.extracted_data:
                    st.session_state.extracted_data[st.session_state.current_doc] = extracted_data
                    st.success("Data extracted! Refresh the dashboard to view.")