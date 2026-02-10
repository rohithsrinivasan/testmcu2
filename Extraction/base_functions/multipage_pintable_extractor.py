import pdfplumber
import re
#import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io

def find_table_starting_and_stopping_based_on_pin_string(pdf_path, page_number_list, pin_keyword, package_keyword):

    with pdfplumber.open(pdf_path) as pdf:
        for page_number in page_number_list:
            if page_number > len(pdf.pages):
                print(f"Skipping page {page_number} - exceeds total number of pages ({len(pdf.pages)})")
                continue

            text = pdf.pages[page_number - 1].extract_text()

            matching_lines = [line for line in text.split('\n')
                            if pin_keyword.lower() in line.lower() and package_keyword.lower() in line.lower()]

            if matching_lines and len(matching_lines[0].split(" ")) == 2:
                for line in matching_lines:
                    words = line.split()
                    if len(words) == 2 and re.match(r'^[A-Z0-9]\.\d+\.\d+$', words[0]):
                        section_number = words[0]
                        sections = section_number.split('.')
                        sections[-1] = str(int(sections[-1]) + 1)
                        next_section_number = '.'.join(sections)

                        new_next_section_number, ending_page_number = find_ending_page(pdf, page_number_list, next_section_number)

                        return page_number, section_number, new_next_section_number, ending_page_number

    # Add this block before returning None
    st.write(f"Keyword '{pin_keyword}' or '{package_keyword}' not found in pages. Checking embedded Excel...")
    found, excel_name = check_keywords_in_embedded_excel(pdf_path, pin_keyword, package_keyword)
    if found:
        return "EMBEDDED_EXCEL", excel_name, None, None
    
    st.write(f"Keywords not found in PDF or embedded Excel.")
    return None, None, None, None


def find_ending_page(pdf, page_number_list, next_section_number):
    next_section_number = next_section_number.lower()

    for page_num in page_number_list:
        if page_num <= 0:
            continue
        text = pdf.pages[page_num - 1].extract_text().lower()
        if next_section_number in text:
            return next_section_number.upper(), page_num

    print(f"'{next_section_number}' not found in specified pages. Using 'Symbol Parameters' as ending point.")
    return "Symbol Parameters", page_number_list[-1]

def generate_list_of_page_numbers(start, end):
  if start > end:
    return None  # Invalid input: start > end

  return list(range(start, end + 1))

def text_filter(input_string):
    lines = input_string.splitlines()
    filtered_lines = [line for line in lines if not (line.startswith('Pin') or line.startswith('Designator') or line.startswith('Name'))]

    return '\n'.join(filtered_lines)


def extract_table_as_text(pdf_path, page_number_list, start_string, ending_string):
    with pdfplumber.open(pdf_path) as pdf:
        texts = []
        capturing = False
        extracted_text = ""
        
        for page_number in page_number_list:
            if page_number > len(pdf.pages):
                continue
            page = pdf.pages[page_number - 1]
            text = page.extract_text()
            
            if text:
                if capturing:
                    end_index = text.find(ending_string)
                    if end_index != -1:
                        extracted_text += text[:end_index + len(ending_string)]
                        texts.append(extracted_text)
                        capturing = False
                        extracted_text = ""
                    else:
                        extracted_text += text
                if start_string in text and not capturing:
                    start_index = text.find(start_string)
                    extracted_text = text[start_index:]
                    capturing = True
                    end_index = text.find(ending_string, start_index)
                    if end_index != -1:
                        extracted_text = text[start_index:end_index + len(ending_string)]
                        texts.append(extracted_text)
                        capturing = False
                        extracted_text = ""
        
        if capturing:
            texts.append(extracted_text)
        
        return "\n".join(texts) if texts else None
    

