import pdfplumber
import pandas as pd
import tabula
import numpy as np
import streamlit as st

def find_pages_between_keywords(pdf_path, start_keyword, end_keyword):
    with pdfplumber.open(pdf_path) as pdf:
        start_page, end_page = None, None
        # Iterate through all the pages in the PDF
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text().lower()
            
            # Update the start_page to the latest occurrence of the start_keyword
            if start_keyword in text:
                start_page = page_num
            
            # Update the end_page to the latest occurrence of the end_keyword
            if end_keyword in text:
                end_page = page_num

        # Return a list containing the page numbers from start_page to end_page
        if start_page and end_page:
            # If start_page and end_page are the same, return that single page
            if start_page == end_page:
                return [start_page]
            else:
                return list(range(start_page, end_page + 1))  # inclusive of end_page
        else:
            return []
        

def table_extraction_logic(file_path, my_list_of_pages, target_columns, detection_keyword):
    """
    Extract tables from a PDF and match by keyword and structure.
    Args:
        file_path: PDF file path or buffer
        my_list_of_pages: List or range of pages (e.g., '1-3')
        target_columns: List of expected column names OR single string for auto-assignment
        detection_keyword: Keyword to look for in combined column headers
    Returns:
        List of matched and cleaned DataFrames
    """
    
    try:
        dfs = tabula.read_pdf(
            file_path,
            pages=my_list_of_pages,
            multiple_tables=True,
            lattice=True,
            encoding='ISO-8859-1'
        )
    except Exception as e:
        st.error(f"📄 Error reading PDF: {e}")
        return []
    
    dfs = [df for df in dfs if not df.empty and df.dropna(how='all').shape[0] > 0]
    st.write(f"📄 Found {len(dfs)} non-empty tables.")
    
    modified_dfs = []
    
    for i, df in enumerate(dfs):
        df = df.replace(to_replace=r'^Unnamed:.*', value=np.nan, regex=True)
        
        # Handle completely unnamed headers
        if all(df.columns.to_series().astype(str).str.contains('^Unnamed')):
            df = df.dropna(how='all')
            if not df.empty:
                df.columns = df.iloc[0]
                df = df[1:]
        
        # Store original cleaned column names
        df.columns = [str(col).strip() for col in df.columns]
        filtered_cols = [col for col in df.columns if pd.notna(col) and "Unnamed" not in col]
        column_string = ''.join(filtered_cols).lower()
        
        # Flatten rows (removes NaNs and shifts left)
        df = df.apply(lambda row: pd.Series(row.dropna().values), axis=1)
        df = df.map(lambda x: int(x) if isinstance(x, float) and x.is_integer() else x)
        
        # Check if keyword is detected
        if detection_keyword.lower() in column_string:
            # Assign column names
            if df.shape[1] == len(target_columns):
                df.columns = target_columns
            else:
                df.columns = [f"Column_{j+1}" for j in range(df.shape[1])]
            
            modified_dfs.append(df)
            print(f"✅ Table {i + 1} matched: Shape = {df.shape}")
            
            # Reassign target columns if shape matches
            if df.shape[1] == len(target_columns):
                df.columns = target_columns
                print (f"🔧 Applied target column names :{str(target_columns)}")
                
        else:
            print(f"⚠️ Table {i + 1} skipped: Keyword not found")
    
    st.write(f"🎯 Extracted {len(modified_dfs)} matching table(s).")
    return modified_dfs



def before_merging(dfs):
    if not dfs:
        return False 
    
    if len(dfs) > 1:
        column_names = [df.columns.tolist() for df in dfs]
        if len(set(map(tuple, column_names))) != 1:
            return False 
    return True


def merge_tables(dfs):
        merged_df = pd.concat(dfs, ignore_index=True)
        return merged_df
    