import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None  # default='warn'

isye_course_to_exclude = {
    "2698",
    "2699",
    "4106",
    "4698",
    "4699",
    "4800",
    "7000",
    "8997",
    "8998",
    "9000",
}

course_columns = [
    'Course 1 Subject Code_Course#_Section_CRN_Credits',
    'Course 2 Subject Code_Course#_Section_CRN_Credits',
    'Course 3 Subject Code_Course#_Section_CRN_Credits',
    'Course 4 Subject Code_Course#_Section_CRN_Credits',
    'Course 5 Subject Code_Course#_Section_CRN_Credits',
    'Course 6 Subject Code_Course#_Section_CRN_Credits',
    'Course 7 Subject Code_Course#_Section_CRN_Credits',
    'Course 8 Subject Code_Course#_Section_CRN_Credits',
    'Course 9 Subject Code_Course#_Section_CRN_Credits',
    'Course 10 Subject Code_Course#_Section_CRN_Credits',
    'Course 11 Subject Code_Course#_Section_CRN_Credits',
    'Course 12 Subject Code_Course#_Section_CRN_Credits'
]


def clean_course_data(filepath):
    course_raw_data = pd.read_excel(filepath)
    course_raw_data_isye = course_raw_data[course_raw_data['Subject Code']=='ISYE']
    course_data_isye = course_raw_data_isye[course_raw_data_isye['Course Number'].apply(lambda num: num not in isye_course_to_exclude)]

    # add Subject Code to be able to incorporate other courses later
    course_data_isye["course_subject_number"] = course_data_isye["Subject Code"] + "_" + course_data_isye["Course Number"]
    # add unique identifier for each row 
    course_data_isye["subject_number_section"] = course_data_isye["Subject Code"] + "_" + course_data_isye["Course Number"] + "_" + course_data_isye["Course Section"]
    # mark courses with multiple meeting times for the same section
    course_data_isye.sort_values(['subject_number_section'], inplace=True)

    course_data_isye["repeated_section"] = course_data_isye['subject_number_section'].eq(course_data_isye['subject_number_section'].shift())
    course_data_isye['twice_repeated_section'] = (course_data_isye['repeated_section'] & course_data_isye['repeated_section'].eq(  course_data_isye['repeated_section'].shift()))
    course_data_isye["section_meeting_occurance"] = course_data_isye.apply(
        lambda row: 0 if not row["repeated_section"]
        else (1 if not row["twice_repeated_section"]
              else 2),
        axis=1).astype(str)
    # confirm no section meets more than 3 times a week
    course_data_isye['three_times_repeated_section'] = (course_data_isye['twice_repeated_section'] & course_data_isye['twice_repeated_section'].eq(course_data_isye['twice_repeated_section'].shift()))
    assert not course_data_isye['three_times_repeated_section'].any()

    #remove helper colummns created earlier
    del course_data_isye['repeated_section']
    del course_data_isye['twice_repeated_section']
    del course_data_isye['three_times_repeated_section']

    # create subject_number_section_orrurance as a true unique identifier for sections
    course_data_isye["subject_number_section_orrurance"] = course_data_isye["subject_number_section"] + "_" + course_data_isye["section_meeting_occurance"]
    # confirm it's a unique identifier for sections
    assert len(course_data_isye["subject_number_section_orrurance"].unique()) == len(course_data_isye)

    #single column to keep track of course day and time
    course_data_isye['full_time'] = course_data_isye['Days'] + "_" + course_data_isye['Begin Time'].astype(str) + "_" + course_data_isye['End Time'].astype(str)

    # create unique identifier for rooms
    course_data_isye['bldg_room'] = course_data_isye['Building Number'] + "_" + course_data_isye['Room #']

    buildings_used_for_isye = course_raw_data[course_raw_data['Subject Code']=='ISYE']['Building Number'].unique()
    return course_data_isye, buildings_used_for_isye


def any_isye_course(student_row):
    isye_course_all = list()
    for column_name in course_columns:
        isye_course_current = type(student_row[column_name]) is str and "ISYE" in student_row[column_name]
        #in_classroom_isye_course_current = isye_course_current and 
        isye_course_all.append(isye_course_current)
    return np.array(isye_course_all).any()


def clean_student_data(filepath):
    students_raw_data = pd.read_excel(filepath)
    student_data_isye = students_raw_data[
        students_raw_data.apply(any_isye_course, axis=1)]
    # confirm SYSGENID is a unique identifier
    assert len(student_data_isye) == len(student_data_isye['SYSGENID'].unique())
    return student_data_isye


def clean_room_data(filepath, buildings):
    rooms_raw_data = pd.read_excel(filepath)
    room_data_isye = rooms_raw_data[rooms_raw_data['Bldg Code'].apply(
        lambda bldg_code: bldg_code in set(buildings))]

    # create unique identifier for rooms
    room_data_isye['bldg_room'] = room_data_isye['Bldg Code'] + "_" + room_data_isye['Rm Nbr']

    # confirm that bldg_room is a unique identifier
    assert len(room_data_isye) == len(room_data_isye['bldg_room'].unique())

    return room_data_isye

def clean_detail_room_data(filepath, buildings):
    # data cleaning of the new raw data with detail capacity information.
    # the output format should be same as the above function.
    # I keep the previous one, so you can choose use which one in your formulation

    rooms_raw_data = pd.read_excel(filepath)


    # fill zero in the beginning of building code
    rooms_raw_data["Facility"] = rooms_raw_data["Facility"].apply(lambda x: str(x).zfill(3)
    if str(x).isnumeric() else (x.zfill(4) if len(x) < 4 else x))

    rooms_raw_data['Room_code'] = rooms_raw_data['Room Name (If different from Room Field)'].fillna(rooms_raw_data['Room'])
    rooms_raw_data['Room_code'] = rooms_raw_data['Room_code'].astype(str).replace('\.0', '', regex=True)
    rooms_raw_data['bldg_room'] = rooms_raw_data["Facility"] + '_' + rooms_raw_data["Room_code"]

    # Some room don't have max cp, so I use 6'cp as max cp
    rooms_raw_data['Station Count (Current)'] = rooms_raw_data['Station Count (Current)'].fillna(
        rooms_raw_data["6' Module Capacity at 36sf"].astype(str))

    room_data_isye = rooms_raw_data[rooms_raw_data['Facility'].apply(
        lambda bldg_name: bldg_name in set(buildings))]

    # confirm that bldg_room is a unique identifier
    assert len(room_data_isye) == len(room_data_isye['bldg_room'].unique())

    return room_data_isye