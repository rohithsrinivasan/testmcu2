import pdfplumber
import pandas as pd
#import tabula
#import streamlit as st
import tempfile 
#import subprocess
#import os, sys
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

    print("Extracting tables from PDF...", file_path)
    #  # Create a temporary file for storing the extracted DataFrame
    # with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
    #     tmp_path = tmp.name
    # # tmp_path is the filename you should pass to both your subprocess script and later for pd.read_pickle()

   
    # print("Console encoding:", sys.stdout.encoding)
    # pages_str = ",".join(str(page) for page in my_list_of_pages)
    # env = os.environ.copy()
    # env["PYTHONUTF8"] = "1"  # force UTF-8 mode

    # try:
    #     res = subprocess.run(
    #         [sys.executable, 'extract_pdf_tables.py', file_path, pages_str,  tmp_path],
    #         capture_output=True, 
    #         env = env,
    #         encoding="utf-8", 
    #         timeout=120)
    #     if res.returncode != 0:
    #         # Could not extract
    #         print(res.stderr)
    #         return []
    #     print("STDOUT:", res.stdout)
    #     print("STDERR:", res.stderr)
    #     print("RETURN CODE:", res.returncode)
    #     dfs = pd.read_pickle(tmp_path)
      
    # except Exception as e:
    #     print("Subprocess failed:", e)
    #     return []
    # try:
    #     dfs = tabula.read_pdf(
    #         file_path,
    #         pages=my_list_of_pages,
    #         multiple_tables=True,
    #         lattice=True,
    #         encoding='ISO-8859-1'
    #     )
    #     print("Extracted tables:", len(dfs))
    # except Exception as e:
    #     print("Error reading PDF:", e)
    #     #st.error(f"📄 Error reading PDF: {e}")
    #     return []
    # print("yes")
    dfs = []
    try:
        with pdfplumber.open(file_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"PDF opened successfully with {num_pages} pages.")
            for page_num in range(num_pages):
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        df = pd.DataFrame(table[1:], columns=table[0])
                    
                        dfs.append(df)
        
            dfs = [df for df in dfs if not df.empty and df.dropna(how='all').shape[0] > 0]
              
        print("Extracted non empty tables:", len(dfs))
    except Exception as e:
        print("Error reading PDF:", e)
        #st.error(f"📄 Error reading PDF: {e}")
        return []
    print("yes")
    #st.write(f"📄 Found {len(dfs)} non-empty tables.")
    
    modified_dfs = []
    nan = float('nan')
    for i, df in enumerate(dfs):
        df = df.replace(to_replace=r'^Unnamed:.*', value=nan, regex=True)
        
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
    
    #st.write(f"🎯 Extracted {len(modified_dfs)} matching table(s).")
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
    