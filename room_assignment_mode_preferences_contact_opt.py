import pandas as pd
import sys
from gurobipy import *

import data_process as dp
import set_process as sp
from room_assignment_contact_opt import RoomAssignmentContactyOpt

class RoomAssignmentPreferencesContactyOpt(RoomAssignmentContactyOpt):
    
    model_description = "preferences_contact_max"
    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room", "delivery_mode", "raw_preference",  "preference"]

    def __init__(self, course_data, room_data, minimum_section_contact_days, weeks_in_semester, preference_objective_tollerance):
        super().__init__(course_data, room_data, minimum_section_contact_days, weeks_in_semester)
        self.preference_objective_tollerance = preference_objective_tollerance
        return


    def get_all_sets_params(self):
        super().get_all_sets_params()

        self.permissible_delivery_mode_section_dict = sp.get_permissible_delivery_mode(self.course_data,
                                                                                      self.all_section
                                                                                      )

        self.preferred_room_section_dictionary, self.preferred_section_room_dictionary = sp.get_preferred_room_sets(self.course_data,
                                                                                                                    self.room_data,
                                                                                                                    self.room_section_dictionary,
                                                                                                                    self.section_room_dictionary,
                                                                                                                    self.permissible_delivery_mode_section_dict,
                                                                                                                    self.delivery_mode_section_room_dict)
        return


    def set_mode_preferences_objective(self, model,model_vars, index, priority):
        X_xr = model_vars["X_xr"]
        model.setObjectiveN(quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section]) +
                            quicksum(1 - quicksum(X_xr[(section, room)] for room in self.room_section_dictionary[section]) for section in self.all_section if "remote" in self.permissible_delivery_mode_section_dict[section]),
                           index=index,
                           priority=priority,
                           reltol=self.preference_objective_tollerance)


    def set_objective(self, model, model_vars):
        model.ModelSense = GRB.MAXIMIZE
        self.set_mode_preferences_objective(model,model_vars, index=0, priority=2)
        self.set_contact_hours_objective(model,model_vars, index=1, priority=1)
        return



if __name__ == "__main__":

    course_data_filepath, room_data_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = RoomAssignmentPreferencesContactyOpt.read_filenames(sys.argv)

    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)

    #generate model
    assign_opt = RoomAssignmentPreferencesContactyOpt(course_data, room_data, minimum_section_contact_days, weeks_in_semester, 0.001)
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