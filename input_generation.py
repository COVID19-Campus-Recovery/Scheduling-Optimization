import pandas as pd
import numpy as np

'''
Input data generation
Three methods: InputRoom, InputCourse2019, InputCourse2020

Assumptions:  
    1. Some rooms in room_level_data don't have Max Capacity, so we used 6' Module Capacity at 36sf instead.
    2. Rooms in ISYE_FallSemesterScenarios_BuildingRooms.xlsx don't have "Class Use" information, so we assumed those 
        classrooms are "Class", i.e. General Classroom.
    3. These input files are used for the model without putting any courses online or adjusting capacity and enrollment，
        so the "enrollment" of the courses are Max Enrollment, the "capacity" of rooms are Max Capacity. 
'''

def InputRoom(room_level_data_path,
              CLSLAB_path,
              BuildingRoom_path,
              output_path="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_rooms_full_capacity",
              room_type = "Class"):
    #
    r'''
    Standard input room file: .xlsx with coulumns:
    ["bldg_room",capacity","use"]

    Parameters:
    -------------
    room_level_data_path: str, default=None
        file path of room_level_data

    CLSLAB_path: str, default=None
        file path of CLSLAB_path

    BuildingRoom_path: str, default=None
        file path of BuildingRoom_path

    output_path: str, default="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_rooms_example.xlsx"
        the output path of the .xlsx file. Save to a new dictionary in /Documents/Madgie_Cleaned_Directory/Data.

    room_type: select which type of class will be in the output, default = "Class"
        if a str is passed, it should be the type of the class, e.g. "Class" "Meeting Classroom", or "nonclass" means other classrooms except "Class"
        if a list is passed, it should be a list of types of class

    '''

    print("Room input file generating")
    global room_type_global
    room_type_global = room_type

    # Read data
    room_level_data = pd.read_excel(room_level_data_path)
    CLSLAB = pd.read_excel(CLSLAB_path)
    BuildingRoom = pd.read_excel(BuildingRoom_path)

    # CLSLAB
    CLSLAB["bldg_room"] = CLSLAB["Facility"] + "_" + CLSLAB["Room"].str.strip("0")
    CLSLAB_out = CLSLAB[["bldg_room", "Station Count", "Use Name"]]
    CLSLAB_out = CLSLAB_out.rename(columns={"Station Count": "capacity_CLSLAB", "Use Name": "use_CLSLAB"})

    # room_level_data
    room_level_data["Facility"] = room_level_data["Facility"].apply(lambda x: str(x).zfill(3) if str(x).isnumeric()
    else (x.zfill(4) if len(x) < 4 else x))

    room_level_data['Room_code'] = room_level_data['Room Name (If different from Room Field)'].fillna(
        room_level_data['Room'])

    room_level_data["Room_code"] = room_level_data["Room_code"].astype(str).replace('\.0', '', regex=True)

    room_level_data["bldg_room"] = room_level_data["Facility"] + "_" + room_level_data["Room_code"]


    # For now, we simply delete those classrooms whose max capacities are NA:
    room_level_data = room_level_data[~room_level_data['Station Count (Current)'].isnull()]
    # room_level_data['Station Count (Current)'] = room_level_data['Station Count (Current)'].fillna(
    #                       room_level_data["6' Module Capacity at 36sf"].astype(str))

    room_level_data['Station Count (Current)'] = room_level_data['Station Count (Current)'].astype(float)
    room_level_data_out = room_level_data[["bldg_room", "Station Count (Current)", "Use Name"]]
    room_level_data_out = room_level_data_out.rename(
        columns={"Station Count (Current)": "capacity_level", "Use Name": "use_level"})

    # BuildingRoom
    BuildingRoom["bldg_room"] = BuildingRoom["Bldg Code"] + "_" + BuildingRoom["Rm Nbr"]
    BuildingRoom_out = BuildingRoom[["bldg_room", "Rm Max Cap"]]
    BuildingRoom_out = BuildingRoom_out.rename(columns={"Rm Max Cap": "capacity_br"})

    # output final cleaning
    room_out = CLSLAB_out.merge(room_level_data_out, on="bldg_room", how="outer")
    room_out["capacity_CLSLAB"] = room_out["capacity_CLSLAB"].fillna(room_out["capacity_level"])
    room_out["use_CLSLAB"] = room_out["use_CLSLAB"].fillna(room_out["use_level"])
    room_out = room_out[["bldg_room", "capacity_CLSLAB", "use_CLSLAB"]]
    room_out = room_out.merge(BuildingRoom_out, on="bldg_room", how="outer")
    room_out["capacity_CLSLAB"] = room_out["capacity_CLSLAB"].fillna(room_out["capacity_br"])
    room_out = room_out.drop(columns="capacity_br")
    room_out = room_out.rename(columns={"capacity_CLSLAB": "capacity", "use_CLSLAB": "use"})

    # check duplication
    if len(room_out) != len(room_out["bldg_room"].unique()):
        room_out.sort_values(by="capacity", na_position='last')
        room_out = room_out.drop_duplicates(subset="bldg_room", keep='first')

    # check symbol value
    room_out['bldg_room'].str.replace(" ", "_")
    room_out = room_out[room_out['bldg_room'] != "*_*"]

    # check na value
    room_out["use"] = room_out["use"].fillna("Class")
    room_out.loc[room_out["use"] == "General Classroom", "use"] = "Class"
    room_out["capacity"] = room_out["capacity"].fillna(0.0)
    room_out["capacity"] = room_out["capacity"].astype(int)

    room_out[["bldg", "room"]] = room_out["bldg_room"].str.split("_", expand=True)
    room_out = room_out[room_out["bldg"] != "209"]
    room_out = room_out[["bldg_room","capacity","use"]]

    # Select Classroom type
    if isinstance(room_type,str):
        if room_type == "nonclass":
            room_out = room_out[room_out["use"] != "Class"]
        else:
            room_out = room_out[room_out["use"] == room_type]

        output_path+=("_"+room_type)

    if isinstance(room_type,list):
        room_out = room_out[room_out["use"].isin(np.array(room_type))]
        output_path+="_other"

    room_out.to_excel(output_path+".xlsx", index=False)

    return room_out


