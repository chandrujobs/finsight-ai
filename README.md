# FinSight AI

## 📊 AI-Powered Financial Document Analysis Tool

FinSight AI is an advanced financial document analyzer that leverages AI to extract, analyze, and visualize data from financial reports. The application processes financial PDFs (such as annual reports and 10-K filings) and provides intelligent insights, data extraction, and financial projections.

## ✨ Features

- **Document Processing**: Analyze single files or entire folders of financial PDFs
- **Intelligent Q&A**: Ask questions about financial documents and get AI-powered answers
- **Data Extraction**: Extract standardized financial metrics and tables automatically
- **Multi-Document Comparison**: Compare metrics across different documents, companies, or time periods
- **Financial Projections**: Generate future financial forecasts based on historical data
- **Interactive Dashboard**: Visualize key financial metrics and trends
- **Source Verification**: View original PDF pages to verify extracted information
- **Confidence Scoring**: Transparent confidence ratings for all extracted data

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- Git

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/chandrujobs/finsight-ai.git
   cd finsight-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your Gemini API key:
   - Create a `.env` file in the project root directory
   - Add your API key: `GOOGLE_API_KEY=your_gemini_api_key_here`

## 🚀 Usage

1. Run the application:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to http://localhost:8501

3. Upload a financial document (PDF) or specify a folder path

4. Use the different tabs to:
   - Ask questions about the document
   - Extract financial data
   - Compare metrics across documents
   - Generate future projections
   - View the financial dashboard

## 📋 Example Queries

- "What was the total revenue in 2022?"
- "How did operating expenses change compared to the previous year?"
- "What are the key risk factors mentioned in the report?"
- "Extract all profit margin percentages from the document"
- "What is the company's R&D spending trend over the last 3 years?"

## 📁 Project Structure

```
financial_analyzer/
├── app.py                    # Main application file
├── config.py                 # Configuration and settings
├── requirements.txt          # Dependencies list
├── modules/                  # Core functionality modules
│   ├── document_processor.py # Document loading and processing
│   ├── embeddings.py         # Vector embeddings and storage
│   ├── qa_chain.py           # QA chain creation and management
│   ├── data_extraction.py    # Financial data extraction
│   ├── visualization.py      # Charts and dashboards
│   ├── prediction.py         # Financial projections
│   └── document_analyzer.py  # Document type detection
├── ui/                       # UI components and pages
│   ├── document_management.py # Document management UI
│   ├── analysis_tab.py        # Financial analysis tab UI
│   ├── extraction_tab.py      # Data extraction tab UI
│   ├── comparison_tab.py      # Comparison & prediction tab UI
│   ├── dashboard_tab.py       # Dashboard tab UI
│   └── components.py          # Reusable UI components
└── utils/                    # Utility functions
    ├── pdf_utils.py          # PDF-specific utilities
    └── file_operations.py    # File handling utilities
```

## 🔧 Technologies Used

- **Streamlit**: For the web interface
- **LangChain**: For working with Gemini LLM
- **Google Generative AI**: LLM and embedding provider
- **FAISS**: For efficient vector storage and retrieval
- **PyMuPDF**: For PDF processing
- **Plotly**: For interactive visualizations
- **Pandas**: For data manipulation

## 🔒 Privacy & Security

All document processing happens locally on your machine. No document data is sent to external servers except for the specific text chunks sent to the Gemini API for analysis. API keys are stored securely in the `.env` file which is not tracked by Git.

## 🔮 Future Enhancements

- User authentication and document access controls
- Database storage for processed documents and extracted data
- Support for additional document types (Excel, Word, etc.)
- Advanced NLP for sentiment analysis and risk assessment
- Industry benchmarking and comparison
- Regulatory compliance checking
- Customizable reporting and exports

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contact & Contributions

Created by [chandrujobs](https://github.com/chandrujobs)

Issues and pull requests are welcome! Feel free to contribute to this project.

⭐ If you find this project useful, please consider giving it a star on GitHub! ⭐