import streamlit as st
import pandas as pd
from PIL import Image
import io
from datetime import datetime
import json
import base64
from google import genai  # NEW API
from dotenv import load_dotenv
import os

load_dotenv()

class PinoutExtractor:
    def __init__(self):
        """Initialize Gemini client from environment"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY not found in .env file")
            st.stop()
        
        # NEW API structure
        os.environ["GOOGLE_API_KEY"] = api_key  # Client reads from env
        self.client = genai.Client()
        self.model = "gemini-3.6-flash"
    
    def run(self):
        """Main entry point - orchestrates entire flow"""
        st.subheader(" AI Pinout Extractor")
        
        # Upload and auto-extract
        uploaded_file = st.file_uploader(
            "📁 Upload Pinout Diagram",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            help="Supports common image formats"
        )
        
        if uploaded_file:
            # Auto-extract on upload
            if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
                st.session_state.last_uploaded = uploaded_file.name
                
                with st.spinner("🔍 Analyzing pinout diagram..."):
                    image = Image.open(uploaded_file)
                    extracted_data = self.extract_with_gemini(image)
                    
                    if extracted_data:
                        st.session_state.extracted_data = extracted_data
                        st.session_state.uploaded_image = uploaded_file
                        st.success("✅ Extraction complete!")
                    else:
                        st.error("❌ Extraction failed - You can manually edit the table below")
                        st.session_state.extracted_data = self.create_empty_data()
                        st.session_state.uploaded_image = uploaded_file
            
            # Display results
            if 'extracted_data' in st.session_state:
                self.display_results()
    
    def extract_with_gemini(self, image):
        """Extract pinout data using NEW Gemini API"""
        try:
            # Convert PIL image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            prompt = """
            Analyze this pinout diagram and extract pin information in JSON format.

            Return ONLY valid JSON in this structure:
            {
                "device_info": {
                    "name": "detected device name",
                    "package": "package type",
                    "total_pins": "number"
                },
                "pins": [
                    {
                        "pin_number": "1",
                        "primary_name": "VCC",
                        "alternate_functions": ["POWER", "5V"],
                        "electrical_type": "Power"
                    }
                ]
            }

            Instructions:
            1. Extract all pin numbers in correct order
            2. Identify primary pin names/labels
            3. If pin name has a line on top, prefix with # (indicates active-low)
            4. Include alternate functions if visible
            5. Determine electrical type: Input, Output, Power, I/O, or Passive
            6. Use standard abbreviations (VCC, GND, GPIO, TX, RX, etc.)
            7. Return ONLY JSON, no markdown or extra text

            Electrical Type Guidelines:
            - Power: VCC, VDD, GND, VSS, VBAT, etc.
            - Input: RX, MISO, sensor inputs, clock inputs
            - Output: TX, MOSI, LED drivers
            - I/O: GPIO, bidirectional data pins
            - Passive: NC (No Connect), shields
            """
            
            # NEW API call structure
            interaction = self.client.interactions.create(
                model=self.model,
                input=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "data": image_base64,
                        "mime_type": "image/png"
                    }
                ]
            )
            
            return self.parse_response(interaction.output_text)
            
        except Exception as e:
            st.error(f"Gemini API Error: {str(e)}")
            return None
    
    def parse_response(self, text):
        """Parse JSON from Gemini response"""
        try:
            # Find JSON in response
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = text[start:end]
                data = json.loads(json_str)
                return data
            else:
                return None
                
        except json.JSONDecodeError:
            return None
    
    def create_empty_data(self):
        """Create empty structure for manual editing"""
        return {
            "device_info": {
                "name": "Unknown Device",
                "package": "Unknown",
                "total_pins": "0"
            },
            "pins": []
        }
    
    def display_results(self):
        """Display image and editable table side-by-side"""
        data = st.session_state.extracted_data
        
        # Device info metrics
        if 'device_info' in data:
            info = data['device_info']
            
            st.caption("Device Information")
            
            device_df = pd.DataFrame({
                'Key': ['Device', 'Package', 'Total Pins'],
                'Value': [
                    info.get('name', 'Unknown'),
                    info.get('package', 'Unknown'),
                    info.get('total_pins', '0')
                ]
            })
            
            st.dataframe(
                device_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Property": st.column_config.TextColumn("Property", width="medium"),
                    "Value": st.column_config.TextColumn("Value", width="large")
                }
            )

        st.markdown("---")
        
        # Side-by-side layout
        col_img, col_table = st.columns([1, 1.5])
        
        with col_img:
            st.caption("Uploaded Image")
            image = Image.open(st.session_state.uploaded_image)
            st.image(image, use_column_width=True)
        
        with col_table:
            st.caption("Extracted Data")
            
            # Convert to DataFrame
            pins_data = []
            if 'pins' in data and data['pins']:
                for pin in data['pins']:
                    pins_data.append({
                        'Pin Designator': pin.get('pin_number', ''),
                        'Pin Display Name': pin.get('primary_name', ''),
                        'Pin Alternate Name': '/'.join(pin.get('alternate_functions', [])),
                        'Electrical Type': pin.get('electrical_type', '') 
                    })
            
            # Create DataFrame (empty if no data)
            if not pins_data:
                pins_data = [{'Pin Designator': '', 'Pin Display Name': '', 'Pin Alternate Name': '', 'Electrical Type': ''}]
            
            df = pd.DataFrame(pins_data)
            
            # Editable table with add/delete rows
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pin Designator": st.column_config.TextColumn("Pin #", width="small"),
                    "Pin Display Name": st.column_config.TextColumn("Name", width="medium"),
                    "Pin Alternate Name": st.column_config.TextColumn("Alt Names", width="medium"),
                    "Electrical Type": st.column_config.SelectboxColumn("Type",width="small",options=["Input", "Output", "Power", "I/O", "Passive"])
                }
            )
            
            # Store edited version
            st.session_state.edited_pin_table = edited_df
        
        # Download and navigation section
        st.markdown("---")
        self.download_and_continue(edited_df, data)
    
    def download_and_continue(self, df, raw_data):
        """Provide download options and grouping navigation"""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # JSON Download
            json_str = json.dumps(raw_data, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"pinout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Continue to Grouping
            if st.button("Continue to Grouping 2.0", type="primary", use_container_width=True):
                self.pass_to_grouping(df, raw_data)
    
    def pass_to_grouping(self, df, raw_data):
        """Prepare data for Grouping 2.0 page"""
        # Extract part number from device name
        part_number = "Unknown"
        if 'device_info' in raw_data:
            part_number = raw_data['device_info'].get('name', 'Unknown')
        
        # Store in session state with correct keys for Grouping page
        st.session_state["part number"] = part_number  # With space!
        st.session_state["pin_table"] = df             # With underscore
        st.session_state["uploaded_csv_name"] = part_number  # Fallback
        
        st.success(f"Data ready for Grouping 2.0")
        st.info("Navigate to **Grouping 2.0** from the sidebar")