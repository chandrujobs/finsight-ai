import re
from config import STANDARD_METRICS

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

def extract_standardized_financials(qa_chain, doc_type):
    """Extract standardized financial data based on document type"""
    # Get the list of metrics to extract based on document type
    metrics_to_extract = STANDARD_METRICS.get(doc_type, STANDARD_METRICS['Annual Report'])
    
    extracted_data = {}
    for metric in metrics_to_extract:
        prompt = f"""
        Extract the exact value of '{metric}' from the document.
        Return ONLY:
        1. The exact value with proper units (e.g., "$123.45 million")
        2. The page number reference
        3. The reporting period (e.g., "FY 2022", "Q3 2022")
        4. A confidence score (1-5)
        
        Format your response as:
        Value: [exact value]
        Page: [page number]
        Period: [reporting period]
        Confidence: [1-5]
        """
        
        # Updated to use invoke() and handle the response properly
        response_obj = qa_chain.invoke(prompt)
        response_text = extract_text_from_response(response_obj)
        
        # Parse the response to extract the value
        value_match = re.search(r'Value:\s*(.*)', response_text)
        page_match = re.search(r'Page:\s*(.*)', response_text)
        period_match = re.search(r'Period:\s*(.*)', response_text)
        confidence_match = re.search(r'Confidence:\s*(.*)', response_text)
        
        extracted_data[metric] = {
            'value': value_match.group(1).strip() if value_match else "Not found",
            'page': page_match.group(1).strip() if page_match else "Not found",
            'period': period_match.group(1).strip() if period_match else "Not found",
            'confidence': confidence_match.group(1).strip() if confidence_match else "0"
        }
    
    return extracted_data

def compare_documents(documents, metric_name):
    """Compare a specific metric across multiple documents"""
    from modules.qa_chain import create_qa_chain
    
    comparison_results = {}
    
    for doc_name, doc_data in documents.items():
        qa_chain = create_qa_chain(doc_data['vectorstore'])
        
        prompt = f"""
        Find the value of '{metric_name}' in this document.
        
        Return ONLY:
        1. The exact value with proper units (e.g., "$123.45 million")
        2. The page number reference
        3. The year or period this value is for
        4. A confidence score (1-5)
        
        Format as:
        Value: [exact value]
        Page: [page number]
        Year: [year]
        Confidence: [1-5]
        """
        
        # Updated to use invoke() and handle the response properly
        response_obj = qa_chain.invoke(prompt)
        response_text = extract_text_from_response(response_obj)
        
        # Parse the response
        value_match = re.search(r'Value:\s*(.*)', response_text)
        year_match = re.search(r'Year:\s*(.*)', response_text)
        confidence_match = re.search(r'Confidence:\s*(.*)', response_text)
        
        comparison_results[doc_name] = {
            'value': value_match.group(1).strip() if value_match else "Not found",
            'year': year_match.group(1).strip() if year_match else doc_data['info']['year'],
            'confidence': confidence_match.group(1).strip() if confidence_match else "0",
            'company': doc_data['info']['company']
        }
    
    return comparison_results

def extract_table_data(qa_chain, table_type):
    """Extract structured tabular data from financial statements"""
    prompt = f"""
    Extract the complete {table_type} table from the document.
    
    Please:
    1. Identify the page where the {table_type} table appears
    2. Extract all rows and columns from the table
    3. Include column headers exactly as they appear
    4. Maintain numerical precision (do not round values)
    5. Keep all footnote references
    6. Include the reporting period (year/quarter) for the table
    
    Format your response as a clean, structured table with proper alignment.
    Also include the page reference where this table was found.
    """
    
    # Updated to use invoke() and handle the response properly
    response_obj = qa_chain.invoke(prompt)
    return extract_text_from_response(response_obj)

def extract_numeric_value(value_str):
    """Extract and normalize numeric values from text"""
    try:
        # Extract numeric value using regex
        num_match = re.search(r'[\$\€\£]?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:billion|million|thousand|B|M|K)?', value_str)
        if num_match:
            raw_value = num_match.group(1).replace(',', '')
            value = float(raw_value)
            
            # Scale based on units
            if 'billion' in value_str.lower() or 'B' in value_str:
                value *= 1_000_000_000
            elif 'million' in value_str.lower() or 'M' in value_str:
                value *= 1_000_000
            elif 'thousand' in value_str.lower() or 'K' in value_str:
                value *= 1_000
            
            return value
    except:
        pass
    
    return None