def InputCourse2019(course_2019_path,
                    room_input_path,
                    output_path="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_full_enrollment_2019",
                    boost = False):
    r'''
    Standard course input room file: .xlsx with coulumns: ["Subject Code","Course Number","Course Section","Enrollment",
                                "Days","Begin Time","End Time","Building Number","Room","Exclusively Online","Room Use"]

       Parameters:
       -------------
       course_2019_path: str, default=None
           file path of 2019 course data

       room_input_path: str OR pandas.dataframe default=None
          if a str is passed, it should be the filepath of room input data.
          if a pandas.dataframe passed, it should be the room input data itself.

       output_path: str, default="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_full_enrollment_2019"
           the output path of the .xlsx file. Save to a new dictionary in /Documents/Madgie_Cleaned_Directory/Data.

        boost: bool, default = False
            if include the boost column

       '''
    print("2019 Course Input Data Generating")

    # Read Data
    course_data_2019 = pd.read_excel(course_2019_path)
    if isinstance(room_input_path, str):
        room_input = pd.read_excel(room_input_path)
    else:
        room_input = room_input_path

    # Join course data with room data
    course_data_2019["bldg_room"] = course_data_2019["Building Number"].astype(str) + "_" + course_data_2019[
        "Room #"].astype(str)
    course_2019_out = course_data_2019.merge(room_input, on="bldg_room", how="left")

    # output generating
    course_2019_out = course_2019_out.drop(columns=["Course Title",
                                                    "Credit Hours ",
                                                    "Original Section Enrollment",
                                                    "Max Enroll",
                                                    "Building Description",
                                                    "bldg_room",
                                                    "capacity"])

    course_2019_out = course_2019_out.rename(
        columns={"Adjusted Enrollment After Combining Cross-Listed Sections": "Enrollment",
                 "Building Neumber": "Building",
                 "Room #": "Room",
                 "use": "Room Use"})

    course_2019_out.insert(course_2019_out.shape[1] - 1, "Exclusively Online", 0)
    course_2019_out = course_2019_out.sort_values(by=["Subject Code", "Course Number", "Course Section"],
                                                  na_position='last')

    course_2019_out = course_2019_out[~course_2019_out["Room Use"].isnull()]

    # Customized output file name
    global room_type_global
    if isinstance(room_type_global, str):
        output_path+=("_"+room_type_global)
    else:
        output_path+="_other"


    # Boost Column
    if boost:
        course_2019_out["Level"] = course_2019_out["Course Number"].str[0]
        num_level = len(course_2019_out["Level"].unique())
        level_mapping = dict(zip(sorted(course_2019_out["Level"].unique()), np.array(range(num_level, 0, -1)) / 2))
        course_2019_out["boost"] = course_2019_out["Level"].map(level_mapping)
        course_2019_out = course_2019_out.drop(columns=["Level"])

        output_path += "_boost"


    course_2019_out.to_excel(output_path+".xlsx", index=False)


