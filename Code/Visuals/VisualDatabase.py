import itertools
from functools import partial

from PyQt5 import uic
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QWidget, QComboBox, QCheckBox, QTabWidget, QLabel, QScrollArea, QVBoxLayout, \
    QGridLayout, QSpinBox, QTextEdit, QDoubleSpinBox, QPushButton, QGraphicsDropShadowEffect, QGraphicsView

import Code.Database.CoreDatabase as Db
from Code.Visuals import DataPiece


class VisualDatabase:
    """Sets up and runs the database menu."""

    controller = None
    currentTable = None
    # this is in the form of [addition, related] with sub-lists of [widget, call to read widget]
    dataWidgets = [[], []]

    def __init__(self):
        """
        Sets up the database menu visuals.
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/DatabaseMenu.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")

        self.tableSelector = self.centre.findChild(QComboBox, "tableSelect")
        self.includeTables = self.centre.findChild(QCheckBox, "allTables")
        self.tabs = {"addition": QVBoxLayout(), "view": QVBoxLayout(), "related": QVBoxLayout()}

    def begin(self, controller):
        """
        Begins the database menu and visualises it.
        :param controller: the controller for the programs visuals
        :type controller: VisualsController
        """
        self.controller = controller

        shadowItems = {"saveChangesBtn": QPushButton,
                       "mainMenuBtn": QPushButton}
        self.centre = self.controller.setup_shadows(self.centre, shadowItems)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        self.centre.findChild(QTabWidget, "tabWidget").findChild(QWidget, "additionTab")\
            .findChild(QPushButton, "addItem").setGraphicsEffect(shadow)

        self.setup_tabs()
        self.setup_table_select()
        self.includeTables.clicked.connect(partial(self.update_table_options))
        self.centre.findChild(QPushButton, "mainMenuBtn").clicked.connect(partial(self.controller.return_to_main_menu))
        self.centre.findChild(QPushButton, "saveChangesBtn").clicked.connect(partial(Db.connection.commit))

        self.window.show()



    def setup_tabs(self):
        """
        Sets up the tabs to be ready for addition.
        """
        tabWidget = self.centre.findChild(QTabWidget, "tabWidget")
        for tab in ["addition", "view", "related"]:
            self.tabs[tab] = tabWidget.findChild(QWidget, tab + "Tab")\
                .findChild(QScrollArea, tab + "Scroller").findChild(QWidget, tab + "ScrollerContents")
            self.tabs[tab].setLayout(QGridLayout())
        tabWidget.findChild(QWidget, "additionTab").findChild(QPushButton, "addItem")\
            .clicked.connect(partial(self.add_item))

    def setup_table_select(self):
        """
        Sets up the table selection combo box.
        """
        self.tableSelector.setPlaceholderText("Select Table")
        self.tableSelector.textActivated.connect(partial(self.new_active_table))
        self.update_table_options()

    def new_active_table(self):
        """
        Sets up a new active table to interact with.
        """
        self.currentTable = self.tableSelector.currentText()
        self.reset_addition()
        self.reset_view()
        self.reset_related()

    def empty_tab(self, tab):
        """
        Empties all the items in the grid of the specified tab.
        :param tab: the tab to empty
        :type tab: str
        """
        grid = self.tabs[tab].findChild(QGridLayout)
        for i in reversed(range(grid.count())):
            grid.itemAt(i).widget().deleteLater()



    def reset_addition(self):
        """
        Resets and sets up the addition tab to fit the new table.
        """
        self.empty_tab("addition")
        counter = 0
        Db.cursor.execute(f"PRAGMA table_info('{self.currentTable}');")

        # build all new inputs
        if sum(1 for letter in self.currentTable if letter.isupper()) == 1 or self.currentTable == "ClashTag":
            for (_, name, datatype, _, _, _) in Db.cursor.fetchall():
                self.construct_input_slot(name, datatype, counter, self.tabs["addition"].findChild(QGridLayout), 0)
                counter += 1

    def add_item(self):
        """
        Adds the inputted data into the database table.
        """
        values = []
        for [_, method] in self.dataWidgets[0]:
            values.append(method())
        values = [Db.highest_id(self.currentTable) + 1] + values
        Db.insert(self.currentTable, tuple(values))
        self.new_active_table()

    def update_table_options(self):
        """
        Updates the available tables to select, based on whether the includeTables box is checked.
        """
        Db.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
        tableItems = sorted(list(itertools.chain(*Db.cursor.fetchall())))
        if not self.includeTables.isChecked():
            tableItemsCopy = tableItems.copy()
            tableItems.clear()
            for table in tableItemsCopy:
                if sum(1 for letter in table if letter.isupper()) == 1 or table == "ClashTag":
                    tableItems.append(table)

        self.tableSelector.clear()
        self.tableSelector.addItems(tableItems)

    def construct_input_slot(self, name, datatype, column, grid, list_index):
        """
        Constructs an input slot for the user to enter data into.
        :param name: the name of the data input
        :type name: str
        :param datatype: the datatype of the data input
        :type datatype: str
        :param column: the y position of the input slot on the grid
        :type column: int
        :param grid: the grid to add the widgets to
        :type grid: QObject
        :param list_index: the index of the data widgets to use
        :type list_index: int
        :return: a 2D array, containing arrays of [widget, widget read call]
        """
        if "Id" in name:
            return
        grid.addWidget(QLabel(f"Enter the data for {name}:"), column, 0)
        widget = QLabel(datatype + " is not supported.")
        widgetReader = None

        if "TINYINT" in datatype:
            widget = QCheckBox()
            widgetReader = widget.isChecked
        elif "INT" in datatype:
            widget = QSpinBox()
            widgetReader = widget.value
        elif "VARCHAR" in datatype:
            widget = QTextEdit()
            widget.setTabChangesFocus(True)
            widget.textChanged.connect(partial(self.limit_text_length, widget,
                                               int(datatype.replace("VARCHAR(", "").replace(")", ""))))
            widgetReader = widget.toPlainText
        elif "DECIMAL" in datatype:
            widget = QDoubleSpinBox()
            widgetReader = widget.value
        elif "MEDIUMTEXT" in datatype:
            widget = QTextEdit()
            widget.setTabChangesFocus(True)
            widgetReader = widget.toPlainText

        grid.addWidget(widget, column, 1)
        self.dataWidgets[list_index].append([widget, widgetReader])



    def reset_view(self):
        """
        Resets and sets up the view tab to fit the new table.
        """
        self.empty_tab("view")
        position = [0, 0]

        # if it's a primary tag, name it from the entered name
        if sum(1 for letter in self.currentTable if letter.isupper()) == 1:
            if self.currentTable == "Name":
                Db.cursor.execute("SELECT name FROM Name")
            else:
                Db.cursor.execute(f"SELECT {self.currentTable.lower()}Name FROM {self.currentTable}")
            for name in sorted(Db.cursor.fetchall()):
                self.view_data_slot(name[0], position)
                position = self.increment_pos_tuple(position, 1)

        # otherwise, name it as "idName1 -> idName2"
        else:
            # gets the positions of the columns that hold an id
            idColumns = []
            Db.cursor.execute(f"PRAGMA table_info('{self.currentTable}');")
            for (pos, name, _, _, _, _) in Db.cursor.fetchall():
                if "Id" in name:
                    idColumns.append((name.replace("Id", "").capitalize(), pos))

            # creates a name for each row of data, based on it's id values
            Db.cursor.execute(f"SELECT * FROM {self.currentTable}")
            names = []
            for row in Db.cursor.fetchall():
                name = ""
                for (table, idPos) in idColumns:
                    name += " -> " + Db.get_name(int(row[idPos]), table)
                names.append((name, row))
            # sorts them before adding them for ease of traversal
            names.sort(key=lambda tup: tup[0])
            for (name, row) in names:
                self.view_data_slot(name[4:], position, row)
                position = self.increment_pos_tuple(position, 1)

    def view_data_slot(self, name, position, data=None):
        """
        Loads and constructs the visuals for a single piece of data for viewing.
        :param name: the name representing the row of data
        :type name: str
        :param position: the x & y position of the input slot on the grid
        :type position: list
        :param data: the data that the data slot will represent, or an empty list if the name is also the <table>Name
                     column value
        :type data: list
        """
        if data is None:
            dbFriendlyName = name.replace("'", "''")
            if self.currentTable == "Name":
                Db.cursor.execute(f"SELECT * FROM Name WHERE name = '{dbFriendlyName}'")
            else:
                Db.cursor.execute(f"SELECT * FROM {self.currentTable} "
                                  f"WHERE {self.currentTable.lower()}Name = '{dbFriendlyName}'")
            data = list(Db.cursor.fetchone())
        widget = QPushButton(name)
        widget.clicked.connect(partial(self.controller.open_view_popup, data, self.currentTable))
        self.tabs["view"].findChild(QGridLayout).addWidget(widget, position[0], position[1])



    def reset_related(self):
        """
        Resets and sets up the related tab to fit the new table.
        """
        self.empty_tab("related")

        rows = self.centre.findChild(QTabWidget, "tabWidget").findChild(QWidget, "relatedTab")\
            .findChild(QComboBox, "rowSelect")
        rows.clear()

        Db.cursor.execute(f"PRAGMA table_info('{self.currentTable}');")
        tableName = self.currentTable[0].lower() + self.currentTable[1:] + "Name"
        if tableName in list(itertools.chain(*Db.cursor.fetchall())):
            Db.cursor.execute(f"SELECT {tableName} FROM {self.currentTable}")
            rows.addItems(list(itertools.chain(*Db.cursor.fetchall())))
        elif self.currentTable == "Name":
            Db.cursor.execute("SELECT name FROM Name")
            rows.addItems(list(itertools.chain(*Db.cursor.fetchall())))

        counter = 0
        Db.cursor.execute(
            f"SELECT tbl_name, sql FROM sqlite_master WHERE sql LIKE('%REFERENCES `{self.currentTable}`%')")

        # for every table that references the current table, create a display for it, providing it's data entries
        # have a column for a name OR it's an intermediary table for two others.
        # Otherwise, it can't be referred to, so shouldn't be connected in this way
        for (name, sql) in Db.cursor.fetchall():
            primaryKeyPos = sql.find("PRIMARY KEY")
            primaryKeys = sql[primaryKeyPos + 13:sql.find(")", primaryKeyPos)].replace("`", "").split(", ")
            if name[0].lower() + name[1:] + "Name" in sql or \
                    (len(primaryKeys) > 1 and name[0].lower() + name[1:] + "Id" not in primaryKeys
                     and "Options" not in ''.join(primaryKeys)):
                self.tabs["related"].findChild(QGridLayout).addWidget(self.related_table(name), counter, 0)
                counter += 1

    def related_table(self, table_name):
        """
        Crafts the UI segment for a single related table.
        :param table_name: the name of the related table to build a UI for
        :type table_name: str
        :return: a widget of the outcome
        """
        tableVisuals = uic.loadUi("Visuals/QtFiles/RelatedTableSubmenu.ui")
        tableVisuals = self.controller.setup_shadows(tableVisuals, {"background": QGraphicsView})
        tableVisuals.findChild(QLabel, "tableName").setText(table_name)
        tableVisuals.findChild(QScrollArea, "extraInfo")\
            .findChild(QWidget, "extraInfoContents").setLayout(QGridLayout())
        tableVisuals.findChild(QScrollArea, "currentConnections") \
            .findChild(QWidget, "currentConnectionsContents").setLayout(QGridLayout())
        extraInfo = tableVisuals.findChild(QScrollArea, "extraInfo") \
                                              .findChild(QWidget, "extraInfoContents").findChild(QGridLayout)
        currentConnections = tableVisuals.findChild(QScrollArea, "currentConnections") \
            .findChild(QWidget, "currentConnectionsContents").findChild(QGridLayout)

        # get the entry options
        tableVisuals.findChild(QPushButton, "addBtn").clicked.connect(partial(self.add_relation, tableVisuals))
        dropdown = tableVisuals.findChild(QComboBox, "comboBox")
        primaryKeys, entries = self.get_related_table_entries(table_name)
        for entry in entries:
            dropdown.addItem(entry[0])

        if len(primaryKeys) > 1:
            counter = 0
            Db.cursor.execute(f"PRAGMA table_info('{table_name}');")
            for (_, name, datatype, _, _, _) in Db.cursor.fetchall():
                if "Id" not in name:
                    self.construct_input_slot(name, datatype, counter, extraInfo, 1)
                    counter += 1

        self.show_current_contents(table_name, currentConnections)

        return tableVisuals

    def get_related_table_entries(self, table_name):
        """
        Gets all the entries in to a given table, or those of the one it's an intermediary for.
        :param table_name: the name of the table to look at relations to
        :type table_name: str
        :return: the primary keys for, and a list of, the entries for the table
        """
        Db.cursor.execute(f"SELECT sql FROM sqlite_master WHERE tbl_name = '{table_name}'")
        tableId = table_name[0].lower() + table_name[1:] + "Id"
        data = Db.cursor.fetchone()[0]

        primaryKeyPos = data.find("PRIMARY KEY")
        primaryKeys = data[primaryKeyPos+13:data.find(")", primaryKeyPos)].replace("`", "").split(", ")

        # if it's used for linking two tables, replace it's info with that of the table being linked
        if len(primaryKeys) > 1:
            currentTableIdPos = primaryKeys.index(self.currentTable[0].lower() + self.currentTable[1:] + "Id")
            tableId = primaryKeys[1-currentTableIdPos]
            table_name = primaryKeys[1-currentTableIdPos].replace("Id", "").capitalize()

        Db.cursor.execute(f"SELECT {tableId.replace('Id', 'Name')} FROM {table_name}")
        return primaryKeys, Db.cursor.fetchall()

    def show_current_contents(self, table_name, grid):
        """
        Shows the current links having been made by the given table.
        :param table_name: the table that made the links
        :param grid: the grid to add the results to
        :type grid: QObject
        """
        Db.cursor.execute(f"PRAGMA table_info('{self.currentTable}');")
        if self.currentTable[0].lower() + self.currentTable[1:] + "Name" not in \
            list(itertools.chain(*Db.cursor.fetchall())):
            return

        tableNameCol = table_name[0].lower() + table_name[1:] + "Name"
        currentTableId = self.currentTable[0].lower() + self.currentTable[1:] + "Id"
        Db.cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = []
        counter = 0
        for (_, name, _, _, _, _) in Db.cursor.fetchall():
            columns.append(name)

        # annoying exception to general rules
        if self.currentTable == "Country":
            Db.cursor.execute("SELECT locationName, country FROM Location")
            for (location, country) in Db.cursor.fetchall():
                grid.addWidget(QLabel(location), counter, 0)
                grid.addWidget(QLabel(country), counter, 1)
                counter += 1

        # if the joining table has a name
        elif tableNameCol in columns:
            Db.cursor.execute(f"SELECT {tableNameCol}, {currentTableId} FROM {table_name}")
            for row in Db.cursor.fetchall():
                result = Db.get_name(row[1], self.currentTable)
                if result is not None:
                    grid.addWidget(QLabel(result[0]), counter, 0)
                    grid.addWidget(QLabel(str(row[0])), counter, 1)
                    counter += 1

        # if the joining table is an intermediary table
        else:
            primaryKeys = list([column for column in columns if "Id" in column])
            Db.cursor.execute(f"SELECT {primaryKeys[0]}, {primaryKeys[1]} FROM {table_name}")
            for ids in Db.cursor.fetchall():
                xCounter = 0
                for cid in ids:
                    Db.cursor.execute(f"SELECT {primaryKeys[xCounter][:-2]}Name FROM "
                                      f"{primaryKeys[xCounter][:-2].capitalize()} WHERE {primaryKeys[xCounter]}={cid}")
                    result = Db.cursor.fetchone()
                    if result is not None:
                        grid.addWidget(QLabel(result[0]), counter, xCounter)
                    xCounter += 1
                counter += 1

    def add_relation(self, visuals):
        """
        Adds a relation into the database, based on the dropdown box.
        """
        data = []
        selectedMainRow = self.centre.findChild(QTabWidget, "tabWidget").findChild(QWidget, "relatedTab")\
            .findChild(QComboBox, "rowSelect").currentText()
        selectedChoice = visuals.findChild(QComboBox, "comboBox").currentText()
        selectedTable = visuals.findChild(QLabel, 'tableName').text()
        if selectedChoice == "Select Entry" or selectedMainRow == "Select Row":
            return

        for item in self.dataWidgets[1]:
            data.append(item[1]())
        Db.cursor.execute(f"PRAGMA table_info('{selectedTable}');")
        for (cid, name, _, _, _, _) in Db.cursor.fetchall():
            if name == selectedTable[0].lower() + selectedTable[1:] + "Id" \
                    or (name == "country" and selectedTable == "Location"):
                data.insert(cid, Db.get_id(selectedChoice, selectedTable))
            elif name == self.currentTable[0].lower() + self.currentTable[1:] + "Id":
                data.insert(cid, Db.get_id(selectedMainRow, self.currentTable))
            elif "Id" in name:
                data.insert(cid, Db.get_id(selectedChoice, name.replace("Id", "").capitalize()))
        if "" in data:
            data.remove("")

        Db.insert(selectedTable, tuple(data))
        index = self.centre.findChild(QTabWidget, "tabWidget").findChild(QWidget, "relatedTab")\
            .findChild(QComboBox, "rowSelect").currentIndex()
        self.reset_related()
        self.centre.findChild(QTabWidget, "tabWidget").findChild(QWidget, "relatedTab") \
            .findChild(QComboBox, "rowSelect").setCurrentIndex(index)



    @staticmethod
    def increment_pos_tuple(pos, y_limit):
        """
        Increments the position stored in a list.
        :param pos: the tuple to increment
        :type pos: list
        :param y_limit: the highest potential value of the y value
        :type y_limit: int
        :return: the new list
        """
        if pos[1] == y_limit:
            pos[0] += 1
            pos[1] -= y_limit
        else:
            pos[1] += 1
        return pos

    @staticmethod
    def limit_text_length(widget, limit):
        """
        Ensures that a QTextEdit box has a character limit.
        :param widget: the text edit box
        :type widget: QTextEdit
        :param limit: the character limit
        :type limit: int
        """
        currText = widget.toPlainText()
        if len(currText) > limit:
            widget.setText(currText[0:limit])
            widget.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
