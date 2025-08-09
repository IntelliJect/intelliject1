# 🧠 IntelliJect: Smart PYQ-PDF Enhancer

IntelliJect is an intelligent academic tool that enhances PDF notes by finding and highlighting relevant Previous Year Questions (PYQs) using semantic search and AI-powered analysis.

## ✨ Features

- *PDF Processing*: Upload and extract content from academic PDF notes
- *Semantic Search*: Find relevant PYQs using FAISS vector similarity search
- *AI-Powered Analysis*: Automatic subtopic inference and answer extraction using OpenAI GPT
- *Visual Highlighting*: Highlight answers directly on PDF pages
- *Subject Support*: Currently supports Cyber Security and Environmental Sciences
- *History Tracking*: Keep track of uploaded PDFs and processing history

## 🏗 Architecture

The application consists of:
- *FastAPI Backend*: RESTful API for PDF processing and PYQ matching
- *Streamlit Frontend*: Interactive web interface
- *PostgreSQL Database*: Store PYQs and processing history
- *LangChain + FAISS*: Semantic search and vector storage
- *OpenAI Integration*: GPT-powered subtopic inference and answer extraction

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL database
- OpenAI API key

### 1. Clone the Repository
bash
git clone https://github.com/your-username/intelliject.git
cd intelliject


### 2. Install Dependencies
bash
pip install -r requirements.txt


### 3. Environment Configuration
bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env


Fill in your environment variables:
bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/intelliject


### 4. Database Setup
bash
# Create database tables
python create_tables.py

# Load PYQ data (place your JSON files in 'subjects' folder)
python data_loader.py


### 5. Download NLTK Data
python
import nltk
nltk.download('punkt')


## 🎯 Running the Application

### Start the FastAPI Server
bash
python fastapi_app.py

The API will be available at http://localhost:8000

### Start the Streamlit Frontend
bash
streamlit run main.py

The web interface will be available at http://localhost:8501

## 📁 Project Structure


intelliject/
├── fastapi_app.py          # FastAPI backend server
├── main.py                 # Streamlit frontend
├── database.py             # Database configuration
├── models.py               # SQLAlchemy models
├── crud.py                 # Database operations
├── rag_pipeline.py         # RAG and semantic search logic
├── utils.py                # PDF processing utilities
├── create_tables.py        # Database initialization
├── data_loader.py          # Load PYQ data from JSON
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── subjects/              # PYQ JSON files (create this folder)
└── README.md              # This file


## 📊 Data Format

PYQ data should be stored in JSON files within the subjects/ folder:

json
[
  {
    "question": "Explain the concept of firewall in network security",
    "sub_topic": "Network Security",
    "marks": 5,
    "year": "2023"
  }
]


## 🛠 API Endpoints

- GET / - Health check
- GET /history - Get PDF upload history
- POST /upload-pdf - Upload PDF file
- POST /process-pdf - Process PDF and get highlighted results

## 🔧 Configuration

### Supported Subjects
- Cyber Security
- Environmental Sciences

### Model Configuration
- *Embedding Model*: OpenAI embeddings
- *LLM Model*: GPT-3.5-turbo
- *Vector Store*: FAISS
- *PDF Processing*: PyMuPDF

## 🚨 Troubleshooting

### Common Issues

1. *API Connection Error*
   - Ensure FastAPI server is running on correct port
   - Check if firewall is blocking connections

2. *Database Connection Error*
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database exists

3. *OpenAI API Error*
   - Verify OPENAI_API_KEY is set correctly
   - Check API quota and billing

4. *PDF Processing Error*
   - Ensure uploaded file is a valid PDF
   - Check if PDF is not password protected

## 🙏 Acknowledgments

- LangChain for RAG framework
- OpenAI for language models
- PyMuPDF for PDF processing
- Streamlit for the web interface
- FastAPI for the backend API