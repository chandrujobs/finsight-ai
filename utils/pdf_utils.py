import re
import base64
import streamlit as st
import fitz  # PyMuPDF

def display_pdf_page(pdf_path, page_num):
    """Display a specific page from a PDF file"""
    try:
        # Open the PDF file
        with fitz.open(pdf_path) as doc:
            if 0 <= page_num-1 < len(doc):
                page = doc[page_num-1]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("png")
                encoded = base64.b64encode(img_bytes).decode()
                return f'<img src="data:image/png;base64,{encoded}" style="width:100%"/>'
            else:
                return "Page number out of range"
    except Exception as e:
        return f"Error displaying PDF: {str(e)}"

def extract_tables_from_pdf(pdf_path, page_numbers):
    """Extract tables from specific pages of a PDF"""
    tables = []
    try:
        # Open the PDF file
        with fitz.open(pdf_path) as doc:
            for page_num in page_numbers:
                if 0 <= page_num < len(doc):
                    page = doc[page_num]
                    tables.append({
                        'page': page_num + 1,
                        'text': page.get_text("text"),
                        'tables': page.get_text("blocks")  # This gets text blocks which often contain tables
                    })
    except Exception as e:
        st.error(f"Error extracting tables: {str(e)}")
    return tables

def create_document_index(pdf_path):
    """Create a table of contents for faster navigation"""
    toc = []
    try:
        with fitz.open(pdf_path) as doc:
            # First try to get the document's built-in TOC
            built_in_toc = doc.get_toc()
            if built_in_toc:
                for item in built_in_toc:
                    level, title, page = item
                    toc.append({
                        "page": page,
                        "title": title,
                        "level": level
                    })
            
            # If no built-in TOC or it's too short, create our own
            if len(toc) < 5:
                for i, page in enumerate(doc):
                    text = page.get_text()
                    
                    # Look for financial section headers
                    if re.search(r'(?i)(consolidated|statement|balance sheet|income|cash flow|notes to|financial)', text):
                        # Try to extract a meaningful title
                        lines = text.split('\n')
                        title = next((line for line in lines if re.search(r'(?i)(consolidated|statement|balance sheet|income|cash flow)', line)), f"Financial content on page {i+1}")
                        toc.append({
                            "page": i+1,
                            "title": title.strip(),
                            "level": 1
                        })
    except Exception as e:
        st.error(f"Error creating document index: {str(e)}")
    return toc

def count_pages(pdf_path):
    """Count the number of pages in a PDF"""
    try:
        with fitz.open(pdf_path) as doc:
            return len(doc)
    except Exception as e:
        st.error(f"Error counting pages: {str(e)}")
        return 0

def extract_text_from_page_range(pdf_path, start_page, end_page):
    """Extract text from a range of pages"""
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for i in range(start_page-1, min(end_page, len(doc))):
                text += doc[i].get_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")
        return ""

def extract_images_from_page(pdf_path, page_num):
    """Extract images from a specific page"""
    images = []
    try:
        with fitz.open(pdf_path) as doc:
            if 0 <= page_num-1 < len(doc):
                page = doc[page_num-1]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to base64 for display
                    encoded = base64.b64encode(image_bytes).decode()
                    
                    images.append({
                        'index': img_index,
                        'width': base_image["width"],
                        'height': base_image["height"],
                        'format': base_image["ext"],
                        'encoded': encoded
                    })
    except Exception as e:
        st.error(f"Error extracting images: {str(e)}")
    
    return images