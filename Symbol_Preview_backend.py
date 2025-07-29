from Extraction import pin_table_extraction
from Grouping.base_functions import general_funct
from Grouping import Assigning_Electrical_Type , Assigning_Pin_Group
from Side_Allocation.base_functions import general_constraints
from Side_Allocation import priority
from Side_Allocation import side
from Side_Allocation import part_division
import pandas as pd

def assign_grouping(partnumber_dict, pdf_path):
	part_number = partnumber_dict.get('Orderable Part Number')
	number_of_pins = partnumber_dict.get('Number of Pins')
	package_type = partnumber_dict.get('Package')
	package_code = partnumber_dict.get('Package Code/POD Number')
	pin_table = pin_table_extraction.extracting_pin_tables(pdf_path, part_number, number_of_pins, package_type, package_code)


	required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name']
	json_paths = {
			'Input': 'Grouping/mcu_database/mcu_input.json',
			'Power': 'Grouping/mcu_database/mcu_power.json',
			'Output': 'Grouping/mcu_database/mcu_output.json',
			'I/O': 'Grouping/mcu_database/mcu_io.json',
			'Passive': 'Grouping/mcu_database/mcu_passive.json'
		}
	before_grouping_flag, added_empty_grouping_column = general_funct.check_excel_format(pin_table,  required_cols, optional_column='Grouping')
	pin_grouping_table = Assigning_Pin_Group.grouping_as_per_database(added_empty_grouping_column, json_paths, SENSITIVITY= False)  
	df_with_no_grouping = general_funct.check_empty_groupings(pin_grouping_table)
	if not df_with_no_grouping.empty:
		#Write logic for empty groupings
		print("No logic written for empty groupins")

	return pin_grouping_table

def assign_side(pin_grouping_table):

	#Side alloc
	required_columns = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping']
	optional_column = 'Priority'
	before_priority_flag, added_empty_priority_column = general_funct.check_excel_format(pin_grouping_table,required_columns, optional_column=optional_column)
	#st.text(f"Before Side Allocation Flag :{before_priority_flag}")
	#st.dataframe(added_empty_priority_column)
	priority_mapping_json = f"Side_Allocation/priority_map.json"
	priority_added = priority.assigning_priority(added_empty_priority_column,priority_mapping_json)

	required_columns = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping','Priority']
	optional_column_side = 'Side'
	before_side_flag, added_empty_side_column = general_funct.check_excel_format(priority_added,required_columns, optional_column=optional_column_side)

	if len(added_empty_side_column) <= 80:
		side_added = side.side_for_singlepart(added_empty_side_column)
		#st.text(f"Side Column Added")
		#st.dataframe(side_added)

	else:
		print(f"Executing Partioning")
		df_dict = part_division.partitioning(added_empty_side_column, Strict_Population = False)
		side_added_dict = side.side_for_multipart(df_dict)
		#st.text(f"Side Column Added")
		#for subheader, dataframe in side_added_dict.items():
		#    st.subheader(subheader)
		#    st.dataframe(dataframe)


		#side_added = SideAllocation_functions.convert_dict_to_list(df_dict)
		side_added = side_added_dict
	
	
	if isinstance(side_added, pd.DataFrame):
		side_added = general_constraints.final_filter(side_added) 

    # Assuming `side_added` is a dictionary of DataFrames
	
	
	elif isinstance(side_added, dict):
		side_added = {k: v for k, v in side_added.items() if not v.empty}
		for key in side_added:
			df = side_added[key]
			df = general_constraints.final_filter(df)   
			side_added[key] = df
			

	return df



		
