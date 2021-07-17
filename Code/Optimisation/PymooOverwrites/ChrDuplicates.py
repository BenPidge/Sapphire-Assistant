from pymoo.model.duplicate import ElementwiseDuplicateElimination


class ChrDuplicates(ElementwiseDuplicateElimination):
    """Detects duplicate chromosome, which the base ElementwiseDuplicateElimination then removes."""

    def is_equal(self, a, b):
        """
        Checks whether two character chromosome elements are equal.
        This is provided for fullness of the system - the core implementation is within the
        Optimisation.Chromosome.__eq__ method overwrite.
        :param a: the first character chromosome to compare
        :type a: Optimisation.Chromosome
        :param b: the second character chromosome to compare
        :type b: Optimisation.Chromosome
        :return: a boolean stating whether they're equal
        """
        return a == b

