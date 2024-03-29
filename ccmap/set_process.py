from math import floor
import numpy as np
import pandas as pd
from haversine import haversine


all_permissible_delivery_mode = {"residential_spread",
                                "hybrid_split",
                                "hybrid_touchpoint",
                                "remote"}


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
    Depricated - conrolling for capacity now happens through remove_remote_rooms_availability. 
    However, we way wish to refactor so we are not adding values to the dictoinaries course_data and room_data in get_room_sets
        only to remove them when we run remove_remote_rooms_availability

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


def remove_remote_rooms_availability(bldgroom_section_dictionary,
                                    section_bldgroom_dictionary,
                                    delivery_mode_section_room_dict):

    """ 
    Input:
        bldgroom_section_dictionary - dict(str, str): maps rooms to sections that may be taught in that timeslot
        section_bldgroom_dictionary - dict(str, str): maps sections to rooms in which they may be taught
        delivery_mode_section_room_dict - dict{str: str}: maps a section and room to the delivery mode that the section must take, it's to be taught in that room
            If the value for a (section, room) pair is "remote", it simply means the section may not be taught in that room
    Output:
        bldgroom_section_dictionary - dict(str, str): maps rooms to sections that may be taught in that timeslot
        section_bldgroom_dictionary - dict(str, str): maps sections to rooms in which they may be taught
  
    If the value for a (section, room) pair is "remote", then those sections and rooms should not be compatible according to bldgroom_section_dictionary and section_bldgroom_dictionary
    This method is intended to be used in room_assignment_contact_opt, after the initial bldgroom_section_dictionary and section_bldgroom_dictionary are created
    Using this method is not essential, but will reduce the complexity of the model
    """

    for section, available_room in bldgroom_section_dictionary.items():
        available_room_list = list(available_room)
        for room in available_room_list:
            if delivery_mode_section_room_dict[section, room] == 'remote':
                available_room.remove(room)

    for room, available_section in section_bldgroom_dictionary.items():
        available_section_list = list(available_section)
        for section in available_section_list:
            if delivery_mode_section_room_dict[section, room] == 'remote':
                available_section.remove(section)

    return bldgroom_section_dictionary, section_bldgroom_dictionary


