import streamlit as st
import pandas as pd
from PIL import Image
import io
from datetime import datetime
import json
import base64

class PinoutExtractor:
    def __init__(self):
        from pathlib import Path
        self.image_dir = Path("captured_images")
        self.image_dir.mkdir(exist_ok=True)
    
    def upload_screenshot(self): 
        uploaded_file = st.file_uploader(
            "📁 Upload your captured pinout image",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            help="Upload the pinout diagram you captured"
        )
        
        if uploaded_file is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pinout_{timestamp}.{uploaded_file.name.split('.')[-1]}"
            filepath = self.image_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.captured_image = uploaded_file
            st.session_state.image_path = str(filepath)
            
            st.success(f"✅ Image saved to: {filepath}")
            
            image = Image.open(uploaded_file)
            st.image(image, caption="Captured Pinout Diagram", use_column_width=True)
            
            if st.button("➡️ Proceed to Extraction", type="primary"):
                st.session_state.current_stage = "extract"
                st.rerun()
    
    def extract_pinout_data(self):
        """Stage 2: AI-powered pinout extraction"""
        st.header("AI Powered Pinout Extraction")
        
        if 'captured_image' not in st.session_state:
            st.warning("⚠️ No image captured yet. Please go back to Stage 1.")
            return
        
        # Check if API is configured
        if 'api_client' not in st.session_state or 'api_provider' not in st.session_state:
            st.error("❌ No valid API configured. Please enter your API key in the sidebar.")
            return
        
        # Display image and options
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Pinout Diagram")
            image = Image.open(st.session_state.captured_image)
            st.image(image, use_column_width=True)
        
        with col2:
            st.subheader("Configure")
            extract_descriptions = st.checkbox("Include pin descriptions", value=True)
            extract_functions = st.checkbox("Extract alternate functions", value=True)
            device_type = st.selectbox(
                "Device Type (optional)",
                ["Auto-detect", "Microcontroller", "IC", "Connector", "Module"]
            )
        
        if st.button("🚀 Extract Pinout Data", type="primary"):
            with st.spinner("Analyzing the pinout diagram..."):
                extracted_data = self.perform_ai_extraction(
                    st.session_state.captured_image,
                    extract_descriptions,
                    extract_functions,
                    device_type
                )
                
                if extracted_data:
                    st.session_state.extracted_data = extracted_data
                    st.success("✅ Pinout data extracted successfully!")
                    self.display_extraction_results(extracted_data)
                else:
                    st.error("❌ Failed to extract pinout data")
    
    def perform_ai_extraction(self, image_file, include_desc, include_func, device_type):
        """Perform AI extraction using active API provider"""
        try:
            provider = st.session_state.api_provider
            prompt = self.create_extraction_prompt(include_desc, include_func, device_type)
            image = Image.open(image_file)
            
            if provider == "gemini":
                return self._extract_with_gemini(prompt, image)
            elif provider == "openai":
                return self._extract_with_openai(prompt, image)
            elif provider == "claude":
                return self._extract_with_claude(prompt, image)
            
        except Exception as e:
            st.error(f"Error during AI extraction: {str(e)}")
            return None
    
    def _extract_with_gemini(self, prompt, image):
        """Extract using Gemini Vision"""
        model = st.session_state.api_client
        response = model.generate_content([prompt, image])
        return self.parse_ai_response(response.text)
    
    def _extract_with_openai(self, prompt, image):
        """Extract using OpenAI GPT-4 Vision"""
        client = st.session_state.api_client
        
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096
        )
        
        return self.parse_ai_response(response.choices[0].message.content)
    
    def _extract_with_claude(self, prompt, image):
        """Extract using Claude Vision"""
        client = st.session_state.api_client
        
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        return self.parse_ai_response(response.content[0].text)
    
    def create_extraction_prompt(self, include_desc, include_func, device_type):
        """Create detailed prompt for AI extraction"""
        prompt = """
        Analyze this pinout diagram and extract the pin information in JSON format.
        
        Please provide the data in this exact JSON structure:
        {
            "device_info": {
                "name": "detected device name",
                "package": "detected package type",
                "total_pins": "number of pins"
            },
            "pins": [
                {
                    "pin_number": "pin number",
                    "primary_name": "primary pin name",
                    "alternate_functions": ["function1", "function2", ...],
                    "description": "detailed description if available"
                }
            ]
        }
        
        Instructions:
        1. Identify all visible pins and their numbers
        2. Extract primary pin names/labels
        3. Some Pin names will have a line on top of it, begin the Pin name with # - It represents Active low pin
        """
        
        if include_func:
            prompt += "\n4. Include all alternate functions for each pin"
        
        if include_desc:
            prompt += "\n5. Provide detailed descriptions for each pin function"
        
        if device_type != "Auto-detect":
            prompt += f"\n6. This is a {device_type} pinout diagram"
        
        prompt += """
        
        7. Ensure pin numbers are in correct order
        8. Group related functions together
        9. Use standard abbreviations for common functions (VCC, GND, GPIO, etc.)
        10. Return only valid JSON, no additional text
        """
        
        return prompt
    
    def parse_ai_response(self, response_text):
        """Parse AI response and convert to structured data"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                return data
            else:
                return self.create_fallback_data(response_text)
                
        except json.JSONDecodeError:
            return self.create_fallback_data(response_text)
    
    def create_fallback_data(self, text):
        """Create fallback structured data if JSON parsing fails"""
        lines = text.split('\n')
        pins = []
        
        for line in lines:
            if 'pin' in line.lower() or any(char.isdigit() for char in line):
                parts = line.split()
                if len(parts) >= 2:
                    pins.append({
                        "pin_number": parts[0],
                        "primary_name": parts[1] if len(parts) > 1 else "Unknown",
                        "alternate_functions": parts[2:] if len(parts) > 2 else [],
                        "description": line
                    })
        
        return {
            "device_info": {
                "name": "Unknown Device",
                "package": "Unknown",
                "total_pins": str(len(pins))
            },
            "pins": pins
        }
    
    def display_extraction_results(self, data):
        """Display extracted pinout data"""
        st.subheader("📊 Extraction Results")
        
        if 'device_info' in data:
            device_info = data['device_info']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Device", device_info.get('name', 'Unknown'))
            with col2:
                st.metric("Package", device_info.get('package', 'Unknown'))
            with col3:
                st.metric("Total Pins", device_info.get('total_pins', '0'))
        
        if 'pins' in data and data['pins']:
            pins_data = []
            for pin in data['pins']:
                pins_data.append({
                    'Pin Designator': pin.get('pin_number', ''),
                    'Pin Display Name': pin.get('primary_name', ''),
                    'Pin Alternate Name': '/'.join(pin.get('alternate_functions', [])),
                    'Description': pin.get('description', '')
                })
            
            df = pd.DataFrame(pins_data)
            st.dataframe(df, use_container_width=True)
            
            # Download options
            self.provide_download_options(df, data)
        else:
            st.warning("No pin data extracted")
    
    def provide_download_options(self, df, raw_data):
        """Provide download options for extracted data"""
        col1, col2 = st.columns(2)
            
        with col1:
            # JSON download
            json_str = json.dumps(raw_data, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"pinout_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                type="primary"
            )

        with col2:
            # Excel download
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
        
            st.download_button(
                label="Download Excel",
                data=excel_buffer,
                file_name=f"pinout_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        
        # Continue to Grouping section
        st.markdown("---")
        st.subheader("🔗 Continue to Grouping")
        
        # Extract part number from device info
        part_number = "Unknown"
        if 'device_info' in raw_data:
            part_number = raw_data['device_info'].get('name', 'Unknown')
        
        # Store basic info in session state
        st.session_state.part_number = part_number
        st.session_state.pin_table = df
        pin_count = len(df)
        
        st.write(f"**Part Number:** {part_number}")
        st.write(f"**Pin Count:** {pin_count}")
        st.dataframe(df)
        st.write("**Ready for Grouping 2.0**")

        return part_number, df, pin_count