def combine_dataframes_and_print_dictionary(dfs):

    def df_to_string(df):
        string_representation = ""
        for index, row in df.iterrows():
            row_string = " ".join(str(value) for value in row)
            string_representation += row_string + "\n"
        return string_representation 
    
    # Create a dictionary of DataFrame indices and their string representations
    df_strings = {i + 1: df_to_string(df) for i, df in enumerate(dfs)}

    # Generate all possible combinations of DataFrame indices and combine their text
    combo_dict = {}
    for i in range(len(df_strings)):
        for j in range(i + 1, len(df_strings) + 1):
            combo_keys = tuple(range(i + 1, j + 1))
            combo_values = "\n".join([df_strings[k] for k in combo_keys])
            combo_dict[combo_keys] = combo_values

    num = len (combo_dict)    
    return combo_dict, num


def filter_top_3_by_size(combo_dict, input_string):
    size_diffs = {combo_keys: abs(len(combo_value) - len(input_string)) 
                  for combo_keys, combo_value in combo_dict.items()}
    sorted_size_diffs = dict(sorted(size_diffs.items(), key=lambda x: x[1]))
    top_3 = {k: sorted_size_diffs[k] for k in list(sorted_size_diffs)[:3]}  
    return top_3

def filter_combo_dict_based_on_size_filter(dict1, dict2):
    # Retain only the key-value pairs in dict1 if the key is also present in dict2
    filtered_dict = {key: dict1[key] for key in dict2 if key in dict1}
    return filtered_dict

def compare_input_string_with_value_string(input_dict, input_string):
    input_lines = set(input_string.splitlines())
    result = {}

    for key, value_string in input_dict.items():
        value_lines = set(value_string.splitlines())
        extra_lines = max(abs(len(value_lines - input_lines)), abs(len(input_lines - value_lines)))
        result[key] = extra_lines

    '''min_key = min(result, key=result.get)
    return result, min_key'''

    min_value = min(result.values())
    min_keys = [key for key, value in result.items() if value == min_value]

    if len(min_keys) > 1:
        # If multiple keys have the same minimum difference, choose the shortest key
        min_key = min(min_keys, key=lambda k: len(str(k)))
    else:
        min_key = min_keys[0]

    return result, min_key


def get_dataframes_from_tuple(dataframes_list, index_tuple):

    if any(i > len(dataframes_list) or i < 1 for i in index_tuple):
        raise IndexError("Index out of range of DataFrame list.")

    selected_dataframes = [dataframes_list[i-1] for i in index_tuple]
    number = len(selected_dataframes)
    
    return selected_dataframes, number


############################################################



def extract_tables_in_these_pages(input_buffer, page_numbers):
  all_tables = []
  with pdfplumber.open(input_buffer) as pdf:
    for page_num in page_numbers:
      try:
        page = pdf.pages[page_num - 1]  # Access by 0-based indexing
        tables = page.extract_tables()
        all_tables.extend(tables)  # Add extracted tables to the list
      except IndexError:
        print(f"Error: Page {page_num} not found in the PDF.")

  return all_tables


def find_page_range(pdf_file, start_string, end_string):

  page_numbers = []
  found_start = False

  for page_num, page in enumerate(pdf_file.pages):
    text = page.extract_text()
    if found_start:
      if end_string in text:
        break
      page_numbers.append(page_num + 1)

    if start_string in text:
      found_start = True
      page_numbers.append(page_num + 1)

  return page_numbers if page_numbers else None


def merge_parameter_tables(tables):
    if not tables:
        return None

    merged_table = []
    header_row = None

    for table in tables:
        if not table:
            continue

        if not header_row:
            header_row = table[0]
            merged_table.append(header_row)

        for row in table[1:]:
            merged_table.append(row)

    # Convert the merged table to a DataFrame
    df = pd.DataFrame(merged_table[1:], columns=merged_table[0])
    return df



