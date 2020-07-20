import pandas as pd
import csv
from gurobipy import *
from abc import ABC
from abc import abstractmethod
import sys

from abc import abstractmethod
import data_process as dp
import set_process as sp
from generic_schedule_opt import GenericScheduleOpt
import pickle
import os


class RoomAssignmentOpt(GenericScheduleOpt):
    
    model_description = "generic_room_assignment"
    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room"]

    def __init__(self, save_sets_flag=False, read_sets_flag=False,
                 sets_path=None):
        super().__init__()
        self.read_sets_flag = read_sets_flag
        if self.read_sets_flag:
            self.save_sets_flag = False
        else:
            self.save_sets_flag = save_sets_flag
        if self.read_sets_flag or self.save_sets_flag:
            assert sets_path is not None
            self.sets_path = sets_path
        return

    def __read_or_save_sets(self, mode):
        """Either read sets from files or save sets to file
    
        Parameters
        ----------
        mode : {"wb", "rb"}
            If "wb", then sets (which should already be defined) are written
            to files whose names match the variable names.
            If "rb", then sets are read from files.
        """
        assert mode == "rb" or mode == "wb"
        path = os.path.join(
            self.sets_path, "section_course_dict.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.section_course_dict = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.section_course_dict, f)

        path = os.path.join(
            self.sets_path, "room_section_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.room_section_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.room_section_dictionary, f)

        path = os.path.join(
            self.sets_path, "section_room_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.section_room_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.section_room_dictionary, f)

        path = os.path.join(
            self.sets_path, "section_timeslot_clash_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.section_timeslot_clash_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.section_timeslot_clash_dictionary, f)

        path = os.path.join(
            self.sets_path, "enrollment_section_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.enrollment_section_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.enrollment_section_dictionary, f)

        path = os.path.join(
            self.sets_path, "capacity_room_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.capacity_room_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.capacity_room_dictionary, f)

        path = os.path.join(
            self.sets_path, "timeslot_section_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.timeslot_section_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.timeslot_section_dictionary, f)
        return

    def get_all_sets_params(self):
        self.all_course = self.course_data['subject_course_section'].unique().tolist()
        self.all_section = self.course_data['subject_course_section_occurrence'].tolist()
        self.all_room = self.room_data['bldg_room'].tolist()
        self.all_timeslot = self.course_data['full_time'].unique()
        self.all_simple_timeslot = sp.get_all_simplieid_timeslot(self.all_timeslot)


        if self.read_sets_flag:
            self.__read_or_save_sets("rb")
        else:
            print("setting course to section set")
            self.section_course_dict = sp.get_section_set(self.course_data, self.all_course)
            print("setting room to section set")
            self.room_section_dictionary, self.section_room_dictionary = sp.get_room_sets(self.course_data, self.room_data,
                                                                                          self.all_room, self.all_section)
            print("setting time to section availability set")
            self.section_timeslot_clash_dictionary = sp.get_sections_with_overlapping_time_slot(self.all_timeslot, self.all_simple_timeslot, self.all_section, self.course_data)

            print("setting parameters")
            self.enrollment_section_dictionary = sp.get_enrollement_per_section(self.course_data,
                                                      enrollment_column='enrollment'
                                                      )
            self.capacity_room_dictionary = sp.get_room_capacity(self.room_data, capacity_column='capacity')
            self.timeslot_section_dictionary = sp.get_course_time(self.course_data)
        if self.save_sets_flag:
            self.__read_or_save_sets("wb")
        pass

    def set_model_vars(self, model):
        print("defining variables")
        X_xr = {}
        for section in self.all_section:
            for room in self.room_section_dictionary[section]:
                X_xr[(section, room)] = model.addVar(vtype=GRB.BINARY, name='X_xr[%s+%s]' % (section, room))

        model_vars = {"X_xr": X_xr}
        return model_vars

    @abstractmethod
    def set_model_constrs(self, model, model_vars):
        pass

    @abstractmethod
    def set_objective(self, model, model_vars):
        pass

    @classmethod
    def read_filenames(cls, system_arguements):
        """
        Input:
            system_arguements - list[str]: should be directly from sys.argv
        Output:
            course_data_filepath - str: filepath to read course input file
            room_data_filepath - str: filepath to read room input file
            output_data_filepath-  str: filepath to store output file
        """
        if len(system_arguements) >= 3:
            course_data_filepath = system_arguements[1]
            room_data_filepath = system_arguements[2]
            output_file_directory = system_arguements[3]
        else:
            raise Exception("""Any room assignment model requires all of the following commandline arguments: 
                            course_data_filepath, room_data_filepath, output_file_directory""")

        course_data_filename = course_data_filepath.split("/")[-1]
        room_data_filename = room_data_filepath.split("/")[-1]
        if course_data_filename.find("room_assignment_opt_course") == 0 and room_data_filename.find("room_assignment_opt_room") == 0:
            course_data_filename_suffix = course_data_filename[len("room_assignment_opt_courses_"):].split(".")[0]
            room_data_filename_suffix = room_data_filename[len("room_assignment_opt_rooms_"):].split(".")[0]
            output_data_filename_suffix = course_data_filename_suffix + "_" + room_data_filename_suffix
            output_data_filename = "room_assignment_opt_output" + "_" + output_data_filename_suffix + "_" + cls.model_description + ".csv"
            output_data_filepath = output_file_directory + "/" + output_data_filename
        else:
            raise Exception("Invalid input file names")

        return course_data_filepath, room_data_filepath, output_data_filepath

    @abstractmethod
    def get_additional_output_columns(self, output):
        pass

    # @classmethod
    def output_result(
            self,
            course_data,
            room_data,
            model=None,
            output_path="room_asignment_opt_output_example.csv",
            occurrence=False
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
        print("Output file generating")

        solution = {}

        if isinstance(model, Model):
            for v in model.getVars():
                if v.x == 1:
                    solution[v.varName] = v.x

        elif isinstance(model, str):
            with open(file=model, newline='\n') as csvfile:
                reader = csv.reader((line.replace('  ', ' ') for line in csvfile), delimiter=' ')
                next(reader)  # skip header

                for var, value in reader:
                    if int(value) == 1:
                        solution[var] = float(value)
        else:
            raise TypeError("model should be str or gurobipy.Model")

        # Split the varName into seperate columns
        sol = pd.DataFrame.from_dict(solution, orient='index')
        sol.reset_index(level=0, inplace=True)
        sol.columns = ["X_xr", "value"]
        sol["X_xr"] = sol.X_xr.str.extract(r'\[(.*)\]')

        output = sol["X_xr"].str.split("+", expand=True)
        temp = output[0].str.split("_", expand=True)
        output["Building"] = output[1].str.extract(r'^(.+?)_')
        output["Room"] = output[1].str.extract(r'[^_]*_(.*)')
        output.rename(columns={0: 'subject_course_section_occurrence', 1: 'bldg_room'}, inplace=True)


        # Merge optimization result with input data
        # final_output = pd.merge(output, course_data, how='left', left_on=["subject_course_section_occurrence"],
        #                         right_on=["subject_course_section_occurrence"])
        final_output = pd.merge(course_data, output, how='left', left_on=["subject_course_section_occurrence"],
                                right_on=["subject_course_section_occurrence"])
        final_output = pd.merge(final_output, room_data, how="left", left_on="bldg_room", right_on="bldg_room")
        # final_output = pd.merge(final_output,room_data, how = "left", left_on ="Bldg_room",right_on = "bldg_room")
        final_output = self.get_additional_output_columns(final_output)
        final_output.rename(columns={"use": 'Room Use'}, inplace=True)
        columns_to_keep = self.informative_output_columns + ["enrollment", "capacity", "days", "begin_time", "end_time",
                                     "exclusively_online", "Room Use", "crn", "contact_hours"]
        final_output = final_output[columns_to_keep]

        # final_output.columns = ["Subject Code", "Course Number", "Course Section", "bldg_room", "Enrollment",
        #                         "capacity", "Days", "Begin Time", "End Time", "Eclusively Online", "Room Use", "crn", "Conatct Hours"]

        # save
        final_output.to_csv(output_path, index=False)

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

    assign_opt.output_result(course_data=course_data,
                                    room_data=room_data,
                                    model=model,
                                    output_path = output_data_filepath,
                                    )
