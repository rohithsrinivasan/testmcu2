import streamlit as st
import pandas as pd
from tabula import read_pdf
import datetime
import re

from Extraction.base_functions import ui_widgets

from Grouping.base_functions import general_funct
from Grouping.base_functions import excel_input

from Side_Allocation.base_functions import general_constraints
from Side_Allocation.base_functions import single80pin_constraints
from Side_Allocation.base_functions import four_sided_symbol
from Side_Allocation.base_functions.symbol_viewer import DataHandler as SymbolDataHandler, SymbolRenderer
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
    #st.text(f"Before Side Allocation Flag :{before_priority_flag}")
    #st.dataframe(added_empty_priority_column)
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
            "Charge-Pump": "Side_Allocation/priority_map_charge-pump.json",
            "FlyBack" : "Side_Allocation/priority_map_flyback.json",
            "Battery-Charger-IC" : 'Side_Allocation/priority_map_battery-charger-IC.json',
            "PWM-Controller" : 'Side_Allocation/priority_map_pwm-controller.json',
            "Volatge-References" : 'Side_Allocation/priority_map_voltage-references.json',
            "Power-Supply-Support" : 'Side_Allocation/priority_map_power-supply-support.json',
            "FET-Drivers" : 'Side_Allocation/priority_map_fet-drivers.json',
            "Battery-Protectors-Monitors-Balancers" :"Side_Allocation/priority_map_Battery-Protectors-Monitors-Balancers.json",
            "LED-Drivers" : "Side_Allocation/priority_map_led-drivers.json",

            "DC-DC-Power-Modules":"Side_Allocation/priority_map_dc-dc-power-modules.json",
            "Multiphase-DC-DC-Switching Controllers":"Side_Allocation/priority_map_multiphase-dcdc-switching-controllers.json",
            "ORing-FET-Controllers":"Side_Allocation/priority_map_oring-fet-controllers.json",
            "Protected-Intelligent-Power-Devices":"Side_Allocation/priority_map_protected-intelligent-power-devices.json",
            "Smart-Power-Stages":"Side_Allocation/priority_map_smart-power-stages.json",
            "Solid-State-Lighting-Interface-Ics":"Side_Allocation/priority_map_solid-state-lightening-interface-ics.json",

            "AC-DC & Isolated DC-DC Converters":"Side_Allocation/priority_map_ac-dc&isolated-dc-dc-converters.json",
            "USB Type-C Port Manager":"Side_Allocation/priority_map_usb-type-c-port-manager.json",
            "PMIC": 'Side_Allocation/priority_map_PMIC.json'
        }
    }
    mpu_splitting = "Side_Allocation/mpu_splitting.json"

    category = st.session_state.get('selected_category')
    #st.text(category)
    if category == 'Power':
        sub_category = st.session_state.get('sub_category')
        priority_file_path = priority_mapping['Power'][sub_category]
    else:
        priority_file_path = priority_mapping['MCU Devices']

    priority_added = priority.assigning_priority(added_empty_priority_column, priority_file_path)

    #st.text(f"Priority Column Added")
    #st.dataframe(priority_added)

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
                if 'MPU_type' not in st.session_state:
                    st.session_state.MPU_type= False

                # Toggle switches
                strict_population = st.sidebar.toggle("Strict Population", value=st.session_state.strict_population,help="Enable strict population mode")
                balanced_assignment = st.sidebar.toggle("Balanced Assignment", value=st.session_state.balanced_assignment,help="Enable balanced assignment mode")
                MPU_type = st.sidebar.toggle("MPU Type", value=st.session_state.MPU_type, help= "Split tables based on Functional Grouping")

                # Update session state
                st.session_state.strict_population = strict_population
                st.session_state.balanced_assignment = balanced_assignment
                st.session_state.MPU_type = MPU_type

            #df_dict = part_division.partitioning(added_empty_side_column, Strict_Population = False, Balanced_Assignment= True)
            df_dict = part_division.partitioning(added_empty_side_column,mpu_splitting, Strict_Population=st.session_state.strict_population, Balanced_Assignment=st.session_state.balanced_assignment , MPU_type = st.session_state.MPU_type )
            side_added_dict = side.side_for_multipart(df_dict)
            #st.text(f"Side Column Added")
            #for subheader, dataframe in side_added_dict.items():
            #    st.subheader(subheader)
            #    st.dataframe(dataframe)


            #side_added = SideAllocation_functions.convert_dict_to_list(df_dict)
            side_added = side_added_dict


    # elif category == "Power":
    #     # side_added is initialized from the priority_added DataFrame
    #     side_added = priority_added.copy()

    #     # Create the 'Side' column and set it to a default value (e.g., None)
    #     side_added['Side'] = None
        
    #     # Use .loc to conditionally assign 'Left' and 'Right'
    #     side_added.loc[side_added['Priority'].str.startswith('L'), 'Side'] = 'Left'
    #     side_added.loc[side_added['Priority'].str.startswith('R'), 'Side'] = 'Right'



    elif category == "Power":
        # side_added is a copy of the priority_added DataFrame
        side_added = priority_added.copy()

        # Create the 'Side' column and set it to a default value (e.g., None)
        side_added['Side'] = None
        
        # Use .loc to conditionally assign 'Left' and 'Right' based on the Priority
        side_added.loc[side_added['Priority'].str.startswith('L'), 'Side'] = 'Left'
        side_added.loc[side_added['Priority'].str.startswith('R'), 'Side'] = 'Right'

        # --- The requested Streamlit toggle button ---
        # This toggle controls whether the new logic is applied.
        #is_fixed_channelwise = st.sidebar.toggle("Fixed (Channelwise)")
        is_fixed_channelwise = st.sidebar.toggle("Fixed (Channelwise)", value=True)

        # --- Core Logic: Conditionally modify Priority based on the toggle ---
        if is_fixed_channelwise:
            # 1. Create a mask to filter rows based on a combination of conditions.
            # The 'Priority' must start with 'R'.
            # The 'Pin Display Name' must either end with a digit OR begin with 'ISEN' and have a digit in the second-to-last position.
            mask = (
                side_added['Priority'].str.startswith('R', na=False) &
                (
                    side_added['Pin Display Name'].str.match(r'.*\d$', na=False) |
                    (
                        side_added['Pin Display Name'].str.startswith('ISEN', na=False) &
                        side_added['Pin Display Name'].str.get(-2).str.isdigit()
                    ) |
                    (
                        side_added['Pin Display Name'].str.startswith('VSEN', na=False) &
                        side_added['Pin Display Name'].str.get(-2).str.isdigit()
                    )
                )
            )

            # 2. Iterate through the filtered rows and update the 'Priority' column.
            for index, row in side_added[mask].iterrows():
                pin_name = row['Pin Display Name']
                
                # Extract the number based on which condition was met.
                # The first pattern '(\d+)$' captures a number at the end of the string.
                # The second pattern '^ISEN(\d)[A-Z]?$' captures the digit after 'ISEN' and before an optional letter.
                #match = re.search(r'(\d+)$', pin_name) or re.search(r'^ISEN(\d)[A-Z]?$', pin_name) or re.search(r'^VSEN(\d)[A-Z]?$', pin_name)
                match = re.search(r'(\d+)$', pin_name) or re.search(r'^ISEN(\d).+$', pin_name) or re.search(r'^VSEN(\d).+$', pin_name)
                
                if match:
                    number = match.group(1)
                    # Prepend the extracted number to the existing 'Priority' value.
                    new_priority = f"{number}_{row['Priority']}"
                    side_added.at[index, 'Priority'] = new_priority

        side_added = single80pin_constraints.assigning_ascending_order_for_similar_group(side_added)        

    if isinstance(side_added, pd.DataFrame):
        side_added = general_constraints.final_filter(side_added) 
        
        # Create tabs for Symbol View and Data Table
        tab1, tab2 = st.tabs(["📊 Symbol View", "📋 Smart Table"])
        
        with tab1:
            # Symbol Viewer
            try:
                renderer = SymbolRenderer()
                part_display_name = part_number if 'part_number' in locals() else "Symbol"
                fig = renderer.render_symbol(part_display_name, side_added)
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error rendering symbol: {str(e)}")
                st.warning("Displaying data table only")
        
        with tab2:
            st.subheader(f"Smart Table:")
            st.dataframe(side_added, use_container_width=True, height=600)
            
            # Download button
            timestamp = datetime.datetime.now().strftime("%d-%m_%H:%M")
            try:
                filename = f"{part_number}_SmartPinTable_{timestamp}.csv"
            except NameError:
                try:
                    filename = f"{input_csv_file_name}_SmartPinTable_{timestamp}.csv"
                except NameError:
                    filename = "SmartPinTable.csv"           

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
        
        # Display each part with tabs
        for key, df in side_added.items():
            st.markdown(f"### {key}")
            
            tab1, tab2 = st.tabs(["📊 Symbol View", "📋 Smart Table"])
            
            with tab1:
                try:
                    renderer = SymbolRenderer()
                    fig = renderer.render_symbol(key, df)
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Error rendering {key}: {str(e)}")
            
            with tab2:
                st.dataframe(df, use_container_width=True, height=400)
            
            st.divider()

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

