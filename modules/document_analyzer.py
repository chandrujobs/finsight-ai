import re
import os
import fitz  # PyMuPDF
import streamlit as st

def detect_document_type(file_path):
    """Detect document type (annual report, 10-K, etc.) and year"""
    doc_info = {
        'type': 'Unknown',
        'year': None,
        'company': None
    }
    
    try:
        # Extract filename for basic info
        filename = os.path.basename(file_path).lower()
        
        # Look for year in filename
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            doc_info['year'] = year_match.group(0)
        
        # Look for document type hints in filename
        if 'annual' in filename or 'report' in filename:
            doc_info['type'] = 'Annual Report'
        elif '10k' in filename or '10-k' in filename:
            doc_info['type'] = 'Form 10-K'
        elif 'q' in filename and ('report' in filename or 'results' in filename):
            doc_info['type'] = 'Quarterly Report'
        
        # Get more detailed info from document content
        with fitz.open(file_path) as doc:
            # Check first few pages for more info
            text = ""
            for i in range(min(5, len(doc))):
                text += doc[i].get_text()
            
            # Look for company name
            company_patterns = [
                r'(?i)(.*?)\s+(?:Inc\.|Corporation|Corp\.|LLC|Company|Co\.|Ltd\.)',
                r'(?i)(.*?)\s+(?:Annual Report)',
                r'(?i)About\s+(.*?)[\.\n]'
            ]
            
            for pattern in company_patterns:
                company_match = re.search(pattern, text)
                if company_match:
                    doc_info['company'] = company_match.group(1).strip()
                    break
            
            # Look for document type
            if 'Form 10-K' in text:
                doc_info['type'] = 'Form 10-K'
            elif 'Annual Report' in text:
                doc_info['type'] = 'Annual Report'
            
            # Look for year if not found in filename
            if not doc_info['year']:
                year_patterns = [
                    r'(?i)(?:fiscal|year)\s+(\d{4})',
                    r'(?i)(?:ended|ending)\s+\w+\s+\d{1,2},?\s+(\d{4})',
                    r'(\d{4})\s+(?:Annual Report|Form 10-K)'
                ]
                
                for pattern in year_patterns:
                    year_match = re.search(pattern, text)
                    if year_match:
                        doc_info['year'] = year_match.group(1)
                        break
            
    except Exception as e:
        st.error(f"Error detecting document type: {str(e)}")
    
    return doc_info

def analyze_financial_charts(pdf_path):
    """Extract data from charts and graphs in the PDF using image analysis"""
    import tempfile
    
    chart_data = []
    try:
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                # Extract images
                image_list = page.get_images(full=True)
                
                # Process each image
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Save to a temporary file for analysis
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        temp_file.write(image_bytes)
                        temp_path = temp_file.name
                    
                    # For now, just log that we found an image
                    # In a production app, you would use OCR or image analysis to extract data
                    chart_data.append({
                        'page': page_num + 1,
                        'image_index': img_index,
                        'size': base_image["width"] * base_image["height"],
                        'format': base_image["ext"],
                        'temp_path': temp_path
                    })
    except Exception as e:
        st.error(f"Error analyzing charts: {str(e)}")
    
    return chart_data

def detect_tables(pdf_path):
    """Detect tables in a PDF document"""
    tables = []
    try:
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # Simple heuristic to detect tables - look for column headers
                # and rows of numbers
                if (re.search(r'[\d,.]+\s+[\d,.]+\s+[\d,.]+', text) and 
                    re.search(r'(?i)(year|quarter|month|total|balance|income|revenue|expense)', text)):
                    
                    # Extract a sample of the table text
                    table_sample = re.findall(r'[\d,.]+\s+[\d,.]+\s+[\d,.]+', text)
                    
                    tables.append({
                        'page': page_num + 1,
                        'sample': table_sample[:3] if table_sample else [], # First 3 rows
                        'type': 'financial_table' if re.search(r'(?i)(balance|income|revenue|expense)', text) else 'table'
                    })
    except Exception as e:
        st.error(f"Error detecting tables: {str(e)}")
    
    return tables