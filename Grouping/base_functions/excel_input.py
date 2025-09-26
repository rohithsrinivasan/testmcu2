import pandas as pd
import streamlit as st

def load_uploaded_file(uploaded_file):
    """Load CSV or Excel file and return DataFrame"""
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        return df, None
    except Exception as e:
        return None, f"An error occurred while processing the uploaded file: {e}"

def process_pin_dataframe(df, testing_electrical_type=False):
    """Process and clean the pin DataFrame"""
    # Convert column names to lowercase for case-insensitive handling
    df.columns = df.columns.str.lower()
    
    # Define required column mappings
    column_mappings = {
        "designator": "Pin Designator",
        "pin designator": "Pin Designator", 
        "name": "Pin Display Name",
        "Pin Display Name": "Pin Display Name",
        "pin name": "Pin Display Name",
        "electrical": "Electrical Type",
        "electrical type": "Electrical Type",
        "description": "Pin Alternate Name",
        "Pin Alternate Name": "Pin Alternate Name"
    }
    
    # Find and rename matching columns
    new_column_names = {}
    warnings = []
    
    for col in df.columns:
        for key, value in column_mappings.items():
            if col.lower() == key.lower():
                new_column_names[col] = value
    
    if new_column_names:
        df = df.rename(columns=new_column_names)
        warnings.append("Column names were adjusted due to mismatches.")
    
    # Select only required columns
    required_columns = ["Pin Designator", "Pin Display Name", "Electrical Type", "Pin Alternate Name"]
    df = df[[col for col in required_columns if col in df.columns]]
    
    # Filter out unwanted rows
    if "Pin Alternate Name" in df.columns:
        filter_terms = ["renesas", "Cortex", "operation", "Microcontroller"]
        for term in filter_terms:
            df = df[~df["Pin Alternate Name"].apply(lambda x: isinstance(x, str) and term.lower() in x.lower())]

    
    # Handle electrical type testing toggle
    electrical_type_status = ""
    if testing_electrical_type and "Electrical Type" in df.columns:
        df = df.drop(columns=["Electrical Type"])
        electrical_type_status = "'Electrical Type' column has been removed."
    elif "Electrical Type" not in df.columns:
        electrical_type_status = "'Electrical Type' column is not present in the DataFrame."
    else:
        electrical_type_status = "'Electrical Type' column is retained."
    
    # Clean DataFrame
    df = df.dropna(how='all')
    df = df[~df.apply(lambda x: x.astype(str).str.isspace().all() or (x.astype(str) == '').all(), axis=1)]
    df = df.reset_index(drop=True)
    
    return df, warnings, electrical_type_status

def handle_file_upload():
    """Main function to handle file upload UI and processing"""
    uploaded_csv = st.file_uploader("Upload a excel file", type=["csv","xlsx"])
    
    if uploaded_csv is not None:
        # Load file
        df, error = load_uploaded_file(uploaded_csv)
        if error:
            st.error(error)
            st.stop()
        
        st.write("File uploaded successfully.")
        st.session_state["uploaded_csv_name"] = uploaded_csv.name
        st.session_state["part number"] = df.loc[0, 'comment'] if 'comment' in df.columns else None
        
        # Process DataFrame
        testing_electrical_type = st.toggle("Testing Electrical Type", value=False)
        df, warnings, electrical_type_status = process_pin_dataframe(df, testing_electrical_type)
        
        # Display status and warnings
        st.write(electrical_type_status)
        if warnings:
            for warning in warnings:
                st.warning(warning)
        
        # Display results
        st.write("Processed Data:")
        st.dataframe(df)
        
        # Update session state
        st.session_state['pin_table'] = df
        st.write("Pin table uploaded successfully.")
        st.rerun()


########################################################
# 
#             New Addition 
# ###################################################        

import pandas as pd
import streamlit as st
import io

def load_uploaded_file(uploaded_file):
    """Load CSV or Excel file and return DataFrame"""
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        return df, None
    except Exception as e:
        return None, f"An error occurred while processing the uploaded file: {e}"

