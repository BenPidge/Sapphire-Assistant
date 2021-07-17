from functools import partial

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QScrollArea, QGridLayout, QLabel
import Code.Database.CoreDatabase as Db


class DataPiece:
    """Views a single piece of data in the database."""

    controller = None

    def __init__(self, controller, data, table):
        """
        Sets up and visualises the data visuals.
        :param controller: the controller for the applications visuals
        :type controller: VisualsController
        :param data: the data values of the row
        :type data: list
        :param table: the table that the data is pulled from
        :type table: str
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/DataPieceMenu.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")

        self.controller = controller
        self.data = data
        self.table = table
        self.centre.findChild(QScrollArea, "scrollArea") \
            .findChild(QWidget, "scrollAreaWidgetContents").setLayout(QGridLayout())
        self.grid = self.centre.findChild(QScrollArea, "scrollArea") \
            .findChild(QWidget, "scrollAreaWidgetContents").findChild(QGridLayout)
        self.setup_data()

        shadowItems = {"deleteBtn": QPushButton}
        self.centre = self.controller.setup_shadows(self.centre, shadowItems)
        self.centre.findChild(QPushButton, "deleteBtn").clicked.connect(partial(self.delete_data))

        self.window.show()

    def setup_data(self):
        """
        Sets up the data to be visually shown.
        """
        Db.cursor.execute(f"PRAGMA table_info('{self.table}');")
        self.centre.findChild(QLabel, "tableLabel").setText(self.table)
        idLabel = self.centre.findChild(QLabel, "idLabel")
        idLabel.setText("")
        counter = 0

        for (index, name, _, _, _, _) in Db.cursor.fetchall():
            if "Id" in name:
                idLabel.setText(idLabel.text() + " / " + str(self.data[index]))
            else:
                title = QLabel(name)
                text = QLabel(str(self.data[index]))
                self.grid.addWidget(title, counter, 0)
                self.grid.addWidget(text, counter, 1)
                counter += 1
        idLabel.setText(idLabel.text()[3:])

    def delete_data(self):
        """
        Deletes the piece of data from the database.
        """
        databaseCall = f"DELETE FROM {self.table} WHERE "
        Db.cursor.execute(f"PRAGMA table_info('{self.table}');")
        for (index, name, _, _, _, _) in Db.cursor.fetchall():
            if type(self.data[index]) is str:
                info = "'" + self.data[index] + "'"
            else:
                info = str(self.data[index])
            databaseCall += name + "=" + info + " AND "
        databaseCall = databaseCall[:-5]
        Db.cursor.execute(databaseCall)
        self.controller.data_piece_deleted()
