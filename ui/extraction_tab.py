import streamlit as st
import re
import pandas as pd
from modules.qa_chain import create_qa_chain, cross_check_data
from modules.data_extraction import extract_standardized_financials, extract_table_data
from ui.components import display_confidence, display_source_page
from config import EXTRACTION_TEMPLATES

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

def render_extraction_tab():
    """Render the data extraction tab"""
    st.header("Data Extraction")
    current_doc_data = st.session_state.processed_docs[st.session_state.current_doc]
    
    st.markdown("Extract and analyze financial data from the report.")
    
    # Add extraction templates
    selected_template = st.selectbox("Choose a template:", options=list(EXTRACTION_TEMPLATES.keys()))
    template_query = EXTRACTION_TEMPLATES[selected_template]
    
    # Data type selection
    data_type = st.selectbox(
        "What type of data would you like to extract?",
        ["Revenue", "Expenses", "Profit Margins", "Cash Flow", "Balance Sheet Items", "Key Metrics", "Custom"]
    )
    
    if data_type == "Custom":
        data_type = st.text_input("Specify what data to extract:")
    
    # Option for high accuracy mode
    high_accuracy = st.checkbox("Enable High Accuracy Mode (slower but more reliable)", value=True)
    
    if st.button("Extract Data", key="extract_data_button"):
        qa_chain = create_qa_chain(current_doc_data['vectorstore'])
        with st.spinner("Extracting data with Gemini 1.5 Flash..."):
            extraction_prompt = f"""
            Extract all {data_type} information from the financial report with maximum accuracy.
            
            For each data point, you MUST include:
            1. The specific value with proper unit (e.g., $1,234.56 million)
            2. The exact page number reference where this information appears
            3. A direct quote of the relevant text from the document
            4. The reporting period (year, quarter, etc.)
            5. A confidence score (1-5) for each extraction
            6. Any contextual information needed to understand the data
            
            Format your response as a structured table with these columns.
            If the same data appears in multiple places in the document with different values, flag this discrepancy.
            
            DO NOT make up or estimate any values. If the exact data isn't available, state that clearly.
            """
            
            # If template was selected, use that instead
            if selected_template:
                extraction_prompt = template_query
            
            # Updated to use invoke() and handle the response properly
            response_obj = qa_chain.invoke(extraction_prompt)
            response_text = extract_text_from_response(response_obj)
            
            st.write("### Extracted Data")
            st.write(response_text)
            
            # Add source verification
            mentioned_pages = re.findall(r"Page (\d+)", response_text)
            if mentioned_pages:
                display_source_page(current_doc_data['path'], mentioned_pages)
    
    # Standardized extraction
    st.subheader("Extract Standardized Financial Data")
    st.markdown("Extract key financial metrics in a standardized format for analysis and comparison.")
    
    if st.button("Extract Standard Metrics"):
        with st.spinner("Extracting standardized financial data..."):
            qa_chain = create_qa_chain(current_doc_data['vectorstore'])
            extracted_data = extract_standardized_financials(qa_chain, current_doc_data['info']['type'])
            
            # Store for future use
            if st.session_state.current_doc not in st.session_state.extracted_data:
                st.session_state.extracted_data[st.session_state.current_doc] = extracted_data
            
            # Display as a table
            st.write("### Standardized Financial Data")
            
            # Convert to DataFrame for display
            data_rows = []
            for metric, details in extracted_data.items():
                data_rows.append({
                    'Metric': metric,
                    'Value': details['value'],
                    'Period': details['period'],
                    'Page': details['page'],
                    'Confidence': details['confidence']
                })
            
            df = pd.DataFrame(data_rows)
            st.dataframe(df)
            
            # Add download button for the data
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{current_doc_data['info']['company']}_{current_doc_data['info']['year']}_financial_data.csv",
                mime="text/csv"
            )
    
    # Table extraction
    st.subheader("Extract Financial Tables")
    st.markdown("Extract complete tables from financial statements.")
    
    table_type = st.selectbox(
        "Select table to extract:",
        ["Income Statement", "Balance Sheet", "Cash Flow Statement", "Segment Information", "Key Ratios"]
    )
    
    if st.button("Extract Table"):
        with st.spinner(f"Extracting {table_type}..."):
            qa_chain = create_qa_chain(current_doc_data['vectorstore'])
            # Updated to use invoke() and handle the response
            table_data_obj = extract_table_data(qa_chain, table_type)
            table_data = extract_text_from_response(table_data_obj)
            
            st.write(f"### Extracted {table_type}")
            st.write(table_data)
            
            # Add source verification
            mentioned_pages = re.findall(r"Page (\d+)", table_data)
            if mentioned_pages:
                display_source_page(current_doc_data['path'], mentioned_pages)