def InputCourse2020(course_2020_path,
                    room_input_path,
                    output_path="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_full_enrollment_2020",
                    boost = False):
    r'''
    Standard course input room file: .xlsx with coulumns: ["Subject Code","Course Number","Course Section","Enrollment",
                                "Days","Begin Time","End Time","Building Number","Room","Exclusively Online","Room Use"]

       Parameters:
       -------------
       course_2019_path: str, default=None
           file path of 2019 course data

       room_input_path: str OR pandas.dataframe default=None
          if a str is passed, it should be the filepath of room input data.
          if a pandas.dataframe passed, it should be the room input data itself.

       output_path: str, default="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_example2019.xlsx"
           the output path of the .xlsx file. Save to a new dictionary in /Documents/Madgie_Cleaned_Directory/Data.

       boost: bool, default = False
           if include the boost column

       '''
    print("2020 Course Input data Generating")

    # Read Data
    course_data_2020 = pd.read_excel(course_2020_path)
    if isinstance(room_input_path, str):
        room_input = pd.read_excel(room_input_path)

    else:
        room_input = room_input_path

    # Data Cleaning
    course_data_2020 = course_data_2020[(course_data_2020["Camp"] == "A") | (course_data_2020["Camp"] == "EM")]
    course_2020_out = course_data_2020[["Subj Code", "Course Number", "Sect", "ENRL Max", "Cross List Group",
                                        "Days", "Start Time", "End Time", "Bldg", "Rm", "RDL","CRN","Contact Hours"]]

    # Join the course data with room data
    course_2020_out["bldg_room"] = course_2020_out["Bldg"].astype(str) + "_" + course_2020_out["Rm"].astype(str)
    course_2020_out = course_2020_out.merge(room_input, on="bldg_room", how="left")

    # Columns Formatting
    course_2020_out["Start Time"] = course_2020_out["Start Time"].astype(str).replace('\.0', '', regex=True)
    course_2020_out["End Time"] = course_2020_out["End Time"].astype(str).replace('\.0', '', regex=True)
    course_2020_out["Days"] = course_2020_out["Days"].str.replace(" ", "")
    course_2020_out.insert(course_2020_out.shape[1], "Exclusively Online", 0)
    course_2020_out.loc[~course_2020_out["RDL"].isnull(),"RDL"] = 1
    course_2020_out.loc[course_2020_out["RDL"].isnull(),"RDL"] =0


    # Merge the cross-list courses
    course_2020_out["Count"] = course_2020_out.groupby(["Cross List Group"])["ENRL Max"].transform("sum")
    course_2020_out["Count"] = course_2020_out["Count"].fillna(course_2020_out["ENRL Max"])
    course_2020_out = course_2020_out[
        (~course_2020_out["Cross List Group"].duplicated()) | course_2020_out["Cross List Group"].isna()]

    # Output Generating
    course_2020_out = course_2020_out[["Subj Code", "Course Number", "Sect", "Count", "Days",
                                       "Start Time", "End Time", "Bldg", "Rm", "Exclusively Online", "use","RDL",
                                       "CRN","Contact Hours"]]

    course_2020_out = course_2020_out.rename(columns={"Subj Code": "Subject Code", "Sect": "Course Section",
                                                      "Count": "Enrollment", "Start Time": "Begin Time",
                                                      "Bldg": "Building Number", "Rm": "Room",
                                                      "use": "Room Use","RDL":"keep assigned room"})

    course_2020_out = course_2020_out.sort_values(by=["Subject Code", "Course Number", "Course Section"],
                                                  na_position='last')

    course_2020_out = course_2020_out[~course_2020_out["Room Use"].isnull()]

    # Customized output file name
    global room_type_global
    if isinstance(room_type_global, str):
        output_path+=("_"+room_type_global)
    else:
        output_path+="_other"

    # Boost Column
    if boost:
        course_2020_out["Level"] = course_2020_out["Course Number"].str[0]
        num_level = len(course_2020_out["Level"].unique())
        level_mapping = dict(zip(sorted(course_2020_out["Level"].unique()), np.array(range(num_level, 0, -1)) / 2))
        course_2020_out["boost"] = course_2020_out["Level"].map(level_mapping)
        course_2020_out = course_2020_out.drop(columns=["Level"])

        output_path+="_boost"

    course_2020_out.to_excel(output_path+".xlsx", index=False)

