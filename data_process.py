import pandas as pd
import numpy as np
import warnings


course_columns = [
    "subject_code",
    "course_number",
    "course_section",
    "enrollment",
    "days",
    "begin_time",
    "end_time",
    "exclusively_online",
    "room_use"
]

course_columns_optional = [
    "bldg_room"
]

room_columns = [
    "bldg_room",
    "capacity",
    "use"
]

def standardize_column_name(column_name):
	"""
	Input: 
		column_name - str : represent column name for some dataframe

	Output:
		column_name: equivalent to the input column name, but standardized 
		such that all characters are lowercase and spaces are replaced with underscores

	Should be called on the column names of any pandas dataframe as soon is read from an 
	excel or csv file, so the column names in the dataframe are consistent with those expected
	in the code.
	"""

	column_name = column_name.lower()
	column_name = column_name.replace(" ", "_")
	return column_name


def read_data(filepath, required_columns, optional_columns=None):
	"""
	Input: 
		filepath - str : full filepath of the excel data that will be read
		required_columns - list[str]: if any of these column names are not present in the data,
									  an exception will be raised
		optional_columns - list[str]: if any of these columns are not present in the data,
			 						  a warning will be displayed

	Output:
		df - pandas.DataFrame: data pulled from filepath

	Should be called to read an excel file into a dataframe if the user
	wants to ensure specific columns are present in the dataset
	"""

    df = pd.read_excel(filepath)

    df.columns = [standardize_column_name(col) for col in df.columns]

    for col in required_columns:
        if col not in df.columns:
            raise Exception("Input data was missing column: " + str(col))

    if optional_columns is not None:
        for col in optional_columns:
            if col not in df.columns:
                warnings.warn("Input data was missing optional column: " + str(col) + ". Some functionality may be missing")

    return df

def clean_course_data(filepath):
	"""
	Input: 
		filepath - str : full filepath of the excel course data that will be read

	Output:
		df - pandas.DataFrame: data pulled from filepath

	Should be called to load course dataframe before being passed into the constructor for RoomAssignmentOpt
	Dataprocessing is very minimal, and mainly to ensure standardization of column names for RoomAssignmentOpt
	"""

    course_data = read_data(filepath, course_columns, course_columns_optional)

    course_data['subject_course_section'] = course_data["subject_code"].astype(str) + "_" + course_data["course_number"].astype(str)  \
                                           + "_" + course_data["course_section"].astype(str)
    

    # add Subject Code to be able to incorporate other courses later
    course_data["subject_course_section_occurrence"] = course_data['subject_course_section'] .astype(str) + course_data["occurrence"].astype(str) 

    # # mark courses with multiple meeting times for the same section
    # course_data.sort_values(['course_subject_number_occurence'], inplace=True)

    # confirm course_subject_number_occurence is a unique identifier for sections
    if len(course_data["subject_course_section_occurrence"].unique()) != len(course_data):
        warnings.warn("""Each row of the course dataset should have unique values for the columns:
                        	Subject Code, Course Number, Course Section, Occurence""")

    #single column to keep track of course timeslot
    course_data['full_time'] = course_data['days'] + "_" + course_data['begin_time'].astype(str) + "_" + course_data['end_time'].astype(str)

    return course_data

def clean_room_data(filepath):
	"""
	Input: 
		filepath - str : full filepath of the excel course data that will be read

	Output:
		df - pandas.DataFrame: data pulled from filepath

	Should be called to load room dataframe before being passed into the constructor for RoomAssignmentOpt
	Dataprocessing is very minimal, and mainly to ensure standardization of column names for RoomAssignmentOpt
	"""

    room_data = read_data(filepath, room_columns)

    if len(room_data["bldg_room"].unique()) != len(room_data):
        warnings.warn("""Each row of the room dataset should have unique values for the column: bldg_room""")

    room_data = room_data[room_data["capacity"]>0]

    return room_data

