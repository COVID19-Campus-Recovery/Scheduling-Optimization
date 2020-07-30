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
    "room_use",
]

course_columns_optional = [
    "building_number",
    "room",
    "priotity_boost",
    "keep_assigned_room",
    "crn",
    "contact_hours",
    "raw_preference",
    "preference"
]

room_columns = [
    "bldg_room",
    "capacity",
    "use"
]

room_assignment_output_columns = [
    "subject_code",
    "course_number",
    "course_section",
    "enrollment",
    "days",
    "begin_time",
    "end_time",
    "room_use",
    "bldg_room",
    "capacity",
]

building_location_columns = [
    "building_number",
    "latitude",
    "longitude"
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


def read_data(filepath, required_columns=None, optional_columns=None):
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
    print("filepath in read_data: " + filepath)
    file_suffix = filepath.split(".")[-1]
    if file_suffix == "xlsx":
        df = pd.read_excel(filepath)
    elif file_suffix == "csv":
        df = pd.read_csv(filepath)
    else:
        raise Exception("filepath passed to read_data must formatted as excel or csv. Filename was: " + filepath)

    df.columns = [standardize_column_name(col) for col in df.columns]

    if required_columns is not None:
        for col in required_columns:
            if col not in df.columns:
                raise Exception("Input data was missing column: " + str(col))

    if optional_columns is not None:
        for col in optional_columns:
            if col not in df.columns:
                warning_str = "Input data was missing optional column: " + str(col) + ". Some functionality may be missing"
                warnings.warn(warning_str)

    return df


def mark_occurances(course_data):
    """
    Input: 
        course_data - pd.DataFrame: properly formatted course dataframe

    Output:
        course_data - same as input dataframe, but now with a new column subject_course_section_occurrence,
                       which will be a unique identifier for each row

    Intended as a helper method to clean_course_data
    """

    course_data["repeated_section"] = course_data['subject_course_section'].eq(course_data['subject_course_section'].shift())
    course_data['twice_repeated_section'] = (course_data['repeated_section'] & course_data['repeated_section'].eq(  course_data['repeated_section'].shift()))
    # confirm no section meets more than 3 times a week
    course_data['three_times_repeated_section'] = (course_data['twice_repeated_section'] & course_data['twice_repeated_section'].eq(course_data['twice_repeated_section'].shift()))
    course_data['four_times_repeated_section'] = (course_data['three_times_repeated_section'] & course_data['three_times_repeated_section'].eq(course_data['three_times_repeated_section'].shift()))
    course_data['five_times_repeated_section'] = (course_data['four_times_repeated_section'] & course_data['four_times_repeated_section'].eq(course_data['four_times_repeated_section'].shift()))

    # print(course_data[course_data['three_times_repeated_section']])
    # print(course_data[course_data['three_times_repeated_section']]['subject_course_section'])

    # print(course_data[course_data['four_times_repeated_section']])
    # print(course_data[course_data['four_times_repeated_section']]['subject_course_section'])
    course_data["occurance"] = course_data.apply(
        lambda row: 0 if not row["repeated_section"]
        else (1 if not row["twice_repeated_section"]
            else (2 if not row["three_times_repeated_section"]
                else (3 if not row["four_times_repeated_section"]
                    else 4
            ))),
        axis=1).astype(str)
    assert not course_data['five_times_repeated_section'].any()

    #remove helper colummns created earlier
    del course_data['repeated_section']
    del course_data['twice_repeated_section']
    del course_data['three_times_repeated_section']
    del course_data['four_times_repeated_section']
    del course_data['five_times_repeated_section']


    # create subject_course_section_occurrence as a true unique identifier for sections
    course_data["subject_course_section_occurrence"] = course_data["subject_course_section"] + "_" + course_data["occurance"]

    # confirm it's a unique identifier for sections
    assert len(course_data["subject_course_section_occurrence"].unique()) == len(course_data)

    return course_data

def clean_course_data(filepath):
    """
    Input: 
        filepath - str : full filepath of the excel course data that will be read

    Output:
        df - pandas.DataFrame: data pulled from filepath

    Should be called to load course dataframe before being passed into the constructor for RoomAssignmentOpt
    Dataprocessing is very minimal, and mainly to ensure standardization of column names for RoomAssignmentOpt
    
    Todo: the waring for uniqueness should actually be an error. Since this is calaculated internall it should always be unique
    """

    course_data = read_data(filepath, course_columns, course_columns_optional)

    course_data['subject_course_section'] = course_data["subject_code"].astype(str) + "_" + course_data["course_number"].astype(str)  \
                                           + "_" + course_data["course_section"].astype(str)
    
    course_data = mark_occurances(course_data)

    if 'building_code' and 'room_number' in course_data.columns:
        course_data['bldg_room'] = course_data['building_code'].astype(str) + "_" + course_data['room_number'].astype(str)

    # confirm course_subject_number_occurence is a unique identifier for sections
    if len(course_data["subject_course_section_occurrence"].unique()) != len(course_data):
        warnings.warn("""Each row of the course dataset should have unique values for the columns:
                            Subject Code, Course Number, Course Section, Occurence""")

    #single column to keep track of course timeslot
    course_data['full_time'] = course_data['days'] + "_" + course_data['begin_time'].astype(str) + "_" + course_data['end_time'].astype(str)

    return course_data

def separate_online_courses(course_data):
    """
    Input: 
        course_data - pd.DataFrame: properly formatted course dataframe

    Output:
        course_data - pd.DataFrame: input data, where the field exclusively_online == 0
        course_data_exclusively_online - pd.DataFrame: input data, where the field exclusively_online == 1

    Intended to be called in model constructor
    so that the in person and online courses can be stored separately in the objects' attributes
    """
    if "preference" not in course_data.columns:
        course_data_local = course_data[course_data["exclusively_online"]==0]
        course_data_exclusively_online = course_data[course_data["exclusively_online"]==1]
    else:
        course_data_local = course_data[(course_data["exclusively_online"]==0) & (course_data["preference"]!='remote')]
        course_data_exclusively_online = course_data[(course_data["exclusively_online"]==1) | (course_data["preference"]=='remote')]
    return course_data_local, course_data_exclusively_online

def separate_online_courses_by_capacity(course_data, weeks_in_semester, minimum_class_days):
    pass

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

def clean_room_assignment_output_data(filepath):
    """
    Input: 
        filepath - str : full filepath of the csv output data that will be read.
                         Should have previously been generated by by a room_assignment_opt model

    Output:
        df - pandas.DataFrame: data pulled from filepath
    
    Should be called to load output dataframe before output analysis

    Todo: the waring for uniqueness should actually be an error. Since this is calaculated internall it should always be unique
    """

    output_data = read_data(filepath, required_columns=room_assignment_output_columns)

    output_data['subject_course_section'] = output_data["subject_code"].astype(str) + "_" + output_data["course_number"].astype(str)  \
                                           + "_" + output_data["course_section"].astype(str)
    
    output_data = mark_occurances(output_data)

    if len(output_data["subject_course_section_occurrence"].unique()) != len(output_data):
        warnings.warn("""Each row of the output dataset should have unique values for the columns:
                       Subject Code, Course Number, Course Section, Occurence""")

    #single column to keep track of course timeslot
    output_data['full_time'] = output_data['days'] + "_" + output_data['begin_time'].astype(str) + "_" + output_data['end_time'].astype(str)

    return output_data

def pad_str_prefix(str_object, desired_length, pad_value):
    """
    Input:
        str_object - str : initial string object
        desired_length - int : the number of characters that are expected to be in str_object
        pad_value - str : a string with length one. This string will be added as many times as necessary to str_object
                         in order to achieve len(str_object) = expected_length
    Output:
        str_object - str: the same object the was passed as input. It's modified in place.

    The intended purpose of this method is for use on strings that are meant to be used as id's and need to be of a certain length
    The method is implemented recursively
    """
    if type(str_object) is not str or type(pad_value) is not str:
        raise Exception("str_object and pad_value must be of type string when calling pad_str_prefix")

    if len(str_object) > desired_length:
        print(str_object)
        raise Exception("pad_str_prefix can only be called when len(str_object) <= expected_length")
    elif len(str_object) == desired_length:
        return str_object
    else:
        return pad_str_prefix(pad_value + str_object, desired_length, pad_value)


def clean_building_location_data(filepath, course_data=None):
    """
    Input: 
        filepath - str : full filepath of the excel building location data that will be read
        course_data - pandas.DataFrame : properly formatted course data. If passed, then this method
                                       ensures that all buildings in course_data are included in building data
    Output:
        df - pandas.DataFrame: data pulled from filepath

    Should be called to load building location dataframe before being passed into the constructor for RoomAssignmentModePreferencesContactyOpt
    """

    building_location_data = read_data(filepath, building_location_columns)
    building_location_data = building_location_data[building_location_data[building_location_columns].notnull()]
    building_location_data['building_number'] = building_location_data['building_number'].apply(lambda building_number: pad_str_prefix(str(building_number), 3, "0") if len(str(building_number)) < 3  else building_number)
    if len(building_location_data["building_number"].unique()) != len(building_location_data):
            warnings.warn("""Each row of the building location dataset should have unique values for the column: building_number""")

    if course_data is not None and "building_number" in course_data:
        buildings_in_course_data = set(course_data['building_number'])
        buildings_in_course_data = set(pad_str_prefix(str(building_number), 3, "0") if len(str(building_number)) < 3  else building_number for building_number in buildings_in_course_data)
        buildings_in_building_location_data = set(building_location_data['building_number'])

        missing_buildings = {building for building in buildings_in_course_data if building not in buildings_in_building_location_data}
        if len(missing_buildings) > 0:
            print(len(missing_buildings))
            warnings.warn("""Not all buildings in course_data were included in building_locaiton_data. The following building numbers were missing: \n""" + 
                            str(missing_buildings))

    return building_location_data
