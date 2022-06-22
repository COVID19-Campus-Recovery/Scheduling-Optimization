from gurobipy import *
import pandas as pd
from abc import ABC
from abc import abstractmethod
import data_process as dp
import set_process as sp

class GenericScheduleOpt(ABC):
    """
    All schedule optimization classes should be a descendant of this abstract class,
    as it provides a framework for methods that should be implemented.
    This class makes no assumptions regarding the algorithm used
    Nor does this class make assumptions about the data inputed to the optimization model
    """

    def __init__(self):
        return

    @abstractmethod
    def get_all_sets_params(self):
        return

    @abstractmethod
    def set_model_vars(self, model):
        pass

    @abstractmethod
    def set_model_constrs(self, model, model_vars):
        pass

    @abstractmethod
    def set_objective(self, model, model_vars):
        pass

    def construct_model(self):
        """
        It is recommended that this method is not overridden by descendant classes

        Output:
            Gurobi.model : gurobi model already has variables, constraints, and objective defined.
            Once returned, the user should run model.optimize() to retrieve results
        """
        self.get_all_sets_params()
        model = Model("")
        model_vars = self.set_model_vars(model)
        self.set_model_constrs(model, model_vars)
        self.set_objective(model, model_vars)
        return model