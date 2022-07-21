from gurobipy import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
                                for x in self.X_w_time),"")

        C_4 = model.addConstrs((quicksum(X_xrt[(x, r, t)] for r in self.R for t in self.T) == 1
                                for x in self.X),"")

        M2 = max(self.room_data["Station Count (Current)"].astype(int))
        C_5 = model.addConstrs((quicksum(self.n_rf[(r, f)] * X_xrt[(x, r, t)] for t in self.T for r in self.R) - self.p_x[x]
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
        self.S_x, self.p_x = sp.get_size_set(self.X_s)
        self.nroom_x = sp.get_noroom_section_sets(self.course_data, self.p_x)

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
        self.X_w_time = sp.get_section_w_time(self.T_x)


        model = Model("Assignment Formulation ISYE")
        model_vars = self.set_model_vars(model)
        self.set_model_constrs(model, model_vars)
        self.set_objective(model, model_vars)
        return model

    def plot_generation(self):

        # AFTER OPT: sections that achieve safe distance level f
        x_f = {}
        for f in sp.F:
            x_f[f] = []
            for x in assign_opt.X:
                if model.getVarByName("D_xf[%s+%s]" % (x, f)).x == 0:
                    x_f[f].append(x)


        # BEFORE OPT:
        x_f_org = {}
        for x, n in assign_opt.p_x.items():
            for f in sp.F:
                if f not in x_f_org.keys():
                    x_f_org[f] = []
                room = course_data_isye[course_data_isye['subject_number_section_orrurance'] == x]['bldg_room'].iloc[0]
                if str(room) == "nan":
                    continue
                if n <= assign_opt.n_rf[(room, f)]:
                    x_f_org[f].append(x)


        # Since in the optimization, a section can achieve 0,6,8,12 at same time, we here need to delete the duplication
        ## BEFORE OPT
        sec = list(x_f_org.values())
        for i in range(len(x_f_org) - 1):
            sec[i] = set(sec[i]).difference(sec[i + 1])
        n_f_org = dict(zip(sp.F, sec))

        # AFTER OPT:
        sec = list(x_f.values())
        for i in range(len(x_f) - 1):
            sec[i] = set(sec[i]).difference(sec[i + 1])
        n_f = dict(zip(sp.F, sec))


        # The original data have some sections that do not have a room assignment.
        # Therefore, we should not consider those when comparing the result
        n_f_subset = {}
        for k, v in n_f.items():
            n_f_subset[k] = set(v).difference(assign_opt.nroom_x)

        # create plot
        n_groups = len(list(map(str, n_f_subset.keys())))

        fig, ax = plt.subplots()
        index = np.arange(n_groups)
        bar_width = 0.35
        opacity = 0.5

        rects1 = plt.bar(index, list(map(len, n_f_org.values())), bar_width,
                         alpha=opacity,
                         color='b',
                         label='Before optimization')

        rects2 = plt.bar(bar_width + index, list(map(len, n_f_subset.values())), bar_width,
                         alpha=opacity,
                         color='g',
                         label='After optimization')

        plt.xlabel('Safe Distance Level')
        plt.ylabel('Number of Section')
        plt.title('# of sections achieve f safe distance level')
        plt.xticks(index + bar_width, list(map(str, n_f_subset.keys())))
        plt.legend()

        plt.tight_layout()
        plt.show()



if __name__ == "__main__":
    course_data_isye, buildings_used_for_isye = dp.clean_course_data(
        'raw_data/ISYE_FallSemesterScenarios_ClassSchedules.xlsx')
    student_data_isye = dp.clean_student_data('raw_data/ISYE_FallSemesterScenarios_Students_Final.xlsx')

    room_data_isye = dp.clean_detail_room_data('raw_data/Room_Level_Data_20200522.xlsx',
                                               buildings=buildings_used_for_isye)


    assign_opt = AssignmentOpt(course_data_isye, student_data_isye, room_data_isye)
    model = assign_opt.construct_model()
    model.update()
    model.printStats()
    model.optimize()

    assign_opt.plot_generation()
