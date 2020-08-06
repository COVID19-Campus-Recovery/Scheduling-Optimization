import pandas as pd
import sys
from gurobipy import *

import data_process as dp
import set_process as sp
from room_assignment_stability_mode_preferences_contact_opt import RoomAssignmentStabilityModePreferencesContactOpt

class RoomAssignmentStabilityOptPreferenceEnforcedResdentialPreferenceEnforced(RoomAssignmentStabilityModePreferencesContactOpt):

    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room", "delivery_mode", "in_person_hours", "preference"]
    model_description = "stability_preference_enforced_resdential_preference_enforced"

    def __init__(self, course_data, room_data, building_location_data, minimum_section_contact_days, weeks_in_semester, residential_spread_preference_bound, total_pererence_bound):
        super().__init__(course_data=course_data, room_data=room_data, building_location_data=building_location_data, minimum_section_contact_days=minimum_section_contact_days, weeks_in_semester=weeks_in_semester, preference_objective_tollerance=0, contact_hours_objective_tollerance=1)
        self.residential_spread_preference_bound = residential_spread_preference_bound
        self.total_pererence_bound = total_pererence_bound
        return


    def set_model_constrs(self, model, model_vars):
        super().set_model_constrs(model, model_vars)
        X_xr = model_vars["X_xr"]

        residential_spread_preferences_lin_expr = quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section] if self.preferred_delivery_mode_section_dict[section] == {"residential_spread"})
        C_residential_preference_bound = model.addConstr(residential_spread_preferences_lin_expr >= self.residential_spread_preference_bound, "")

        preferences_lin_expr = quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section])
        C_residential_preference_bound = model.addConstr(preferences_lin_expr >= self.total_pererence_bound, "")


    def set_objective(self, model, model_vars):
        model.ModelSense = GRB.MAXIMIZE
        self.set_plan_stability_objective(model,model_vars, index=0, priority=1)
        return


if __name__ == "__main__":

    course_data_filepath, room_data_filepath, building_location_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = RoomAssignmentStabilityOptPreferenceEnforcedResdentialPreferenceEnforced.read_filenames(sys.argv)
    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)
    building_location_data = dp.clean_building_location_data(building_location_filepath, course_data)
    #generate model
    assign_opt = RoomAssignmentStabilityOptPreferenceEnforcedResdentialPreferenceEnforced(course_data=course_data,
                                                                                          room_data=room_data,
                                                                                          building_location_data=building_location_data,
                                                                                          minimum_section_contact_days=minimum_section_contact_days,
                                                                                          weeks_in_semester=weeks_in_semester,
                                                                                          residential_spread_preference_bound=214,
                                                                                          total_pererence_bound=int(1721*0.98)
                                                                                          )

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