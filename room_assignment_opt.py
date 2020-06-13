import pandas as pd
from gurobipy import *
from abc import ABC
from abc import abstractmethod

import data_process as dp
import set_process as sp
from generic_schedule_opt import GenericScheduleOpt

class RoomAssignmentOpt(GenericScheduleOpt):

    def __init__(self, course_data, room_data):
        super().__init__()
        self.course_data = course_data
        self.room_data = room_data
        return

    def get_all_sets_params(self):
        self.C = self.course_data['subject_course_section'].unique().tolist()
        self.X = self.course_data['subject_course_section_occurrence'].tolist()
        self.R = self.room_data['bldg_room'].tolist()
        self.T = self.course_data['full_time'].unique()
        self.timeintervals = sp.generate_simple_time_intervals()

        print("setting course to section set")
        self.X_c = sp.get_section_set(self.course_data, self.C)
        print("setting room to section set")
        self.R_x, self.X_r = sp.get_room_sets_trivial(self.course_data, self.room_data,
                                              self.R, self.X)
        print("setting time to section availability set")
        self.X_t = sp.get_sections_with_overlapping_time_slot(self.T, self.X, self.course_data, self.timeintervals)
        print("setting parameters")
        self.p_x = sp.get_enrollement_per_section(self.course_data,
                                                  enrollment_column='enrollment'
                                                  )
        self.n_r = sp.get_room_capacity(self.room_data, capacity_column='capacity')
        self.t_x = sp.get_course_time(self.course_data)
        pass

    def set_model_vars(self, model):
        print("defining variables")
        X_xr = {}
        for x in self.X:
            for r in self.R_x[x]:
                X_xr[(x, r)] = model.addVar(vtype=GRB.BINARY, name='X_xr[%s+%s]' % (x, r))

        model_vars = {"X_xr": X_xr}
        return model_vars

    def set_model_constrs(self, model, model_vars):
        print("setting model constraints")
        X_xr = model_vars["X_xr"]

        # Each section is assigned to exactly one room
        print("constraint: each section assigned to room")
        C_1 = model.addConstrs((quicksum(X_xr[(x,r)] for r in self.R_x[x]) == 1
                                 for x in self.X),"")

        # At most one section can be to a room at a given time
        # will need to be modified to exclude courses taught online
        print("constraint: at most one section in room at a given time")
        C_2 = model.addConstrs((quicksum(X_xr[(x, r)] for x in set(self.X).intersection(set(self.X_r[r])).intersection(set(self.X_t[t]))) <= 1
                                for r in self.R for t in self.timeintervals), "")

        return

    def set_objective(self, model, model_vars):
        print("setting objective")
        X_xr = model_vars["X_xr"]
        model.setObjective(quicksum(self.p_x[x] / self.n_r[r] * X_xr[(x, r)] for x in self.X for r in self.R_x[x]), GRB.MINIMIZE)
        return


if __name__ == "__main__":

    #load data
    course_data_filepath = "~/Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_example.xlsx"
    room_data_filepath = "~/Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_rooms_example.xlsx"
    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)

    #generate model
    assign_opt = RoomAssignmentOpt(course_data, room_data)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()

    #solve model
    model.optimize()
