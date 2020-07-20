import pandas as pd
import sys
from gurobipy import *

import data_process as dp
import set_process as sp
from room_assignment_contact_opt import RoomAssignmentContactyOpt

from time import time
import pickle
import os

class RoomAssignmentPreferencesContactyOpt(RoomAssignmentContactyOpt):
    
    model_description = "preferences_contact_max"
    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room", "delivery_mode", "raw_preference",  "preference"]

    def __init__(self, course_data, room_data, minimum_section_contact_days, weeks_in_semester, preference_objective_tollerance, save_sets_flag=False, read_sets_flag=False, sets_path=None):
        super().__init__(course_data, room_data, minimum_section_contact_days, weeks_in_semester, save_sets_flag, read_sets_flag, sets_path)
        self.preference_objective_tollerance = preference_objective_tollerance
        return

    def __read_or_save_sets(self, mode):
        """Either read sets from files or save sets to file

        Path used for either reading or saving is self.sets_path.

        Parameters
        ----------
        mode : {"wb", "rb"}
            If "wb", then sets (which should already be defined) are written
            to files whose names match the variable names.
            If "rb", then sets are read from files.
        """
        assert mode == "rb" or mode == "wb"
        path = os.path.join(
            self.sets_path, "preferred_delivery_mode_section_dict.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.preferred_delivery_mode_section_dict = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.preferred_delivery_mode_section_dict, f)

        path = os.path.join(
            self.sets_path, "total_contact_hours_section_room_dict.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.total_contact_hours_section_room_dict = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.total_contact_hours_section_room_dict, f)

        path = os.path.join(
            self.sets_path, "delivery_mode_section_room_dict.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.delivery_mode_section_room_dict = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.delivery_mode_section_room_dict, f)

        path = os.path.join(
            self.sets_path, "preferred_room_section_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.preferred_room_section_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.preferred_room_section_dictionary, f)

        path = os.path.join(
            self.sets_path, "preferred_section_room_dictionary.pkl")
        with open(path, mode) as f:
            if mode == "rb":
                self.preferred_section_room_dictionary = pickle.load(f)
            elif mode == "wb":
                pickle.dump(self.preferred_section_room_dictionary, f)
        return

    def get_all_sets_params(self):
        t_params = time()
        super().get_all_sets_params()

        if self.read_sets_flag:
            self.__read_or_save_sets("rb")
        else:
            self.preferred_delivery_mode_section_dict = sp.get_preferred_delivery_mode(self.course_data,
                                                                                          self.all_section
                                                                                          )

            self.total_contact_hours_section_room_dict, self.delivery_mode_section_room_dict = sp.get_contact_hours(all_section=self.all_section,
                                                                                                                    all_room=self.all_room,
                                                                                                                    capacity_room_dictionary=self.capacity_room_dictionary,
                                                                                                                    enrollment_section_dictionary=self.enrollment_section_dictionary,
                                                                                                                    meeting_hours_section_dictionary=self.meeting_hours_section_dictionary,
                                                                                                                    num_weekly_meeting_days_section_dictionary=self.num_weekly_meeting_days_section_dictionary,
                                                                                                                    minimum_section_contact_days=self.minimum_section_contact_days,
                                                                                                                    weeks_in_semester=self.weeks_in_semester,
                                                                                                                    preferred_delivery_mode_section_dict=self.preferred_delivery_mode_section_dict,
                                                                                                                    )

            self.preferred_room_section_dictionary, self.preferred_section_room_dictionary = sp.get_preferred_room_sets(self.course_data,
                                                                                                                        self.room_data,
                                                                                                                        self.room_section_dictionary,
                                                                                                                        self.section_room_dictionary,
                                                                                                                        self.preferred_delivery_mode_section_dict,
                                                                                                                        self.delivery_mode_section_room_dict)
        if self.save_sets_flag:
            self.__read_or_save_sets("wb")

        print("Time to get params:", time() - t_params)
        return


    def set_mode_preferences_objective(self, model,model_vars, index, priority):
        X_xr = model_vars["X_xr"]
        model.setObjectiveN(quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section]) +
                            quicksum(1 - quicksum(X_xr[(section, room)] for room in self.room_section_dictionary[section]) for section in self.all_section if "remote" in self.preferred_delivery_mode_section_dict[section]),
                           index=index,
                           priority=priority,
                           reltol=self.preference_objective_tollerance)


    def set_objective(self, model, model_vars):
        model.ModelSense = GRB.MAXIMIZE
        self.set_mode_preferences_objective(model,model_vars, index=0, priority=2)
        self.set_contact_hours_objective(model,model_vars, index=1, priority=1)
        return


if __name__ == "__main__":
    t_start = time()
    course_data_filepath, room_data_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = RoomAssignmentPreferencesContactyOpt.read_filenames(sys.argv)

    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)
    print("Time to clean data:", time() - t_start)
    #generate model
    sets_path = "/home/mtonbari/Projects/covid_recovery/Sets"  # path where sets are read from or saved to
    assign_opt = RoomAssignmentPreferencesContactyOpt(course_data, room_data, minimum_section_contact_days, weeks_in_semester, 0.01,
        save_sets_flag=True, read_sets_flag=True, sets_path=sets_path)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()
    print("Time to preprocess:", time() - t_start)

    # Adjust parameters
    # model.setParam("MipGap", 0.01)

    #solve model
    model.optimize()
    print("Total time:", time() - t_start)

    nSolutions = model.SolCount
    nObjectives = model.NumObj
    solutions = []
    for s in range(nSolutions):
        # Set which solution we will query from now on
        model.params.SolutionNumber = s

        # Print objective value of this solution in each objective
        print('Solution', s, ':', end='')
        for o in range(nObjectives):
            # Set which objective we will query
            model.params.ObjNumber = o
            # Query the o-th objective value
            print(' ', model.ObjNVal, end=',')
        print("\n")
    # assign_opt.output_result(course_data=course_data,
    #                         room_data=room_data,
    #                         model=model,
                            # output_path = output_data_filepath,
                            # )