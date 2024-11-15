import os
import groq
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from serpapi import GoogleSearch
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq.api_key = GROQ_API_KEY

# Groq model using langchain_groq
model = ChatGroq(model="llama3-8b-8192")

# Google Sheets integration setup
credentials = service_account.Credentials.from_service_account_file(
    "credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)

def fetch_google_sheet_data(spreadsheet_id, range_name):
    try:
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get("values", [])
        
        if not values:
            st.warning("No data found in the specified range.")
            return None
        else:
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
    except Exception as e:
        st.error(f"An error occurred while fetching Google Sheets data: {e}")
        return None

# Search using SerpAPI
def perform_search(query):
    try:
        search = GoogleSearch({"q": query, "api_key": SERP_API_KEY})
        result = search.get_dict()
        return result.get("organic_results", [])
    except Exception as e:
        st.error(f"An error occurred while performing a web search: {e}")
        return []


def process_with_groq(query, search_results, custom_prompt):
    try:
        search_text = "\n".join([f"{result['title']}: {result['link']}\n{result['snippet']}" for result in search_results])
        prompt = f"{custom_prompt} from the following search results:\n\n{search_text}\n\nPlease extract the information requested and give me one result only, no additional dialogue, just few words/url info. Do not respond with 'here's the information:', just give the result"

        completion = groq.Groq().chat.completions.create(
            model="llama3-8b-8192", 
            messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150,
            top_p=1,
            stream=True,
            stop=None
        )

        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content or ""

        return response_text.strip()
    except Exception as e:
        st.error(f"An error occurred while processing with Groq: {e}")
        return "Error in processing"

# Streamlit UI setup
st.title("AI Agent Dashboard")
st.write("Upload a CSV file or connect to a Google Sheet to get started.")

df = None
queries = []

# File upload section
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Here's a preview of your uploaded data:")
    st.dataframe(df)

# Google Sheets data input
st.write("Or connect to a Google Sheet:")
spreadsheet_id = st.text_input("Enter Google Sheets ID")
range_name = st.text_input("Enter the range (e.g., Sheet1!A1:D10)")

if spreadsheet_id and range_name:
    df = fetch_google_sheet_data(spreadsheet_id, range_name)
    if df is not None:
        st.write("Here’s a preview of your Google Sheets data:")
        st.dataframe(df)

if df is not None:
    # Dynamic query input for search prompt
    st.subheader("Define Your Search Query")

    # User-defined placeholder 
    placeholder_text = st.text_input("Enter your placeholder name (e.g., 'company')", value="entity")
    custom_prompt = st.text_input(f"Enter your prompt (e.g., 'Get me the email address of {{{placeholder_text}}}')")

    st.write("Select the main column (e.g., company names):")
    column_choice = st.selectbox("Column:", df.columns)

    # Custom query generation
    if custom_prompt and column_choice:
        placeholder = f"{{{placeholder_text}}}"
        queries = [custom_prompt.replace(placeholder, str(entity)) for entity in df[column_choice]]
        st.write("Generated Queries:")
        st.write(queries)


# Tools for Langchain agent
search_tool = Tool(
    name="Google Search",
    func=perform_search,
    description="Use this tool to perform a web search"
)

groq_tool = Tool(
    name="Groq Processing",
    func=process_with_groq,
    description="Use this tool to process search results using Groq"
)

tools = [search_tool, groq_tool]

agent = initialize_agent(
    tools,
    model,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

if st.button("Execute Agent"):
    if queries:
        results = []
        for query in queries:
             # Fetch search results adn extract information
            results_for_query = perform_search(query) 
            extracted_info = process_with_groq(query, results_for_query, custom_prompt)
            
            results.append({"Query": query, "Extracted Information": extracted_info})
        
        # Display the results
        results_df = pd.DataFrame(results)
        st.write("Agent Responses:")
        st.dataframe(results_df)

        # Download button for CSV export
        csv_data = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Agent Responses as CSV",
            data=csv_data,
            file_name="agent_responses.csv",
            mime="text/csv"
        )