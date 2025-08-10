import streamlit as st

from .base_functions import methods
from .base_functions import multipage_pintable_extractor


def extracting_pin_tables(file_path, part_number, number_of_pins, package_type, package_code):
    #pin_string = f"{number_of_pins}-{package_type}"
    start_keyword = "symbol pin information"
    end_keyword = "symbol parameters"
    pin_configuration_pages  = methods.find_pages_between_keywords(file_path, start_keyword, end_keyword)
    #st.text(f'Pin Configuration Pages : {pin_configuration_pages}')
    pin_string = f"{number_of_pins}-"
    package_string = f"{package_type}"
    table_starting_page_number, table_start_string, table_stop_string, table_ending_page_number = multipage_pintable_extractor.find_table_starting_and_stopping_based_on_pin_string(file_path, pin_configuration_pages, pin_string, package_string)
    st.text(f"Starting Page Number : {table_starting_page_number}, Table Starting Section : {table_start_string}, Table Stopping Section : {table_stop_string} , Ending Page Number : {table_ending_page_number}" )
    pin_table_pages = multipage_pintable_extractor.generate_list_of_page_numbers(table_starting_page_number, table_ending_page_number)
    # Use these dfs as tables
    target_columns=['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name']
    detection_keyword="elect"
    st.text(f"Pin Table Pages : {pin_table_pages}")
    dfs = methods.table_extraction_logic(file_path, pin_table_pages,target_columns,detection_keyword)
    #for df in dfs:
    #    st.dataframe(df)
    # Use these dfs as text
    extracted_table_as_text = multipage_pintable_extractor.extract_table_as_text(file_path, pin_table_pages, table_start_string,table_stop_string )
    page_numbers = multipage_pintable_extractor.generate_list_of_page_numbers(table_starting_page_number,table_ending_page_number)
    #st.image(file_path, pages=page_numbers)
    table_as_text = multipage_pintable_extractor.text_filter(extracted_table_as_text)
    #st.text_area(f" Table as text : \n {table_as_text}")
    # Creating combinatios of tablesas strings
    combo_dict, num = multipage_pintable_extractor.combine_dataframes_and_print_dictionary(dfs)
    top_3_combinations = multipage_pintable_extractor.filter_top_3_by_size(combo_dict, table_as_text)
    #st.text(top_3_combinations)
    reduced_combo_dict  = multipage_pintable_extractor.filter_combo_dict_based_on_size_filter(combo_dict, top_3_combinations)
    #st.text(reduced_combo_dict)
    noise_calculation_combo_dict, min_key = multipage_pintable_extractor.compare_input_string_with_value_string(reduced_combo_dict, table_as_text)
    #st.text(f"Mapping After noise filter Algo : {noise_calculation_combo_dict}")
    #st.text(min_key)
    final_pin_tables_to_be_merged, number= multipage_pintable_extractor.get_dataframes_from_tuple(dfs, min_key)
    #st.text(f" Number of Selected Dataframes : {number}")
    Before_merging_flag  = methods.before_merging(final_pin_tables_to_be_merged)
    #st.text(f"Before Merging Flag : {Before_merging_flag}")
    if Before_merging_flag:
        merged_df = methods.merge_tables(final_pin_tables_to_be_merged)
        st.header(f"\nExtracted Pin Table")
        merged_df = st.data_editor(merged_df) 
        #st.write("Page Preview:")
        #binary_data = file_path.getvalue()
        #pdf_viewer(binary_data, pages_to_render = page_numbers)                      

        #create_navigation_button(merged_df)
        st.session_state["page"] = "grouping"    

    return merged_df