def get_preferred_room_sets(course_data,
                           room_data,
                           room_section_dictionary,
                           section_room_dictionary,
                           permissible_delivery_mode_section_dict,
                           delivery_mode_section_room_dict):

    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        room_data - pd.DataFrame: properly formatted room dataframe
        room_section_dictionary - dict(str, str): maps rooms to sections that may be taught in that timeslot
        section_room_dictionary - dict(str, str): maps sections to rooms in which they may be taught
        permissible_delivery_mode_section_dict - dict{str: set(str)}: maps a section to a list of the delivery modes it may be taught in
    Output:
        preferred_room_section_dictionary - dict(str, set{str}): maps rooms to sections that may be taught in that timeslot according to sections' instruction mode preferences
        preferred_section_room_dictionary - dict(str, set{str}): maps sections to rooms in which they may be taught according to sections' instruction mode preferences
  
    Intended for use in RoomAssignmentPreferencesContactyOpt. This model optimizes the number of sections that are taught in their preferred mode.
    It is therefore necessary to be able to map sections to rooms (and vice versa) that can be used to teach the section in their preferred mode.
    Note that the keys of room_section_dictionary will be idential to that of preferred_room_section_dictionary.
    Moreover, for a given key, the corresponding value in preferred_room_section_dictionary will be a subset of the corresponding value in room_section_dictionary
    """

    preferred_room_section_dictionary = dict()
    for section, available_room_set in room_section_dictionary.items():
        available_room_list = list(available_room_set)
        permissible_delivery_mode_set = permissible_delivery_mode_section_dict[section]
        preferred_room_set = set()
        preferred_room_section_dictionary[section] = preferred_room_set
        for room in available_room_list:
            delivery_mode = delivery_mode_section_room_dict[section, room]
            if delivery_mode in permissible_delivery_mode_set:
                preferred_room_set.add(room)

    preferred_section_room_dictionary = dict()
    for room, available_section_set in section_room_dictionary.items():
        available_section_list = list(available_section_set)
        preferred_section_set = set()
        preferred_section_room_dictionary[room] = preferred_section_set
        for section in available_section_list:
            permissible_delivery_mode_set = permissible_delivery_mode_section_dict[section]
            delivery_mode = delivery_mode_section_room_dict[section, room]
            if delivery_mode in permissible_delivery_mode_set:
                preferred_section_set.add(section)

    return preferred_room_section_dictionary, preferred_section_room_dictionary


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


def get_all_simplieid_timeslot(all_timeslot):
    """
     Input:
        all_timeslot - list[str]: all possible timeslots
    Output:
        all_simplified_timeslot - list[str]: Includes one or more values for each value in all_timeslot
            However, each value only includes dow and beginning time
            e.g. if an entry in all_timeslot is 'M_1000_1115'
            then the corresponding entry in all_simplified_timeslot would be 'M_1000_x'
            Moreover, each day dow element of an entry in all_simplified_timeslot may only involve a single day
            For example, if an entry in all_timeslot is 'MWF_13100_1400', 
            then the corresponding entries in all_simplified_timeslot would be 'M_13100_x', 'W_13100_x', 'F_13100_x'
    """

    all_simplified_timeslot = set()
    for timeslot in all_timeslot:
        dow, start_time, end_time = timeslot.split("_")
        for single_dow in dow:
            simplified_timeslot = single_dow + "_" + start_time + "_x"
            all_simplified_timeslot.add(simplified_timeslot)

    return all_simplified_timeslot

def pad_time_str(timeslot):
    """
    Input:
        timeslot - str: any timeslot value
    Output:
        timeslot - str: identical to input value, with a leading 0 if necessary
                        to ensure the timeslot has a length of 4

    Returns a new string, rather than changing the original string in place
    Helper method to get_overlapping_time_slots() and potential other methods used to manipulate timeslots
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
        raise Exception("timeslot must have 4 digits, may need to call pad_time_str")
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
    """

    current_dow, current_start_time, current_end_time = current_timeslot.split("_")
    current_start_time = pad_time_str(current_start_time)
    current_dow = set(current_dow)
    timeslot_clash = set()

    for other_timeslot in all_timeslot:
        other_dow, other_start_time, other_end_time = other_timeslot.split("_")
        other_dow = set(other_dow)
        other_start_time = pad_time_str(other_start_time)
        other_end_time = pad_time_str(other_end_time)
        if (len(current_dow.intersection(other_dow)) > 0) and (other_start_time <= current_start_time) and (current_start_time < other_end_time):
            timeslot_clash.add(other_timeslot)

    return timeslot_clash


def get_sections_with_overlapping_time_slot(all_timeslot, all_simplified_timeslot, all_section, course_data):
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

    for current_timeslot in all_simplified_timeslot:
        all_conflicting_timeslot = get_overlapping_time_slots(all_timeslot, current_timeslot) #here, current_timeslot should refer only to times from TS. But need to find timeslots from T, that conflict
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
        capacity_room_dictionary - dict{str: str}: maps a room to it's capacity, according to room_data
    """

    capacity_room_dictionary = pd.Series(room_data[capacity_column].values,index=room_data['bldg_room']).to_dict()
    return capacity_room_dictionary


