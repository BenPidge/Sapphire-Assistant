from collections import Counter

import numpy as np
from pymoo.model.crossover import Crossover

from Code.Optimisation import ChromosomeController


class ChrCrossover(Crossover):
    """Combines the parent chromosomes to create new offspring."""

    def __init__(self):
        # 2 parents will produce 2 offspring
        super().__init__(2, 2)

    def _do(self, problem, x, **kwargs):
        """
        Takes parent chromosomes in order to produce offspring.
        :param problem: the problem the algorithm is trying to optimise
        :type problem: class: `Optimisation.ChrProblem`
        :param x: a list of the chromosomes to crossover
        :type x: class: `Pymoo.Model.Population`
        :param kwargs: arguments connected to their arg number
        :type kwargs: dict
        :return: the list of offspring
        """
        parents_num, matings_num, vars_num = x.shape
        output = np.full_like(x, None, dtype=np.object_)

        for cross in range(matings_num):
            # get parents and setup offspring list
            parents = []
            offspring = []
            for i in range(parents_num):
                parents.append(x[i, cross, 0])

            offspring.append(self.breed(parents))
            offspring.append(self.breed(parents))

            # empty offspring list into the output
            for i in range(len(offspring)):
                output[i, cross, 0] = offspring[i]
        return output

    @staticmethod
    def breed(parents):
        """
        Breeds all parents passed through to produce a single offspring, with randomly selected elements from the
        parents provided.
        :param parents: a list of the parent chromosomes to utilise
        :type parents: list
        :return: a new chromosome
        """
        # randomly allocate the class, race and background from one parent
        filters = dict({"Race": None, "Class": None, "Background": None,
                        "Equipment": [], "Spells": [], "Skills": [], "Proficiencies": [], "Languages": []})
        parentsNum = len(parents)
        elements = dict({"Race": [parent.character.race for parent in parents],
                         "Class": [parent.character.chrClass for parent in parents],
                         "Background": [parent.character.background for parent in parents]})

        for key, objs in elements.items():
            parentIndex = np.random.randint(0, parentsNum)
            filters[key] = objs[parentIndex].name
            if key == "Race":
                filters = ChrCrossover.get_ability_score(filters, parents[parentIndex].character.abilityScores)
            parentInfo = objs[parentIndex].get_data()
            for sub_element in ["Equipment", "Spells", "Skills", "Proficiencies", "Languages"]:
                filters[sub_element] += parentInfo.get(sub_element.lower(), [])

        filters["Primary"] = parents[0].archs[0]
        if parents[0].archs[1] is not None:
            filters["Secondary"] = parents[0].archs[1]

        chromosome = ChromosomeController.build_chromosome(filters)
        return chromosome

    @staticmethod
    def get_ability_score(filters, abilities):
        """
        Gets the ability score filter from the abilities provided.
        :param filters: the current filters applied
        :type filters: dict
        :param abilities: the abilities to match
        :type abilities: dict
        :return: the new filter, including the abilities
        """
        abilityFilter = dict()
        for ability, score in abilities.items():
            abilityFilter[ability] = [score, score]

        filters["Abilities"] = abilityFilter
        return filters

