from gurobipy import *

import data_process as dp
import set_process as sp
import schedule_opt as sopt


class AssignmentOpt(sopt.ScheduleOpt):
    def __init__(self, course_data, student_data, room_data):
        sopt.ScheduleOpt.__init__(self, course_data, student_data, room_data)


    def set_model_vars(self, model):
        # Define decision variables
        X_xrt, D_xf = {}, {}
        for x in self.X:
            for r in self.R:
                for t in self.T:
                    X_xrt[(x, r, t)] = model.addVar(vtype=GRB.BINARY, name='X_xrt[%s+%s+%s]' % (x, r, t))

        for x in self.X:
            for f in self.F:
                D_xf[(x, f)] = model.addVar(vtype=GRB.BINARY, name='D_xf[%s+%s]' % (x, f))

        model_vars = {"X_xrt": X_xrt, "D_xf": D_xf}
        return model_vars

    def set_model_constrs(self, model, model_vars):
        X_xrt = model_vars["X_xrt"]
        D_xf = model_vars["D_xf"]


        # define constraints

        C_1 = model.addConstrs((quicksum(X_xrt[(x,r,t)] for r in self.R for t in self.T) == 1
                                 for x in self.X),"")

        # At most one section can be to a room for a give time block
        C_2 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for x in self.X) <= 1
                                for r in self.R for t in self.T), "")

        # for those section has a time block on schedule, we have to assign the section to this time.
        C_3 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for r in self.R for t in self.T_x[x]) == 1
                                for x in self.X_wo_time),"")

        C_4 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for r in self.R for t in self.T) == 1
                                for x in self.X),"")

        M2 = max(self.room_data["Station Count (Current)"].astype(int))
        C_5 = model.addConstrs((quicksum(self.n_rf[(r, f)] * X_xrt[(x, r, t)] for t in self.T for r in self.R) - self.Size_x[x]
                                 >= M2 * (-D_xf[(x, f)])
                                 for x in self.X for f in self.F), "")
        return

    def set_objective(self, model, model_vars):
        D_xf = model_vars["D_xf"]
        model.setObjective(quicksum(self.k_f[f] * D_xf[(x, f)] for x in self.X for f in self.F), GRB.MINIMIZE)

        return

    def construct_model(self):
        '''
        construct normal formulation
        '''

        # initialize sets
        self.X_s, self.C_s = sp.get_student_sets(self.student_data, self.X)
        self.S_x, self.Size_x = sp.get_size_set(self.X_s)
        self.nroom_x = sp.get_noroom_section_sets(self.course_data, self.Size_x)

        # update new X
        self.X = set(self.X).difference(set(self.nroom_x))

        # update new R
        room = self.course_data[self.course_data['subject_number_section_orrurance'].isin(self.X)]['bldg_room']
        room_detail_isye = self.room_data[self.room_data['bldg_room'].isin(room)]
        self.R = room_detail_isye['bldg_room']

        self.k_f = sp.k_f
        self.F = sp.F

        self.n_rf = sp.get_capacity_sets(room_detail_isye)

        self.T_x, self.X_t, self.T_d = sp.get_timeslot_sets(self.course_data, self.X, self.T)
        self.X_wo_time = sp.get_section_wo_time(self.T_x)


        model = Model("Assignment Formulation ISYE")
        model_vars = self.set_model_vars(model)
        self.set_model_constrs(model, model_vars)
        self.set_objective(model, model_vars)
        return model


if __name__ == "__main__":
    course_data_isye, buildings_used_for_isye = dp.clean_course_data(
        'raw_data/ISYE_FallSemesterScenarios_ClassSchedules.xlsx')
    student_data_isye = dp.clean_student_data('raw_data/ISYE_FallSemesterScenarios_Students_Final.xlsx')

    room_data_isye = dp.clean_detail_room_data('raw_data/ISYE_FallSemesterScenarios_BuildingRooms.xlsx',
                                               buildings=buildings_used_for_isye)


    assign_opt = AssignmentOpt(course_data_isye, student_data_isye, room_data_isye)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()
    model.optimize()
