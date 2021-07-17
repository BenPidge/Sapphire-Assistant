import numpy as np
from pymoo.model.problem import Problem


class ChrProblem(Problem):
    """Defines the problem that the optimisation system must solve."""

    def __init__(self, tag_num):
        """
        Stores the amount of tags to optimise and calls the Problem initialisation with the appropriate parameters.
        :param tag_num: the amount of tags to optimise
        :type tag_num: int
        """
        self.n_obj = tag_num
        super().__init__(n_var=1, n_obj=tag_num, n_constr=0, elementwise_evaluation=True)

    def _evaluate(self, x, out, *args, **kwargs):
        """
        Evaluates a chromosome for it's value in meeting the objectives of the task.
        :param x: a list of the variables to evaluate.
        :type x: list
        :param out: the output of the evaluations, with the F key for objective values and G for constraints
        :type out: dict
        :param args: the arguments passed through
        :type args: list
        :param kwargs: arguments connected to their arg number
        :type kwargs: dict
        """
        fitness_values = x[0].get_tag_fitness_values()
        # change all fitness values to their negative counterparts as Pymoo only minimises
        for i in range(self.n_obj):
            try:
                fitness_values[i] *= -1
            # defensive code to set any non-covered objectives to 0. This theoretically should never be called
            except IndexError:
                fitness_values[i] = 0
        out["F"] = np.array(fitness_values, dtype=float)
