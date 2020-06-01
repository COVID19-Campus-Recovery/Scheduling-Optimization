import pandas as pd
import sys
from gurobipy import *

import data_process as dp
import set_process as sp
from room_assignment_stability_mode_preferences_contact_opt_nondominated import RoomAssignmentStabilityModePreferencesContactOptNondominated

class RoomAssignmentStabilityModePreferencesContactOptNondominatedResidentialPreference(RoomAssignmentStabilityModePreferencesContactOptNondominated):
    
    # model_description = "stability_mode_preferences_contact_max"
    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room", "delivery_mode", "in_person_hours", "preference", "raw_preference"]
    model_description = "nondominated_stability_mode_preferences_contact_residential_preference_max"

    def __init__(self, course_data, room_data, building_location_data, minimum_section_contact_days, weeks_in_semester, preference_objective_weight, contact_hours_objective_weight, plan_stability_objective_weight, preference_min_bound, contact_hours_min_bound, same_room_min_count, distance_max_bound, residential_preference_tollerance):
        super().__init__(course_data, room_data, building_location_data, minimum_section_contact_days, weeks_in_semester, preference_objective_weight, contact_hours_objective_weight, plan_stability_objective_weight, preference_min_bound, contact_hours_min_bound, same_room_min_count, distance_max_bound)
        self.residential_preference_tollerance = residential_preference_tollerance
        return


    def set_residential_preference_objective(self, model, model_vars, index, priority):

        X_xr = model_vars["X_xr"]
        residential_spread_preferences_lin_expr = quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section] if self.preferred_delivery_mode_section_dict[section] == {"residential_spread"})
        model.setObjectiveN(residential_spread_preferences_lin_expr, index=index, priority=priority, reltol=self.residential_preference_tollerance)


    def set_objective(self, model, model_vars):
        model.ModelSense = GRB.MAXIMIZE
        self.set_residential_preference_objective(model, model_vars, index=0, priority=2)
        self.set_full_mode_preference_contact_hours_plan_stability_objective(model, model_vars, index=1, priority=1)
        return


if __name__ == "__main__":

    course_data_filepath, room_data_filepath, building_location_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = RoomAssignmentStabilityModePreferencesContactOptNondominatedResidentialPreference.read_filenames(sys.argv)
    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)
    building_location_data = dp.clean_building_location_data(building_location_filepath, course_data)
    #generate model
    assign_opt = RoomAssignmentStabilityModePreferencesContactOptNondominatedResidentialPreference(course_data,
                                                                  room_data,
                                                                  building_location_data,
                                                                  minimum_section_contact_days,
                                                                  weeks_in_semester,
                                                                  preference_objective_weight=60, 
                                                                  contact_hours_objective_weight=1, 
                                                                  plan_stability_objective_weight=0.001, 
                                                                  preference_min_bound=1679, 
                                                                  contact_hours_min_bound=0, 
                                                                  same_room_min_count=1000, 
                                                                  distance_max_bound=sys.maxsize,
                                                                  residential_preference_tollerance=0.01)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()

    #solve model
    model.optimize()
    assign_opt.output_result(course_data=course_data,
                            room_data=room_data,
                            model=model,
                            output_path=output_data_filepath,
                            )