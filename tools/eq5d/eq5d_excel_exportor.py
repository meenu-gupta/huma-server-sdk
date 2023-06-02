import json
import os

import pandas
import pathlib

path = pathlib.Path(__file__).parent.absolute()
file_path = os.path.join(path, "EQ-5D-5L_Crosswalk_Index_Value_Calculator.xlsx")

excel_data_df = pandas.read_excel(file_path, sheet_name="EQ-5D-5L Value Sets")

json_str = excel_data_df.set_index("5L profile").to_json(orient="index")

with open("EQ-5D-5L_index_value.json", "w") as json_file:
    json.dump(json_str, json_file)
