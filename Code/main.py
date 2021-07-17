from Database import DataConverter
from Optimisation import ChromosomeController
from Visuals import VisualsController


visuals = VisualsController.VisualsController()


def testing():
    ChromosomeController.begin()


def begin():
    """
    Begins the program.
    """
    DataConverter.create_all_equipment()
    visuals.begin()

begin()
