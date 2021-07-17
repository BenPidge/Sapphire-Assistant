import numpy as np
from pymoo.model.mutation import Mutation

from Code.Database import CharacterBuilder
from Code.Optimisation import ChromosomeController


class ChrMutation(Mutation):
    """Mutates a character chromosome, with the potential to leave it unchanged."""

    randomResults = [["Race", "Subrace"], ["Class", "Subclass"], "Background", "Languages",
                     "Proficiencies", "Spells", "Equipment", "Skills"]

    def _do(self, problem, x, **kwargs):
        """
        Performs a randomised mutation on provided chromosomes.
        :param problem: the problem the algorithm is trying to optimise
        :type problem: class: `Optimisation.ChrProblem`
        :param x: a list of the chromosomes to mutate
        :type x: class: `Pymoo.Model.Population`
        :param kwargs: arguments connected to their arg number
        :type kwargs: dict
        :return: the list of modified chromosomes
        """
        for i in range(len(x)):
            randVal = np.random.randint(0, 100)
            filters = x[i, 0].get_data_as_filters()

            if randVal < 80:
                # gets the elements data from randomResult, and the sub-value to edit it with
                elementSubdata = randVal % 10
                element = self.randomResults[(randVal//10) - 1]

                # if the element is a list, get the appropriate sub-element from it
                if type(element) is list:
                    newElement = element[elementSubdata//5]
                    if newElement not in filters:
                        newElement = element[0]
                    element = newElement

                filters = CharacterBuilder.change_filter(x[i, 0].character, filters, element, elementSubdata)
                x[i, 0] = ChromosomeController.build_chromosome(filters)

        return x

