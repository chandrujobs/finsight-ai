# Application settings
APP_TITLE = "FinSight AI"
APP_DESCRIPTION = "AI-powered tool for analyzing financial documents"

# Default paths
DEFAULT_SINGLE_DOC_PATH = r"C:\Users\admin\OneDrive\Desktop\AI Business Chatbot\Uploads\2022-alphabet-annual-report.pdf"
DEFAULT_FOLDER_PATH = r"C:\Users\admin\OneDrive\Desktop\AI Business Chatbot\Uploads"

# Model settings
EMBEDDING_MODEL = "models/embedding-001"
LLM_MODEL = "gemini-1.5-flash"
LLM_TEMPERATURE = 0

# Document processing settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
RETRIEVER_K = 8
RETRIEVER_SCORE_THRESHOLD = 0.7

# Financial metrics
STANDARD_METRICS = {
    'Annual Report': [
        'Total Revenue', 
        'Net Income', 
        'Total Assets',
        'Total Liabilities',
        'Operating Income',
        'EPS (Basic)',
        'Cash and Cash Equivalents'
    ],
    'Form 10-K': [
        'Revenue',
        'Net Income',
        'Total Assets',
        'Total Liabilities',
        'Operating Income',
        'EPS',
        'Cash and Cash Equivalents'
    ],
    'Quarterly Report': [
        'Revenue',
        'Net Income',
        'EPS',
        'Operating Expenses'
    ]
}

# Extraction templates
EXTRACTION_TEMPLATES = {
    "Annual Revenue": "Extract all revenue figures for the past 3 years with page references",
    "Profit Margins": "Extract all profit margin percentages with page references",
    "Balance Sheet Summary": "Extract key balance sheet items with page references",
    "Income Statement Summary": "Extract key income statement line items with page references",
    "Cash Flow Summary": "Extract key cash flow statement items with page references",
    "Segment Information": "Extract revenue by business segment with page references"
}