from Extraction import pin_table_extraction
from utils.path import submodule_path
import pandas as pd
from resource_path import resource_path
from Side_Allocation.base_functions import general_constraints
from Side_Allocation import priority
from Side_Allocation import side
from Side_Allocation import part_division
from Grouping import Assigning_Electrical_Type , Assigning_Pin_Group
from Grouping.base_functions import general_funct

def extracting_pin_tables_pdf(partnumber_dict, pdf_path):
	part_number = partnumber_dict.get('Orderable Part Number')
	number_of_pins = partnumber_dict.get('Number of Pins')
	package_type = partnumber_dict.get('Package')
	package_code = partnumber_dict.get('Package Code/POD Number')
	pin_table = pin_table_extraction.extracting_pin_tables(pdf_path, part_number, number_of_pins, package_type, package_code)
	print("eXtracted pin table")
	return pin_table


def assign_grouping(pin_table):
	#Grouping
	required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name']
	json_paths = {
			'Input': submodule_path('Grouping','mcu_database', 'mcu_input.json'),
			'Power': submodule_path('Grouping','mcu_database', 'mcu_power.json'),
			'Output': submodule_path('Grouping','mcu_database', 'mcu_output.json'),
			'I/O': submodule_path('Grouping','mcu_database', 'mcu_io.json'),
			'Passive': submodule_path('Grouping','mcu_database', 'mcu_passive.json')
		}
	json_paths_Single = {
    'Single': resource_path("Symbol_Automation/Grouping/shrinidhi_database/combined.json")
    }
	#submodule_path("Symbol_Automation", 'Grouping', 'shrinidhi_database', 'combined.json')
	before_grouping_flag, added_empty_grouping_column = general_funct.check_excel_format(pin_table,  required_cols, optional_column='Grouping')
	print("Checked grouping format")
	pin_grouping_table = Assigning_Pin_Group.grouping_as_per_database(added_empty_grouping_column, json_paths_Single, SENSITIVITY= False,SMARTSEARCH= False, SINGLE_FILE=True)  
	df_with_no_grouping = general_funct.check_empty_groupings(pin_grouping_table)
	if not df_with_no_grouping.empty:
		#Write logic for empty groupings
		print("No logic written for empty groupins")
	print(f"Pin Grouping Table: {pin_grouping_table}")
	return pin_grouping_table

def assign_side(pin_grouping_table):

	#Side alloc
	required_columns = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping']
	optional_column = 'Priority'
	before_priority_flag, added_empty_priority_column = general_funct.check_excel_format(pin_grouping_table,required_columns, optional_column=optional_column)
	#st.text(f"Before Side Allocation Flag :{before_priority_flag}")
	#st.dataframe(added_empty_priority_column)
	priority_mapping_json = resource_path("Symbol_Automation/Side_Allocation/priority_map_Shrinidhi.json")
	
	#submodule_path("Symbol_Automation", "Side_Allocation","priority_map_Shrinidhi.json")
	priority_added = priority.assigning_priority(added_empty_priority_column,priority_mapping_json)

	required_columns = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping','Priority']
	optional_column_side = 'Side'
	before_side_flag, added_empty_side_column = general_funct.check_excel_format(priority_added,required_columns, optional_column=optional_column_side)
	side_added_dict = {}
	if len(added_empty_side_column) <= 80:
		side_added_df = side.side_for_singlepart(added_empty_side_column)
		side_added_df = general_constraints.final_filter(side_added_df) 
		#st.text(f"Side Column Added")
		#st.dataframe(side_added)
		side_added_dict["Single_Part"] = side_added_df
	else:
		print(f"Executing Partioning")
		df_dict = part_division.partitioning(added_empty_side_column, Strict_Population = False, Balanced_Assignment=False)
		side_added_dict = side.side_for_multipart(df_dict)
		side_added_dict = {k: v for k, v in side_added_dict.items() if not v.empty}
		for key in side_added_dict:
			df = side_added_dict[key]
			df = general_constraints.final_filter(df)   
			side_added_dict[key] = df
	
	return side_added_dict