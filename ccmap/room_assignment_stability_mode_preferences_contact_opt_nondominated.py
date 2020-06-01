import pandas as pd
import sys
from gurobipy import *

import data_process as dp
import set_process as sp
from room_assignment_stability_mode_preferences_contact_opt import RoomAssignmentStabilityModePreferencesContactOpt

class RoomAssignmentStabilityModePreferencesContactOptNondominated(RoomAssignmentStabilityModePreferencesContactOpt):
    
    informative_output_columns = ["subject_code", "course_number", "course_section", "bldg_room", "delivery_mode", "in_person_hours", "preference", "raw_preference"]
    model_description = "nondominated_stability_mode_preferences_contact_max"

    def __init__(self, course_data, room_data, building_location_data, minimum_section_contact_days, weeks_in_semester, preference_objective_weight, contact_hours_objective_weight, plan_stability_objective_weight, preference_min_bound, contact_hours_min_bound, same_room_min_count, distance_max_bound):
        super().__init__(course_data, room_data, building_location_data, minimum_section_contact_days, weeks_in_semester, preference_objective_tollerance=None, contact_hours_objective_tollerance=None)
        self.preference_objective_weight = preference_objective_weight
        self.contact_hours_objective_weight = contact_hours_objective_weight
        self.plan_stability_objective_weight = plan_stability_objective_weight
        self.preference_min_bound = preference_min_bound
        self.contact_hours_min_bound = contact_hours_min_bound
        self.same_room_min_count = same_room_min_count
        self.distance_max_bound = distance_max_bound
        return


    def set_full_mode_preference_contact_hours_plan_stability_objective(self, model, model_vars, index=0, priority=1):
        X_xr = model_vars["X_xr"]

        plan_stability_lin_expr = quicksum(self.reassginment_cost_section_room_dict[section, room] *  X_xr[(section, room)] \
                                                for section in self.all_section for room in self.room_section_dictionary[section])
        preferences_lin_expr = quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section]) + \
                                    quicksum(1 - quicksum(X_xr[(section, room)] for room in self.room_section_dictionary[section]) for section in self.all_section if "remote" in self.preferred_delivery_mode_section_dict[section])
        contact_hours_lin_expr = quicksum(self.total_contact_hours_section_room_dict[section, room] * self.enrollment_section_dictionary[section] * self.priority_boost_section_dict[section] * X_xr[(section, room)] \
                                          for section in self.all_section for room in self.room_section_dictionary[section])
        
        model.setObjectiveN( plan_stability_lin_expr * self.plan_stability_objective_weight + preferences_lin_expr * self.preference_objective_weight + contact_hours_lin_expr * self.contact_hours_objective_weight, index=index, priority=priority)
        pass

    def set_model_constrs(self, model, model_vars):

        super().set_model_constrs(model, model_vars)

        X_xr = model_vars["X_xr"]

        preferences_lin_expr = quicksum(X_xr[(section, room)] for section in self.all_section for room in self.preferred_room_section_dictionary[section]) + \
                                    quicksum(1 - quicksum(X_xr[(section, room)] for room in self.room_section_dictionary[section]) for section in self.all_section if "remote" in self.preferred_delivery_mode_section_dict[section])

        contact_hours_lin_expr = quicksum(self.total_contact_hours_section_room_dict[section, room] * self.enrollment_section_dictionary[section] * self.priority_boost_section_dict[section] * X_xr[(section, room)] \
                                          for section in self.all_section for room in self.room_section_dictionary[section])
        same_room_lin_expr = quicksum(X_xr[(section, self.existing_room_assignment_section_dict[section])] for section in self.all_section if section in self.existing_room_assignment_section_dict and self.existing_room_assignment_section_dict[section] in self.room_section_dictionary[section])
        plan_stability_lin_expr = quicksum(self.reassginment_cost_section_room_dict[section, room] *  X_xr[(section, room)] \
                                                for section in self.all_section for room in self.room_section_dictionary[section])

        C_preference_bound = model.addConstr(preferences_lin_expr >= self.preference_min_bound, "")
        C_preference_bound = model.addConstr(preferences_lin_expr >= self.preference_min_bound, "")
        C_contact_hours_bound = model.addConstr(contact_hours_lin_expr >= self.contact_hours_min_bound, "")
        C_stability_same_room_bound = model.addConstr(same_room_lin_expr >= self.same_room_min_count, "")

    def set_objective(self, model, model_vars):
        model.ModelSense = GRB.MAXIMIZE
        self.set_full_mode_preference_contact_hours_plan_stability_objective(model, model_vars)
        return


if __name__ == "__main__":

    course_data_filepath, room_data_filepath, building_location_filepath, output_data_filepath, minimum_section_contact_days, weeks_in_semester = RoomAssignmentStabilityModePreferencesContactyOptNondominated.read_filenames(sys.argv)
    course_data = dp.clean_course_data(course_data_filepath)
    room_data = dp.clean_room_data(room_data_filepath)
    building_location_data = dp.clean_building_location_data(building_location_filepath, course_data)
    #generate model
    assign_opt = RoomAssignmentStabilityModePreferencesContactOptNondominated(course_data,
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
                                                                  distance_max_bound=sys.maxsize)
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