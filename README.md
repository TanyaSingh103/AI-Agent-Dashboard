# AI Agent Dashboard
## Project Overview

The AI Agent Dashboard is an interactive tool that allows users to automatically generate custom queries based on data from a CSV file or Google Sheets and retrieve relevant information through automated web searches. Using LangChain’s agent framework, the dashboard integrates SerpAPI for web searches and Groq API for processing search results, delivering valuable extracted insights directly on the dashboard.

## Features
- CSV & Google Sheets Integration: Upload a CSV file or connect to a Google Sheet to use entity data for queries.
- Custom Query Generation: Create dynamic queries using custom prompts with placeholders.
- Automated Web Search & Processing: Fetch search results with SerpAPI and process them with Groq for valuable information extraction.
- LangChain Agent Workflow: Organizes automated workflows using SerpAPI and Groq tools.
- Results Display & CSV Export: View extracted information in a table and download it as a CSV file.

## Setup Instructions

### 1. Prerequisites
Ensure you have the following installed:
- Python (version 3.8 or higher recommended)
- Streamlit for the interactive dashboard
- LangChain for agent functionality

### 2. Clone the Repository
Clone the repository to your local machine:
```
git clone [https://github.com/yourusername/ai-agent-dashboard.git](https://github.com/TanyaSingh103/AI-Agent-Project.git
cd AI-Agent-Project
```

### 3. Set Up a Virtual Environment
Create and activate a virtual environment:
```
python -m venv venv
```
For Windows:
```
venv\Scripts\activate
```
For macOS/Linux:
```
source venv/bin/activate
```
### 4. Install Requirements
Install all dependencies from the requirements.txt file:
```
pip install -r requirements.txt
```
### 5. Set Up API Keys
Create a .env file in the project root directory with the following keys:
```
SERP_API_KEY=your_serpapi_key
GROQ_API_KEY=your_groq_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=langchain_api_key
```
### 6. Configure Google Sheets API

- Enable the Google Sheets API and create service account credentials.
- Download the credentials.json file and place it in the project root directory.
- Make sure your credentials.json has access permissions set to read Google Sheets data.

## Usage Guide
### 1. Run the Dashboard
Start the Streamlit app:
```
streamlit run agent_dashboard.py
```
### 2. Upload Data or Connect to Google Sheets
- Upload a CSV: Use the “Choose a CSV file” option to upload a file containing entity data.
- Connect to Google Sheets: Enter the Google Sheets ID and specify the range (e.g., Sheet1!A1:D10) to load data.

### 3. Define Search Query 
- Define Placeholder and Custom Prompt: Enter a placeholder (e.g., {company}) and create a custom prompt.
- Select Column for Query Generation: Choose the column that contains entities for your search.

### 4. Execute Agent 
Use the "Execute Agent" button to let LangChain’s agent organize the workflow dynamically between the tools. It will run the queries, retrieve search results, and process them with Groq.

### 5. View and Export Results
- View Results: Extracted information is displayed in a table on the dashboard.
- Download Results: Download the results as a CSV by clicking the download button.

## API Details

- SerpAPI: Used to perform web searches based on the generated queries. 
- Groq API: Processes the search results using custom prompts.
- LangChain: A framework that enables the creation of custom agents to manage workflows. 
