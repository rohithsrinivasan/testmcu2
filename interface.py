import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image


from Extraction.base_functions import ui_widgets
from Extraction.gemini_api_functions import setup
from Extraction.gemini_api_functions import chat_interface
from Extraction.gemini_api_functions import pinout_reader
from Extraction import part_number_extraction
from Extraction import pin_table_extraction
from Extraction import fetch_from_url

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

st.set_page_config(page_icon= 'dados/logo_small.png', page_title= "SymbolGen" )

st.page_link("interface.py", label="Extraction")
st.page_link("pages/01_Grouping_2.py", label="Grouping 2.0")
st.page_link("pages/02_Side_Allocation.py", label="SideAlloc")
st.page_link("pages/03_Parameters.py", label="Parameters")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
#st.markdown(hide_st_style, unsafe_allow_html=True)

ui_widgets.renesas_logo()
ui_widgets.header_intro() 
ui_widgets.header_intro_2()

# File uploader
if "input_buffer" not in st.session_state:
    st.session_state.input_buffer = None

input_buffer = None

input_method = st.radio("Choose input method:", ["Upload File", "Enter URL"])

if input_method == "Upload File":
    input_buffer = st.file_uploader("Upload a file", type=("PDF"))
else:
    pdf_url = st.text_input("Enter PDF URL:")
    if pdf_url and st.button("Load PDF from URL"):
        # Add URL validation and PDF fetching logic here
        input_buffer = fetch_from_url.fetch_pdf_from_url(pdf_url) 

if input_buffer:
    st.session_state.input_buffer = input_buffer  # Store in session state

# Optionally, add a clear button to reset session state
if st.button("Clear Inputs"):
    st.session_state.input_buffer = None
    st.session_state.part_number = None
    st.session_state.pin_table = None
    st.rerun()

# Toggle for Gemini API
use_ai_extraction = st.toggle("Use Gemini API for extraction")
pinout_read = st.toggle("Read From Pinout Diagram")
# Part number input
if "part_number" not in st.session_state:
    st.session_state.part_number = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'document_content' not in st.session_state:
    st.session_state.document_content = ""
if 'gemini_model' not in st.session_state:
    st.session_state.gemini_model = None

if st.session_state.input_buffer:
    if not (use_ai_extraction or pinout_read):
        input_part_number = st.text_input("Enter a valid Part Number", value=st.session_state.part_number or "")
        with st.spinner('Processing...'):
            part_number, number_of_pins, package_type, package_code = part_number_extraction.fetch_part_number_details(
                input_part_number, st.session_state.input_buffer
            )
            st.session_state["part number"] = part_number
            pin_table = pin_table_extraction.extracting_pin_tables(
                st.session_state.input_buffer, part_number, number_of_pins, package_type, package_code
            )
            st.success("Done!")

        # Store values in session state
        st.session_state.part_number = part_number
        st.session_state.pin_table = pin_table

        if "page" in st.session_state and st.session_state["page"] == "grouping":
            st.page_link("pages/01_Grouping_2.py", label="Grouping 2.0")
        else:
            st.write("Pin table displayed")

    elif use_ai_extraction:
        api_key = setup.get_and_validate_api_key()
    # Document upload
        with st.spinner("Processing document..."):
            if api_key and not st.session_state.gemini_model:
                if setup.setup_gemini(api_key):
                    print("✅ Gemini API configured!")
            document_text = chat_interface.process_document(input_buffer)
            if document_text:
                st.session_state.document_content = document_text
                st.success(f"✅ Document processed! ({len(document_text)} characters)")               
                # Show document preview
                with st.expander("📄 Document Preview"):
                    st.text_area("Content preview:", document_text[:1000] + "...", height=200, disabled=True)

            # Add the chat interface
            chat_interface.display_chat_interface_2()

    else:
        st.warning("Please enter a valid Part Number.")

else:
    st.info("Please upload a PDF file.")

if pinout_read:
    # Initialize extractor
    extractor = pinout_reader.PinoutExtractor()

    # Initialize session state
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 'capture'
    
    # Sidebar navigation
    st.sidebar.title("AI Extractor")
    
    # Stage selection
    stage = st.sidebar.radio(
        "Select Stage:",
        ["Step 1: upload", "Step 2: Extract"],
        index=0 if st.session_state.current_stage == 'capture' else 1
    )
    
    # Update current stage based on selection
    if "Step 1" in stage:
        st.session_state.current_stage = 'capture'
    elif "Step 2" in stage:
        st.session_state.current_stage = 'extract'
    
    # Display current stage info
    st.sidebar.markdown("---")
    st.sidebar.info(f"**Current Stage:** {st.session_state.current_stage.title()}")
        
    # Main content based on stage
    if st.session_state.current_stage == 'capture':
        extractor.upload_screenshot()
    elif st.session_state.current_stage == 'extract':
        extractor.extract_pinout_data()

        if "page" in st.session_state and st.session_state["page"] == "grouping":
            st.page_link("pages/01_Grouping_2.py", label="Grouping 2.0")




    
    
