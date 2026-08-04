import streamlit as st
import json
from pathlib import Path
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

# Get the API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class APIManager:
    def __init__(self):
        self.config_dir = Path("user_data")
        self.config_file = self.config_dir / "api_config.json"
        self.config_dir.mkdir(exist_ok=True)
        
        # Load saved API key on init
        self.load_api_config()
    
    def detect_provider(self, api_key: str) -> str:
        """Auto-detect API provider from key format"""
        if api_key.startswith("AIza") or api_key.startswith("AQ."):
            return "gemini"
        elif api_key.startswith("sk-"):
            return "openai"
        elif api_key.startswith("sk-ant-"):
            return "claude"
        else:
            return "unknown"
    
    def validate_and_setup_api(self, api_key: str):
        """Validate API key and setup client"""
        if not api_key or len(api_key) < 10:
            return {"status": "error", "message": "❌ Invalid API key format"}
        
        provider = self.detect_provider(api_key)
        
        if provider == "unknown":
            return {"status": "warning", "message": "⚠️ Unknown LLM - Check manually"}
        
        # Validate based on provider
        if provider == "gemini":
            return self._validate_gemini(api_key)
        elif provider == "openai":
            return self._validate_openai(api_key)
        elif provider == "claude":
            return self._validate_claude(api_key)
    
    def _validate_gemini(self, api_key: str):
        """Validate Google Gemini API"""
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-3.5-pro')
            
            # Test with minimal request
            response = model.generate_content("Hi")
            
            # Store in session state
            st.session_state.api_client = model
            st.session_state.api_provider = "gemini"
            st.session_state.api_key = api_key
            
            # Save to file
            self.save_api_config(api_key, "gemini")
            
            return {
                "status": "success",
                "message": "✅ Google Gemini API - Valid",
                "provider": "gemini"
            }
        except Exception as e:
            error_msg = str(e).lower()
            
            # IMPORTANT: Store client even if validation test fails
            # The key might still be valid for actual usage
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-3.5-pro')
            st.session_state.api_client = model
            st.session_state.api_provider = "gemini"
            st.session_state.api_key = api_key
            self.save_api_config(api_key, "gemini")
            
            if "quota" in error_msg or "limit" in error_msg:
                return {"status": "error", "message": "❌ Quota exceeded - Use another key"}
            elif "invalid" in error_msg or "401" in error_msg or "403" in error_msg:
                return {"status": "error", "message": "❌ Invalid Gemini API key"}
            else:
                return {"status": "warning", "message": f"⚠️ Key configured - Verify on first use"}


    def _validate_openai(self, api_key: str):
        """Validate OpenAI API"""
        try:
            client = OpenAI(api_key=api_key)
            
            # Test with minimal request
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            
            # Store in session state
            st.session_state.api_client = client
            st.session_state.api_provider = "openai"
            st.session_state.api_key = api_key
            
            # Save to file
            self.save_api_config(api_key, "openai")
            
            return {
                "status": "success",
                "message": "✅ OpenAI API - Valid",
                "provider": "openai"
            }
        except Exception as e:
            error_msg = str(e).lower()
            
            # IMPORTANT: Store client even if validation test fails
            client = OpenAI(api_key=api_key)
            st.session_state.api_client = client
            st.session_state.api_provider = "openai"
            st.session_state.api_key = api_key
            self.save_api_config(api_key, "openai")
            
            if "quota" in error_msg or "insufficient" in error_msg:
                return {"status": "error", "message": "❌ Quota exceeded - Use another key"}
            elif "invalid" in error_msg or "incorrect" in error_msg:
                return {"status": "error", "message": "❌ Invalid OpenAI API key"}
            else:
                return {"status": "warning", "message": "⚠️ Key configured - Verify on first use"}


    def _validate_claude(self, api_key: str):
        """Validate Anthropic Claude API"""
        try:
            client = Anthropic(api_key=api_key)
            
            # Test with minimal request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            # Store in session state
            st.session_state.api_client = client
            st.session_state.api_provider = "claude"
            st.session_state.api_key = api_key
            
            # Save to file
            self.save_api_config(api_key, "claude")
            
            return {
                "status": "success",
                "message": "✅ Anthropic Claude API - Valid",
                "provider": "claude"
            }
        except Exception as e:
            error_msg = str(e).lower()
            
            # IMPORTANT: Store client even if validation test fails
            client = Anthropic(api_key=api_key)
            st.session_state.api_client = client
            st.session_state.api_provider = "claude"
            st.session_state.api_key = api_key
            self.save_api_config(api_key, "claude")
            
            if "quota" in error_msg or "limit" in error_msg:
                return {"status": "error", "message": "❌ Quota exceeded - Use another key"}
            elif "invalid" in error_msg or "authentication" in error_msg:
                return {"status": "error", "message": "❌ Invalid Claude API key"}
            else:
                return {"status": "warning", "message": "⚠️ Key configured - Verify on first use"}
            
            
    
    def save_api_config(self, api_key: str, provider: str):
        """Save API configuration to file"""
        config = {
            "api_key": api_key,
            "provider": provider
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
    
    def load_api_config(self):
        """Load saved API configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    api_key = config.get("api_key")
                    provider = config.get("provider")
                    
                    if api_key and provider:
                        st.session_state.api_key = api_key
                        st.session_state.api_provider = provider
                        # Re-validate on load
                        self.validate_and_setup_api(api_key)
            except Exception as e:
                pass  # Ignore errors, user will re-enter key
    
    def get_masked_key(self, api_key: str) -> str:
        """Return masked API key for display"""
        if len(api_key) > 12:
            return f"{api_key[:6]}{'*' * 20}{api_key[-4:]}"
        return "*" * len(api_key)