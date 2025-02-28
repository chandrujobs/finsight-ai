import os
import re
import glob
import streamlit as st
from datetime import datetime
import fitz  # PyMuPDF
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from modules.embeddings import create_vectorstore
from modules.document_analyzer import detect_document_type
from utils.pdf_utils import create_document_index

def process_document_folder(folder_path):
    """Process all PDF documents in a folder"""
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        st.error(f"Invalid folder path: {folder_path}")
        return None
    
    processed_docs = {}
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    
    if not pdf_files:
        st.warning(f"No PDF files found in {folder_path}")
        return None
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, pdf_file in enumerate(pdf_files):
        file_name = os.path.basename(pdf_file)
        status_text.text(f"Processing {i+1}/{len(pdf_files)}: {file_name}")
        
        # Process each document
        doc_result = process_single_document(pdf_file)
        if doc_result:
            vectorstore, file_info, num_pages, doc_index = doc_result
            
            # Add to the processed documents dictionary
            processed_docs[file_name] = {
                'path': pdf_file,
                'vectorstore': vectorstore,
                'info': file_info,
                'pages': num_pages,
                'index': doc_index
            }
        
        # Update progress
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.text(f"Processed {len(processed_docs)} documents successfully")
    progress_bar.empty()
    
    return processed_docs

def process_single_document(file_path):
    """Process a single PDF document"""
    if not os.path.exists(file_path):
        st.error(f"File not found: {file_path}")
        return None
    
    with st.spinner(f"Processing document: {os.path.basename(file_path)}"):
        # Get document type and info
        doc_info = detect_document_type(file_path)
        
        # Load the PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Add enhanced metadata to each document
        for doc in documents:
            if 'source' in doc.metadata and 'page' in doc.metadata:
                doc.metadata['page_display'] = f"Page {doc.metadata['page'] + 1}"
                doc.metadata['doc_type'] = doc_info['type']
                doc.metadata['doc_year'] = doc_info['year']
                doc.metadata['company'] = doc_info['company']
                
                # Extract section headers for better context
                section_match = re.search(r'(?i)(PART\s+[IVX]+|Item\s+\d+[A-Za-z]*)', doc.page_content)
                if section_match:
                    doc.metadata['section'] = section_match.group(0)
                
                # Look for tables and financial data
                if re.search(r'(?i)(table|figure|chart|financial|statement|balance sheet|income statement|cash flow)', doc.page_content):
                    doc.metadata['content_type'] = 'financial_data'
        
        # Use smarter text splitting - customize for financial documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Smaller chunks for more precise retrieval
            chunk_overlap=200,  # Larger overlap to maintain context
            separators=["\n\n", "\n", ".", " ", ""],  # Prioritize splitting at paragraph boundaries
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create vector store with embeddings
        vectorstore = create_vectorstore(chunks)
        
        # Create document index for navigation
        doc_index = create_document_index(file_path)
        
        # Get number of pages
        with fitz.open(file_path) as doc:
            num_pages = len(doc)
        
        # Create file info dictionary
        file_info = {
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path) / (1024 * 1024),  # MB
            'type': doc_info['type'],
            'year': doc_info['year'],
            'company': doc_info['company'],
            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return vectorstore, file_info, num_pages, doc_index