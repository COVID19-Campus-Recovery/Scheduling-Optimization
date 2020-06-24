import pandas as pd
from gurobipy import *
from abc import ABC
from abc import abstractmethod
import sys

import data_process as dp
import set_process as sp
from room_assignment_opt import RoomAssignmentOpt

class RoomAssignmentDensityOpt(RoomAssignmentOpt):
    
    model_description = "density_min"

    def __init__(self, course_data, room_data):
        super().__init__()
        self.course_data, self.course_data_exclusively_online = dp.separate_online_courses(course_data)
        self.room_data = room_data
        return

    def set_model_constrs(self, model, model_vars):
        print("setting model constraints")
        X_xr = model_vars["X_xr"]

        print("constraint: each section assigned to room")
        C_1 = model.addConstrs((quicksum(X_xr[(section,room)] for room in self.room_section_dictionary[section]) == 1
                                 for section in self.all_section),"")

        print("constraint: at most one section in room at a given time")
        C_2 = model.addConstrs((quicksum(X_xr[(section, room)] for section in set(self.all_section).intersection(set(self.section_room_dictionary[room])).intersection(set(self.section_timeslot_clash_dictionary[day_starttime]))) <= 1
                                for room in self.all_room for day_starttime in self.all_simple_timeslot), "")

        return

    def set_objective(self, model, model_vars):
        print("setting objective")
        X_xr = model_vars["X_xr"]
        model.setObjective(quicksum(self.enrollment_section_dictionary[section] / self.capacity_room_dictionary[room] * X_xr[(section, room)] \
                           for section in self.all_section for room in self.room_section_dictionary[section]), GRB.MINIMIZE)
        return


if __name__ == "__main__":

    course_data_filepath, room_data_filepath, output_data_filepath = RoomAssignmentDensityOpt.read_filenames(sys.argv)

    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)

    #generate model
    assign_opt = RoomAssignmentDensityOpt(course_data, room_data)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()

    #solve model
    model.optimize()

    RoomAssignmentDensityOpt.output_result(course_data=course_data,
                                        room_data=room_data,
                                        model=model,
                                        output_path = output_data_filepath,
                                        )