import math
from functools import partial

from PyQt5 import uic
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QGridLayout, QPushButton

from Code.Optimisation import ChromosomeController


class ConfirmationScreen:
    """Sets up and runs the loading screen between filters and optimisation."""

    controller = None
    filterVbox = QVBoxLayout()
    filters = None

    loadingScreenThread = None
    thread = None

    def __init__(self):
        """
        Sets up the loading screen visuals.
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/ConfirmationMenu.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")

    def begin(self, controller):
        """
        Begins the loading screen and visualises it.
        :param controller: the controller for the programs visuals
        :type controller: VisualsController
        """
        self.controller = controller
        self.centre.findChild(QScrollArea, "filtersScroller")\
            .findChild(QWidget, "scrollerContents").setLayout(self.filterVbox)

        self.extract_filters()
        self.centre.findChild(QLabel, "loadingLabel").hide()
        self.setup_buttons()

        self.window.show()

    def setup_buttons(self):
        """
        Sets up the inbuilt buttons to make the appropriate calls upon being clicked.
        """
        confirm = self.centre.findChild(QPushButton, "confirmBtn")
        confirm.clicked.connect(partial(self.confirmed))
        cancel = self.centre.findChild(QPushButton, "cancelBtn")
        cancel.clicked.connect(partial(self.controller.show_selector_menu))

    def confirmed(self):
        """
        Upon the options being confirmed, the two buttons are replaced with a label, the title label is updated
        and after the optimisation is complete, the next menu is loaded. This is done by connecting threads.
        """
        if self.thread is None:
            # load a new thread and loading screen object
            self.loadingScreenThread = LoadingScreenThread(self.centre)
            self.thread = QThread()

            # connect the thread and custom object to one another, set them to call run_optimisation upon completion,
            # and start the thread
            self.loadingScreenThread.moveToThread(self.thread)
            self.thread.started.connect(self.loadingScreenThread.run)
            self.loadingScreenThread.finished.connect(self.thread.quit)
            self.thread.finished.connect(self.run_optimisation)
        self.thread.start()

    def run_optimisation(self):
        """
        Updates the screen, runs the optimisation algorithm, then launches the review screen once it's finished.
        """
        self.window.show()
        ChromosomeController.set_const_filters(self.controller.filters)
        ChromosomeController.begin_optimising()
        self.controller.load_character_review()

    def extract_filters(self):
        """
        Extracts the filters applied from the previous menu, and visualises them in the loading screen.
        """
        self.filters = self.controller.filters

        self.extract_core_stats()
        self.extract_abilities()
        # goes through and adds all list-based filters
        for filterType, elements in self.filters.items():
            if type(elements) == list and len(elements) > 0:
                self.extract_filter_list(filterType, elements)

    def extract_core_stats(self):
        """
        Extracts the core statistics and adds them to the scroll area.
        """
        titleLabel = QLabel("Core Statistics")
        titleLabel.setStyleSheet('font: 20pt "Imprint MT Shadow"; color: #ffffff;')
        self.filterVbox.addWidget(titleLabel, alignment=Qt.AlignCenter)
        potentialLabels = ["Primary", "Secondary", "Class", "Subclass",
                           "Background", "Race", "Subrace", "Minimum AC"]

        for label in potentialLabels:
            if label in ["Primary", "Secondary"]:
                textAddition = " Archetype"
            else:
                textAddition = ""
            try:
                nextLabel = QLabel(f"{label + textAddition}: {self.filters[label]}")
                nextLabel.setStyleSheet('font: 14pt "Times New Roman"; color: rgb(188, 189, 177);')
                self.filterVbox.addWidget(nextLabel, alignment=Qt.AlignCenter)
            except KeyError:
                pass

    def extract_abilities(self):
        """
        Extracts the ability score boundaries and visualises them in the scroll area.
        """
        titleLabel = QLabel("Ability Scores")
        titleLabel.setStyleSheet('font: 20pt "Imprint MT Shadow"; color: #ffffff;')
        grid = QGridLayout()
        self.filterVbox.addWidget(titleLabel, alignment=Qt.AlignCenter)
        self.filterVbox.addLayout(grid)

        counter = 0
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        for [minVal, maxVal] in self.filters["Abilities"].values():
            nextLabel = QLabel(f"{abilities[counter]} - Between {str(minVal)} & {str(maxVal)}")
            nextLabel.setStyleSheet('font: 12pt "Times New Roman"; color: rgb(188, 189, 177);')
            grid.addWidget(nextLabel, math.floor(counter / 2), counter % 2, alignment=Qt.AlignCenter)
            counter += 1

    def extract_filter_list(self, filter_type, elements):
        """
        Extracts one filter groups' elements from it's array and adds them to the scroll area.
        :param filter_type: the name of the filter group, such as Equipment
        :type filter_type: str
        :param elements: the list of filters to be applied
        :type elements: list
        """
        titleLabel = QLabel(filter_type)
        titleLabel.setStyleSheet('font: 20pt "Imprint MT Shadow"; color: #ffffff;')
        grid = QGridLayout()
        self.filterVbox.addWidget(titleLabel, alignment=Qt.AlignCenter)
        self.filterVbox.addLayout(grid)

        counter = 0
        for element in elements:
            nextLabel = QLabel(element)
            nextLabel.setStyleSheet('font: 12pt "Times New Roman"; color: rgb(188, 189, 177);')
            grid.addWidget(nextLabel, math.floor(counter/3), counter % 3, alignment=Qt.AlignCenter)
            counter += 1


class LoadingScreenThread(QObject):
    """
    An object allowing a thread to be used for the confirmation screen updates.
    """
    finished = pyqtSignal()
    def __init__(self, centre):
        """
        Call the parent initialisation, and set the centre variable
        :param centre: the centre object of the Qt file being threaded
        :type centre: QtWidget
        """
        super().__init__()
        self.centre = centre

    def run(self):
        """
        Runs the thread, which updates the confirmation screen to visually show it is preparing results.
        """
        self.centre.findChild(QPushButton, "confirmBtn").hide()
        self.centre.findChild(QPushButton, "cancelBtn").hide()
        self.centre.findChild(QLabel, "loadingLabel").show()
        self.centre.findChild(QLabel, "title").setText("Optimisation & Visualisation Processing")
        self.finished.emit()