def process_pin_dataframe(df, testing_electrical_type=False):
    """Process and clean the pin DataFrame"""
    # Convert column names to lowercase for case-insensitive handling
    df.columns = df.columns.str.lower()
    
    # Define required column mappings
    column_mappings = {
        "designator": "Pin Designator",
        "pin designator": "Pin Designator", 
        "name": "Pin Display Name",
        "Pin Display Name": "Pin Display Name",
        "pin name": "Pin Display Name",
        "electrical": "Electrical Type",
        "electrical type": "Electrical Type",
        "description": "Pin Alternate Name",
        "Pin Alternate Name": "Pin Alternate Name"
    }
    
    # Find and rename matching columns
    new_column_names = {}
    warnings = []
    
    for col in df.columns:
        for key, value in column_mappings.items():
            if col.lower() == key.lower():
                new_column_names[col] = value
    
    if new_column_names:
        df = df.rename(columns=new_column_names)
        warnings.append("Column names were adjusted due to mismatches.")
    
    # Select only required columns
    required_columns = ["Pin Designator", "Pin Display Name", "Electrical Type", "Pin Alternate Name"]
    df = df[[col for col in required_columns if col in df.columns]]
    
    # Filter out unwanted rows
    if "Pin Alternate Name" in df.columns:
        filter_terms = ["renesas", "Cortex", "operation", "Microcontroller"]
        for term in filter_terms:
            df = df[~df["Pin Alternate Name"].apply(lambda x: isinstance(x, str) and term.lower() in x.lower())]

    
    # Handle electrical type testing toggle
    electrical_type_status = ""
    if testing_electrical_type and "Electrical Type" in df.columns:
        df = df.drop(columns=["Electrical Type"])
        electrical_type_status = "'Electrical Type' column has been removed."
    elif "Electrical Type" not in df.columns:
        electrical_type_status = "'Electrical Type' column is not present in the DataFrame."
    else:
        electrical_type_status = "'Electrical Type' column is retained."
    
    # Clean DataFrame
    df = df.dropna(how='all')
    df = df[~df.apply(lambda x: x.astype(str).str.isspace().all() or (x.astype(str) == '').all(), axis=1)]
    df = df.reset_index(drop=True)
    
    return df, warnings, electrical_type_status

def handle_file_upload():
    """Main function to handle file upload UI and processing"""
    
    st.write("Upload File or Paste Table Data")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["Upload Excel/CSV", "Paste Clipboard Data"])

    with tab1:
        uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
        if uploaded_file:
            df, error = load_uploaded_file(uploaded_file)
            if error:
                st.error(error)
                st.stop()
            process_and_display(df, uploaded_file.name)
    
    with tab2:
        clipboard_data = st.text_area("Paste your table data here (e.g., from Excel)", height=250, help="Paste tab-separated or comma-separated data. The first line should be the header.")
        if st.button("Process Pasted Data"):
            if clipboard_data:
                # Use io.StringIO to treat the string as a file
                df = pd.read_csv(io.StringIO(clipboard_data), sep='\t')
                process_and_display(df, "Clipboard Data")
            else:
                st.warning("Please paste data into the text area first.")

def process_and_display(df, source_name):
    """Helper function to process and display the dataframe."""
    st.write(f"Data from '{source_name}' loaded successfully.")
    
    # Get part number if available
    st.session_state["part number"] = df.loc[0, 'comment'] if 'comment' in df.columns else None
    
    # Process DataFrame
    testing_electrical_type = st.toggle("Testing Electrical Type", value=False)
    df, warnings, electrical_type_status = process_pin_dataframe(df, testing_electrical_type)
    
    # Display status and warnings
    st.write(electrical_type_status)
    if warnings:
        for warning in warnings:
            st.warning(warning)
    
    # Display results
    st.write("Processed Data:")
    st.dataframe(df)
    
    # Update session state
    st.session_state['pin_table'] = df
    st.session_state["uploaded_csv_name"] = source_name
    st.write("Pin table uploaded successfully.")
    st.rerun()