else:
    st.warning("Invalid data in session state. No Grouped Pin Table Available")
    st.session_state['no_grouping_pin_table'] = None 
    excel_input.handle_file_upload()

    if 'pin_table' in st.session_state:
        pin_table = st.session_state['pin_table']

    col1, col2, col3 = st.columns(3)

    # Button 1: Clear Pin Table (Light Blue)
    with col1:
        if st.button("Clear Pin Table", type="secondary"):
            del st.session_state['pin_table']
            st.write("Pin table cleared.")
            st.rerun()


    part_number = st.session_state["part number"]
    if part_number is None:
        st.session_state["part number"] = st.session_state["uploaded_csv_name"]
        part_number = st.session_state["uploaded_csv_name"]
    # Display the part number
    # Ensure pin_table is initialized before proceeding further
    if 'pin_table' in st.session_state and st.session_state['pin_table'] is not None:
        pin_table = st.session_state['pin_table']
        part_number = st.session_state.get('part_number', 'Unknown')

        st.write(f"Part Number : **{part_number}**")
        st.write("Pin Table:")
        st.dataframe(pin_table)

        # Process only when pin_table is available
        required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type']
        before_side_flag, without_grouping = general_funct.check_excel_format(
            pin_table, required_cols, optional_column='Side'
        )

        suggested_four_sided = four_sided_symbol.default_four_sided_toggle(without_grouping)
        four_sided_toggle = st.sidebar.toggle(
            "Use 4-Sided Pin Assignment", value=suggested_four_sided
        )

        side_assigned_df = four_sided_symbol.assign_pin_sides(
            without_grouping, use_four_sided=suggested_four_sided
        )

        st.write("Side-assigned Pin Table:")
        st.dataframe(side_assigned_df)

    else:
        st.warning("No pin table found. Please upload a valid Excel file to proceed.")




