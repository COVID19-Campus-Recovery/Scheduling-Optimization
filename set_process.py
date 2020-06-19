import numpy as np
import pandas as pd

all_day = ("M", "T", "W", "R", "F")

F = [0, 6, 8, 12]

k_f = {0:10000,6:20,8:10,12:5}

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


def get_section_set(course_data, all_course):
    """
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        all_course - set(str): set of all courses available in the optimization problem
    Output:
        section_course_dict dict(str: str): maps courses to all sections of that course
    """

    section_course_dict = dict()
    for course_current in all_course:
        section_course_dict[course_current] = course_data[course_data['subject_course_section'] == course_current][
            'subject_course_section_occurrence'].tolist()
    return section_course_dict


def get_student_sets(student_data, all_section):
    """ 
    Depricated (at least temporarily)
    A revised version of this method, considering the proper input data format
    will likely be created after we have finalized how individual students will 
    be considered in the optimization model
    """
    student_data.fillna("-", inplace=True)
    section_student_dict = dict()
    for row in student_data.iterrows():
        s_courses = []
        for c in course_columns:
            if "ISYE" in row[1][c]:
                templist = row[1][c].split()
                course_section = '_'.join(templist[:3])
                for i in range(3):
                    standard_form = course_section + "_" + str(i)
                    if standard_form in all_section:
                        s_courses.append(standard_form)
        section_student_dict[row[1]["SYSGENID"]] = s_courses
    # set of courses that student is enrolled in
    course_student_dict = dict()
    for s, x in section_student_dict.items():
        cou = set()
        for i in x:
            cou.add(i[:9])
        course_student_dict[s] = list(cou)
    return section_student_dict, course_student_dict


def get_timeslot_sets(course_data, all_section, all_timeslot):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        all_section - set(str): set of all sections available in the optimization problem
        all_timeslot - set(str): set of all timeslots available in the optimization problem
    Output:
        timeslot_section_dictionary - dict(str, str): maps timeslots to sections that may be taught in that timeslot
        section_timeslot_dictionary - dict(str, str): maps sections to timeslots in which they may be taught
        timeslot_day_dictionary - dict(str, str): maps timeslots to days of the week where the timeslot if taught

    Currently, this method does not enforce any restrictions and allows any section to be assigned to any time
    This method is to be used by the ScheduleOpt model, and potentially other classes that inherit ScheduleOpt
    this method is not NOT to be used by RoomAssignmentOpt, or any classes that inherit RoomAssignmentOpt, 
        as this set is irrelevant to the formulation for RoomAssignmentOpt
    """

    timeslot_section_dictionary = dict()
    for section in all_section:
        timeslot_section_dictionary[section] = course_data[course_data["subject_course_section_occurrence"] == x]["full_time"].tolist()

    section_timeslot_dictionary = dict()
    for timeslot in all_timeslot:
        section_timeslot_dictionary[timeslot] = all_section

    # associate times with days of week
    timeslot_day_dictionary = dict()
    for day in all_day:
        relevant_time_slots = [timeslot for timeslot in all_timeslot if type(timeslot) is str and day in timeslot]
        timeslot_day_dictionary[day] = relevant_time_slots

    return timeslot_section_dictionary, section_timeslot_dictionary, timeslot_day_dictionary


def get_room_sets_capacity_restricted(course_data, room_data, all_room, all_section):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        room_data - pd.DataFrame: properly formatted room dataframe
        all_section - set(str): set of all sections available in the optimization problem
        all_room - set(str): set of all rooms available in the optimization problem
    Output:
        room_section_dictionary - dict(str, str): maps rooms to sections that may be taught in that timeslot
        section_room_dictionary - dict(str, str): maps sections to rooms in which they may be taught

    Uses rooms' capacities and sections enrollment to determine whether it is feasible to assign a section to a given room
    The interpretation of the capacity and enrollment field is irrelevant to this method. 
    The meaning of the capacity and enrollment fields is determined when designing the input data files used to generate room_data and course data
        and the restriction is enforced by this method regardless of the meaning.
    Other methods, such as get_rooms_set_trivial, can alternatively be used to generate room_section_dictionary and section_room_dictionary
        if this restriction is not desired
    """
    room_section_dictionary = dict()
    section_room_dictionary = dict()
    for room in all_room:
        relevant_sections_for_room = list()
        for section in all_section:
            if section in room_section_dictionary:
                relevant_room_for_sections = room_section_dictionary[section]
            else:
                relevant_room_for_sections = list()
                room_section_dictionary[section] = relevant_room_for_sections
            room_capacity = room_data[room_data['bldg_room'] == room]["capacity"].iloc[0] #changed Rm Max Cap to capacity
            course_enrollment_capacity = \
            course_data[course_data['subject_course_section_occurrence'] == section]['enrollment'].iloc[0] #changed Max Enroll to enrollment
            if room_capacity >= course_enrollment_capacity:
                relevant_sections_for_room.append(section)
                relevant_room_for_sections.append(room)
        section_room_dictionary[room] = relevant_sections_for_room
    return room_section_dictionary, section_room_dictionary


