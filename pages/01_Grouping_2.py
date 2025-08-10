import os
import streamlit as st
import pandas as pd
import json

#import grouping_functions
from Extraction.base_functions import ui_widgets
from Grouping.base_functions import general_funct
from Grouping.base_functions import helper_funct
from Grouping.base_functions import excel_input
from Grouping import Assigning_Electrical_Type , Assigning_Pin_Group


st.set_page_config(page_icon= 'dados/logo_small.png', page_title= "SymbolGen" )

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
#st.markdown(hide_st_style, unsafe_allow_html=True)

ui_widgets.header_intro()
ui_widgets.header_intro_2()

st.subheader("Grouping Page")

if 'pin_table' in st.session_state:
    pin_table = st.session_state['pin_table']

    col1, col2, col3 = st.columns(3)

    # Button 1: Clear Pin Table (Light Blue)
    with col1:
        if st.button("Clear Pin Table", type="secondary"):
            del st.session_state['pin_table']
            st.write("Pin table cleared.")
            st.rerun()

    # Button 2: Remove Electrical Type (Darker Blue)        
    with col2:
        if st.button("Remove Electrical Type", type="secondary"):
            pin_table_without_type, electrical_type_removed = general_funct.remove_electrical_type(pin_table)
            st.session_state['pin_table'] = pin_table_without_type 
            st.session_state['electrical_type_removed'] = electrical_type_removed 


    with col3:
        if st.button("Remove Description", type="secondary"):  # Fixed button text
            pin_table_without_Description, description_removed = general_funct.remove_description_type(pin_table)
            st.session_state['pin_table'] = pin_table_without_Description
            st.session_state['description_removed'] = description_removed  # Store the flag
            

    part_number = st.session_state["part number"]
    if part_number is None:
        st.session_state["part number"] = st.session_state["uploaded_csv_name"]
        part_number = st.session_state["uploaded_csv_name"]
    # Display the part number
    st.write (f"Part Number : **{part_number}**")
    st.write("Pin Table:")
    st.dataframe(st.session_state['pin_table'])
    #st.text(f"Before Pin Grouping Flag :{before_grouping_flag}")
    #st.dataframe(added_empty_grouping_column)
    electrical_type_removed = "Electrical Type" not in st.session_state['pin_table'].columns
    database_for_pin_type = False
    database_for_grouping = False

    if electrical_type_removed:
        # Show this checkbox if "Electrical Type" is removed
        database_for_pin_type = st.checkbox("Use database for pin type")
    else:
        # Show this checkbox if "Electrical Type" is present
        database_for_grouping = st.checkbox("Use database for grouping")

    json_paths = {
        'Input': 'Grouping/mcu_database/mcu_input.json',
        'Power': 'Grouping/mcu_database/mcu_power.json',
        'Output': 'Grouping/mcu_database/mcu_output.json',
        'I/O': 'Grouping/mcu_database/mcu_io.json',
        'Passive': 'Grouping/mcu_database/mcu_passive.json'
    }
    json_paths_Single = {
    'Single': 'Grouping/shrinidhi_database/combined.json'
    }

    if database_for_pin_type:
        st.success("Using database for Type Assignment")
        pin_table = st.session_state['pin_table']
        required_cols = ['Pin Designator', 'Pin Display Name', 'Pin Alternate Name']
        before_pin_type_flag, added_empty_pin_type_column = general_funct.check_excel_format(pin_table, required_cols, optional_column='Electrical Type')
        pin_type_added_table = Assigning_Electrical_Type.pin_type_as_per_database(added_empty_pin_type_column, json_paths, sensitivity=False) 
        st.dataframe(pin_type_added_table)
        st.session_state['pin_table'] = pin_type_added_table
        database_for_grouping = st.checkbox("Use database for grouping")
        
    if database_for_grouping:
        st.success("Using database for grouping")
        pin_table = st.session_state['pin_table']
        required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name']
        before_grouping_flag, added_empty_grouping_column = general_funct.check_excel_format(pin_table,  required_cols, optional_column='Grouping')
        pin_grouping_table = Assigning_Pin_Group.grouping_as_per_database(added_empty_grouping_column, json_paths_Single, SENSITIVITY= False,SMARTSEARCH= False, SINGLE_FILE=True)  

    # Common operations after grouping
        st.dataframe(pin_grouping_table)
        no_grouping_assigned = general_funct.check_empty_groupings(pin_grouping_table)
        
        if no_grouping_assigned.empty:
            st.info("All grouping values are filled.") 
            st.success("Done!")
            st.session_state["page"] = "SideAlloc" 
            st.session_state['grouped_pin_table'] = pin_grouping_table            

        else:

            st.info("Please fill in group values for these:")

            with st.sidebar:
                st.header("Dynamic Database")
                show_suggestions_automatic = st.toggle("Enable Pin Suggestions Automatic")
                show_suggestions_manual = st.toggle("Enable Pin Suggestions Manual")
                threshold = st.slider("Minimum Match Percentage", min_value=80, max_value=100, value=100)
                edit_database = st.toggle("Edit Database", value=False)
                with open(json_paths_Single['Single'], 'r') as f:
                    json_data = json.load(f)

            # Conditionally apply auto-fill logic
            if show_suggestions_automatic:
                no_grouping_assigned = helper_funct.auto_fill_grouping_if_exact_match(no_grouping_assigned, json_data,threshold)

            # Show the editor after applying any suggestions
            edited_df = st.data_editor(no_grouping_assigned)


            if show_suggestions_manual:
                with st.sidebar:
                    with st.expander("Priority Mapping Rules"):
                        st.markdown("""
                        - `after_input` → **Placement After Input Section**
                        - `after_io` → **Placement After IO Section**
                        - `after_output` → **Placement After Output Section**
                        - `after_power+` → **Placement After Power Positive Section**
                        - `after_power-` → **Placement After Power negetive Section**
                        """)

                user_input = st.text_input("Enter Pin Name:")

                if user_input:
                    suggestions = helper_funct.get_suggestions(user_input, json_data)

                    if suggestions:
                        closest_pin, score, group = suggestions[0]
                        st.success(f"Closest Pin: **{closest_pin}** (Match: {score}%)")
                        st.info(f"Group: **{group}**")

                        if len(suggestions) > 1:
                            st.write("Other close matches:")
                            for pin, s_score, s_group in suggestions[1:]:
                                st.write(f"- {pin} (Match: {s_score}%, Group: {s_group})")
                    else:
                        st.warning("No matching pins found.")

            if edit_database:
                json_data_labelled = helper_funct.load_json_files_with_type_labels('mcu_database')
                for index, row in edited_df.iterrows():
                    pin_name = row['Pin Display Name']
                    group_name = row['Grouping']

                    if group_name:  # If Grouping is filled
                        group_found = False
                        for file_path, data in json_data_labelled.items():
                            if group_name in data:  # Check if group exists in this JSON file
                                if pin_name not in data[group_name]:  # Check if pin already exists
                                    data[group_name].append(pin_name)  # Add pin to the group
                                    helper_funct.save_json_file(file_path, data)  # Save updated JSON file
                                    st.markdown(
                                        f"<p style='color: green;'>Pin '{pin_name}' has been added to Group '{group_name}' in '{os.path.basename(file_path)}'.</p>",
                                        unsafe_allow_html=True
                                    )
                                    #st.info(f"Pin '{pin_name}' has been added to Group '{group_name}' in '{os.path.basename(file_path)}'.")
                                else:
                                    st.info(f"Pin '{pin_name}' already exists in Group '{group_name}' in '{os.path.basename(file_path)}'.")
                                group_found = True
                                break  # Exit loop once the group is found

                        if not group_found:  # If group is not found in any JSON file
                            st.warning(f"Group '{group_name}' not found in any JSON file. Skipping update for Pin '{pin_name}'.")
            else:
                print("Edit Database is OFF. No updates will be made to JSON files.")
                #st.info("Edit Database is OFF. No updates will be made to JSON files.")



            if edited_df['Grouping'].isnull().any():
                st.info("Please enter group names for all.")

            else:
                pin_grouping_table.update(edited_df)
                st.header("Final Grouping Table")
                st.dataframe(pin_grouping_table)
                st.success("Done!")
                st.session_state["page"] = "SideAlloc" 
                st.session_state['grouped_pin_table'] = pin_grouping_table 

    else:
        st.info("Please the checkbox for using database")
        pin_grouping_table = pd.DataFrame()                            


    # Check if redirection to "SideAlloc" page is needed
    if "page" in st.session_state and st.session_state["page"] == "SideAlloc":
        st.page_link("pages/02_Side_Allocation.py", label="SideAlloc")
    #else:
        #print("Grouped Pin table displayed") 
        #st.write("Grouped Pin table displayed")           

else:
    st.write("No pin table available.")
    excel_input.handle_file_upload()


