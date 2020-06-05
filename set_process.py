import numpy as np
D = ("M", "T", "W", "R", "F")

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


def get_section_set(course_data, C):
    # Sections for each course
    X_c = dict()
    for c_current in C:
        X_c[c_current] = course_data[course_data['course_subject_number'] == c_current][
            'subject_number_section_orrurance'].tolist()
    return X_c


def get_student_sets(student_data, X):
    # set of sections which each student is enrolled
    # change the student registeration courses to standard form: subject_number_section_orrurance
    student_data.fillna("-", inplace=True)
    X_s = dict()
    for row in student_data.iterrows():
        s_courses = []
        for c in course_columns:
            if "ISYE" in row[1][c]:
                templist = row[1][c].split()
                course_section = '_'.join(templist[:3])
                for i in range(3):
                    standard_form = course_section + "_" + str(i)
                    if standard_form in X:
                        s_courses.append(standard_form)
        X_s[row[1]["SYSGENID"]] = s_courses
    # set of courses that student is enrolled in
    C_s = dict()
    for s, x in X_s.items():
        cou = set()
        for i in x:
            cou.add(i[:9])
        C_s[s] = list(cou)
    return X_s, C_s


def get_timeslot_sets(course_data,X, T):
    # Associate sections and time slots
    # For now, we don't enforce any restrictions and
    # allow any section to be assigned to any time

    # For now, we don't enforce any restrictions and allow any section to be assigned to any time
    T_x = dict()
    for x in X:
        T_x[x] = course_data[course_data["subject_number_section_orrurance"] == x]["full_time"].tolist()

    X_t = dict()
    for t in T:
        X_t[t] = X
    # associate times with days of week
    T_d = dict()
    for d in D:
        relevant_time_slots = [t for t in T if type(t) is str and d in t]
        T_d[d] = relevant_time_slots
    return T_x, X_t, T_d


def get_room_sets(course_data, room_data, R, X):
    # associate classrooms with applicable sections
    # currently, the only restriction we account for are course capacities
    R_x = dict()
    X_r = dict()
    for r in R:
        relevant_sections_for_room = list()
        for x in X:
            if x in R_x:
                relevant_room_for_sections = R_x[x]
            else:
                relevant_room_for_sections = list()
                R_x[x] = relevant_room_for_sections
            room_capacity = room_data[room_data['bldg_room'] == r]["Rm Max Cap"].iloc[0]
            course_enrollment_capacity = \
            course_data[course_data['subject_number_section_orrurance'] == x]['Max Enroll'].iloc[0]
            if room_capacity > course_enrollment_capacity:
                relevant_sections_for_room.append(x)
                relevant_room_for_sections.append(r)
        X_r[r] = relevant_sections_for_room
    return R_x, X_r

def get_capacity_sets(room_data):
    #n_rf: capacity of room r under safe distance f
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

def get_size_set(X_s):
    # S_x: the set of students choosing section x
    # p_x: class size of section x
    S_x = {}
    p_x = {}
    for s, x in X_s.items():
        for i in x:
            if i not in S_x.keys():
                S_x[i] = [s]
            else:
                S_x[i].append(s)

    for k, v in S_x.items():
        p_x[k] = len(v)

    return S_x, p_x



def get_noroom_section_sets(course_data, Size_x):
    # X_wo_room: a set of sections that have no room assignment in 2019 fall
    X_wo_room = set()

    for x, n in Size_x.items():
        room = course_data[course_data['subject_number_section_orrurance'] == x]['bldg_room'].iloc[0]
        if str(room) == "nan":
            X_wo_room.add(x)
    return X_wo_room


def get_section_wo_time(T_x):
    #X_wo_time: a set of sections that have no time assignment in 2019 fall
    X_wo_time = list(dict(filter(lambda ele: np.NaN not in ele[1], T_x.items())).keys())
    return X_wo_time


def get_overlapping_time_slots(T, t):

    """ 
    Author: Mehran Navabi

    Input:
        T - list[str]: all possible timeslots
        t - str: timeslot currently being considered
            Timeslots must be formated as: "dow_starttime_endtime"
    Output:
        T_clash: subset of timeslots from T which conflict with t
            For example, say t = 'F_1010_1205'
            Then T_clash may look like {'F_1010_1205', 'F_1115_1205', 'MWF_1010_1100'}
            However T_clash could not include 'F_905_955' or 'TR_1200_1445'

    Todo: Fix times so that times before noon are padded with a leading 0
    It so happens that with the times we have courses running, this lingering bug 
    does not lead to any issues, but should be fixed regardless
    """

    t_dow, t_start_time, t_end_time = t.split("_")
    t_dow = set(t_dow)

    T_clash = set()
    for t_other in T:
        if type(t_other) is float:
            continue
        t_other_dow, t_other_start_time, t_other_end_time = t_other.split("_")
        t_other_dow = set(t_other_dow)
        
        if (len(t_dow.intersection(t_other_dow)) > 0) and (t_other_start_time <= t_end_time) and (t_start_time <= t_other_end_time):
            T_clash.add(t_other)

    return T_clash


def get_sections_with_overlapping_time_slot(T, X, course_data):

    """ 
    Author: Mehran Navabi

    Input:
        T - list[str]: All possible timeslots
            Timeslots must be formated as: "dow_starttime_endtime"
        X - list[str]: All sections
            Sections must be formatted as: "subject_coursenumber_section_occurance"
        course_data - pd.DataFrame : dataframe of coursedata, must follow format of raw_data/ISYE_FallSemesterScenarios_ClassSchedules.xlsx
    Output:
        X_t_clash - dict{str: set{str}}: All times in T are included as a key
                    The corresponding values represent the sections that conflict with the time for that section
                    For example, X_t_clash['F_1010_1205'] will include any sections that are taught at the 
                    following times accourding to course_data
                    'F_1010_1205', 'F_1115_1205', or 'MWF_1010_1100'
    """


    T_t_clash = dict()
    X_t_clash = dict()
    for t in T:
        T_t_clash[t] = get_overlapping_time_slots(T, t)
        X_t_clash[t] = set()

    for x in X:
        t_current_section = course_data[course_data['subject_number_section_orrurance'] == x]["full_time"].iloc[0]
        if type(t_current_section) is float:
            continue
        conflicting_times = T_t_clash[t_current_section]
        for t in conflicting_times:
            X_t_clash[t].add(x)

    return X_t_clash


def get_enrollement_per_section(course_data, max_enrollment=False):

    if max_enrollment:
        enrollment_column = 'Max Enroll'
    else:
        enrollment_column = 'Enrollment'

    return pd.Series(course_data[enrollment_column].values,index=course_data['subject_number_section_orrurance']).to_dict()


def get_room_capacity(room_data):

    return pd.Series(room_data["Rm Max Cap"].values,index=room_data['bldg_room']).to_dict()

def get_course_time(course_data):

    return pd.Series(course_data["full_time"].values,index=course_data['subject_number_section_orrurance']).to_dict()

