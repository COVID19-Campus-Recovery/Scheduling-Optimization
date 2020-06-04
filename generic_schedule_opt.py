from gurobipy import *
import pandas as pd
from abc import ABC
from abc import abstractmethod
import data_process as dp
import set_process as sp


class GenericScheduleOpt(ABC):

    def __init__(self, course_data, room_data):
        self.course_data = course_data
        self.room_data = room_data
        return

    @abstractmethod
    def get_all_sets_params(self):
        self.C = self.course_data['course_subject_number'].unique().tolist()
        self.X = self.course_data['subject_number_section_orrurance'].tolist()
        self.R = self.room_data['bldg_room'].tolist()
        T = self.course_data['full_time'].unique()
        self.T = T[~pd.isnull(T)].tolist()
        return

    @abstractmethod
    def set_model_vars(self, model):
        # Define decision variables
        pass

    @abstractmethod
    def set_model_constrs(self, model, model_vars):
        # Define constraints
        pass

    @abstractmethod
    def set_objective(self, model, model_vars):
        pass


    def construct_model(self, model_name="Generic Model"):
        self.get_all_sets_params()
        model = Model(model_name)
        model_vars = self.set_model_vars(model)
        self.set_model_constrs(model, model_vars)
        self.set_objective(model, model_vars)
        return model