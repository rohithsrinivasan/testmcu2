import streamlit as st
import pandas as pd
from tabula import read_pdf
import datetime

from Extraction.base_functions import ui_widgets
from Grouping.base_functions import general_funct

from Side_Allocation.base_functions import general_constraints

from Side_Allocation import priority
from Side_Allocation import side
from Side_Allocation import part_division

st.set_page_config(page_icon= 'dados/logo_small.png', page_title= "SymbolGen" )

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
#st.markdown(hide_st_style, unsafe_allow_html=True)

if "part number" in st.session_state:
    part_number = st.session_state["part number"]
if "uploaded_csv_name" in st.session_state:
    input_csv_file_name = st.session_state["uploaded_csv_name"]


ui_widgets.header_intro()
ui_widgets.header_intro_2()


st.sidebar.markdown("### Your Selections")
category = st.session_state.get('selected_category')
sub_category = st.session_state.get('sub_category')
if category:
    st.sidebar.info(f"**Category:** {category}")
    if sub_category:
        st.sidebar.info(f"**Sub-Category:** {sub_category}")

st.subheader("Side Allocation Page")
if 'grouped_pin_table' in st.session_state:
    grouped_pin_table = st.session_state['grouped_pin_table']

    #st.write("Grouped Pin Table:")
    #st.dataframe(grouped_pin_table)


    required_columns = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping']
    optional_column = 'Priority'
    before_priority_flag, added_empty_priority_column = general_funct.check_excel_format(grouped_pin_table,required_columns, optional_column=optional_column)
    st.text(f"Before Side Allocation Flag :{before_priority_flag}")
    st.dataframe(added_empty_priority_column)
    #priority_mapping_json = f"Side_Allocation/priority_map.json"

    #priority_mapping_json_new = f"Side_Allocation\priority_map_mpuadded.json"
    #priority_added = priority.assigning_priority(added_empty_priority_column,priority_mapping_json_new)

    priority_mapping = {
        'MCU Devices': "Side_Allocation/priority_map_mpuadded.json",
        'Power': {
            "Buck": "Side_Allocation/priority_map_buck.json",
            "Boost": "Side_Allocation/priority_map_boost.json",
            "LDO" : "Side_Allocation/priority_map_ldo.json",
            "Buck-Boost": "Side_Allocation/priority_map_buck-boost.json",

        }
    }

    category = st.session_state.get('selected_category')
    #st.text(category)
    if category == 'Power':
        sub_category = st.session_state.get('sub_category')
        priority_file_path = priority_mapping['Power'][sub_category]
    else:
        priority_file_path = priority_mapping['MCU Devices']

    priority_added = priority.assigning_priority(added_empty_priority_column, priority_file_path)

    st.text(f"Priority Column Added")
    st.dataframe(priority_added)

    ### Adding Side ###

    required_columns = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping','Priority']
    ooptional_column = 'Side'
    before_side_flag, added_empty_side_column = general_funct.check_excel_format(priority_added,required_columns, optional_column=optional_column)

    if category == 'MCU Devices' :

        if len(added_empty_side_column) <= 80:
            side_added = side.side_for_singlepart(added_empty_side_column)
            #st.text(f"Side Column Added")
            #st.dataframe(side_added)
        
        else:
            st.text(f"Executing Partioning")
            with st.sidebar:
                st.sidebar.subheader("Customize")

                # Reset to default button
                if st.sidebar.button("Reset to Default"):
                    st.session_state.strict_population = False
                    st.session_state.balanced_assignment = False

                # Initialize session state if not exists
                if 'strict_population' not in st.session_state:
                    st.session_state.strict_population = False
                if 'balanced_assignment' not in st.session_state:
                    st.session_state.balanced_assignment = False

                # Toggle switches
                strict_population = st.sidebar.toggle("Strict Population", value=st.session_state.strict_population,help="Enable strict population mode")
                balanced_assignment = st.sidebar.toggle("Balanced Assignment", value=st.session_state.balanced_assignment,help="Enable balanced assignment mode")

                # Update session state
                st.session_state.strict_population = strict_population
                st.session_state.balanced_assignment = balanced_assignment

            #df_dict = part_division.partitioning(added_empty_side_column, Strict_Population = False, Balanced_Assignment= True)
            df_dict = part_division.partitioning(added_empty_side_column, Strict_Population=st.session_state.strict_population, Balanced_Assignment=st.session_state.balanced_assignment)
            side_added_dict = side.side_for_multipart(df_dict)
            #st.text(f"Side Column Added")
            #for subheader, dataframe in side_added_dict.items():
            #    st.subheader(subheader)
            #    st.dataframe(dataframe)


            #side_added = SideAllocation_functions.convert_dict_to_list(df_dict)
            side_added = side_added_dict


    elif category == "Power":
        # side_added is initialized from the priority_added DataFrame
        side_added = priority_added.copy()

        # Create the 'Side' column and set it to a default value (e.g., None)
        side_added['Side'] = None
        
        # Use .loc to conditionally assign 'Left' and 'Right'
        side_added.loc[side_added['Priority'].str.startswith('L'), 'Side'] = 'Left'
        side_added.loc[side_added['Priority'].str.startswith('R'), 'Side'] = 'Right'



    if isinstance(side_added, pd.DataFrame):
        side_added = general_constraints.final_filter(side_added) 
        st.subheader(f"Smart_Table: ")
        st.dataframe(side_added)  # Display single DataFrame
        #st.success("Side Alloction Done!")

        timestamp = datetime.datetime.now().strftime("%d-%m_%H:%M")
        try:
            filename = f"{part_number}_SmartPinTable_{timestamp}.csv"
        except NameError:
            try:
                filename = f"{input_csv_file_name}_SmartPinTable_{timestamp}.csv"
            except NameError:
                print("Error: File name could not be generated. Please check the variables 'part_number' and 'input_csv_file_name'.")
                filename = "None"           

        st.download_button(
            label="Download Smart Table",
            data=side_added.to_csv(index=False),
            file_name=filename,
            mime='text/csv',
            type="primary"
        )

    # Assuming `side_added` is a dictionary of DataFrames
    elif isinstance(side_added, dict):

        side_added = {k: v for k, v in side_added.items() if not v.empty}

        for key in side_added:
            df = side_added[key]
            df = general_constraints.final_filter(df)   
            side_added[key] = df
            st.markdown(f"<h5>Smart Table: {key}</h5>", unsafe_allow_html=True)
            st.dataframe(df)

        # Prepare the filename
        timestamp = datetime.datetime.now().strftime("%d-%m_%H:%M")
        try:
            filename = f"{part_number}_SmartPinTable_{timestamp}.xlsx"
        except NameError:
            try:
                filename = f"{input_csv_file_name}_SmartPinTable_{timestamp}.xlsx"
            except NameError:
                st.error("Error: File name could not be generated. Please check the variables 'part_number' and 'input_csv_file_name'.")
                filename = None

        if filename:
            # Save to an Excel file with multiple sheets using 'openpyxl'
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for sheet_name, df in side_added.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Read the Excel file as binary to enable download
            with open(filename, 'rb') as f:
                excel_data = f.read()

            # Provide download button for the Excel file
            st.download_button(
                label="Download All",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )


    else:   
        st.text(f"Error Occured in Displaying Dataframes") 
        # testing pyxl features
        
