import pandas as pd
from gurobipy import *
from abc import ABC
from abc import abstractmethod
import sys

import data_process as dp
import set_process as sp
from room_assignment_opt import RoomAssignmentOpt

class RoomAssignmentContactyOpt(RoomAssignmentOpt):
    
    model_description = "contact_max"

    def __init__(self, course_data, room_data, minimum_course_meeting_days, weeks_in_semester):
        super().__init__()
        self.course_data, self.course_data_exclusively_online = dp.separate_online_courses_by_capacity(course_data) #need to implement
        self.room_data = room_data
        self.minimum_course_meeting_days = minimum_course_meeting_days
        self.weeks_in_semester = weeks_in_semester
        return

    def get_all_sets_params(self):
        super().get_all_sets_params()
        self.weekly_hours_section_dictionary = sp.get_weekly_hours_section_dictionary(self.timeslot_section_dictionary) #need to implement
        self.num_weekly_meeting_days_section_dictionary = sp.get_num_weekly_meeting_days(self.timeslot_section_dictionary)

    def set_model_constrs(self, model, model_vars):
        print("setting model constraints")
        X_xr = model_vars["X_xr"]

        print("constraint: each section assigned to room")
        C_1 = model.addConstrs((quicksum(X_xr[(section,room)] for room in self.room_section_dictionary[section]) <= 1
                                 for section in self.all_section),"")

        print("constraint: at most one section in room at a given time")
        C_2 = model.addConstrs((quicksum(X_xr[(section, room)] for section in set(self.all_section).intersection(set(self.section_room_dictionary[room])).intersection(set(self.section_timeslot_clash_dictionary[day_starttime]))) <= 1
                                for room in self.all_room for day_starttime in self.all_simple_timeslot), "")

        return

    def set_objective(self, model, model_vars):
        print("setting objective")
        X_xr = model_vars["X_xr"]
        model.setObjective(quicksum(self.get_contact_hours(section, room) * self.enrollment_section_dictionary[section] * X_xr[(section, room)] \
                           for section in self.all_section for room in self.room_section_dictionary[section]), GRB.MINIMIZE)
        return

    @staticmethod
    def get_contact_hours(section, room):
        pass

    @staticmethod
    def read_filenames(system_arguements):

        if len(system_arguements) < 6:
            raise Exception("""RoomAssignmentContactyOpt model requires all of the following commandline arguments: 
                            course_data_filename, room_data_filename, output_file_directory, minimum_course_meeting_days, weeks_in_semester""")

        course_data_filepath, room_data_filepath, output_data_filepath = super().read_filenames(system_arguements,
                                                                                                input_file_directory,
                                                                                                output_file_directory)

        minimum_course_meeting_days = system_arguements[4]
        weeks_in_semester = system_arguements[5]

        return course_data_filepath, room_data_filepath, output_data_filepath, minimum_course_meeting_days, weeks_in_semester

if __name__ == "__main__":

    course_data_filepath, room_data_filepath, output_data_filepath, minimum_course_meeting_days, weeks_in_semester = RoomAssignmentContactyOpt.read_filenames(sys.argv)

    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)

    #generate model
    assign_opt = RoomAssignmentContactyOpt(course_data, room_data, minimum_course_meeting_days, weeks_in_semester)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()

    #solve model
    model.optimize()

    RoomAssignmentContactyOpt.output_result(course_data=course_data,
                                        room_data=room_data,
                                        model=model,
                                        output_path = output_data_filepath,
                                        )