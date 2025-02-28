import os
import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import re
import base64
import fitz  # PyMuPDF

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Financial Document Analyzer", layout="wide")
st.title("Financial Document Analyzer")

# Sidebar for configuration
st.sidebar.header("Configuration")

# API Key handling - try .env first, then allow manual input
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if GOOGLE_API_KEY:
        # Set the API key in environment for the session
        os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
        st.sidebar.success("API Key set for this session!")
    else:
        st.warning("Please enter your Gemini API Key to continue.")

# Function to extract tables from PDF pages (for verification)
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

# Function to get PDF page for verification
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

# Function to create document index for faster navigation
def create_document_index(pdf_path):
    """Create a table of contents for faster navigation"""
    toc = []
    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                text = page.get_text()
                # Look for financial section headers
                if re.search(r'(?i)(consolidated|statement|balance sheet|income|cash flow|notes to|financial)', text):
                    # Try to extract a meaningful title
                    lines = text.split('\n')
                    title = next((line for line in lines if re.search(r'(?i)(consolidated|statement|balance sheet|income|cash flow)', line)), f"Financial content on page {i+1}")
                    toc.append({
                        "page": i+1,
                        "title": title.strip()
                    })
    except Exception as e:
        st.error(f"Error creating document index: {str(e)}")
    return toc

# Function to display confidence score visually
def display_confidence(score):
    """Display a visual confidence indicator"""
    try:
        score = int(score)
        if score >= 4:
            return st.success(f"High confidence: {score}/5")
        elif score >= 3:
            return st.info(f"Medium confidence: {score}/5")
        else:
            return st.warning(f"Low confidence: {score}/5")
    except:
        return st.error("Invalid confidence score")

