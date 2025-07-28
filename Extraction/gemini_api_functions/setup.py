import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

def get_and_validate_api_key():
    """Get API key from .env and validate it with Gemini"""
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        st.error("❌ GOOGLE_API_KEY not found in .env file")
        return None
    
    # Display masked API key
    masked_key = f"{api_key[:8]}{'*' * (len(api_key) - 12)}{api_key[-4:]}"
    st.info(f"🔑 Using API Key: {masked_key}")
    
    # Validate API key
    try:
        genai.configure(api_key=api_key)
        # Test with a minimal request
        model = genai.GenerativeModel('gemini-1.5-flash')
        test_response = model.generate_content("Test")
        st.session_state.gemini_model = model
        st.success("✅ API Key is valid and active")
        return api_key
    except genai.types.BrokenResponseError:
        st.error("❌ API Key is invalid or expired")
        return None
    except Exception as e:
        st.error(f"❌ API validation failed: {str(e)[:100]}")
        return None
    

def setup_gemini(api_key: str):
    """Initialize Gemini API"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.session_state.gemini_model = model
        return True
    except Exception as e:
        st.error(f"Error setting up Gemini: {e}")
        return False