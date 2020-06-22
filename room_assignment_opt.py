import pandas as pd
from gurobipy import *
from abc import ABC
from abc import abstractmethod
import sys

import data_process as dp
import set_process as sp
from generic_schedule_opt import GenericScheduleOpt

class RoomAssignmentOpt(GenericScheduleOpt):

    def __init__(self, course_data, room_data):
        super().__init__()
        self.course_data, self.course_data_exclusively_online = dp.separate_online_courses(course_data)
        self.room_data = room_data
        return

    def get_all_sets_params(self):
        self.C = self.course_data['subject_course_section'].unique().tolist()
        self.X = self.course_data['subject_course_section_occurrence'].tolist()
        self.R = self.room_data['bldg_room'].tolist()
        self.T = self.course_data['full_time'].unique()
        self.TS = sp.get_all_simplieid_timeslot(self.T)
        # self.timeintervals = sp.generate_simple_time_intervals()

        print("setting course to section set")
        self.X_c = sp.get_section_set(self.course_data, self.C)
        print("setting room to section set")
        self.R_x, self.X_r = sp.get_room_sets(self.course_data, self.room_data,
                                              self.R, self.X)
        print("setting time to section availability set")
        # self.X_t = sp.get_sections_with_overlapping_time_slot(self.T, self.X, self.course_data, self.timeintervals)
        self.X_t = sp.get_sections_with_overlapping_time_slot(self.T, self.TS, self.X, self.course_data)

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
        # C_2 = model.addConstrs((quicksum(X_xr[(x, r)] for x in set(self.X).intersection(set(self.X_r[r])).intersection(set(self.X_t[t]))) <= 1
        #                         for r in self.R for t in self.timeintervals), "")
        C_2 = model.addConstrs((quicksum(X_xr[(x, r)] for x in set(self.X).intersection(set(self.X_r[r])).intersection(set(self.X_t[t]))) <= 1
                                for r in self.R for t in self.TS), "")

        return

    def set_objective(self, model, model_vars):
        print("setting objective")
        X_xr = model_vars["X_xr"]
        model.setObjective(quicksum(self.p_x[x] / self.n_r[r] * X_xr[(x, r)] for x in self.X for r in self.R_x[x]), GRB.MINIMIZE)
        return

    @staticmethod
    def read_filenames(system_arguements,
                      input_file_directory="~/Documents/Madgie_Cleaned_Directory/Data/",
                      output_file_directory="~/Documents/Madgie_Cleaned_Directory/Output/"):
        """
        Input:
            system_arguements - list[str]: should be directly from sys.argv
            input_file_directory - str: location directory that stores all input files
            output_file_directory - str: location directory that stores all output files.
        Output:

        """

        if len(system_arguements) >= 3:
            course_data_filename = system_arguements[1]
            room_data_filename = system_arguements[2]
        else:
            course_data_filename = "room_assignment_opt_courses_example.xlsx"
            room_data_filename = "room_assignment_opt_rooms_example.xlsx"

        course_data_filepath = input_file_directory + course_data_filename
        room_data_filepath = input_file_directory + room_data_filename

        if course_data_filename.find("room_assignment_opt_courses") == 0 and room_data_filename.find("room_assignment_opt_rooms") == 0:
            course_data_filename_suffix = course_data_filename[len("room_assignment_opt_courses_"):].split(".")[0]
            room_data_filename_suffix = room_data_filename[len("room_assignment_opt_rooms_"):].split(".")[0]
            output_data_filename_suffix = course_data_filename_suffix + "_" + room_data_filename_suffix
            output_data_filename = "room_assignment_opt_output" + "_" + output_data_filename_suffix + ".csv"
            output_data_filepath = output_file_directory + output_data_filename
        else:
            raise Exception("Invalid input file names")
        print("output filepath")
        print(output_data_filepath)
        return course_data_filepath, room_data_filepath, output_data_filepath

    @staticmethod
    def output_result(
        model = None,
        output_path = "room_asignment_opt_output_example.csv",
        occurrence = False
        ):

        r'''
        Standard output file: .csv with coulumns: 
        ["Subject Code","Course Code", "Course Section","Occurrence","Bldg_room","Bldg Code","Room Code"]
        
        Parameters:
        -------------
        model: str or gurobipy.Model, default=None
            If a str is passed, it should be the filepath of .sol file.
            ATTENTION: if read from a .sol file, the variable name must not have white space when define. 
            If a gurobipy.Model is passes, it should be a solved gurobi Model

        output_path: str, default="room_asignment_opt_output_example.csv"
            the output path of the .csv file. Save to the same path as project file by default. 
        
        occurrence: bool, default = False
            Wether include occurrence column in the output file, false by default
        '''
        solution = {}

        if isinstance(model,Model):
            for v in model.getVars():
                if v.x ==1:
                    solution[v.varName] = v.x

        elif isinstance(model,str):
            import csv
            with open(file = model, newline='\n') as csvfile:
                reader = csv.reader((line.replace('  ', ' ') for line in csvfile), delimiter=' ')
                next(reader)  # skip header
                
                for var, value in reader:
                    if int(value) ==1:
                        solution[var] = float(value)
        else:
            raise TypeError("model should be str or gurobipy.Model")

        # Split the varName into seperate columns
        sol = pd.DataFrame.from_dict(solution, orient='index')
        sol.reset_index(level=0, inplace=True)
        sol.columns = ["X_xr","value"]
        sol["X_xr"]=sol.X_xr.str.extract(r'\[(.*)\]')
        output = sol["X_xr"].str.split("+",expand = True) 
        temp = output[0].str.split("_",expand = True) 
        output["Subject Code"] = temp[0]
        output["Course Code"] = temp[1]
        output["Course Section"] = temp[2].astype(str).str[:-1]

        #TODO:
        if occurrence:
            pass

        output["Occurrence"] = temp[2].astype(str).str[-1]
        output["Bldg Code"]=output[1].str.extract(r'^(.+?)_')
        output["Room Code"]=output[1].str.extract(r'[^_]*_(.*)')
        output = output.drop(columns = [0])
        output.rename(columns={1:'Bldg_room'}, inplace=True)

        output = output[["Subject Code","Course Code", "Course Section","Occurrence","Bldg_room","Bldg Code","Room Code"]]

        output.to_csv(output_path,index = False)


if __name__ == "__main__":

    course_data_filepath, room_data_filepath, output_data_filepath = RoomAssignmentOpt.read_filenames(sys.argv)

    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)

    #generate model
    assign_opt = RoomAssignmentOpt(course_data, room_data)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()

    #solve model
    model.optimize()

    RoomAssignmentOpt.output_result(model=model,
                                    output_path = output_data_filepath)
