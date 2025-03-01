from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from modules.embeddings import get_retriever
from config import LLM_MODEL, LLM_TEMPERATURE, RETRIEVER_K, RETRIEVER_SCORE_THRESHOLD
import json

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

def create_qa_chain(vectorstore):
    """Create the QA chain with LLM model"""
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    
    # Create an improved prompt that asks for source references and confidence levels
    custom_prompt_template = """
    Please answer the following question about the financial document with high accuracy.
    
    If you're extracting specific financial data (numbers, percentages, dates), please:
    1. Include exact page references where the information was found
    2. Quote the original text containing the data
    3. Include a confidence score (1-5) for each data point, where:
       - 5: Directly quoted from document with clear context
       - 4: Clearly implied by document text
       - 3: Reasonably inferred from context
       - 2: Educated guess based on partial information
       - 1: Uncertain, needs verification
    4. If the data appears in multiple places, include ALL references to ensure accuracy
    5. If you cannot find specific information, clearly state that instead of guessing
    
    Context: {context}
    Question: {question}
    
    Answer with proper formatting, citations, and confidence scores:
    """
    
    # Create a proper PromptTemplate object
    prompt = PromptTemplate(
        template=custom_prompt_template,
        input_variables=["context", "question"]
    )
    
    # Get retriever
    retriever = get_retriever(
        vectorstore, 
        k=RETRIEVER_K, 
        score_threshold=RETRIEVER_SCORE_THRESHOLD
    )
    
    # Use custom retrieval QA with improved retrieval settings
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={
            "prompt": prompt
        }
    )
    return qa_chain

def verify_financial_data(qa_chain, data_point, expected_value=None):
    """Double-check a specific financial data point"""
    verification_prompt = f"""
    I need to verify the accuracy of this financial data point: "{data_point}"
    
    Please:
    1. Find ALL occurrences of this data in the document
    2. Provide exact page numbers and direct quotes for each occurrence
    3. Check if there are any inconsistencies in how this data is reported
    4. If an expected value of {expected_value if expected_value else 'None'} was provided, confirm if this matches what's in the document
    5. Explain any context that might affect the interpretation of this data
    
    This is for critical verification, so precision is essential.
    """
    # Use invoke() and extract text from response
    response_obj = qa_chain.invoke(verification_prompt)
    return extract_text_from_response(response_obj)

def cross_check_data(qa_chain, data_point):
    """Ask the same question with slight variations for verification"""
    results = []
    variations = [
        f"What is the exact value of {data_point}?",
        f"Find the {data_point} in the financial statements",
        f"Extract {data_point} with page references"
    ]
    
    for query in variations:
        # Use invoke() and extract text from response
        response_obj = qa_chain.invoke(query)
        results.append(extract_text_from_response(response_obj))
    
    return results

def generate_financial_insights(qa_chain, extracted_data):
    """Generate intelligent financial insights based on the data"""
    # Create a summary of the extracted data
    data_summary = json.dumps(extracted_data, indent=2)
    
    insights_prompt = f"""
    Based on the following financial data extracted from the document, generate 5 key insights:
    
    {data_summary}
    
    For each insight:
    1. Provide a clear, concise statement of the insight
    2. Explain why this is significant for investors or analysts
    3. Add relevant context from the industry or market if applicable
    4. Give a confidence score (1-5) for each insight
    
    Format each insight as:
    
    ## Insight [number]: [brief title]
    [Detailed explanation]
    
    Significance: [Why this matters]
    
    Confidence: [score]/5
    """
    
    # Use invoke() and return the result
    response_obj = qa_chain.invoke(insights_prompt)
    return response_obj