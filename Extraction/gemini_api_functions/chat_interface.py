import PyPDF2
import docx
import re
import streamlit as st
import json

def process_document(uploaded_file):

    def extract_text_from_pdf(file):
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""

    def extract_text_from_docx(file):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {e}")
            return ""

    def extract_text_from_txt(file):
        """Extract text from TXT file"""
        try:
            return str(file.read(), "utf-8")
        except Exception as e:
            st.error(f"Error reading TXT: {e}")
            return ""

    """Process uploaded document and extract text"""
    if uploaded_file is not None:
        file_type = uploaded_file.type
        
        if file_type == "application/pdf":
            return extract_text_from_pdf(uploaded_file)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(uploaded_file)
        elif file_type == "text/plain":
            return extract_text_from_txt(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload PDF, DOCX, or TXT files.")
            return ""
    return ""


########################################

def display_chat_interface_2():
    """
    Display the main chat interface for document Q&A with automatic part number extraction
    and pin table extraction functionality
    """
    # Fixed first prompt (hidden from user)
    FIXED_FIRST_PROMPT = """List out all the Part Numbers and their Pin count and Package as a json from this document
Example:
  {"Part Number": "R7FA2E2A33CNK#AA1", "Pin Count": 24, "Package": "HWQFN"},"""
    
    # Fixed second prompt template (hidden from user)
    FIXED_SECOND_PROMPT_TEMPLATE = """Extract Pin Table from the Document for the Part Number {part_number}. Response should be in json like this Example: {{"Pin Designator" : "A1", "Pin Name": "SWDIO", "Electrical Type": "I/O", "Alternate Pin Names": "P108/AGTOA1_B/GTOULO_C/GTIOC7B_C/TXD9_H/MOSI9_H/SDA9_H/CTS9_RTS9_B/SS9_B/MOSIA_C/IRQ5_C"}}"""
    
    # Initialize session state variables
    if 'part_numbers_list' not in st.session_state:
        st.session_state.part_numbers_list = []
    if 'part_numbers_response' not in st.session_state:
        st.session_state.part_numbers_response = ""
    if 'pin_table_responses' not in st.session_state:
        st.session_state.pin_table_responses = {}
    
    # Step 1: Process document automatically if available (First Prompt - Hidden)
    if (st.session_state.document_content and 
        st.session_state.gemini_model and 
        not st.session_state.part_numbers_response):
        
        with st.spinner("Processing document for part numbers..."):
            response = get_ai_response(FIXED_FIRST_PROMPT, st.session_state.document_content)
            st.session_state.part_numbers_response = response
            st.session_state.part_numbers_list = extract_part_numbers_from_response(response)
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("Upload Renesas Datasheet")
        
        # Display Part Numbers section if we have processed content
        if st.session_state.part_numbers_response:
            st.subheader("📋 Part Number List")
            st.markdown(st.session_state.part_numbers_response)
            st.divider()
        
        # Display pin table responses if any
        if st.session_state.pin_table_responses:
            st.subheader("Pin Table")
            for part_num, response in st.session_state.pin_table_responses.items():
                st.markdown(f"**Part Number: {part_num}**")
                st.markdown(response)
                st.divider()
        
        # Single chat input for part numbers
        if part_number_input := st.chat_input("Enter a part number to get its pin table (e.g., R7FA2E2A33CBY#HC1)..."):
            if not st.session_state.document_content:
                st.error("Please upload a document first!")
            elif not st.session_state.gemini_model:
                st.error("Please configure your Gemini API key first!")
            else:
                # Check if the entered part number exists in our list
                part_number_clean = part_number_input.strip()
                
                # Step 2: Process the part number (Second Prompt - Hidden)
                with st.spinner(f"Extracting pin table for {part_number_clean}..."):
                    second_prompt = FIXED_SECOND_PROMPT_TEMPLATE.format(part_number=part_number_clean)
                    pin_response = get_ai_response(second_prompt, st.session_state.document_content)
                    
                    # Store the response
                    st.session_state.pin_table_responses[part_number_clean] = pin_response
                
                # Rerun to show the new response
                st.rerun()
    
    with col2:
        st.header("📊 Stats")
        if st.session_state.document_content:
            st.metric("Document Length", f"{len(st.session_state.document_content):,} chars")
            st.metric("Words", f"{len(st.session_state.document_content.split()):,}")
            
            # Show part numbers count if available
            if st.session_state.part_numbers_list:
                st.metric("Part Numbers Found", len(st.session_state.part_numbers_list))
            
            # Show pin tables extracted
            if st.session_state.pin_table_responses:
                st.metric("Pin Tables Extracted", len(st.session_state.pin_table_responses))
        else:
            st.info("Upload a Datasheet to see stats")
        
        # Show available part numbers for reference
        if st.session_state.part_numbers_list:
            st.subheader("Available Part Numbers")
            for part_num in st.session_state.part_numbers_list[:5]:  # Show first 5
                st.code(part_num, language=None)
            if len(st.session_state.part_numbers_list) > 5:
                st.caption(f"... and {len(st.session_state.part_numbers_list) - 5} more")
    
    # Footer
    st.divider()

def extract_part_numbers_from_response(response_content):
    """
    Extract part numbers from the AI response content
    Handles both JSON format and plain text format
    """
    part_numbers = []
    
    try:
        # Try to parse as JSON first
        if response_content.strip().startswith('[') or response_content.strip().startswith('{'):
            # Handle JSON array format
            if response_content.strip().startswith('['):
                data = json.loads(response_content)
                for item in data:
                    if isinstance(item, dict) and "Part Number" in item:
                        part_numbers.append(item["Part Number"])
            else:
                # Handle single JSON object format
                data = json.loads(response_content)
                if "Part Number" in data:
                    part_numbers.append(data["Part Number"])
        else:
            # Try to extract part numbers using regex patterns
            patterns = [
                r'R7FA[A-Z0-9]+#[A-Z0-9]+',  # Renesas part number pattern
                r'"Part Number":\s*"([^"]+)"',  # JSON format
                r'Part Number:\s*([A-Z0-9#]+)',  # Plain text format
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response_content, re.IGNORECASE)
                part_numbers.extend(matches)
    
    except (json.JSONDecodeError, KeyError):
        # If JSON parsing fails, try regex extraction
        patterns = [
            r'R7FA[A-Z0-9]+#[A-Z0-9]+',  # Renesas part number pattern
            r'"Part Number":\s*"([^"]+)"',  # JSON format
            r'Part Number:\s*([A-Z0-9#]+)',  # Plain text format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_content, re.IGNORECASE)
            part_numbers.extend(matches)
    
    # Remove duplicates and return
    return list(set(part_numbers))

def get_ai_response(question: str, document_content: str) -> str:
    """Get response from Gemini API"""
    if not st.session_state.gemini_model:
        return "Please configure Gemini API key first."
    
    try:
        prompt = f"""
        Based on the following document content, please answer the question accurately and concisely.
        
        Document Content:
        {document_content[:10000]}  # Limit to first 10k characters
        
        Question: {question}
        
        Answer:
        """
        
        response = st.session_state.gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {e}"