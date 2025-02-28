import streamlit as st
import os
import pandas as pd
import glob
from modules.document_processor import process_single_document, process_document_folder
from modules.document_analyzer import detect_document_type
from config import DEFAULT_SINGLE_DOC_PATH, DEFAULT_FOLDER_PATH

def render_document_management():
    """Render the document management tab"""
    st.header("Document Management")
    
    # Option to select between single file and folder
    input_mode = st.radio("Select input mode:", ["Single File", "Folder of Documents"])
    
    if input_mode == "Single File":
        render_single_file_mode()
    else:
        render_folder_mode()
    
    # Document selection (only show if we have processed documents)
    if st.session_state.processed_docs:
        st.subheader("Select Document to Analyze")
        doc_options = list(st.session_state.processed_docs.keys())
        selected_doc = st.selectbox(
            "Choose a document:", 
            doc_options, 
            index=doc_options.index(st.session_state.current_doc) if st.session_state.current_doc in doc_options else 0
        )
        
        if selected_doc != st.session_state.current_doc:
            st.session_state.current_doc = selected_doc
            st.success(f"Switched to document: {selected_doc}")

def render_single_file_mode():
    """Render single file mode UI"""
    # Allow the user to change the path if needed
    file_path = st.text_input("PDF File Path", value=DEFAULT_SINGLE_DOC_PATH)
    
    # Display file information
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        st.success(f"File found: {file_name} ({file_size:.2f} MB)")
        
        # Get document info
        doc_info = detect_document_type(file_path)
        
        # Display document info
        if doc_info['company']:
            st.info(f"Company: {doc_info['company']}")
        if doc_info['type']:
            st.info(f"Document Type: {doc_info['type']}")
        if doc_info['year']:
            st.info(f"Year: {doc_info['year']}")
        
        # Process the document button
        if st.button("Process Document"):
            result = process_single_document(file_path)
            
            if result:
                vectorstore, file_info, num_pages, doc_index = result
                
                # Store in session state
                st.session_state.processed_docs = {
                    file_name: {
                        'path': file_path,
                        'vectorstore': vectorstore,
                        'info': file_info,
                        'pages': num_pages,
                        'index': doc_index
                    }
                }
                
                st.session_state.current_doc = file_name
                
                st.success(f"Successfully processed: {file_name}")
                st.info(f"Document contains {num_pages} pages")
                
                # Display table of contents
                if doc_index:
                    st.subheader("Document Table of Contents")
                    toc_df = pd.DataFrame(doc_index)
                    st.dataframe(toc_df)
    else:
        st.error(f"File not found: {file_path}")

def render_folder_mode():
    """Render folder mode UI"""
    # Allow the user to input folder path
    folder_path = st.text_input("PDF Folder Path", value=DEFAULT_FOLDER_PATH)
    
    # Display folder information
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        st.success(f"Folder found. Contains {len(pdf_files)} PDF files.")
        
        # List available PDFs
        if pdf_files:
            st.subheader("Available PDF Files")
            for pdf in pdf_files:
                file_name = os.path.basename(pdf)
                file_size = os.path.getsize(pdf) / (1024 * 1024)  # Convert to MB
                st.write(f"- {file_name} ({file_size:.2f} MB)")
        
        # Process all documents button
        if st.button("Process All Documents"):
            processed_docs = process_document_folder(folder_path)
            
            if processed_docs:
                st.session_state.processed_docs = processed_docs
                st.session_state.current_doc = list(processed_docs.keys())[0]  # Set first doc as current
                
                st.success(f"Successfully processed {len(processed_docs)} documents")
                
                # Show document summary
                st.subheader("Processed Documents Summary")
                
                summary_data = []
                for doc_name, doc_data in processed_docs.items():
                    summary_data.append({
                        'Document': doc_name,
                        'Company': doc_data['info']['company'] or 'Unknown',
                        'Type': doc_data['info']['type'] or 'Unknown',
                        'Year': doc_data['info']['year'] or 'Unknown',
                        'Pages': doc_data['pages']
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df)
    else:
        st.error(f"Folder not found: {folder_path}")