# Only proceed if we have an API key
if GOOGLE_API_KEY:
    # Configure Gemini API
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Default to your specific file path
    default_path = r"C:\Users\admin\OneDrive\Desktop\AI Business Chatbot\Uploads\2022-alphabet-annual-report.pdf"
    
    # Allow the user to change the path if needed
    file_path = st.sidebar.text_input("PDF File Path", value=default_path)
    
    # Display file information
    if os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
        st.sidebar.success(f"File found: {file_name} ({file_size:.2f} MB)")
        
        # Add document statistics
        try:
            with fitz.open(file_path) as doc:
                st.sidebar.info(f"Document pages: {len(doc)}")
                if doc.metadata:
                    if 'title' in doc.metadata and doc.metadata['title']:
                        st.sidebar.info(f"Title: {doc.metadata['title']}")
        except:
            pass
    else:
        st.sidebar.error(f"File not found: {file_path}")

    # Function to process a single PDF file with improved chunking
    @st.cache_resource
    def process_document(file_path):
        if not os.path.exists(file_path):
            st.error(f"File not found: {file_path}")
            return None
        
        with st.spinner("Processing document with enhanced chunking..."):
            # Load the PDF
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # Add enhanced metadata to each document
            for doc in documents:
                if 'source' in doc.metadata and 'page' in doc.metadata:
                    doc.metadata['page_display'] = f"Page {doc.metadata['page'] + 1}"
                    
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
            
            # Create vector store with Gemini embeddings
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            vectorstore = FAISS.from_documents(chunks, embeddings)
            
            # Create document index for navigation
            doc_index = create_document_index(file_path)
            
            return vectorstore, os.path.basename(file_path), len(documents), doc_index

    # Function to create the QA chain with Gemini model that includes page references and confidence
    def create_qa_chain(vectorstore):
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
        
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
        
        # Use custom retrieval QA with improved retrieval settings
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_kwargs={
                    "k": 8,  # Retrieve more documents for better context
                    "score_threshold": 0.7  # Only include relevant chunks
                },
                metadata_keys=["page_display", "section", "content_type"]
            ),
            chain_type_kwargs={
                "prompt": prompt
            }
        )
        return qa_chain

    # Function to verify specific financial data
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
        return qa_chain.run(verification_prompt)

    # Function to cross-check data with multiple approaches
    def cross_check_data(qa_chain, data_point):
        """Ask the same question with slight variations for verification"""
        results = []
        variations = [
            f"What is the exact value of {data_point}?",
            f"Find the {data_point} in the financial statements",
            f"Extract {data_point} with page references"
        ]
        
        for query in variations:
            results.append(qa_chain.run(query))
        
        return results

    # Function to add extraction templates
    def add_extraction_templates(tab):
        """Add quick extraction templates for common financial data"""
        tab.subheader("Quick Extract Templates")
        template_options = {
            "Annual Revenue": "Extract the exact annual revenue figures for the past 3 years with page references",
            "Profit Margins": "Extract all profit margin percentages (gross, operating, net) with page references",
            "Balance Sheet Summary": "Extract key balance sheet items (assets, liabilities, equity) with page references",
            "Income Statement Summary": "Extract key income statement line items with page references",
            "Cash Flow Summary": "Extract key cash flow statement items with page references",
            "Segment Information": "Extract revenue and operating income by business segment with page references"
        }
        
        selected_template = tab.selectbox("Choose a template:", options=list(template_options.keys()))
        
        if tab.button("Use Template"):
            return template_options[selected_template]
        return None

    # Process the document
    if os.path.exists(file_path):
        result = process_document(file_path)

        if result:
            vectorstore, file_name, num_pages, doc_index = result
            st.sidebar.success(f"Successfully processed: {file_name}")
            
            # Display document index in sidebar
            with st.sidebar.expander("Document Index"):
                st.write("Key Financial Sections:")
                for item in doc_index:
                    if st.button(f"{item['title']} (p.{item['page']})", key=f"idx_{item['page']}"):
                        st.session_state.page_to_view = item['page']
            
            # Create tabs for different functionalities
            tab1, tab2, tab3, tab4 = st.tabs(["Financial Analysis", "Data Extraction", "Financial Metrics", "Data Verification"])
            
            with tab1:
                st.header("Financial Analysis Q&A")
                st.markdown(f"Ask questions about {file_name} and get AI-powered insights.")
                
                # Provide some example questions
                st.markdown("### Example questions:")
                example_questions = [
                    "What were Alphabet's total revenues in 2022?",
                    "How did Google's advertising revenue change compared to 2021?",
                    "What are the key risks mentioned in the report?",
                    "Summarize the company's financial performance",
                    "What is the company's R&D spending?"
                ]
                
                for q in example_questions:
                    if st.button(q, key=q):
                        user_question = q
                        st.session_state.user_question = q
                        break
                
                # Manual question input
                if 'user_question' in st.session_state:
                    user_question = st.text_input("Or type your own question:", value=st.session_state.user_question)
                else:
                    user_question = st.text_input("Or type your own question:")
                
                if user_question:
                    qa_chain = create_qa_chain(vectorstore)
                    with st.spinner("Analyzing with Gemini 1.5 Flash..."):
                        response = qa_chain.run(user_question)
                        st.write("### Answer")
                        st.write(response)
                        
                        # Extract and display confidence scores if present
                        confidence_scores = re.findall(r"confidence score[:\s]*(\d+)", response, re.IGNORECASE)
                        if confidence_scores:
                            avg_confidence = sum(int(score) for score in confidence_scores) / len(confidence_scores)
                            st.write("### Overall Confidence")
                            display_confidence(avg_confidence)
                        
                        # Add an information note about page references
                        st.info("Page numbers are included to help verify information in the original document.")
                        
                        # Add source verification
                        mentioned_pages = re.findall(r"Page (\d+)", response)
                        if mentioned_pages:
                            st.write("### Source Verification")
                            selected_page = st.selectbox("View source page:", options=[int(p) for p in set(mentioned_pages)])
                            if selected_page:
                                st.markdown(display_pdf_page(file_path, selected_page), unsafe_allow_html=True)
            
            with tab2:
                st.header("Extract Financial Data")
                st.markdown("Extract structured financial data from the annual report for visualization and analysis.")
                
                # Add extraction templates
                template_query = add_extraction_templates(tab2)
                if template_query:
                    st.session_state.extraction_query = template_query
                
                # Data type selection
                data_type = st.selectbox(
                    "What type of data would you like to extract?",
                    ["Revenue", "Expenses", "Profit Margins", "Cash Flow", "Balance Sheet Items", "Key Metrics", "Custom"]
                )
                
                if data_type == "Custom":
                    data_type = st.text_input("Specify what data to extract:")
                
                # Option for high accuracy mode
                high_accuracy = st.checkbox("Enable High Accuracy Mode (slower but more reliable)", value=True)
                
                if st.button("Extract Data"):
                    qa_chain = create_qa_chain(vectorstore)
                    with st.spinner("Extracting data with Gemini 1.5 Flash..."):
                        if 'extraction_query' in st.session_state:
                            extraction_prompt = st.session_state.extraction_query
                            # Clear the session state
                            del st.session_state.extraction_query
                        else:
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
                        
                        response = qa_chain.run(extraction_prompt)
                        
                        # For high accuracy mode, perform cross-checking
                        if high_accuracy and not 'extraction_query' in st.session_state:
                            with st.spinner("Cross-checking data for accuracy..."):
                                # Get multiple extractions for verification
                                verification_results = cross_check_data(qa_chain, data_type)
                                
                                # Check for consistency between extractions
                                st.write("### Data Consistency Check")
                                st.info("The system extracted the data multiple ways to verify consistency.")
                                
                                # Simple check for consistency - just look for matching numerical values
                                all_numbers = []
                                for result in verification_results:
                                    # Extract numbers from the result
                                    numbers = re.findall(r"\$?[\d,]+\.?\d*\s*(?:billion|million|thousand)?", result)
                                    all_numbers.extend(numbers)
                                
                                # Count frequency of each number
                                number_counts = {}
                                for num in all_numbers:
                                    number_counts[num] = number_counts.get(num, 0) + 1
                                
                                # Check for inconsistencies
                                inconsistencies = []
                                for num, count in number_counts.items():
                                    if count == 1:  # Only appears once across all extractions
                                        inconsistencies.append(num)
                                
                                if inconsistencies:
                                    st.warning(f"Potential inconsistencies detected in: {', '.join(inconsistencies)}")
                                    st.write("These values only appeared in one extraction method and should be verified.")
                                else:
                                    st.success("No major inconsistencies detected between multiple extraction methods.")
                        
                        st.write("### Extracted Data")
                        st.write(response)
                        st.info("Page numbers are included to help verify information in the original document.")
                        
                        # Add source verification
                        mentioned_pages = re.findall(r"Page (\d+)", response)
                        if mentioned_pages:
                            st.write("### Source Verification")
                            selected_page = st.selectbox("View source page:", options=[int(p) for p in set(mentioned_pages)], key="extract_page")
                            if selected_page:
                                st.markdown(display_pdf_page(file_path, selected_page), unsafe_allow_html=True)
                        
                        # Visualization section
                        st.write("### Would you like to visualize this data?")
                        if st.button("Generate Visualization"):
                            with st.spinner("Creating visualization..."):
                                viz_prompt = f"""
                                Based on the {data_type} data from the annual report, create a description of what 
                                a visualization should look like. Focus on showing trends over time or comparisons.
                                Describe the type of chart that would be most appropriate and what data should be included.
                                Also mention which page numbers contain the source data for the visualization.
                                """
                                viz_response = qa_chain.run(viz_prompt)
                                st.write("### Visualization Recommendation")
                                st.write(viz_response)
                                
                                # Sample visualization (would be replaced with actual data extraction and parsing)
                                st.write("### Sample Visualization")
                                st.write("(This is a placeholder - in a production app, this would be generated from the actual data)")
                                
                                if data_type == "Revenue":
                                    # Sample revenue data for Alphabet
                                    sample_data = {
                                        "Year": ["2018", "2019", "2020", "2021", "2022"],
                                        "Revenue (in billions USD)": [136.8, 161.9, 182.5, 257.6, 282.8]
                                    }
                                    df = pd.DataFrame(sample_data)
                                    
                                    fig, ax = plt.subplots(figsize=(10, 5))
                                    sns.barplot(x="Year", y="Revenue (in billions USD)", data=df, ax=ax)
                                    plt.title("Alphabet Annual Revenue")
                                    st.pyplot(fig)
                                    
                                    st.write("Sample Data Table:")
                                    st.dataframe(df)
                                else:
                                    st.write("Custom visualization would be generated based on extracted data")
            
            with tab3:
                st.header("Financial Metrics Analysis")
                st.markdown("Analyze key financial metrics from the annual report.")
                metric_type = st.selectbox(
                    "Select financial metric to analyze",
                    ["Price-to-Earnings (P/E) Ratio", "Return on Equity (ROE)", "Revenue Growth", 
                    "Operating Margin", "Net Profit Margin", "R&D Spending", "Custom Metric"]
                )
                
                if metric_type == "Custom Metric":
                    metric_type = st.text_input("Enter custom financial metric:")
                
                # Option to enable comparable data
                show_comparables = st.checkbox("Include industry comparables (if available)")
                
                if st.button("Analyze Metric"):
                    qa_chain = create_qa_chain(vectorstore)
                    with st.spinner("Analyzing financial metrics with Gemini 1.5 Flash..."):
                        comparables_text = "6. Industry comparables or benchmarks for this metric if mentioned" if show_comparables else ""
                        
                        analysis_prompt = f"""
                        Provide a detailed analysis of {metric_type} from this financial report.
                        
                        Include in your analysis:
                        1. The actual {metric_type} values for the current year and previous years if available
                        2. Historical trends of this metric
                        3. Direct quotes from the document showing where this data appears
                        4. What this metric indicates about the company's financial health
                        5. Any insights or forward-looking statements related to this metric
                        {comparables_text}
                        7. Page references where this information was found
                        8. Confidence score (1-5) for each data point
                        
                        Return the data in a structured, detailed format with clear sections.
                        Include ALL occurrences of this data in the document for verification purposes.
                        """
                        response = qa_chain.run(analysis_prompt)
                        
                        st.write("### Metric Analysis")
                        st.write(response)
                        
                        # Extract and display confidence scores if present
                        confidence_scores = re.findall(r"confidence score[:\s]*(\d+)", response, re.IGNORECASE)
                        if confidence_scores:
                            avg_confidence = sum(int(score) for score in confidence_scores) / len(confidence_scores)
                            st.write("### Analysis Confidence")
                            display_confidence(avg_confidence)
                        
                        st.info("Page numbers are included to help verify information in the original document.")
                        
                        # Add source verification
                        mentioned_pages = re.findall(r"Page (\d+)", response)
                        if mentioned_pages:
                            st.write("### Source Verification")
                            selected_page = st.selectbox("View source page:", options=[int(p) for p in set(mentioned_pages)], key="metric_page")
                            if selected_page:
                                st.markdown(display_pdf_page(file_path, selected_page), unsafe_allow_html=True)
            
            with tab4:
                st.header("Data Verification")
                st.markdown("Double-check specific financial data points for accuracy")
                
                data_point = st.text_input("Enter the financial data point to verify:", 
                                        placeholder="e.g., 'Total revenue for 2022' or 'R&D expenses'")
                expected_value = st.text_input("Expected value (optional):", 
                                            placeholder="e.g., '$282.8 billion'")
                
                # Multiple verification methods
                verification_methods = st.multiselect("Verification methods:", 
                                                    ["Direct quotes", "Page references", "Cross-checking", "Multiple sources"],
                                                    default=["Direct quotes", "Page references"])
                
                if st.button("Verify Data"):
                    if data_point:
                        qa_chain = create_qa_chain(vectorstore)
                        with st.spinner("Performing detailed verification..."):
                            verification_result = verify_financial_data(qa_chain, data_point, expected_value)
                            st.subheader("Verification Results")
                            st.write(verification_result)
                            
                            # If cross-checking is selected, perform additional verification
                            if "Cross-checking" in verification_methods:
                                with st.spinner("Performing cross-verification..."):
                                    st.subheader("Cross-Verification Results")
                                    cross_check_results = cross_check_data(qa_chain, data_point)
                                    
                                    # Display a condensed version of cross-check results
                                    for i, result in enumerate(cross_check_results):
                                        with st.expander(f"Verification Method {i+1}"):
                                            st.write(result)
                            
                            # Extract page numbers using regex
                            page_refs = re.findall(r"Page (\d+)", verification_result)
                            if page_refs:
                                st.subheader("View Referenced Pages")
                                page_to_view = st.selectbox("Select page to view:", 
                                                        options=[int(p) for p in set(page_refs)],
                                                        key="verify_page")
                                
                                if page_to_view:
                                    st.markdown("### Source Document Page")
                                    st.markdown(display_pdf_page(file_path, page_to_view), unsafe_allow_html=True)
                                    
                                    # Add option to extract tables from this page
                                    if st.button("Extract Tables from This Page"):
                                        tables = extract_tables_from_pdf(file_path, [page_to_view-1])
                                        if tables:
                                            st.write("### Extracted Table Data")
                                            st.code(tables[0]['text'])
                    else:
                        st.warning("Please enter a financial data point to verify")
                
                # Add manual page viewer
                st.subheader("Manual Page Viewer")
                st.markdown("View any page from the document directly")
                
                # If we have a page to view from the document index
                if 'page_to_view' in st.session_state:
                    manual_page = st.number_input("Enter page number:", min_value=1, max_value=num_pages, value=st.session_state.page_to_view)
                    # Clear the session state
                    del st.session_state.page_to_view
                else:
                    manual_page = st.number_input("Enter page number:", min_value=1, max_value=num_pages, value=1)
                
                if st.button("View Page"):
                    st.markdown("### Document Page")
                    st.markdown(display_pdf_page(file_path, manual_page), unsafe_allow_html=True)

            # Executive summary feature
            st.sidebar.markdown("---")
            st.sidebar.header("Executive Summary")
            if st.sidebar.button("Generate Executive Summary"):
                qa_chain = create_qa_chain(vectorstore)
                with st.spinner("Generating comprehensive summary with high accuracy..."):
                    summary_prompt = """
                    Create a comprehensive executive summary of this financial report.
                    
                    Include:
                    1. Overall financial performance highlights with exact figures
                    2. Key revenue streams and their performance with percentage changes
                    3. Major business developments mentioned
                    4. Risk factors and challenges
                    5. Forward-looking statements and guidance
                    6. Page references for each major point
                    7. Confidence scores (1-5) for key data points
                    
                    Make the summary concise but informative, focusing on the most important information
                    an investor or analyst would need to know. Include direct quotes for critical financial data.
                    """
                    summary = qa_chain.run(summary_prompt)
                    
                    st.sidebar.write(summary)
                    
                    # Extract confidence scores
                    confidence_scores = re.findall(r"confidence score[:\s]*(\d+)", summary, re.IGNORECASE)
                    if confidence_scores:
                        avg_confidence = sum(int(score) for score in confidence_scores) / len(confidence_scores)
                        st.sidebar.write("### Summary Confidence")
                        if avg_confidence >= 4:
                            st.sidebar.success(f"High confidence summary: {avg_confidence}/5")
                        elif avg_confidence >= 3:
                            st.sidebar.info(f"Medium confidence summary: {avg_confidence}/5")
                        else:
                            st.sidebar.warning(f"Low confidence summary: {avg_confidence}/5")
                    
                    st.sidebar.info("Page numbers are included to help verify information in the original document.")

    else:
        st.info(f"Please ensure the file path is correct: {file_path}")

