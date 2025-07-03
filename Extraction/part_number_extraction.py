import streamlit as st
from .base_functions import methods

def fetch_part_number_details(input_part_number,input_buffer):
    start_keyword = "part number indexing"
    end_keyword = "symbol pin information"
    part_number_index_pages = methods.find_pages_between_keywords(input_buffer, start_keyword, end_keyword)
    st.text(f'Part Number Indexing pages : {part_number_index_pages}')
    target_columns=["Orderable Part Number", "Number of Pins", "Package", "Package Code/POD Number"]
    detection_keyword="orderable part"
    dfs = methods.table_extraction_logic(input_buffer, part_number_index_pages,target_columns,detection_keyword)
    #dfs = methods.extracting_tables_in_pages(input_buffer, part_number_index_pages)
    st.text(f"Number of PartNumber indexing table(s): {len(dfs)}")

    Before_merging_flag = methods.before_merging(dfs)
    #st.text(f"Before_merging_flag : {Before_merging_flag}")
    if Before_merging_flag:
        merged_df = methods.merge_tables(dfs)
        st.dataframe(merged_df)
        part_number,number_of_pins,package_type,package_code = search_for_part_number_in_the_indexing_table(merged_df, input_part_number)
        if not all(value is not None for value in (part_number, number_of_pins, package_type, package_code)):
            st.text(f" User entered Part Number is not matching, please select one from the below")
            part_number, number_of_pins, package_type, package_code = create_selectbox_for_user_to_select(merged_df)

        st.caption(f"Part Number : {part_number}, Number of Pins: {number_of_pins}, Package: {package_type}, Package Code: {package_code}")
        number_of_pins = int(number_of_pins)
        st.caption(f"Part Info : {number_of_pins} - {package_type}")
        #st.divider()

    return part_number, number_of_pins, package_type, package_code 


def search_for_part_number_in_the_indexing_table(merged_table, part_number):
    #print(f"merged table : {merged_table}")
    part_number_row = merged_table[merged_table['Orderable Part Number'] == part_number]
    if not part_number_row.empty:
        number_of_pins = part_number_row['Number of Pins'].values[0]
        package_type = part_number_row['Package'].values[0]
        package_code = part_number_row['Package Code/POD Number'].values[0]
        return part_number, number_of_pins, package_type, package_code
    else:
        return None, None, None, None
    

def create_selectbox_for_user_to_select(merged_table):
    # Create a formatted dropdown of valid part numbers
    merged_table['Formatted Part Number'] = merged_table.apply(
        lambda row: f"{row['Orderable Part Number']} ({row['Number of Pins']}-{row['Package']})", axis=1
    )

    part_numbers = merged_table['Formatted Part Number'].unique()
    selected_part_number = st.selectbox("Select a part number", part_numbers)

    # Extract the original part number from the selected formatted string
    original_part_number = selected_part_number.split(" ")[0]

    # Search for part number details
    part_number, number_of_pins, package_type, package_code = search_for_part_number_in_the_indexing_table(
        merged_table, original_part_number)
    
    if part_number is not None:
        return part_number, number_of_pins, package_type, package_code
    else:
        st.error("Part number not found.")
            