def get_room_sets(course_data, room_data, all_room, all_section):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        room_data - pd.DataFrame: properly formatted room dataframe
        all_section - set(str): set of all sections available in the optimization problem
        all_room - set(str): set of all rooms available in the optimization problem
    Output:
        bldgroom_section_dictionary - dict(str, str): maps rooms to sections that may be taught in that timeslot
        section_bldgroom_dictionary - dict(str, str): maps sections to rooms in which they may be taught
   
    The "use" column of room_data and the "room_use" column of all_sections
        are used to determine which sections may be taught in each room
    A room may only have one "use", while a section might have multiple valid
        "room_use" values, which should already be comma separated
    For example, a row in course_data may have the string "class,conference room"
        in the "room_use" column. This indicates that any bldgroom in room_data
        with a value of "class" or "conference room" in its "use" is applicable 
        to the given row in course_data

    The implmentation bellow is naive and may be improved for runtime
    """


    #naive implementation
    bldgroom_section_dictionary = dict()
    section_bldgroom_dictionary = dict()
    use_section_dict = pd.Series(course_data['room_use'].values,index=course_data['subject_course_section_occurrence']).to_dict()
    use_section_dict = {section: use.replace(" ", "").split(",") for section, use in use_section_dict.items()}
    use_bldgroom_dict = pd.Series(room_data['use'].values,index=room_data['bldg_room']).to_dict()
    use_bldgroom_dict = {bldgroom: use.replace(" ", "") for bldgroom, use in use_bldgroom_dict.items()}
    
    for bldgroom in all_room:
        section_bldgroom_dictionary[bldgroom] = set()

    for section in all_section:
        current_section_all_use = set(use_section_dict[section])
        bldgroom_current_section = set() #initialize set of bldgroom for current section
        for bldgroom in all_room:
            current_room_use = use_bldgroom_dict[bldgroom]
            if current_room_use in current_section_all_use:
                bldgroom_current_section.add(bldgroom)
                section_bldgroom_dictionary[bldgroom].add(section)
        bldgroom_section_dictionary[section] = bldgroom_current_section #let the value of bldgroom_section_dictionary point to this set

    return bldgroom_section_dictionary, section_bldgroom_dictionary


def get_room_sets_trivial(course_data, room_data, all_room, all_section):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        room_data - pd.DataFrame: properly formatted room dataframe
        all_section - set(str): set of all sections available in the optimization problem
        all_room - set(str): set of all rooms available in the optimization problem
    Output:
        room_section_dictionary - dict(str, str): maps rooms to sections that may be taught in that timeslot
        section_room_dictionary - dict(str, str): maps sections to rooms in which they may be taught

    Should be used if every room should be made available to every section.
    This is unrealistic for generating final results, but this method may be useful for testing and model validation purposes
    """

    room_section_dictionary = dict()
    section_room_dictionary = dict()
    for room in all_room:
        section_room_dictionary[room] = all_section
    for section in all_section:
        room_section_dictionary[section] = all_room
    return room_section_dictionary, section_room_dictionary


def get_capacity_sets(room_data):
    """
    Depricated
    """
    n_rf = dict()
    for f in F:
        if f == 0:
            temp = dict(zip(room_data["bldg_room"], room_data["Station Count (Current)"]))
        else:
            colname = "%d' Module Capacity at %dsf" % (f, f ** 2)
            temp = dict(zip(room_data["bldg_room"], room_data[colname]))

        for k, v in temp.items():
            n_rf[(k, f)] = int(v)

    return n_rf