# Add the enrollment updated file
def InputCourse2020_adjust(course_2020_path,
                    room_input_path,
                    updated_enrollment_path,
                    output_path="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_full_enrollment_2020",
                    boost=False):
    r'''
    Standard course input room file: .xlsx with coulumns: ["Subject Code","Course Number","Course Section","Enrollment",
                                "Days","Begin Time","End Time","Building Number","Room","Exclusively Online","Room Use"]

       Parameters:
       -------------
       course_2019_path: str, default=None
           file path of 2019 course data

       room_input_path: str OR pandas.dataframe default=None
          if a str is passed, it should be the filepath of room input data.
          if a pandas.dataframe passed, it should be the room input data itself.

       output_path: str, default="../Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_example2019.xlsx"
           the output path of the .xlsx file. Save to a new dictionary in /Documents/Madgie_Cleaned_Directory/Data.

       boost: bool, default = False
           if include the boost column

       '''
    print("2020 Course Input data Generating")

    # Read Data
    course_data_2020 = pd.read_excel(course_2020_path)
    if isinstance(room_input_path, str):
        room_input = pd.read_excel(room_input_path)

    else:
        room_input = room_input_path

    # Data Cleaning

    course_data_2020 = course_data_2020[(course_data_2020["Camp"] == "A") | (course_data_2020["Camp"] == "EM")]
    #course_data_2020["Cross List Max ENRL"] = course_data_2020["Cross List Max ENRL"].fillna(course_data_2020["Assumed Enrollment for Planning"])

    course_2020_out = course_data_2020[["Subj Code", "Crse Num", "Sect", "Assumed Enrollment for Planning",
                                        "Days", "Start Time", "End Time", "Bldg", "Rm",
                                        "RDL", "CRN", "Contact Hrs", "Delivery Mode Preference"]]


    # Join the course data with room data
    course_2020_out["bldg_room"] = course_2020_out["Bldg"].astype(str) + "_" + course_2020_out["Rm"].astype(str)
    course_2020_out = course_2020_out.merge(room_input, on="bldg_room", how="left")

    # Columns Formatting
    course_2020_out["Start Time"] = course_2020_out["Start Time"].astype(str).replace('\.0', '', regex=True)
    course_2020_out["End Time"] = course_2020_out["End Time"].astype(str).replace('\.0', '', regex=True)
    course_2020_out["Days"] = course_2020_out["Days"].str.replace(" ", "")
    course_2020_out.insert(course_2020_out.shape[1], "Exclusively Online", 0)
    course_2020_out.loc[~course_2020_out["RDL"].isnull(), "RDL"] = 1
    course_2020_out.loc[course_2020_out["RDL"].isnull(), "RDL"] = 0




    # Columns select
    course_2020_out = course_2020_out[["Subj Code", "Crse Num", "Sect", "Assumed Enrollment for Planning", "Days",
                                       "Start Time", "End Time", "Bldg", "Rm", "Exclusively Online", "use", "RDL",
                                       "CRN", "Contact Hrs", "Delivery Mode Preference"]]

    course_2020_out = course_2020_out.rename(
        columns={"Subj Code": "Subject Code", "Crse Num": "Course Number", "Sect": "Course Section",
                 "Assumed Enrollment for Planning": "Enrollment", "Start Time": "Begin Time",
                 "Bldg": "Building Number", "Rm": "Room",
                 "use": "Room Use", "RDL": "keep assigned room",
                 "Delivery Mode Preference": "Preference"})

    course_2020_out = course_2020_out.sort_values(by=["Subject Code", "Course Number", "Course Section"],
                                                  na_position='last')

    course_2020_out = course_2020_out[(~course_2020_out["Room Use"].isnull()) | course_2020_out["Room"].isnull()]
    course_2020_out = course_2020_out[course_2020_out["Preference"] != "Cancel"]

    # Customized output file name
    global room_type_global
    if isinstance(room_type_global, str):
        output_path += ("_" + room_type_global)
    else:
        output_path += "_other"

    # Boost Column
    if boost:
        course_2020_out["Level"] = course_2020_out["Crse Num"].str[0]
        num_level = len(course_2020_out["Level"].unique())
        level_mapping = dict(zip(sorted(course_2020_out["Level"].unique()), np.array(range(num_level, 0, -1)) / 2))
        course_2020_out["boost"] = course_2020_out["Level"].map(level_mapping)
        course_2020_out = course_2020_out.drop(columns=["Level"])

        output_path += "_boost"




    ## Adjust Enrollment
    updated_enrollment = pd.read_excel(updated_enrollment_path)
    updated_enrollment.drop_duplicates(keep="first", inplace=True)
    course_2020_out = course_2020_out.merge(updated_enrollment[["CRN", "Assumed Enrollment Updated"]], on="CRN", how="left")
    course_2020_out["Enrl"] = course_2020_out["Assumed Enrollment Updated"].fillna(course_2020_out["Enrollment"]).astype(int)
    course_2020_out = course_2020_out.drop(columns=["Enrollment", "Assumed Enrollment Updated"])


    course_2020_out = course_2020_out.rename(columns={"Enrl": "Enrollment", "Contact Hrs": "Contact Hours","Preference": "Raw Preference"})
    course_2020_out = course_2020_out[["Subject Code", "Course Number", "Course Section", "Enrollment","Days",
                                       "Begin Time", "End Time","Building Number", "Room", "Exclusively Online",
                                       "Room Use", "keep assigned room", "CRN", "Contact Hours","Raw Preference"]]

    # Fill NA Class USE
    course_2020_out["Room Use"] = course_2020_out["Room Use"].fillna("Class")

    # Preference Handle
    course_2020_out["Preference"] = course_2020_out["Raw Preference"]
    course_2020_out.loc[course_2020_out["Raw Preference"] == "Hybrid", "Preference"] = "hybrid_split, hybrid_touchpoint,residential_spread"
    course_2020_out.loc[course_2020_out["Raw Preference"] == "Remote", "Preference"] = "remote"
    course_2020_out.loc[course_2020_out["Raw Preference"] == "Residential", "Preference"] = "residential_spread"
    course_2020_out.to_excel(output_path + ".xlsx", index=False)
    return course_2020_out


if __name__ == "__main__":
    room_input = InputRoom("../Documents/Madgie_Raw_Directory/Data/Room_Level_Data_20200522.xlsx",
                           "../Documents/Madgie_Raw_Directory/Data/20200604_CLSLAB_List.xlsx",
                           "../Documents/Madgie_Raw_Directory/Data/ISYE_FallSemesterScenarios_BuildingRooms.xlsx",
                           room_type="Class")


    # InputCourse2019(
    #     course_2019_path="../Documents/Madgie_Raw_Directory/Data/Fall 2019 Schedule of Classes After Crosslisted Sections are combined and no classroom classes removed.xlsx",
    #     room_input_path=room_input,boost=False)

    InputCourse2020_adjust(course_2020_path="../Documents/Madgie_Raw_Directory/Data/Room and Mode Allocator Input File July 9.xlsx",
                           room_input_path=room_input,
                           updated_enrollment_path="../Documents/Madgie_Raw_Directory/Data/Updated enrollments.xlsx",
                           boost=False)
