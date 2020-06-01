from gurobipy import *
import data_process as dp
import set_process as sp


class ScheduleOpt():

    def __init__(self, course_data, student_data, room_data):
        self.course_data = course_data
        self.student_data = student_data
        self.room_data = room_data
        self.S = student_data['SYSGENID'].tolist()
        self.C = course_data['course_subject_number'].unique().tolist()
        self.X = course_data['subject_number_section_orrurance'].tolist()
        self.R = room_data['bldg_room'].tolist()
        self.T = course_data['full_time'].unique().tolist()
        return

    def set_model_vars(self, model):
        # Define decision variables
        X_xrt, Y_sxt, Z_ixt, W_sc = {},{},{},{}
        for x in self.X:
            for r in self.R:
                for t in self.T:  
                    X_xrt[(x, r, t)] = model.addVar(vtype=GRB.BINARY, name='X_xrt[%s+%s+%s]' %(x, r, t))
        for s in self.S:
            for x in self.X:
                for t in self.T:
                    Y_sxt[(s, x, t)] = model.addVar(vtype=GRB.BINARY, name='Y_sxt[%s+%s+%s]' %(s, x, t))
        '''
        for i in I:
            for x in X:
                for t in T:
                    Z_ixt[(i,x,t)] = model.addVar(vtype=GRB.BINARY, name='Z_ixt[%s+%s+%s]' %(i,x,t)) 
        '''
        for s in self.S:
            for c in self.C:
                W_sc[(s, c)] = model.addVar(vtype=GRB.BINARY, name='W_sc[%s+%s]' %(s, c))
        model_vars = {"X_xrt": X_xrt, "Y_sxt": Y_sxt, "Z_ixt": Z_ixt, "W_sc": W_sc}
        return model_vars

    def set_model_constrs(self, model, model_vars):
        X_xrt = model_vars["X_xrt"]
        Y_sxt = model_vars["Y_sxt"]
        W_sc = model_vars["W_sc"]

        # define constraints
        C_2_1 = model.addConstrs((quicksum(Y_sxt[(s, x, t)] for x in set(self.X)-set(self.X_s[s])) == 0
                                  for s in self.S for t in self.T), "")

        C_1 = model.addConstrs((quicksum(Y_sxt[(s,x,t)] for x in self.X_c[c] for t in self.T_x[x]) == W_sc[(s,c)]
                               for s in self.S for c in self.C), "")
        # This constraint should be met for sure, since we assume that we cannot change the sections here.

        C_2 = model.addConstrs((quicksum(Y_sxt[(s, x, t)] for x in self.X_s[s]) <= 1
                                for s in self.S for t in self.T), "")

        C_3 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for x in self.X_r[r]) <= 1
                                for r in self.R for t in self.T), "")

        C_4 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for t in self.T for r in self.R) == 1
                                for x in self.X), "")
        '''
        # This new constraint is too time-consuming, I added a M to reduce the complexity.

        model.addConstrs((quicksum(X_xrt[(x,r,t)] for r in R) >= Y_sxt[(s,x,t)]
                                       for x in X for t in T for s in S), "")
        '''
        M = len(self.S)
        C_5 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for r in self.R)*M >= quicksum(Y_sxt[(s, x, t)] for s in self.S)
                                       for x in self.X for t in self.T), "")
        return

    def set_objective(self, model, model_vars):
        W_sc = model_vars["W_sc"]
        model.setObjective(quicksum(W_sc[(s, c)] for s in self.S for c in self.C),
                           GRB.MAXIMIZE)
        return

    def construct_model(self):
        '''
        construct normal formulation
        '''

        # initialize sets
        self.X_c = sp.get_section_set(self.course_data, self.C)
        self.X_s, self.C_s = sp.get_student_sets(self.student_data, self.X)
        self.T_x, self.X_t, self.T_d = sp.get_timeslot_sets(self.X, self.T)
        self.R_x, self.X_r = sp.get_room_sets(self.course_data, self.room_data,
                                              self.R, self.X)

        model = Model("Normal Formulation")
        model_vars = self.set_model_vars(model)
        self.set_model_constrs(model, model_vars)
        self.set_objective(model, model_vars)
        return model


if __name__ == "__main__":
    course_data_isye, buildings_used_for_isye = dp.clean_course_data('raw_data/ISYE_FallSemesterScenarios_ClassSchedules.xlsx')
    student_data_isye = dp.clean_student_data('raw_data/ISYE_FallSemesterScenarios_Students_Final.xlsx')

    room_data_isye = dp.clean_room_data('raw_data/ISYE_FallSemesterScenarios_BuildingRooms.xlsx',
                                        buildings=buildings_used_for_isye)


    schedule_opt = ScheduleOpt(course_data_isye, student_data_isye, room_data_isye)
    model = schedule_opt.construct_model()
    model.optimize()