def get_size_set(section_student_dict):
    """
    Depricated
    """
    S_x = {}
    p_x = {}
    for s, x in section_student_dict.items():
        for i in x:
            if i not in S_x.keys():
                S_x[i] = [s]
            else:
                S_x[i].append(s)

    for k, v in S_x.items():
        p_x[k] = len(v)

    return S_x, p_x


def get_noroom_section_sets(course_data, Size_x):
    """
    Depricated
    """
    # X_wo_room: a set of sections that have no room assignment in 2019 fall
    X_wo_room = set()

    for x, n in Size_x.items():
        room = course_data[course_data['subject_course_section_occurrence'] == x]['bldg_room'].iloc[0]
        if str(room) == "nan":
            X_wo_room.add(x)
    return X_wo_room


def get_section_w_time(T_x):
    """
    Depricated
    """
    #X_w_time: a set of sections that have no time assignment in 2019 fall
    X_w_time = list(dict(filter(lambda ele: np.NaN not in ele[1], T_x.items())).keys())
    return X_w_time


def generate_simple_time_intervals(min_hour=6,max_hour=20,interval_length=0.25):
    """
    Depricated
    """
    all_dow = ['M', 'T', 'W', 'R', 'F']

    minute_values = [int(60*interval_length*i) for i in range(int(1/interval_length))]
    all_times_of_day = list()
    for hour in range(min_hour, max_hour):
        all_times_of_day.append(str(hour)+"00")
        for minute_value in minute_values[1:]:
            all_times_of_day.append(str(hour)+str(minute_value))
        
    all_times_of_day.append(str(max_hour) +"00")

    all_time_intervals=list()
    for dow in all_dow:
        for i in range(len(all_times_of_day)-1):
            all_time_intervals.append(dow + "_" + all_times_of_day[i] + "_" + all_times_of_day[i+1])

    return(all_time_intervals)


def get_sections_with_overlapping_time_slot_depricated(all_timeslot, all_section, course_data, timeinterval):
    """ 
    Depricated
    """

    X_t_clash = dict()
    X_timeslot = dict()

    for section in all_section:
        timeslot_current_section = course_data[course_data['subject_course_section_occurrence'] == section]["full_time"].iloc[0]
        if timeslot_current_section in X_timeslot:
            X_timeslot[t_current_section].add(section)
        else:
            X_timeslot[t_current_section] = {section}

    section_student_dictimpletime = dict()
    for simpletime in timeinterval:
        timeslots_conflicting = get_overlapping_time_slots(all_timeslot, simpletime)
        sections_conflicting = set()
        for timeslot in timeslots_conflicting:
            if timeslot in X_timeslot:
                sections_conflicting = sections_conflicting.union(X_timeslot[timeslot])
        section_student_dictimpletime[simpletime] = sections_conflicting

    return section_student_dictimpletime


def pad_timeslot_str(timeslot):
    """
    Input:
        timeslot - str: any timeslot value
    Output:
        timeslot - str: identical to input value, with a leading 0 if necessary
                        to ensure the timeslot has a length of 4

    Returns a new string, rather than changing the original string in place
    Helper method to get_overlapping_time_slots()
    """

    if type(timeslot) is not str:
        raise Exception("timeslot must be of type str")
    if len(timeslot) not in {3, 4}:
        raise Exception("timeslot read from data must have 3 or 4 digits. Ex. 900, 1300")
    elif len(timeslot) == 3:
        return "0" + timeslot
    else:
        return timeslot


def add_to_timeslot(timeslot, minutes):
    """
    Input:
        timeslot - str: any timeslot value. Must have 4 digits
        minutes - str: 
    Output:
        timeslot - str: equivalent to timeslot, but with minutes added
    """

    if len(timeslot) != 4:
        raise Exception("timeslot must have 4 digits, may need to call pad_timeslot_str")
    if len(minutes) != 2:
        raise Exception("minutes must have 2 digits")

    total_minutes = int(timeslot[3:]) + int(minutes)
    if total_minutes > 60:
        adjusted_minutes = total_minutes - 60
        total_hours = int(timeslot[:3]) + 1
        return str(total_hours) + str(adjusted_minutes)
    else:
        return timeslot[:3] + str(total_minutes)

