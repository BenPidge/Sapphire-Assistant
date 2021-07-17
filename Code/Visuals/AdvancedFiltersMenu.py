import itertools
from functools import partial

from PyQt5 import uic
from PyQt5.QtWidgets import *

from Code.Database import CoreDatabase as Db


class AdvancedFiltersMenu:
    """Sets up and runs the menu that allows the application of advanced character features."""

    controller = None
    selectedSpells = set()
    selectedEquipment = set()

    def __init__(self):
        """
        Sets up the advanced filters menu visuals.
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/AdvancedFiltersMenu.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")

    def begin(self, controller):
        """
        Begins the advanced filters menu and visualises it.
        :param controller: the controller for the applications visuals
        :type controller: VisualsController
        """
        self.controller = controller
        # if it's first being opened
        if self.centre.findChild(QScrollArea, "chosenEquipmentOptions")\
                .findChild(QWidget, "chosenEquipmentContents").layout() is None:
            self.centre.findChild(QScrollArea, "chosenEquipmentOptions")\
                .findChild(QWidget, "chosenEquipmentContents").setLayout(QVBoxLayout())
            self.centre.findChild(QScrollArea, "chosenSpellOptions") \
                .findChild(QWidget, "chosenSpellContents").setLayout(QVBoxLayout())
            self.centre.findChild(QScrollArea, "languagesScroller")\
                .findChild(QWidget, "scrollAreaWidgetContents").setLayout(QVBoxLayout())

        shadowItems = {"coreStatsView": QGraphicsView, "spellsView": QGraphicsView, "equipmentView": QGraphicsView,
                       "proficienciesView": QGraphicsView, "saveAdvancedOptions": QPushButton}
        self.centre = self.controller.setup_shadows(self.centre, shadowItems)
        self.setup_core_stats()
        self.setup_spell_and_equipment()
        self.setup_language_options(1)
        self.setup_tools()

        btn = self.centre.findChild(QPushButton, "saveAdvancedOptions")
        btn.clicked.connect(partial(self.save_btn_clicked))
        languageAmnt = self.centre.findChild(QSpinBox, "langAmntSpinner")
        languageAmnt.valueChanged.connect(self.setup_language_options)

        self.window.show()

    def get_filters(self):
        """
        Combines all filters into a dictionary and returns them.
        :return: a dictionary of filters
        """
        filters = {"Spells": [], "Equipment": [], "Proficiencies": [], "Languages": []}

        # Core Stats
        stats = ["Class", "Subclass", "Race", "Subrace", "Background"]
        for stat in stats:
            text = self.centre.findChild(QComboBox, "select" + stat).currentText()
            if text != "Select " + stat:
                filters.update({stat: text})

        # Proficiencies
        for child in self.centre.findChildren(QCheckBox):
            if child.isChecked():
                filters["Proficiencies"].append(child.text())
        matchEquip = self.centre.findChild(QRadioButton, "weaponsMatchEquipmentBtn").isChecked()

        # Languages
        for dropdown in self.centre.findChild(QScrollArea, "languagesScroller")\
                .findChild(QWidget, "scrollAreaWidgetContents").children()[1:]:
            text = dropdown.currentText()
            if text != "Necessary Language":
                filters["Languages"].append(text)


        # Spells & Equipment
        elements = [["Spell", "Spells"], ["Equipment", "Equipment"]]
        for [singular, plural] in elements:
            vbox = self.centre.findChild(QScrollArea, "chosen" + singular + "Options")\
                .findChild(QWidget, "chosen" + singular + "Contents").children()[0]
            for x in range(vbox.count()):
                text = vbox.itemAt(x).widget().text()[2:]
                filters[plural].append(text)

                # if they've asked for proficiency in all equipment, and the current item is a weapon, add it
                if plural == "Equipment" and matchEquip:
                    Db.cursor.execute("SELECT COUNT(*) FROM Proficiency WHERE proficiencyName='"
                                      + text.replace("'", "''").title() + "' AND proficiencyType='Weapon'")
                    if Db.cursor.fetchone()[0] > 0:
                        filters["Proficiencies"].append(text)

        return filters



    def setup_core_stats(self):
        """
        Sets up the core stats subsections' dropdown boxes.
        """
        for element in ["Class", "Race", "Background"]:
            dropdownBox = self.centre.findChild(QComboBox, "select" + element)
            if element != "Background":
                dropdownBox.currentTextChanged.connect(self.setup_core_subgroup_stats)
            Db.cursor.execute(f"SELECT {element.lower()}Name FROM {element}")
            names = list(itertools.chain(*Db.cursor.fetchall()))
            dropdownBox.addItems(names)

    def setup_core_subgroup_stats(self, value):
        """
        Sets up the subgroup dropdown boxes options when it's parent box has it's value changed.
        This subgroup gets all options applicable to the parent group, such as the subclasses available to a cleric if
        the parent is the class dropdown and selects Cleric.
        :param value: the value selected within the parent subclass
        :type value: str
        """
        if value not in ["", "Select Class", "Select Race"]:
            Db.cursor.execute("SELECT raceName FROM Race")
            races = list(itertools.chain(*Db.cursor.fetchall()))
            table = ["class", "race"].pop(int(value in races))
            dropdownBox = self.centre.findChild(QComboBox, "selectSub" + table)

            Db.cursor.execute(f"SELECT sub{table}Name FROM Sub{table} WHERE {table}Id="
                              f"{str(Db.get_id(value, table.capitalize()))}")
            suboptions = ["Select Sub"+table] + list(itertools.chain(*Db.cursor.fetchall()))

            dropdownBox.clear()
            dropdownBox.addItems(suboptions)

    def setup_spell_and_equipment(self):
        """
        Sets up the area which allows for spells to be searched for, selected and deselected.
        """
        spellBtn = self.centre.findChild(QPushButton, "spellSearchBtn")
        equipmentBtn = self.centre.findChild(QPushButton, "equipmentSearchBtn")

        spellBtn.clicked.connect(partial(self.populate_scroll_area, scroll_type="spell"))
        equipmentBtn.clicked.connect(partial(self.populate_scroll_area, scroll_type="equipment"))

    def setup_language_options(self, amnt):
        """
        Sets up dropdown boxes equal to the amount of languages specified.
        :param amnt: the amount of languages
        :type amnt: int
        """
        holder = self.centre.findChild(QScrollArea, "languagesScroller")\
            .findChild(QWidget, "scrollAreaWidgetContents").children()[0]
        Db.cursor.execute("SELECT languageName FROM Language")
        languages = list(itertools.chain(*Db.cursor.fetchall()))
        languages.sort()

        for i in reversed(range(holder.count())):
            text = holder.itemAt(i).widget().currentText()
            if text in languages:
                languages.remove(text)
            if i >= amnt:
                holder.itemAt(i).widget().setParent(None)
        for x in range(amnt - holder.count()):
            nextBox = QComboBox()
            nextBox.addItems(["Necessary Language"] + languages)
            nextBox.textActivated.connect(partial(self.setup_language_selection_options, holder))
            holder.addWidget(nextBox)

    def setup_tools(self):
        """
        Sets up the screens that procedurally show the available tools as check boxes.
        """
        stack = self.centre.findChild(QStackedWidget, "toolsStack")
        artisans, instruments, misc = uic.loadUi("Visuals/QtFiles/ToolSubmenu.ui"), \
                                      uic.loadUi("Visuals/QtFiles/ToolSubmenu.ui"), \
                                      uic.loadUi("Visuals/QtFiles/ToolSubmenu.ui")
        calls = ["Artisan's tools", "Instrument"]

        index = 0
        Db.cursor.execute("SELECT proficiencyType FROM Proficiency")
        for page in [artisans, instruments, misc]:
            scroller = page.findChild(QScrollArea, "scrollArea")\
                .findChild(QWidget, "scrollAreaWidgetContents")
            scroller.setLayout(QVBoxLayout())
            holder = scroller.children()[0]
            comboBox = page.findChild(QComboBox, "comboBox")
            comboBox.setCurrentIndex(index)
            comboBox.currentIndexChanged.connect(self.swap_tools_page)

            if index != 2:
                Db.cursor.execute(f"SELECT equipmentName FROM Equipment WHERE equipmentId IN ("
                                  f"SELECT equipmentId FROM EquipmentTag WHERE genericTagId="
                                  f"{Db.get_id(calls[index], 'GenericTag')})")
            else:
                Db.cursor.execute(f"SELECT proficiencyName FROM Proficiency WHERE proficiencyType IN ('Tool', "
                                  f"'Vehicle', 'Gaming Set') AND proficiencyName NOT IN ("
                                  f"SELECT equipmentName FROM Equipment WHERE equipmentId IN ("
                                  f"SELECT equipmentId FROM EquipmentTag WHERE genericTagId="
                                  f"{Db.get_id('Instrument', 'GenericTag')}))")

            for option in list(itertools.chain(*Db.cursor.fetchall())):
                holder.addWidget(QCheckBox(option))
            holder.addWidget(QLabel("End of Results"))
            index += 1

        stack.addWidget(artisans)
        stack.addWidget(instruments)
        stack.addWidget(misc)
        stack.setCurrentIndex(2)



    def populate_scroll_area(self, scroll_type):
        """
        Populates a scroll area with the appropriate contents based on the value entered into it's search bar.
        :param scroll_type: the group the scroll area is part of - spell or equipment
        :type scroll_type: str
        """
        elements = set()
        options = self.centre.findChild(QScrollArea, scroll_type + "Options")
        searchBar = self.centre.findChild(QTextEdit, scroll_type + "SearchBar")

        # get the resulting items
        Db.cursor.execute(f"SELECT {scroll_type}Name FROM {scroll_type.capitalize()} WHERE "
                          f"{scroll_type}Name LIKE '%{searchBar.toPlainText()}%'")
        elements.update(itertools.chain(*Db.cursor.fetchall()))
        Db.cursor.execute(f"SELECT {scroll_type}Name FROM {scroll_type.capitalize()} WHERE {scroll_type}Id IN "
                          f"(SELECT {scroll_type}Id FROM {scroll_type.capitalize()}Tag WHERE genericTagId IN "
                          f"(SELECT genericTagId FROM GenericTag WHERE genericTagName="
                          f"'{searchBar.toPlainText().capitalize()}'))")
        elements.update(itertools.chain(*Db.cursor.fetchall()))

        # if its a a spell, get more results based on further info
        Db.cursor.execute("SELECT spellName, castingTime, duration, school, damageOrEffect FROM Spell")
        for (name, cast, dur, school, effect) in Db.cursor.fetchall():
            if effect[0].isdigit():
                effect = effect.split(" ")[1]
            if searchBar.toPlainText().lower() in [cast.lower(), dur.lower(), school.lower(), effect.lower()]:
                elements.add(name)

        if scroll_type == "spell":
            selectedItems = self.selectedSpells
        else:
            selectedItems = self.selectedEquipment

        vbox = QVBoxLayout()
        elements = list(elements.difference(selectedItems))
        elements.sort()
        for element in elements:
            btn = QPushButton("+ " + element)
            btn.setStyleSheet("background-color: rgb(23, 134, 3); color: rgb(255, 255, 255); "
                              "font: 87 8pt 'Arial Black'; Text-align:left;")
            btn.clicked.connect(partial(self.selected_item, scroll_type=scroll_type, name=element))
            vbox.addWidget(btn)
        widget = QWidget()
        widget.setLayout(vbox)
        options.setWidget(widget)

    def selected_item(self, scroll_type, name):
        """
        Marks an item as selected, and moves it to the selected scrollbar.
        :param scroll_type: the group the scroll area is part of - spell or equipment
        :type scroll_type: str
        :param name: the name of the selected item
        :type name: str
        """
        options = self.centre.findChild(QScrollArea, "chosen" + scroll_type.capitalize() + "Options")
        vbox = options.findChild(QWidget, "chosen" + scroll_type.capitalize() + "Contents").children()[0]

        if scroll_type == "spell":
            selectedItems = self.selectedSpells
        else:
            selectedItems = self.selectedEquipment

        if name != "":
            selectedItems.add(name)
            self.populate_scroll_area(scroll_type)
            btn = QPushButton("- " + name)
            btn.setStyleSheet("background-color: rgb(23, 134, 3); color: rgb(255, 255, 255); "
                              "font: 87 8pt 'Arial Black'; Text-align:left;")
            vbox.addWidget(btn)
            btn.clicked.connect(lambda: self.deselected_item(scroll_type=scroll_type, name=btn.text()[2:]))

        options.verticalScrollBar().setValue(0)
        if scroll_type == "spell":
            self.selectedSpells = selectedItems
        else:
            self.selectedEquipment = selectedItems

    def deselected_item(self, scroll_type, name):
        """
        Unmarks the selection of an item, returning it to the options scrollbar.
        :param scroll_type: the group the scroll area is part of - spell or equipment
        :type scroll_type: str
        :param name: the name of the deselected item
        :type name: str
        """
        if scroll_type == "spell":
            selectedItems = self.selectedSpells
        else:
            selectedItems = self.selectedEquipment

        options = self.centre.findChild(QScrollArea, "chosen" + scroll_type.capitalize() + "Options")
        selectedItems.remove(name)

        vbox = options.findChild(QWidget, "chosen" + scroll_type.capitalize() + "Contents").layout()
        for i in reversed(range(vbox.count())):
            vbox.itemAt(i).widget().setParent(None)
        for element in selectedItems.difference(set(name)):
            btn = QPushButton("+ " +element)
            btn.setStyleSheet("background-color: rgb(23, 134, 3); color: rgb(255, 255, 255); "
                              "font: 87 8pt 'Arial Black'; Text-align:left;")
            btn.clicked.connect(lambda: self.deselected_item(scroll_type=scroll_type, name=btn.text()[2:]))
            vbox.addWidget(btn)

        self.populate_scroll_area(scroll_type)
        if scroll_type == "spell":
            self.selectedSpells = selectedItems
        else:
            self.selectedEquipment = selectedItems
        options.verticalScrollBar().setValue(0)

    def save_btn_clicked(self):
        """
        Reacts to the save advanced options button being placed, by calling the controller.
        """
        self.controller.stop_advanced_filters_menu()

    def swap_tools_page(self, index):
        """
        Swaps the tools page to the inputted page.
        :param index: the index of the page combobox selected. This index is 2 below the related page's
        :type index: int
        """
        stack = self.centre.findChild(QStackedWidget, "toolsStack")
        stack.setCurrentIndex(index+2)



    @staticmethod
    def setup_language_selection_options(holder):
        """
        Sets up the options available within all combo boxes for languages, based on what's already selected.
        :param holder: the holder that contains all combo boxes
        :type holder: QScrollArea
        """
        Db.cursor.execute("SELECT languageName FROM Language")
        languages = list(itertools.chain(*Db.cursor.fetchall()))
        for i in reversed(range(holder.count())):
            text = holder.itemAt(i).widget().currentText()
            if text in languages:
                languages.remove(text)

        languages.sort()
        for i in range(holder.count()):
            # gets the current selection, and adds necessary language to languages
            # if the current selection is a language
            comboBox = holder.itemAt(i).widget()
            text = comboBox.currentText()
            if text != "Necessary Language":
                languages = ["Necessary Language"] + languages

            # recreates the combobox contents with the same item selected
            comboBox.clear()
            comboBox.addItem(text)
            comboBox.addItems(languages)
