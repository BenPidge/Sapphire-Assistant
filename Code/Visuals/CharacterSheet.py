import itertools
import math
from functools import partial

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QScrollArea, QGraphicsView, QLabel, QTabWidget, QVBoxLayout, QHBoxLayout, \
    QGridLayout, QCheckBox, QPushButton, QSpacerItem

from Code.CharacterElements.PC import Character


class CharacterSheet:
    """Visualises a character sheet for a single character."""

    controller = None
    character = None
    archetypes = []

    def __init__(self, controller, chromosome):
        """
        Sets up and visualises the character sheet visuals.
        :param controller: the controller for the applications visuals
        :type controller: VisualsController
        :param chromosome: the chromosome holding the character to visualise
        :type chromosome: class: `Optimisation.Chromosome`
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/CharacterSheet.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")

        self.controller = controller
        self.character = chromosome.character
        self.archetypes = chromosome.archs

        shadowItems = {"skillsView": QGraphicsView, "armorVisLabel": QLabel, "speedVisLabel": QLabel,
                       "healthVisLabel": QLabel, "tabWidget": QTabWidget}
        self.centre = self.controller.setup_shadows(self.centre, shadowItems)
        btn = self.centre.findChild(QPushButton, "backBtn")
        btn.clicked.connect(partial(self.window.hide))

        self.load_core_data()
        self.load_ability_scores()
        self.load_skills()
        self.setup_pages()

        self.window.show()

    def load_core_data(self):
        """
        Loads the core data into the visual slots assigned for them.
        This refers to the race, class, background, archetype, armor, speed, health, proficiencies, languages.
        """
        # race, class, background & archetypes
        archetype = self.archetypes[0]
        if self.archetypes[1] is not None:
            archetype += "\n" + self.archetypes[1]
        for datatype, data in [["race", self.character.race.name], ["class", self.character.chrClass.name],
                               ["background", self.character.background.name], ["archetype", archetype]]:
            self.centre.findChild(QLabel, datatype + "Name").setText(data)

        # AC, speed & health
        for datatype, data in [["armorClass", str(self.character.armorClass)],
                               ["speed", str(self.character.race.speed)],
                               ["health", str(math.trunc(self.character.health))]]:
            if len(str(data)) == 1:
                data = " " + data
            self.centre.findChild(QLabel, datatype + "Val").setText(data)

        # languages & proficiencies
        langVbox = QVBoxLayout()
        profVbox = QVBoxLayout()
        self.centre.findChild(QScrollArea, "languageScroller") \
            .findChild(QWidget, "scrollAreaWidgetContents").setLayout(langVbox)
        self.centre.findChild(QScrollArea, "proficiencyScroller") \
            .findChild(QWidget, "scrollAreaWidgetContents_3").setLayout(profVbox)

        proficiencies = list(itertools.chain(*self.character.proficiencies.values()))
        proficiencies = set([prof for prof in proficiencies if prof not in
                             list(itertools.chain(*Character.character_skills))])
        for vbox, data in [[langVbox, set(self.character.languages)],
                           [profVbox, proficiencies]]:
            for dataPiece in data:
                nextLabel = QLabel(dataPiece)
                nextLabel.setStyleSheet('font: 14pt "Times New Roman"; color: rgb(188, 189, 177);')
                vbox.addWidget(nextLabel, alignment=Qt.AlignCenter)

    def load_ability_scores(self):
        """
        Loads the ability scores into their visualised slots.
        """
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            holder = self.centre.findChild(QWidget, ability + "Ability")
            abilityBrief = ability[0:3]
            holder.findChild(QLabel, abilityBrief + "BaseValue")\
                .setText(str(self.character.abilityScores[abilityBrief.upper()]))
            modifier = self.character.abilityScores[abilityBrief.upper()]//2 - 5
            if modifier > -1:
                modifier = "+" + str(modifier)
            holder.findChild(QLabel, abilityBrief + "Modifier") \
                .setText(str(modifier))

    def load_skills(self):
        """
        Loads the skill values into their visualised slots.
        """
        parentHolder = self.centre.findChild(QGridLayout, "skills")
        counter = 0
        for skillGroup in Character.character_skills:
            for skill in skillGroup:
                proficient = False
                if skill in list(itertools.chain(*self.character.proficiencies.values())):
                    proficient = True

                skillLabel = QLabel(skill)
                skill = skill.replace(" ", "")
                modifier = self.character.abilityScores[Character.character_abilities[counter]]
                modifier = modifier//2 - 5
                if proficient:
                    modifier += self.character.proficiencyBonus
                if modifier > -1:
                    modifier = "+" + str(modifier)

                holder = parentHolder.findChild(QHBoxLayout, skill)
                skillLabel.setStyleSheet("color: rgb(255, 255, 255);")
                if proficient:
                    label = QLabel()
                    pixmap = QPixmap("./Visuals/Images/profRadioBox.png")
                    label.setPixmap(pixmap.scaled(50, 100, Qt.KeepAspectRatio))
                    holder.addWidget(label)
                else:
                    holder.addItem(QSpacerItem(55, 100))

                holder.addWidget(skillLabel)
                holder.addStretch()
                holder.addWidget(QLabel(str(modifier)))
            counter += 1

    def setup_pages(self):
        """
        Sets up the contents of the three Equipment/Traits/Spells tabs.
        """
        tab = self.centre.findChild(QTabWidget, "tabWidget")

        # builds the traits tab grid with headings
        scroller = tab.findChild(QWidget, "traitTab").findChild(QScrollArea, "traitArea") \
            .findChild(QWidget, "traitAreaWidget")
        scroller.setLayout(QGridLayout())
        traitHolder = scroller.children()[0]
        traitHolder.addWidget(QLabel("Name:"), 0, 0)
        traitHolder.addWidget(QLabel("Description:"), 0, 1)

        # adds every trait to the grid
        counter = 1
        for (trait, desc) in self.character.traits:
            traitHolder.addWidget(QLabel(trait), counter, 0)

            text = '\n'.join(desc[index:index + 49] for index in range(0, len(desc), 49))
            descScroller = QScrollArea()
            descScroller.setBaseSize(50, 10)
            descScroller.setWidget(QLabel(text))
            traitHolder.addWidget(descScroller, counter, 1)
            counter += 1

        self.setup_equip_page(tab)
        self.setup_spell_page(tab)

    def setup_equip_page(self, tab):
        """
        Sets up the page tab for the equipment items.
        :param tab: the tab that holds all the pages in Qt.
        :type tab: class: `QTabWidget`
        """
        scroller = tab.findChild(QWidget, "equipmentTab").findChild(QScrollArea, "equipmentArea") \
            .findChild(QWidget, "equipmentAreaWidget")
        scroller.setLayout(QGridLayout())
        equipHolder = scroller.children()[0]

        # sets up column headings
        counter = 0
        for heading in ["Name", "Description", "Damage dice", "Armor Class", "Range", "Weight", "Value"]:
            label = QLabel(heading + ":")
            label.setFont(QFont("MS Shell DIg2", weight=QFont.Bold))
            equipHolder.addWidget(label, 0, counter)
            counter += 1

        # for each equipment piece, it goes through and adds their elements
        # if there isn't one, it adds a label stating '-'
        counter = 1
        for equip in self.character.chrClass.equipment:
            equipHolder.addWidget(QLabel(equip.name), counter, 0)

            if equip.description != 0:
                text = equip.description
                text = '\n'.join(text[index:index+99] for index in range(0, len(text), 99))
                nextWidget = QScrollArea()
                nextWidget.setFixedSize(200, 50)
                nextWidget.setWidget(QLabel(text))
            else:
                nextWidget = QLabel("-")
            equipHolder.addWidget(nextWidget, counter, 1)

            if equip.dice is not None:
                # gets the equipments damage type. Ensures there's an item 0 even if none is found
                damageType = [x for x in ["bludgeoning", "piercing", "slashing"]
                              if x in [s.lower() for s in equip.tags]] + [""]
                nextWidget = QLabel(equip.dice + " " + damageType[0] + " damage")
            else:
                nextWidget = QLabel("-")
            equipHolder.addWidget(nextWidget, counter, 2)

            if equip.armorClass > 0:
                nextWidget = QLabel(str(equip.armorClass) + " AC")
            else:
                nextWidget = QLabel("-")
            equipHolder.addWidget(nextWidget, counter, 3)

            if equip.range != [5, 5]:
                nextWidget = QLabel(str(equip.range[0]) + "/" + str(equip.range[1]))
            else:
                nextWidget = QLabel("-")
            equipHolder.addWidget(nextWidget, counter, 4)

            equipHolder.addWidget(QLabel(str(equip.weight) + "lb"), counter, 5)
            equipHolder.addWidget(QLabel(equip.value), counter, 6)
            counter += 1

    def setup_spell_page(self, tab):
        """
        Sets up the page tab for the equipment items.
        :param tab: the tab that holds all the pages in Qt.
        :type tab: class: `QTabWidget`
        """
        spellTab = tab.findChild(QWidget, "spellTab")

        # creates the spellslot grid
        scroller = spellTab.findChild(QScrollArea, "spellslotArea").findChild(QWidget, "spellslotAreaWidget")
        scroller.setLayout(QGridLayout())
        spellslotHolder = scroller.children()[0]
        spellslotHolder.addWidget(QLabel("Casting level:"), 0, 0)
        spellslotHolder.addWidget(QLabel("Spellslots:"), 0, 1)

        # adds spellslot data to the grid
        counter = 1
        for (lvl, amnt) in self.character.magic.spellSlot.items():
            spellslotHolder.addWidget(QLabel("Level " + str(lvl) + ":"), counter, 0)
            checkBoxes = QHBoxLayout()
            for i in range(amnt):
                checkBoxes.addWidget(QCheckBox(""))
            spellslotHolder.addLayout(checkBoxes, counter, 1)
            counter += 1


        prepSpellAbility = None
        if self.character.magic.preparedSpellCalculation is not None:
            prepSpellAbility = self.character.magic.preparedSpellCalculation[0:3]
        spellcasting = self.character.magic.spellcasting
        spellcasting[next(iter(spellcasting))] = [x for x in spellcasting[next(iter(spellcasting))]
                                                if x not in self.character.magic.preparedSpellOptions]
        for datatype, data in [["knownSpell", spellcasting],
                               ["preparedSpell", dict({prepSpellAbility:
                                                           self.character.magic.preparedSpellOptions})]]:
            scrollerBase = spellTab.findChild(QScrollArea, datatype + "Area")
            scroller = QWidget()
            scrollerBase.setWidget(scroller)
            scrollerBase.setWidgetResizable(True)
            dataHolder = QGridLayout()
            scroller.setLayout(dataHolder)

            # sets up column headings
            counter = 0
            for heading in ["Lvl", "Name", "Description", "Attack/Save", "Damage", "Range", "Casting Time", "Duration",
                            "Components", "School", "Spell Tags"]:
                label = QLabel(heading + ":")
                label.setFont(QFont("MS Shell DIg2", weight=QFont.Bold))
                dataHolder.addWidget(label, 0, counter)
                counter += 1

            spellCounter = 1
            # for each ability score with related spells
            for (ability, spells) in data.items():
                spells.sort(key=lambda x: str(x.level) + x.name)
                # for each spell in this subgroup
                for spell in spells:
                    # calculate the attack bonus or save DC of a spell
                    spellModifier = self.character.abilityScores[ability] // 2 - 5 + self.character.proficiencyBonus
                    if spell.save not in [None, "None"]:
                        spellModifier += 8
                        attackSave = "DC" + str(spellModifier) + " " + spell.save
                    elif spell.attack not in [None, "None"]:
                        attackSave = "+" + str(spellModifier) + " " + spell.attack
                    else:
                        attackSave = None

                    # for each required piece of info, add a tag for it, or a '-' tag if it's empty
                    # if the info is long, give it a scroller to contain it
                    spellInfoCounter = 0
                    for info in [str(spell.level), spell.name, spell.description, attackSave, spell.damage,
                                 str(spell.range), spell.castingTime, spell.duration, spell.components, spell.school,
                                 ", ".join(spell.tags)]:
                        if info is None or len(info.replace(" ", "")) == 0:
                            info = "-"

                        if len(info) > 50:
                            text = '\n'.join(info[index:index + 99] for index in range(0, len(info), 99))
                            nextWidget = QScrollArea()
                            nextWidget.setFixedSize(200, 50)
                            nextWidget.setWidget(QLabel(text))
                        else:
                            nextWidget = QLabel(info)
                        dataHolder.addWidget(nextWidget, spellCounter, spellInfoCounter)
                        spellInfoCounter += 1
                    spellCounter += 1

