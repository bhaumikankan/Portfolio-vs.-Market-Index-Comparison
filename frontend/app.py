import streamlit as st
import requests
import time
import csv
from index_symbol import index_symbol

def csv_to_dict(csv_content):
    # Assuming the CSV has a header row
    reader = csv.DictReader(csv_content.splitlines())
    rows = list(reader)
    return rows

# Function to call FastAPI and get response
def call_fastapi(stock_data, index,percentage_down):
    api_url = 'http://127.0.0.1:8000/hadge'

    query_params = {
        'index': index,
        'percentage_down': percentage_down
    }
    
    # Make a POST request to the FastAPI endpoint
    response = requests.post(api_url,params=query_params, json=stock_data)
    
    try:
        if response.json()['success']:
            return response.json()['html_content']
        else:
            return f"<h4>{response.json()['msg']}</h4>"
    except :
        return "<h3>Somethig went wrong..😢</h3>"

# Streamlit app
def main():
    st.title('Portfolio vs. Market Index Comparison Tool')

    # File upload
    uploaded_file = st.file_uploader('Choose a file', type=['csv'])

    st.markdown("Sample File Structure: [Google Sheets Link](https://docs.google.com/spreadsheets/d/1-RQtKXMsQ-pS36asVueu6mIyEeVn-9uEVWJ4y9tmAts/edit#gid=0)")
    
    options = index_symbol
    index = st.selectbox('Select market index symbol', options)

    
    percentage_down = st.number_input('Enter the percentage your portfolio is expected to go down (e.g., 10 for 10%)', min_value=1.0, max_value=100.0,step=0.1)

    # Check if an option is selected
    if not index:
        st.error('Please select a market index symbol')
        return
    
    if not percentage_down or percentage_down==0:
        st.error('Enter the percentage your portfolio is expected to go down (e.g., 10 for 10%)')
        return

    # Submit button
    if st.button('Submit'):
        if uploaded_file is not None:
            # Display loading spinner animation
            with st.spinner('Loading...'):
                # Call FastAPI
                csv_data = uploaded_file.read()
                stock_data = csv_to_dict(csv_data.decode())
                api_response = call_fastapi(stock_data, index,percentage_down)

                # Display API response (HTML code)
                st.write('Analysis:')
                st.markdown(api_response, unsafe_allow_html=True)

if __name__=="__main__":
    main()