# Add instructions
st.sidebar.markdown("---")
st.sidebar.subheader("How to use this app")
st.sidebar.markdown("""
1. Verify your PDF file path
2. Use the Financial Analysis tab to ask questions about the report
3. Use the Data Extraction tab to pull structured financial data
4. Use the Financial Metrics tab to analyze specific financial indicators
5. Use the Data Verification tab to double-check specific data points
6. Click "Generate Executive Summary" for a quick overview
7. Page numbers and source documents are provided for all answers to help verify information
""")

# Display Gemini model information
st.sidebar.markdown("---")
st.sidebar.subheader("Model Information")
st.sidebar.info("Using Gemini 1.5 Flash model for analysis")

# Add help for API key setup
st.sidebar.markdown("---")
st.sidebar.subheader("API Key Setup Help")
with st.sidebar.expander("How to set up your API key"):
    st.markdown("""
    **Option 1: Using .env file (recommended)**
    1. Create a file named `.env` in the same directory as this app
    2. Add the following line to the file: `GOOGLE_API_KEY=your_gemini_api_key_here`
    3. Save the file and restart the app
    
    **Option 2: Direct input**
    Simply enter your API key in the text field at the top of this sidebar.
    Note: This is less secure and will need to be re-entered each time you restart the app.
    """)