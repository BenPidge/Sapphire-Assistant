import copy

import numpy as np
from pymoo.model.sampling import Sampling

from Code.Optimisation import ChromosomeController


class ChrSampling(Sampling):
    """A Sampling overwrite that allows the creation of character samples."""

    def _do(self, problem, n_samples, **kwargs):
        """
        Creates a set amount of character chromosome samples.
        :param problem: the problem being optimised
        :type problem: ChrProblem
        :param n_samples: the amount of chromosome samples to build
        :type n_samples: int
        :param kwargs: arguments connected to their arg number
        :type kwargs: dict
        :return: a numpy array holding the chromosomes
        """
        results = np.full((n_samples, 1), None, np.object_)
        filters = copy.deepcopy(ChromosomeController.constFilters)
        for i in range(n_samples):
            results[i, 0] = ChromosomeController.build_chromosome(filters)
        return results

