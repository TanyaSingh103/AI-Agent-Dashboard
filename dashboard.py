import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from serpapi import GoogleSearch
import groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq.api_key = GROQ_API_KEY

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

# Initialize the Groq client
client = groq.Groq()

def process_with_groq(query, search_results, custom_prompt):
    """
    Uses the Groq API to extract specific information based on the custom prompt and search results.
    """
    # Format the prompt with the search results
    search_text = "\n".join([f"{result['title']}: {result['link']}\n{result['snippet']}" for result in search_results])
    prompt = f"{custom_prompt} from the following search results:\n\n{search_text}\n\nPlease extract the information requested and give me one result only, no additional dialogue, just few words/url info. Do not respond with 'here's the information:', just give the result"

    # Send the prompt to Groq and handle streaming response
    completion = client.chat.completions.create(
        model="llama3-8b-8192",  # Replace with the correct model if needed
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=150,
        top_p=1,
        stream=True,
        stop=None
    )

    # Collect the streamed response
    response_text = ""
    for chunk in completion:
        response_text += chunk.choices[0].delta.content or ""

    return response_text.strip()

# def update_google_sheet(spreadsheet_id, range_name, data):
#     # Convert DataFrame to list of lists for Google Sheets API format
#     values = data.values.tolist()
    
#     # Prepare the request body for appending data
#     body = {
#         "values": values
#     }

#     try:
#         # Append data to the Google Sheet
#         service = build("sheets", "v4", credentials=credentials)
#         response = service.spreadsheets().values().append(
#             spreadsheetId=spreadsheet_id,
#             range=range_name,  # E.g., 'Sheet1!A:D' or simply 'Sheet1'
#             valueInputOption="USER_ENTERED",
#             insertDataOption="INSERT_ROWS",  # This ensures rows are added without overwriting
#             body=body
#         ).execute()
        
#         # Confirm success
#         st.write("Data successfully appended to Google Sheet!")
#     except Exception as e:
#         st.write(f"An error occurred: {e}")

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
            # Get search results
            result = perform_search(query)
            # Process results with Groq API
            extracted_info = process_with_groq(query, result, custom_prompt)
            search_results.append({"Query": query, "Extracted Information": extracted_info})
        
        # Convert the results to a DataFrame for display
        results_df = pd.DataFrame(search_results)
        
        # Display the extracted information in a table
        st.write("Extracted Information:")
        st.dataframe(results_df)  # You can also use st.table(results_df) if you prefer a static table

        # Add download button for CSV export
        csv_data = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Extracted Information as CSV",
            data=csv_data,
            file_name="extracted_information.csv",
            mime="text/csv"
        )

        # Button to update Google Sheets with extracted information
        # if st.button("Update Google Sheet with Extracted Information"):
        #     update_google_sheet(spreadsheet_id, range_name, results_df)