def remove_rows_with_more_empty_values(df, threshold=8):
    # Check if column names are numeric (e.g., 0, 1, 2, ...)
    if all(isinstance(col, int) for col in df.columns):
        # Replace column names with the first row
        df.columns = df.iloc[0]
        # Drop the first row (since it's now the column names)
        df = df.drop(df.index[0]).reset_index(drop=True)

    # Count the number of missing values in each row
    empty_counts = df.isnull().sum(axis=1)

    # Filter rows with more empty values than the threshold
    filtered_df = df[empty_counts <= threshold]
    return filtered_df

def check_keywords_in_embedded_excel(pdf_path, pin_keyword, package_keyword):
    """Check if keywords exist in embedded Excel attachments in PDF"""
    
    if isinstance(pdf_path, io.BytesIO):
        pdf_path.seek(0)
        doc = fitz.open(stream=pdf_path.read(), filetype="pdf")
        pdf_path.seek(0)
    else:
        doc = fitz.open(pdf_path)
    
    # Step 1: Get all attachments
    attachment_list = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        annots = page.annots()
        if annots:
            for annot in annots:
                if annot.type[0] == 17:  # FileAttachment type
                    file_info = annot.file_info
                    file_name = file_info.get('filename', 'Unknown')
                    file_content = annot.get_file()
                    attachment_list.append((page_num + 1, file_name, file_content))
    
    doc.close()
    
    if not attachment_list:
        st.write("⚠️ No file attachments found.")
        return False, None
    
    # Step 2: Filter Excel files that START WITH "EDI"
    edi_excel_files = [
        (page, name, content) 
        for page, name, content in attachment_list 
        if name.endswith(('.xlsx', '.xls')) and name.startswith('EDI')
    ]
    
    if not edi_excel_files:
        st.write("⚠️ No Excel files starting with 'EDI' found.")
        return False, None
    
    # Step 3: Auto-select if only 1 file, otherwise show checkboxes
    if len(edi_excel_files) == 1:
        # ✅ AUTO-SELECT: Only 1 EDI Excel file
        selected_file = edi_excel_files[0]
        st.write(f"📄 Auto-selected: **{selected_file[1]}** (Page {selected_file[0]})")
    else:
        # ✅ MULTIPLE FILES: Let user choose
        st.write("Select an Excel file to search:")
        
        selected_file = None
        for i, (page, file_name, content) in enumerate(edi_excel_files):
            if st.checkbox(f"Page {page}: {file_name}", key=f"edi_cb_{i}"):
                selected_file = (page, file_name, content)
                break  # Take first selected
        
        # If nothing selected, stop and wait
        if selected_file is None:
            st.info("👆 Select an Excel file to continue")
            st.stop()
    
    # Step 4: Process selected file
    page, file_name, file_content = selected_file
    search_keyword = f"{pin_keyword}{package_keyword}"
    
    st.write(f"🔍 Searching for: **{search_keyword}** in **{file_name}**")
    
    try:
        xls = pd.ExcelFile(io.BytesIO(file_content))
        st.write(f"Available sheets: {xls.sheet_names}")
        
        # Search for matching sheet
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
            if df.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False, na=False)).any().any():
                st.write(f"✅ Found in sheet: **{sheet}**")
                df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
                
                # Find and set header row
                header_keywords = ["Primary Pin Name", "Primary Electrical Type", "Pin Number"]
                header_row = None
                for idx, row in df.iterrows():
                    if any(keyword in str(cell) for cell in row for keyword in header_keywords):
                        header_row = idx
                        break
                
                if header_row is not None:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
                
                # change header to these before printing df : ["Pin Designator", "Pin Display Name", "Electrical Type", "Pin Alternate Name"]
                df.columns = ["Pin Designator", "Pin Display Name", "Electrical Type", "Pin Alternate Name"]
                st.dataframe(df)
                return True, df  # ✅ SUCCESS
        
        st.write(f"❌ Keyword '{search_keyword}' not found in any sheet")
        
    except Exception as e:
        st.error(f"Error processing {file_name}: {e}")
    
    return False, None