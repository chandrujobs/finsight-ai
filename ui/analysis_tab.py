import streamlit as st
import re
from modules.qa_chain import create_qa_chain, generate_financial_insights
from modules.data_extraction import extract_standardized_financials
from ui.components import display_confidence, display_source_page

def render_analysis_tab():
    """Render the financial analysis tab"""
    st.header("Financial Analysis Q&A")
    current_doc_data = st.session_state.processed_docs[st.session_state.current_doc]
    
    st.markdown(f"Ask questions about {st.session_state.current_doc} and get AI-powered insights.")
    
    # Provide some example questions
    st.markdown("### Example questions:")
    example_questions = [
        "What were the total revenues in the most recent fiscal year?",
        "How did advertising revenue change compared to the previous year?",
        "What are the key risks mentioned in the report?",
        "Summarize the company's financial performance",
        "What is the company's R&D spending?"
    ]
    
    for q in example_questions:
        if st.button(q, key=f"q_{q}"):
            user_question = q
            st.session_state.user_question = q
            break
    
    # Manual question input
    if 'user_question' in st.session_state:
        user_question = st.text_input("Or type your own question:", value=st.session_state.user_question)
    else:
        user_question = st.text_input("Or type your own question:")
    
    if user_question:
        qa_chain = create_qa_chain(current_doc_data['vectorstore'])
        with st.spinner("Analyzing with Gemini 1.5 Flash..."):
            # Using invoke() and handling the response properly
            response_obj = qa_chain.invoke(user_question)
            
            # Extract the text response from the dictionary returned by invoke()
            if isinstance(response_obj, dict):
                if 'result' in response_obj:
                    response_text = response_obj['result']
                else:
                    # Try common keys or convert the whole response to string
                    response_text = response_obj.get('answer', 
                                  response_obj.get('output_text',
                                  response_obj.get('output',
                                  str(response_obj))))
            else:
                response_text = str(response_obj)
            
            st.write("### Answer")
            st.write(response_text)
            
            # Extract and display confidence scores if present
            confidence_scores = re.findall(r"confidence score[:\s]*(\d+)", response_text, re.IGNORECASE)
            if confidence_scores:
                avg_confidence = sum(int(score) for score in confidence_scores) / len(confidence_scores)
                st.write("### Overall Confidence")
                display_confidence(avg_confidence)
            
            # Add source verification
            mentioned_pages = re.findall(r"Page (\d+)", response_text)
            if mentioned_pages:
                display_source_page(current_doc_data['path'], mentioned_pages)
    
    # Financial insights button
    st.subheader("Automated Financial Insights")
    if st.button("Generate Financial Insights"):
        # Check if we have extracted data
        if st.session_state.current_doc in st.session_state.extracted_data:
            extracted_data = st.session_state.extracted_data[st.session_state.current_doc]
        else:
            # Extract standardized financial data first
            with st.spinner("Extracting key financial data..."):
                qa_chain = create_qa_chain(current_doc_data['vectorstore'])
                extracted_data = extract_standardized_financials(qa_chain, current_doc_data['info']['type'])
                
                # Store for future use
                if st.session_state.current_doc not in st.session_state.extracted_data:
                    st.session_state.extracted_data[st.session_state.current_doc] = extracted_data
        
        # Generate insights
        with st.spinner("Generating intelligent financial insights..."):
            qa_chain = create_qa_chain(current_doc_data['vectorstore'])
            
            # Updated to use invoke() and handle the response properly
            insights_obj = generate_financial_insights(qa_chain, extracted_data)
            
            # Extract the text response
            if isinstance(insights_obj, dict):
                if 'result' in insights_obj:
                    insights_text = insights_obj['result']
                else:
                    insights_text = insights_obj.get('answer',
                                   insights_obj.get('output_text',
                                   insights_obj.get('output',
                                   str(insights_obj))))
            else:
                insights_text = str(insights_obj)
            
            st.subheader("Key Financial Insights")
            st.markdown(insights_text)