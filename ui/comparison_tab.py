import streamlit as st
import pandas as pd
import numpy as np
import re
from modules.data_extraction import compare_documents, extract_numeric_value, extract_text_from_response
from modules.prediction import predict_future_performance
from modules.visualization import plot_metric_comparison, plot_financial_projection

def render_comparison_tab():
    """Render the comparison and prediction tab"""
    st.header("Comparison & Prediction")
    
    # Document comparison (only available with multiple documents)
    if len(st.session_state.processed_docs) > 1:
        render_document_comparison()
    else:
        st.info("Upload multiple documents to enable document comparison.")
    
    # Financial projections
    render_financial_projections()

def render_document_comparison():
    """Render the document comparison section"""
    st.subheader("Multi-Document Comparison")
    st.markdown("Compare specific financial metrics across multiple documents.")
    
    # Select documents for comparison
    doc_options = list(st.session_state.processed_docs.keys())
    selected_docs = st.multiselect("Select documents to compare:", doc_options, default=[st.session_state.current_doc])
    
    # Select metric for comparison
    comparison_metric = st.selectbox("Select metric to compare:", [
        "Total Revenue", 
        "Net Income", 
        "Operating Income", 
        "EPS", 
        "R&D Expenses",
        "Cash and Cash Equivalents",
        "Total Assets",
        "Total Liabilities"
    ])
    
    if st.button("Compare Documents") and selected_docs:
        with st.spinner("Comparing documents..."):
            # Get subset of documents to compare
            docs_to_compare = {doc: st.session_state.processed_docs[doc] for doc in selected_docs}
            
            # Run comparison
            comparison_results = compare_documents(docs_to_compare, comparison_metric)
            
            # Display results
            st.write("### Comparison Results")
            
            # Convert to DataFrame for display
            comparison_rows = []
            for doc_name, result in comparison_results.items():
                comparison_rows.append({
                    'Document': doc_name,
                    'Company': result['company'] or docs_to_compare[doc_name]['info']['company'] or 'Unknown',
                    'Year': result['year'] or docs_to_compare[doc_name]['info']['year'] or 'Unknown',
                    'Value': result['value'],
                    'Confidence': result['confidence']
                })
            
            comparison_df = pd.DataFrame(comparison_rows)
            st.dataframe(comparison_df)
            
            # Create visualization
            st.write("### Visual Comparison")
            
            # Try to extract numeric values for plotting
            try:
                # Add numeric column for plotting
                comparison_df['Numeric Value'] = comparison_df['Value'].apply(
                    lambda x: extract_numeric_value(x) or np.nan
                )
                
                # Create visualization if we have numeric data
                if not comparison_df['Numeric Value'].isna().all():
                    plot_metric_comparison(comparison_df, comparison_metric)
                else:
                    st.warning("Could not extract numeric values for visualization.")
            except Exception as e:
                st.warning(f"Could not create visualization: {str(e)}")

def render_financial_projections():
    """Render the financial projections section"""
    st.subheader("Financial Projections")
    st.markdown("Project future financial performance based on historical data.")
    
    # Only show if we have extracted data for the current document
    if st.session_state.current_doc in st.session_state.extracted_data:
        # Select metric for prediction
        prediction_metric = st.selectbox("Select metric to project:", [
            "Total Revenue", 
            "Net Income", 
            "Operating Income", 
            "EPS"
        ])
        
        projection_years = st.slider("Years to project:", min_value=1, max_value=5, value=3)
        
        if st.button("Generate Projection"):
            with st.spinner("Generating financial projection..."):
                # Get the extracted data
                extracted_data = {st.session_state.current_doc: st.session_state.extracted_data[st.session_state.current_doc]}
                
                # Run prediction
                prediction_result = predict_future_performance(extracted_data, prediction_metric, projection_years)
                
                if prediction_result and all(x is not None for x in prediction_result):
                    all_years, all_values, predictions, r_squared = prediction_result
                    
                    # Display results
                    st.write("### Projected Values")
                    
                    # Format prediction results
                    prediction_rows = []
                    
                    # Check if predictions is not None
                    if predictions is not None:
                        for year, value in predictions.items():
                            prediction_rows.append({
                                'Year': year,
                                'Projected Value': f"${value:,.2f}",
                                'Confidence': f"Model R² = {r_squared:.2f}"
                            })
                        
                        prediction_df = pd.DataFrame(prediction_rows)
                        st.dataframe(prediction_df)
                        
                        # Create visualization
                        st.write("### Projection Visualization")
                        plot_financial_projection(prediction_result)
                        
                        # Show model quality
                        if r_squared < 0.7:
                            st.warning(f"Caution: The prediction model has low confidence (R² = {r_squared:.2f}). Results may not be reliable.")
                        elif r_squared > 0.9:
                            st.success(f"High confidence prediction model (R² = {r_squared:.2f})")
                        else:
                            st.info(f"Moderate confidence prediction model (R² = {r_squared:.2f})")
                        
                        # Add prediction explanation
                        st.markdown("""
                        **Prediction Methodology:**
                        - Linear trend projection based on historical data
                        - Shaded area represents prediction uncertainty
                        - R² value indicates how well the model fits historical data (higher is better)
                        
                        **Note:** These projections are simplified and should be used as a starting point for further analysis, not as definitive forecasts.
                        """)
                    else:
                        st.warning("Could not generate predictions from the available data.")
                else:
                    st.warning("Insufficient historical data for projection. Need at least 2 data points.")
    else:
        st.info("First extract standardized data in the Data Extraction tab.")
        
        if st.button("Extract Data Now"):
            with st.spinner("Extracting standardized financial data..."):
                from modules.qa_chain import create_qa_chain
                from modules.data_extraction import extract_standardized_financials
                
                current_doc_data = st.session_state.processed_docs[st.session_state.current_doc]
                qa_chain = create_qa_chain(current_doc_data['vectorstore'])
                extracted_data = extract_standardized_financials(qa_chain, current_doc_data['info']['type'])
                
                # Store for future use
                if st.session_state.current_doc not in st.session_state.extracted_data:
                    st.session_state.extracted_data[st.session_state.current_doc] = extracted_data
                    st.success("Data extracted! You can now generate projections.")