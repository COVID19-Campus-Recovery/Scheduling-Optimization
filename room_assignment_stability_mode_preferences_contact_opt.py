import pandas as pd
import sys
from gurobipy import *

import data_process as dp
import set_process as sp
from room_assignment_mode_preferences_contact_opt import RoomAssignmentModePreferencesContactOpt

class RoomAssignmentStabilityModePreferencesContactOpt(RoomAssignmentModePreferencesContactOpt):
    
    # model_description = "stability_mode_preferences_contact_max"
    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room", "delivery_mode", "in_person_hours", "preference"]
    model_description = "stability_mode_preferences_contact_max"

    def __init__(self, course_data, room_data, building_location_data, minimum_section_contact_days, weeks_in_semester, preference_objective_tollerance, contact_hours_objective_tollerance):
        super().__init__(course_data, room_data, minimum_section_contact_days, weeks_in_semester, preference_objective_tollerance)
        self.building_location_data = building_location_data
        self.contact_hours_objective_tollerance = contact_hours_objective_tollerance
        return


    def get_all_sets_params(self):
        super().get_all_sets_params()

        self.existing_room_assignment_section_dict = sp.get_existing_room_assignment_section_dict(self.course_data)
        self.room_building_dict, self.building_room_dict = sp.get_room_building_sets(self.all_room, self.course_data)
        self.all_building = set(self.room_building_dict.keys())
        self.dist_between_building_dict = sp.get_dist_between_buildings(self.building_location_data,
                                                                        self.all_building)
        self.reassginment_cost_section_room_dict = sp.get_reassignment_cost(self.all_section,
                                                                            self.all_room,
                                                                            self.dist_between_building_dict,
                                                                            self.existing_room_assignment_section_dict,
                                                                            self.building_room_dict)
        return

    def set_plan_stability_objective(self, model, model_vars, index, priority):
        X_xr = model_vars["X_xr"]
        model.setObjectiveN(-1 * quicksum(self.reassginment_cost_section_room_dict[section, room] *  X_xr[(section, room)] \
                           for section in self.all_section for room in self.room_section_dictionary[section]),
                           index=index,
                           priority=priority)


    def set_objective(self, model, model_vars):
        model.ModelSense = GRB.MAXIMIZE
        self.set_mode_preferences_objective(model,model_vars, index=0, priority=3)
        self.set_contact_hours_objective(model,model_vars, index=1, priority=2)
        self.set_plan_stability_objective(model,model_vars, index=2, priority=1)
        return


    @classmethod
    def read_filenames(cls, system_arguements):

        if len(system_arguements) < 7:
            raise Exception("""RoomAssignmentStabilityModePreferencesContactOpt model requires all of the following commandline arguments: 
                            course_data_filename, room_data_filename, building_location_filepath, output_file_directory, minimum_section_contact_days, weeks_in_semester""")


        course_data_filepath, room_data_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = super().read_filenames(system_arguements[0:3] + system_arguements[4:])

        building_location_filepath = system_arguements[3]

        return course_data_filepath, room_data_filepath, building_location_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester


if __name__ == "__main__":

    course_data_filepath, room_data_filepath, building_location_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = RoomAssignmentStabilityModePreferencesContactOpt.read_filenames(sys.argv)
    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)
    building_location_data = dp.clean_building_location_data(building_location_filepath, course_data)
    assign_opt = RoomAssignmentStabilityModePreferencesContactOpt(course_data,
                                                                    room_data,
                                                                    building_location_data,
                                                                    minimum_section_contact_days,
                                                                    weeks_in_semester,
                                                                    preference_objective_tollerance=0.01,
                                                                    contact_hours_objective_tollerance=1)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()

    #solve model
    model.optimize()
    modified_output_filepath = output_data_filepath.split("stability_mode_preferences_contact_max")[0] + "stability_mode_preferences_" + str(0.01) + "_max.csv"
    assign_opt.output_result(course_data=course_data,
                            room_data=room_data,
                            model=model,
                            output_path=modified_output_filepath,
                            )


