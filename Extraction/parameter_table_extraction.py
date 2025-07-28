import pdfplumber
import streamlit as st
import pandas as pd

from .base_functions import multipage_pintable_extractor

def parameter_tables(input_buffer,part_number):

  with pdfplumber.open(input_buffer) as pdf:
    page_numbers = multipage_pintable_extractor.find_page_range(pdf, "Symbol Parameters", "Footprint Design Information")

    if page_numbers:
      st.write(f"Pages containing 'Symbol Parameters' to 'Footprint Design Information': {page_numbers}")
      parameter_tables = multipage_pintable_extractor.extract_tables_in_these_pages(input_buffer, page_numbers)
      st.table(parameter_tables)

      #if parameter_tables:
      #  merged_table = merge_parameter_tables(parameter_tables)


      if parameter_tables:
          # Convert all tables to Pandas DataFrames (if they aren't already)
          parameter_tables = [pd.DataFrame(table) for table in parameter_tables]

          # Check if all tables are of the same size
          table_shapes = [table.shape for table in parameter_tables]  # Get the shape (rows, columns) of each table
          if all(shape == table_shapes[0] for shape in table_shapes):
              # If all tables are of the same size, merge them
              merged_table = multipage_pintable_extractor.merge_parameter_tables(parameter_tables)
              final_table = multipage_pintable_extractor.remove_rows_with_more_empty_values(merged_table)
              st.text("Debug Table")
              st.table(final_table)
              return final_table
          else:
              # If tables are not of the same size, find the table with the `part_number` string
              part_number_table = None
              for table in parameter_tables:
                  if table.astype(str).apply(lambda row: row.str.contains(part_number).any(), axis=1).any():
                      merged_table = table
                      final_table = multipage_pintable_extractor.remove_rows_with_more_empty_values(merged_table)
                      st.text("debug Table")
                      st.table(final_table)
                      return final_table
      else:
        st.write("No tables found in the specified pages.")
    else:
      st.write("Page with 'Symbol Parameters' not found.")

  return None