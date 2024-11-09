import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from serpapi import GoogleSearch
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.title("AI Agent Dashboard")
st.write("Upload a CSV file or connect to a Google Sheet to get started.")

# Initialize df
df = None

# File upload section
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Here's a preview of your uploaded data:")
    st.dataframe(df)

# Google Sheets integration setup
credentials = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)

def fetch_google_sheet_data(spreadsheet_id, range_name):
    service = build("sheets", "v4", credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get("values", [])

    if not values:
        st.write("No data found in the specified range.")
        return None
    else:
        df = pd.DataFrame(values[1:], columns=values[0])
        return df

# Function to perform a search using SerpAPI
def perform_search(query):
    search = GoogleSearch({"q": query, "api_key": SERP_API_KEY})
    result = search.get_dict()
    return result.get("organic_results", [])  # Returns list of organic search results

# Google Sheets data input
st.write("Or connect to a Google Sheet:")
spreadsheet_id = st.text_input("Enter Google Sheets ID")
range_name = st.text_input("Enter the range (e.g., Sheet1!A1:D10)")

if spreadsheet_id and range_name:
    # Fetch and display data from Google Sheets
    df = fetch_google_sheet_data(spreadsheet_id, range_name)
    if df is not None:
        st.write("Here’s a preview of your Google Sheets data:")
        st.dataframe(df)

if df is not None:
    # Dynamic query input for search prompt
    st.subheader("Define Your Search Query")

    # User-defined placeholder (e.g., 'company' for '{company}')
    placeholder_text = st.text_input("Enter your placeholder name (e.g., 'company')", value="entity")
    custom_prompt = st.text_input(f"Enter your prompt (e.g., 'Get me the email address of {{{placeholder_text}}}')")

    # Column selection for entity list
    st.write("Select the main column (e.g., company names):")
    column_choice = st.selectbox("Column:", df.columns)

    # Generate custom queries if prompt and column are chosen
    if custom_prompt and column_choice:
        # Replace user-defined placeholder in the prompt for each entity
        placeholder = f"{{{placeholder_text}}}"
        queries = [custom_prompt.replace(placeholder, str(entity)) for entity in df[column_choice]]

        # Display generated queries
        st.write("Generated Queries:")
        st.write(queries)

    # Button to confirm and start processing (e.g., web search, API calls)
    if st.button("Generate Searches"):
        if queries:
            # Perform searches and collect results
            search_results = []
            for query in queries:
                result = perform_search(query)
                search_results.append({"query": query, "results": result})
            
            st.write("Search Results:")
            for result in search_results:
                st.write(f"Query: {result['query']}")
                st.write("Results:")
                for item in result["results"]:
                    st.write(f" - {item.get('title')}: {item.get('link')}")
        else:
            st.write("Please make sure you have entered a prompt and selected a column.")

openai.api_key = OPENAI_API_KEY

def process_with_llm(query, search_results, custom_prompt):
    """
    Uses the LLM to extract specific information based on the custom prompt and search results.
    """
    # Combine the search results into a single text for the LLM
    search_text = "\n".join([f"{result['title']}: {result['link']}\n{result['snippet']}" for result in search_results])

    # Create a prompt for the LLM
    llm_prompt = f"{custom_prompt} from the following search results:\n\n{search_text}\n\nPlease extract the information requested."

    # Call the LLM API (e.g., OpenAI's GPT-4)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=llm_prompt,
        max_tokens=150,
        temperature=0.5
    )

    # Return the LLM's response text
    return response.choices[0].text.strip()