def get_course_time(course_data):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        timeslot_section_dictionary - dict{str: str}: maps a section to its timeslot, according to course_data
    """

    timeslot_section_dictionary = pd.Series(course_data["full_time"].values,index=course_data['subject_course_section_occurrence']).to_dict()
    return timeslot_section_dictionary


def get_num_weekly_meeting_days(timeslot_section_dictionary):
    """
    Input:
        timeslot_section_dictionary - dict{str: str}: maps a section to its timeslot
    Output:
        meeting_days_section_dictionary - dict{str: str}: maps a section to the number of days a week it meets
    """

    num_weekly_meeting_days_section_dictionary = {section: len(timeslot.split("_")[0]) for section, timeslot in timeslot_section_dictionary.items()}
    return num_weekly_meeting_days_section_dictionary


def get_section_room_assignment(output_data):
    """
    Input:
        output_data - pd.DataFrame: properly formatted output dataframe from a room_assignment model
    Output:
        room_section_dict - dict{str: str}: maps a section to its assigned room
    """

    room_section_dict = pd.Series(output_data["bldg_room"].values,index=output_data['subject_course_section_occurrence']).to_dict()
    return room_section_dict


def get_weekly_hours(course_data):
    """ 
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        weekly_hours_section_dictionary - dict{str: str}: maps a section to the number of weekly hours the section meets
    """

    weekly_hours_section_dictionary = pd.Series(course_data["contact_hours"].values,index=course_data['subject_course_section_occurrence']).to_dict()
    return weekly_hours_section_dictionary


def get_timeslot_duration(timeslot):
    """ 
    Input:
        timeslot - str: full timeslot information, formatted as "DOW_starttime_endtime"
    Output:
        duration_hours - float: the duration of the timeslot for a single meeting day
            e.g. if timeslot = "MWF_1000_1115", then duration_hours = 1.25
            if timeslot = "F_1300_1445", then duration_hours = 1.75
    Intended as a helper function to get_meeting_hours
    """

    dow, start_time, end_time = timeslot.split("_")
    start_time = pad_time_str(start_time)
    end_time = pad_time_str(end_time)
    duration_hours = (int(end_time[:2]) - int(start_time[:2])) + (int(end_time[2:]) - int(start_time[2:]))/60
    if duration_hours < 0:
        raise Exception("duration hours neg: " + str(timeslot) + " " + start_time + " " + end_time)
    elif duration_hours > 8:
        raise Exception("duration hours large: " + str(timeslot) + " " + start_time + " " + end_time)
    return duration_hours


def get_meeting_hours(timeslot_section_dictionary):
    """
    Input:
        timeslot_section_dictionary - dict{str: str}: maps a section to its timeslot
    Output:
        meeting_hours_section_dictionary - dict{str: str}: maps a section to the number of hours it meets, on any day it meetings
    """

    meeting_hours_section_dictionary = {section: get_timeslot_duration(timeslot) for section, timeslot in timeslot_section_dictionary.items()}
    return meeting_hours_section_dictionary


def get_contact_hours(all_section,
                      all_room,
                      capacity_room_dictionary,
                      enrollment_section_dictionary,
                      meeting_hours_section_dictionary,
                      num_weekly_meeting_days_section_dictionary,
                      minimum_section_contact_days,
                      weeks_in_semester,
                      preferred_delivery_mode_section_dict=None):

    """
    Input:
        all_section - set(str): set of all sections available in the optimization problem
        all_room - set(str): set of all rooms available in the optimization problem
        capacity_room_dictionary -  dict{str: str}: maps a room to it's capacity 
        enrollment_section_dictionary - dict{str: str}: maps a section to it's enrollment
        meeting_hours_section_dictionary - dict{str: str}: maps a section to its the number of hours it meets, on any day it meetings
        num_weekly_meeting_days_section_dictionary -  dict{str: int}: maps a section to the number of days a week it meets
        minimum_section_contact_days - int: minimum number of days any section must meet in person, in a semester
        weeks_in_semester - int: number of weeks in the semester; it's assumed these are full weeks
    Output:
        total_contact_hours_section_room_dict - dict{str: str}: maps a section and room to the contact hours the section would have, if it were assigned to the given room
        delivery_mode_section_room_dict - dict{str: str}: maps a section and room to the delivery mode that the section must take, it's to be taught in that room
    """

    total_contact_hours_section_room_dict = dict()
    delivery_mode_section_room_dict = dict()
    for section in all_section:
        for room in all_room:
            if preferred_delivery_mode_section_dict is not None:
                preferred_delivery_mode_set = preferred_delivery_mode_section_dict[section]
            else:
                preferred_delivery_mode_set = all_permissible_delivery_mode
            total_contact_hours, delivery_mode = get_contact_hours_helper(capacity=capacity_room_dictionary[room],
                                                                          enrollment=enrollment_section_dictionary[section],
                                                                          meeting_hours=meeting_hours_section_dictionary[section],
                                                                          weekly_meeting_days=num_weekly_meeting_days_section_dictionary[section],
                                                                          minimum_section_contact_days=minimum_section_contact_days,
                                                                          weeks_in_semester=weeks_in_semester,
                                                                          preferred_delivery_mode_set=preferred_delivery_mode_set)

            total_contact_hours_section_room_dict[section, room] = total_contact_hours
            delivery_mode_section_room_dict[section, room] = delivery_mode

    return total_contact_hours_section_room_dict, delivery_mode_section_room_dict


def get_contact_hours_helper(capacity,
                             enrollment,
                             meeting_hours,
                             weekly_meeting_days,
                             minimum_section_contact_days,
                             weeks_in_semester,
                             preferred_delivery_mode_set):
    """
    Input:
        capacity - int: capacity for the room on interest
        enrollment - int: enrollment for the section of interest
        meeting_hours - float: the number of hours the section of interest meetings, on any day it meeints
        weekly_meeting_days - int: number of days a week the section of interet meets
    Output:
        contact_hours - float: number of contact hours for the section of interest if it is scheduled in the room of interest
        delivery_mode -  str: delivery mode that the section must take, it's to be taught in that room
                              possible values are: "residential_spread", "hybrid_split", "hybrid_touchpoint", "remote"

    Inteneded as a helper method to get_contact_hours.
    All input paramters are specific to a given room and section.
    """

    if enrollment <= capacity:
        if "residential_spread" in preferred_delivery_mode_set:
            return meeting_hours * weekly_meeting_days, "residential_spread"
        else:
            return meeting_hours * (weekly_meeting_days - 1), "residential_spread"
    elif enrollment <= weekly_meeting_days * capacity:
        for limited_weekly_meeting_days in range(2, weekly_meeting_days + 1):
            if enrollment <= limited_weekly_meeting_days * capacity:
                contact_days_per_week = weekly_meeting_days - limited_weekly_meeting_days + 1
                contact_hours = meeting_hours * contact_days_per_week
                return contact_hours, "hybrid_split"
    elif enrollment <= weeks_in_semester * weekly_meeting_days * capacity / minimum_section_contact_days:
        avg_contact_days_per_week = floor(weeks_in_semester * weekly_meeting_days * capacity / enrollment) / weeks_in_semester
        contact_hours = meeting_hours * avg_contact_days_per_week
        return contact_hours, "hybrid_touchpoint"
    else:
        return 0, "remote"

def get_contact_hours_no_mixing_helper(capacity,
                                      enrollment,
                                      meeting_hours,
                                      weekly_meeting_days,
                                      minimum_section_contact_days,
                                      weeks_in_semester,
                                      preferred_delivery_mode_set):
    """
    Input:
        capacity - int: capacity for the room on interest
        enrollment - int: enrollment for the section of interest
        meeting_hours - float: the number of hours the section of interest meetings, on any day it meeints
        weekly_meeting_days - int: number of days a week the section of interet meets
    Output:
        contact_hours - float: number of contact hours for the section of interest if it is scheduled in the room of interest
        delivery_mode -  str: delivery mode that the section must take, it's to be taught in that room
                              possible values are: "residential_spread", "hybrid_split", "hybrid_touchpoint", "remote"

    Inteneded as a helper method to get_contact_hours. 
    It is an alternative function that may be called instead of get_contact_hours_helper. The difference is in the contact_hours calculation for the hyrid_split mode.
    Specifically, this method involves distinct cohorts of students so that students in each cohort never meet students from the other cohorts when attending their class for the section
    All input paramters are specific to a given room and section.
    """

    if enrollment <= capacity:
        delivery_mode = "residential_spread"
    elif capacity < enrollment and enrollment <= weekly_meeting_days * capacity:
        delivery_mode = "hybrid_split"
    elif enrollment <= weeks_in_semester * weekly_meeting_days * capacity / minimum_section_contact_days:
        delivery_mode = "hybrid_touchpoint"
    else:
        delivery_mode = "remote"

    if enrollment == 0:
        contact_hours = 0
    elif enrollment <= capacity and "residential_spread" in preferred_delivery_mode_set:
        contact_hours = meeting_hours * weekly_meeting_days
    elif weekly_meeting_days in {2,3} and enrollment <= weekly_meeting_days * capacity:
        contact_hours = meeting_hours
    elif weekly_meeting_days == 4 and 2 * capacity < enrollment and enrollment <= 4 * capacity:
        contact_hours = meeting_hours
    elif weekly_meeting_days == 4 and enrollment <= 2 * capacity:
        contact_hours = 2 * meeting_hours
    elif enrollment <= weeks_in_semester * weekly_meeting_days * capacity / minimum_section_contact_days:
        avg_contact_days_per_week = floor(weeks_in_semester * weekly_meeting_days * capacity / enrollment) / weeks_in_semester
        contact_hours = meeting_hours * avg_contact_days_per_week
    else:
        contact_hours = 0

    return contact_hours, delivery_mode


def get_priority_boost(course_data,
                      all_section):
    """
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        all_section - set(str): set of all sections available in the optimization problem
    Output:
        priority_boost_section_dict - dict{str: float}: maps each section to the priority of that section

    The priority of a section is used as a weighting factor in the objective function of the room_assignment_contact_opt model
    This model maximizes total contact hours. The contact hours of a section will then be weighted by priority_boost_section_dict
    """

    if "priority" in course_data.columns:
        priority_boost_section_dict = pd.Series(course_data["priority"].values,index=course_data['subject_course_section_occurrence']).to_dict()
    else:
        priority_boost_section_dict = {section: 1 for section in all_section}
    return priority_boost_section_dict



def get_unit_section_sets(course_data,
                         all_section):
    """
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        all_section - set(str): set of all sections available in the optimization problem
    Output:
        section_unit_dict - dict{str: str}: maps each unit to a set of all sections in that unit
        unit_section_dict - dict{str: set(str)}: maps each section to its corresponding unit
    
    Intended for use in room_assignment_contact_opt_building_pref, where the relationship between specific sections
        and their corresponding units is relevant in determining sections' building and room assignments
    """

    unit_section_dict = dict()
    section_unit_dict = dict()
    for section in all_secction:
        corresponding_unit = all_section[all_section['subject_course_section_occurrence']==section]['subject_code'][0]
        unit_section_dict[section] = corresponding_unit
        if corresponding_unit in section_unit_dict:
            section_unit_dict[corresponding_unit].add(section)
        else:
            section_unit_dict[corresponding_unit] = {section}

    return unit_section_dict, section_unit_dict


def get_room_building_sets(all_room, course_data=None):
    """
    Input:
        all_room - list(str): set of all rooms available in the optimization problem
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        room_building_dict - dict{str: str}: maps each building to a set of all room in that building
        building_room_dict - dict{str: str}: maps each room to its corresponding building
    
    Intended for use in room_assignment_contact_opt_building_pref, where the relationship between specific rooms
        and their buildings units is relevant in determining sections' building and room assignments
    Recall that each room in all_room already encodes building information. Specifically, each room is specified as
        "buildingcode_roomnumber". In the output dictionaries, rooms are specified in the same manner, and the building
        code from the prefix of each room is used. For example, if a all_room contains the entries:
        "172_102, 172_224, 172_300, 172_101", then room_building_dict may contain the the key value paid:
        "172": {"172_102, 172_224, 172_300, 172_101"}
    """

    all_room = set(all_room)
    if course_data is not None:
        rooms_from_course_data = set(str(row["building_number"]) + "_" + str(row["room"]) for index, row in course_data.iterrows())
        all_room.update(rooms_from_course_data)
    room_building_dict = dict()
    building_room_dict = dict()
    for bldg_room in all_room:
        building = bldg_room.split("_")[0]
        building_room_dict[bldg_room] = building
        if building in room_building_dict:
            room_building_dict[building].add(bldg_room)
        else:
            room_building_dict[building] = {bldg_room}


    return room_building_dict, building_room_dict

def get_unit_building_sets(unit_requirements_data):
    """
    Input:
        unit_building_data - pd.DataFrame: properly formatted unit building dataframe
    Output:
        fraction_unit_building_dict - dict{(str, str): float}: maps tuples of unit code and building number to the desired fraction of
            a given unit's sections we wish to assign to the given building. Note there does not need to be an entry each possible
            combination of units and buildings. We simply include elements if there is a corresponding room in unit_requirements_data

    Intended for use in room_assignment_contact_opt_building_pref, room assignments will be influenced by fraction_unit_building_dict
    """

    unit_building_tuples = [(row["subject_code"], row["building_number"]) for row in unit_requirements_data.iterrows()]
    fraction_unit_building_dict = pd.Series(unit_requirements_data["fraction"].values,index=unit_building_tuples).to_dict()
    return fraction_unit_building_dict

def get_assigned_delivery_mode(output_data):
    """
    Input:
        output_data - pd.DataFrame: properly formatted output dataframe
    Output:
        output_delivery_mode_section_dict - dict{str: set(str)}: maps a section to a list of the delivery modes it may be taught in
    """

    output_delivery_mode_section_dict = pd.Series(output_data['delivery_mode'].values,index=output_data['subject_course_section_occurrence']).to_dict()
    return output_delivery_mode_section_dict


def get_preferred_delivery_mode(course_data,
                                 all_section):
    """
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
        all_section - set(str): set of all sections available in the optimization problem
    Output:
        permissible_delivery_mode_section_dict - dict{str: set(str)}: maps a section to a list of the delivery modes it may be taught in
    """

    if 'preference' not in course_data.columns: 
        permissible_delivery_mode_section_dict = {section: all_permissible_delivery_mode for section in all_section}
    else:
        permissible_delivery_mode_all = [{permissible_mode.strip() for permissible_mode in permissible_mode_full_str.split(",")} if type(permissible_mode_full_str) is str else all_permissible_delivery_mode for permissible_mode_full_str in course_data["preference"].values]
        permissible_delivery_mode_section_dict = pd.Series(permissible_delivery_mode_all,index=course_data['subject_course_section_occurrence']).to_dict()
    return permissible_delivery_mode_section_dict

def get_existing_room_assignment_section_dict(course_data):

    """
    Input:
        course_data - pd.DataFrame: properly formatted course dataframe
    Output:
        existing_room_assignment_section_dict - dict{str: str}: maps each section to its existing room assignment
    """

    if "building_number" not in course_data.columns or "room" not in course_data.columns:
        raise Exception("course_data must include columns 'building_number' and 'room' in order to call get_existing_room_assignment_section_dict")

    indecies_w_room_assignment = (course_data["room"].notnull()) & (course_data["building_number"].notnull())
    subject_course_section_occurrence_list = course_data[indecies_w_room_assignment]['subject_course_section_occurrence'].tolist()
    bldg_room_list = (course_data[indecies_w_room_assignment]["building_number"].astype(str) + "_" + course_data[indecies_w_room_assignment]["room"].astype(str)).tolist()
    existing_room_assignment_section_dict = pd.Series(bldg_room_list,index=subject_course_section_occurrence_list).to_dict()
    return existing_room_assignment_section_dict

def get_output_room_section_dict(output_data):
    """
    Input:
        output_data - pd.DataFrame: properly formatted output dataframe
    Output:
        output_room_section_map - dict{str: str}: maps each section to its assigned room in output_data
    """

    output_room_section_map = pd.Series(output_data['bldg_room'].values,index=output_data['subject_course_section_occurrence'].tolist()).to_dict()
    return output_room_section_map

def get_dist_between_buildings(building_location_data,
                              all_building,
                              square_distance=True):
    """
    Input:
        building_location_data - pd.DataFrame: properly formatted building location dataframe
        all_building - set{str}: set of all buildings
        square_distance - bool: If True, the square of distances between buildings is used instead of the actual distance
                                This may be ideal if one wishes to penalize large values more healvily
    Output:
        dist_between_building_dict - dict{(str, str): float}: maps each pairs of buildings, to the distance between these buildings in meters
    """

    lat_building_dict = pd.Series(building_location_data["latitude"].values,index=building_location_data['building_number']).to_dict()
    lng_building_dict = pd.Series(building_location_data["longitude"].values,index=building_location_data['building_number']).to_dict()

    building_w_location = building_location_data['building_number'].tolist()
    building_w_location_pair = [(building_1, building_2) for building_1 in building_w_location for building_2 in building_w_location]
    all_building_pair = [(building_1, building_2) for building_1 in all_building for building_2 in all_building]
    building_wo_location_pair = [building_pair for building_pair in all_building_pair if building_pair not in building_w_location_pair]
    
    dist_between_building_dict = dict()
    for building_1, building_2 in building_w_location_pair:
        distance = haversine((lat_building_dict[building_1], lng_building_dict[building_1]),
                                 (lat_building_dict[building_2], lng_building_dict[building_2]),
                                 unit='m')
        if square_distance:
            dist_between_building_dict[building_1, building_2] = distance ** 2
        else:
            dist_between_building_dict[building_1, building_2] = distance
    
    avg_building_dist = sum(dist_between_building_dict.values())/len(dist_between_building_dict.values())
    
    for building_1, building_2 in building_wo_location_pair:
        dist_between_building_dict[building_1, building_2] = avg_building_dist

    return dist_between_building_dict

def get_reassignment_cost(all_section,
                          all_room,
                          dist_between_building_dict,
                          existing_room_assignment_section_dict,
                          building_room_dict,
                          same_building_penalty=50):
    """
    Input:
        all_section - set(str): set of all sections available in the optimization problem
        all_room - set(str): set of all rooms available in the optimization problem
        dist_between_building_dict - dict{(str, str): float}: maps each pairs of buildings, to the distance between these buildings in meters
        existing_room_assignment_section_dict - dict{str: set(str)}: maps each section to its existing room assignment
        building_room_dict - dict{str: str}: maps each room to its corresponding building
        delta - float: if two rooms are in the same building, then the cost of reassignment bewteen these two rooms will be equal to: delta * min(dist_between_building_dict.values())
    Output:
        reassginment_cost_section_room_dict - dict{(str, str): float} - maps a (section, room) pair to the cost of reassigning the section to that room
    """

    reassginment_cost_section_room_dict = dict()
    for section in all_section:
        if section in existing_room_assignment_section_dict:
            existing_room_assignment = existing_room_assignment_section_dict[section]
            existing_building_assignment = building_room_dict[existing_room_assignment]
            for room in all_room:
                building = building_room_dict[room]
                if existing_room_assignment == room:
                    penalty = 0
                elif existing_building_assignment == building:
                    penalty = same_building_penalty
                else:
                    penalty = dist_between_building_dict[existing_building_assignment, building]
                reassginment_cost_section_room_dict[section, room] = penalty
        else:
            for room in all_room:
                reassginment_cost_section_room_dict[section, room] = 0
    return reassginment_cost_section_room_dict
