import streamlit as st
import io

def fetch_pdf_from_url(url):
    try:
        import requests
        response = requests.get(url)
        if response.headers.get('content-type') == 'application/pdf':
            return io.BytesIO(response.content)
        else:
            st.error("URL does not point to a PDF file")
            return None
    except Exception as e:
        st.error(f"Error fetching PDF: {str(e)}")
        return None