def get_overlapping_time_slots(all_timeslot, current_timeslot):

    """
    Input:
        all_timeslot - list[str]: all possible timeslots
        current_timeslot - str: timeslot currently being considered
                                Timeslots must be formated as: "dow_starttime_endtime"
    Output:
        timeslot_clash: subset of timeslots from T which conflict with t
            For example, say current_timeslot = 'F_1010_1205'
            Then timeslot_clash may look like {'F_1010_1205', 'F_1115_1205', 'MWF_1010_1100'}
            However timeslot_clash could not include 'F_905_955' or 'TR_1200_1445'

    This method is intended as a helper method to get_sections_with_overlapping_time_slot()

    TODO: enforce 15 minute time gap between sections
    """

    current_dow, current_start_time, current_end_time = current_timeslot.split("_")
    current_start_time = pad_timeslot_str(current_start_time)
    current_end_time = pad_timeslot_str(current_end_time)
    current_dow = set(current_dow)

    timeslot_clash = set()
    for other_timeslot in all_timeslot:
        if type(other_timeslot) is float:
            continue
        other_dow, other_start_time, other_end_time = other_timeslot.split("_")
        other_dow = set(other_dow)
        other_start_time = pad_timeslot_str(other_start_time)
        other_end_time = pad_timeslot_str(other_end_time)
        # if (len(current_dow.intersection(other_dow)) > 0) and (other_start_time < current_end_time) and (current_start_time < other_end_time):
        if (len(current_dow.intersection(other_dow)) > 0) and (other_start_time <= current_start_time) and (current_start_time < other_end_time):

            timeslot_clash.add(other_timeslot)

    return timeslot_clash


def get_sections_with_overlapping_time_slot(all_timeslot, all_section, course_data, timeslot):
    """ 
    Input:
        all_timeslot - list[str]: set of all timeslots available in the optimization problem
                                Timeslots must be formated as: "dow_starttime_endtime"
        all_section - list[str]: set of all sections available in the optimization problem
                                Sections must be formatted as: "subject_course_section_occurrence"
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        section_timeslot_clash_dictionary - dict{str: set{str}}: All times in T are included as a key
                    The corresponding values represent the sections that conflict with the time for that section
                    For example, X_t_clash['F_1010_1205'] will include any sections that are taught at the 
                    following times accourding to course_data
                    'F_1010_1205', 'F_1115_1205', or 'MWF_1010_1100'
    """

    section_timeslot_dictionary = dict() #store sections that are taught at a given timeslot

    for section in all_section:
        timeslot_current_section = course_data[course_data['subject_course_section_occurrence'] == section]["full_time"].iloc[0]
        if timeslot_current_section in section_timeslot_dictionary:
            section_timeslot_dictionary[timeslot_current_section].add(section)
        else:
            section_timeslot_dictionary[timeslot_current_section] = {section}

    section_timeslot_clash_dictionary = dict() #stores sections that are taught a timeslot that conflicts with the given timeslot

    for current_timeslot in all_timeslot:
        all_conflicting_timeslot = get_overlapping_time_slots(all_timeslot, current_timeslot)
        sections_conflicting = set()
        for conflicting_timeslot in all_conflicting_timeslot:
            if conflicting_timeslot in section_timeslot_dictionary:
                sections_conflicting = sections_conflicting.union(section_timeslot_dictionary[conflicting_timeslot])
        section_timeslot_clash_dictionary[current_timeslot] = sections_conflicting

    return section_timeslot_clash_dictionary


def get_enrollement_per_section(course_data, enrollment_column='enrollment'):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        enrollment_section_dict - dict{str: str}: maps a section to it's enrollment, according to course_data

    Todo: This method is very simple and repetitive, considering the the two methods that follow.
        Should consider a more elegant design.
    """

    enrollment_section_dictionary = pd.Series(course_data[enrollment_column].values,index=course_data['subject_course_section_occurrence']).to_dict()
    return enrollment_section_dictionary


def get_room_capacity(room_data, capacity_column='capacity'):
    """ 
    Input:
        room_data - pd.DataFrame: properly formatted room dataframe
    Output:
        enrollment_section_dict - dict{str: str}: maps a section to it's enrollment, according to room_data
    """

    capacity_room_dictionary = pd.Series(room_data[capacity_column].values,index=room_data['bldg_room']).to_dict()
    return capacity_room_dictionary


def get_course_time(course_data):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        timeslot_section_dictionary - dict{str: str}: maps a section to it's timeslot, according to course_data
    """

    timeslot_section_dictionary = pd.Series(course_data["full_time"].values,index=course_data['subject_course_section_occurrence']).to_dict()
    return timeslot_section_dictionary

