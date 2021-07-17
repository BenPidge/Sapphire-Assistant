import threading
import sqlite3 as sql
from functools import partial

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication

from Code.Database import CoreDatabase, DatabaseSetup, DataExtractor


class MainMenu:
    """Sets up and runs the main menu."""

    controller = None

    def __init__(self):
        """
        Sets up the main menu visuals.
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/MainMenu.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")
        self.thread = threading.Thread(target=self.dev_btn)

    def begin(self, controller):
        """
        Begins the main menu and visualises it.
        :param controller: the controller for the programs visuals
        :type controller: VisualsController
        """
        self.controller = controller

        self.centre.findChild(QPushButton, "devBtn").clicked.connect(self.dev_btn_pressed)
        shadowItems = {"optimiseBtn": QPushButton,
                       "npcBtn": QPushButton,
                       "databaseBtn": QPushButton,
                       "exitBtn": QPushButton}
        self.centre = self.controller.setup_shadows(self.centre, shadowItems)

        self.centre.findChild(QPushButton, "optimiseBtn").clicked.connect(partial(self.controller.start_selector_menu))
        self.centre.findChild(QPushButton, "databaseBtn").clicked.connect(partial(self.controller.start_database_menu))
        self.centre.findChild(QPushButton, "exitBtn").clicked.connect(partial(lambda x: exit(0)))

        self.window.show()



    def dev_btn_pressed(self):
        """
        Sets up the threading necessary to access the dev menu.
        """
        QApplication.quit()
        self.window.close()
        CoreDatabase.complete_setup()
        self.thread.start()

    @staticmethod
    def dev_btn():
        """
        Calls the systems reaction to the Dev Menu button being pressed.
        """
        CoreDatabase.connection = sql.connect(CoreDatabase.dir_path + "/Resources/ChrDatabase.db")
        CoreDatabase.cursor = CoreDatabase.connection.cursor()
        print("Enter which service you'd like to use:\n"
              "1. Database Setup\n"
              "2. View Tables\n"
              "3. General testing\n"
              "4. Exit")
        menu = CoreDatabase.int_input("> ")
        if menu == 1:
            DatabaseSetup.begin()
        elif menu == 2:
            CoreDatabase.view_tables()
        elif menu == 3:
            # replace me with whatever needs testing!
            DataExtractor.begin()
        else:
            SystemExit(0)
        CoreDatabase.complete_setup()
