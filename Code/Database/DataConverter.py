import itertools
import random

from Code.Database import ChoiceStruct, CoreDatabase as Db, DataExtractor
from Code.CharacterElements import Equipment, Race, Spell
from Code.CharacterElements.PC import Class, Character, Magic, Background

selected_results = None


def create_character(chr_lvl, chr_choices=None, ability_scores=None):
    """
    Creates a character object at the given level.
    :param chr_lvl: the level to build the character at
    :type chr_lvl: int
    :param chr_choices: the choices made to apply for this character
    :type chr_choices: optional, list
    :param ability_scores: the ability score ranges inputted
    :type ability_scores: optional, dict
    :return: a character object
    """
    global selected_results
    if chr_choices is not None:
        selected_results = ChoiceStruct.ChoiceStruct(chr_choices)

    Db.cursor.execute(f"SELECT backgroundName FROM Background")
    backgrounds = list(itertools.chain(*Db.cursor.fetchall()))
    background = create_background(make_choice(1, backgrounds, "Background")[0])

    Db.cursor.execute(f"SELECT raceName FROM Race")
    races = list(itertools.chain(*Db.cursor.fetchall()))
    race = make_choice(1, races, "Race")[0]
    Db.cursor.execute(f"SELECT subraceName FROM Subrace WHERE raceId={Db.get_id(race, 'Race')}")
    subraces = list(itertools.chain(*Db.cursor.fetchall()))
    if len(subraces) > 0:
        subraceId = Db.get_id(make_choice(1, subraces, "Subrace")[0], "Subrace")
        race = create_race(race, chr_lvl, subraceId)
    else:
        race = create_race(race, chr_lvl)

    Db.cursor.execute(f"SELECT className FROM Class")
    classes = list(itertools.chain(*Db.cursor.fetchall()))
    chrClass = make_choice(1, classes, "Class")[0]
    Db.cursor.execute(f"SELECT subclassName FROM Subclass WHERE classId={Db.get_id(chrClass, 'Class')}")
    subclasses = list(itertools.chain(*Db.cursor.fetchall()))
    if len(subclasses) > 0:
        subclass = create_subclass(make_choice(1, subclasses, "Subclass")[0], chr_lvl)
        chrClass = create_class(chrClass, chr_lvl, subclass)
    else:
        chrClass = create_class(chrClass, chr_lvl)

    raceAdditions = dict()
    if ability_scores is not None:
        for ability, mod in race.abilityScores.items():
            if ability == "ALL":
                if chrClass.mainAbility not in race.abilityScores.keys():
                    ability = chrClass.mainAbility.split("/")[0]
                else:
                    ability = chrClass.secondAbility.split("/")[0]

            ability_scores[ability][0] -= mod
            ability_scores[ability][1] -= mod
            raceAdditions.update({ability: mod})
    else:
        ability_scores = dict()
        for score in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
            ability_scores.update({score: [8, 15]})

    abilityScores = create_ability_scores((chrClass.mainAbility, chrClass.secondAbility), ability_scores)
    return Character.Character(race, chrClass, background, abilityScores)


def create_background(background_name):
    """
    Creates and returns a background object, given the name of the background to use.
    :param background_name: the name of the background selected
    :type background_name: str
    :return: a python object representing the background
    """
    tools, skills, languages = DataExtractor.background_connections(background_name)
    finalProfs, finalLanguages = [], []

    finalProfs += make_choice(tools[0], tools[1], background_name)
    finalProfs += make_choice(skills[0], skills[1], background_name)
    finalLanguages = make_choice(languages[0], languages[1], background_name)

    return Background.Background(background_name, finalProfs, finalLanguages)


def create_class(class_name, class_lvl, subclass=""):
    """
    Creates and returns a class object, given the name of the class to use.
    :param class_name: the name of the class selected
    :type class_name: str
    :param class_lvl: the level to build the class at
    :type class_lvl: int
    :param subclass: the subclass to add to this object
    :type subclass: object, optional
    :return: a python object representing the class
    """
    classId = Db.get_id(class_name, "Class")
    Db.cursor.execute("SELECT hitDiceSides, primaryAbility, secondaryAbility, isMagical, savingThrows FROM Class "
                      "WHERE classId=" + str(classId))
    hitDice, primaryAbility, secondaryAbility, isMagical, savingThrows = Db.cursor.fetchone()

    if subclass == "":
        subclass = None

    traits, proficiencies, languages = collect_class_option_data(class_name, class_lvl)
    equipment = create_equipment(class_name)

    if isMagical:
        magic = create_class_magic(class_name, class_lvl)
        return Class.Class(class_name, traits, proficiencies, equipment, primaryAbility, secondaryAbility,
                           savingThrows, hitDice, languages, class_lvl, magic, subclass)
    else:
        return Class.Class(class_name, traits, proficiencies, equipment, primaryAbility, secondaryAbility,
                           savingThrows, hitDice, languages, class_lvl, subclass=subclass)


def create_subclass(subclass_name, class_lvl):
    """
    Extracts the subclass options data from the database.
    :param subclass_name: the name of the subclass being extracted
    :type subclass_name: str
    :param class_lvl: the current level in this subclass
    :type class_lvl: int
    :return:
    """
    Db.cursor.execute("SELECT subclassId, classId, secondaryAbility FROM Subclass WHERE subclassName='"
                      + subclass_name + "'")
    subclassId, classId, secondAbility = Db.cursor.fetchone()
    Db.cursor.execute("SELECT className, secondaryAbility FROM Class WHERE classId=" + str(classId))
    className, classSecondAbility = Db.cursor.fetchone()

    traits, proficiencies, languages = collect_class_option_data(className, class_lvl, subclassId)
    magic = create_class_magic(className, class_lvl, subclass_name)
    if secondAbility is None:
        secondAbility = classSecondAbility

    return Class.Subclass(subclass_name, className, secondAbility, traits, magic, languages, proficiencies)


def create_race(race_name, chr_lvl, subrace_id=-1, is_subrace=False):
    """
    Creates and returns a race object, given the name and level of the race to use.
    :param race_name: the name of the race to create
    :type race_name: str
    :param chr_lvl: the level of the character being created
    :type chr_lvl: int
    :param subrace_id: the id of the subrace being built
    :type subrace_id: int, optional
    :param is_subrace: whether the current pass is creating the subrace
    :type is_subrace: bool, optional
    :return: a race object of the inputted race
    """
    # recursively builds a subrace from the data
    if subrace_id > -1 and is_subrace is False:
        subrace = create_race(race_name, chr_lvl, subrace_id, True)
        subrace_id = -1
    else:
        subrace = None

    # get basic variable data
    if subrace_id == -1:
        subraceStr = " IS NULL"
    else:
        subraceStr = "=" + str(subrace_id)

    raceId = Db.get_id(race_name, "Race")
    # get basic racial data
    Db.cursor.execute("SELECT size FROM Race WHERE raceId=" + str(raceId))
    size = Db.cursor.fetchone()[0]
    if subrace_id == -1:
        Db.cursor.execute("SELECT speed, darkvision, resistance FROM Race WHERE raceId=" + str(raceId))
    else:
        Db.cursor.execute("SELECT speed, darkvision, resistance FROM Subrace WHERE raceId="
                          + str(raceId) + " AND subraceId" + subraceStr)
    speed, darkvision, resistance = Db.cursor.fetchone()


    # gets the trait data
    traits = []
    traitNames = DataExtractor.get_names_from_connector("Race", "Trait", raceId)
    for trait in traitNames:
        Db.cursor.execute("SELECT subraceId FROM RaceTrait WHERE traitId=" + str(Db.get_id(trait, "Trait")))
        subId = Db.cursor.fetchone()[0]
        if (subId is None and subrace_id == -1) or (subId == subrace_id):
            Db.cursor.execute("SELECT traitDescription FROM Trait WHERE traitName='" + trait.replace("'", "''") + "'")
            traits.append((trait, Db.cursor.fetchone()[0]))
    traits = choose_trait_option(traits, race_name)

    # extracts data from options
    spells, modUsed, proficiencies, languages = collect_race_option_data(race_name, chr_lvl, subrace_id)

    # gets the ability score data
    Db.cursor.execute("SELECT abilityScore, scoreIncrease FROM RaceAbilityScore WHERE raceId="
                      + str(raceId) + " AND subraceId" + subraceStr)
    abilityScores = dict()
    for scoreName, scoreIncrease in Db.cursor.fetchall():
        abilityScores.update({scoreName: scoreIncrease})

    # converts data into the required formats
    darkvision = darkvision == 1
    if len(spells) == 0:
        spells = None
        modUsed = None

    if is_subrace:
        Db.cursor.execute("SELECT subraceName FROM Subrace WHERE subraceId=" + str(subrace_id))
        race_name = Db.cursor.fetchone()[0]

    return Race.Race(race_name, languages, proficiencies, abilityScores, traits, speed, size, darkvision,
                     spells, modUsed, resistance, subrace)


def create_equipment(class_name):
    """
    Creates and selects all equipment options for one class.
    :param class_name: the name of the class to get the equipment for
    :type class_name: str
    :return: a list of equipment objects
    """
    optionsData = DataExtractor.equipment_connections(Db.get_id(class_name, "Class"))
    equipment = []
    for option in optionsData:
        equipment += create_equipment_option(option, class_name)[1]
    return equipment


def create_ability_scores(priorities, filters):
    """
    Creates ability scores using point buy, and the inputted priorities.
    :param priorities: a (primary, secondary) pair of the two main priorities
    :type priorities: tuple
    :param filters: the filters stating the ranges that ability scores must be in
    :type filters: dict
    :param race_additions: the additional bonuses gained from race
    :type race_additions: dict
    :return: a dictionary holding the 6 ability scores, with the layout {ability: score}
    """
    availablePoints = 27
    abilityScores = dict({"STR": 8, "DEX": 8, "CON": 8, "INT": 8, "WIS": 8, "CHA": 8})
    abilityPriorities = list(priorities)
    if "/" in priorities[0]:
        abilityPriorities[0] = priorities[0].split("/")[random.randint(0, 1)]
    if "CON" not in priorities:
        abilityPriorities.append("CON")
    for key in abilityScores.keys():
        if key not in abilityPriorities:
            abilityPriorities.append(key)

    for ability, [min_val, _] in filters.items():
        if min_val > abilityScores[ability]:
            abilityScores.update({ability: min_val})
            availablePoints -= convert_score_to_points(min_val)

    # if ability score requirements are too high, reduce them
    while availablePoints < 0:
        for ability in abilityPriorities:
            score = abilityScores[ability]
            if score > 8:
                score -= 1
                availablePoints += (convert_score_to_points(score+1) - convert_score_to_points(score))
                abilityScores[ability] = score
    # if abilities exceed their maximum, reduce them
    for ability in abilityPriorities:
        if abilityScores[ability] > filters[ability][1]:
            availablePoints += (
                        convert_score_to_points(abilityScores[ability]) - convert_score_to_points(filters[ability][1]))
            abilityScores[ability] = filters[ability][1]
    # if there are still points available, use them
    for ability in abilityPriorities:
        score = abilityScores[ability]
        score, availablePoints = attempt_score_increase(score, availablePoints, filters[ability][1])
        abilityScores[ability] = score

    return abilityScores


def convert_score_to_points(score):
    """
    Converts an ability score value to the points it costs to purchase.
    :param score: the score to convert
    :type score: int
    :return: an integer value of the points it costs
    """
    if score > 15:
        return 28
    elif score > 13:
        return (score - 13) * 2 + 5
    else:
        return score - 8


def attempt_score_increase(score, available_points, max_val):
    """
    Attempts to increase the score as much as possible.
    :param score: the current score to increase
    :type score: int
    :param available_points: the amount of available points left
    :type available_points: int
    :param max_val: the maximum value the score can be
    :type max_val: int
    :return: the new score and available points
    """
    while available_points > 0 and score < max_val and score < 15:
        available_points += convert_score_to_points(score)
        score += 1
        available_points -= convert_score_to_points(score)
    return score, available_points


def make_choice(num_of_choices, choices, element):
    """
    Lets the user choose a certain amount of items from an array of options.
    Any use of this should be replaced with the optimising algorithm when possible.
    :param num_of_choices: how many of the choices must be selected
    :type num_of_choices: int
    :param choices: a list of the choices available
    :type choices: list
    :param element: the element to be building for - such as Class or the class name you're making a suboption for
    :type element: str
    :return: a list of the choices selected
    """
    output = []
    if num_of_choices >= len(choices):
        output = choices

    # automatic output
    elif selected_results is not None:
        for x in range(num_of_choices):
            choice = selected_results.get_element(choices, element)
            if choice == 0 or choice in output:
                random_choice = random.randint(0, len(choices)-1)
                output.append(choices[random_choice])
                choices.pop(random_choice)
            else:
                output.append(choice)

    # manual output
    else:
        output = manual_output(num_of_choices, choices)

    safe = True
    for x in range(0, len(output)):
        if type(output[x]) not in (str, Spell.Spell):
            safe = False

    if not(len(output) == 1 and type(output[0]) is not list) and safe is False and type(output[0]) is not tuple:
        output = list(itertools.chain(*output))
    return output


def manual_output(num_of_choices, choices):
    """
    Gets a manual output for a choice.
    :param num_of_choices: the amount of choices to make
    :type num_of_choices: int
    :param choices: the choices to select from
    :type choices: list
    :return: a list of the choices selected
    """
    output = []
    choiceCount = []
    choiceDict = dict()

    # converts any list choices into a single string, directing a dictionary to the list of objects
    for x in range(0, len(choices)):
        if type(choices[x]) is list:
            fullStr = ""
            for y in list({i: choices[x].count(i) for i in choices[x]}.items()):
                fullStr += f"({str(y[1])}x) {str(y[0])}\n"
            choiceDict.update({fullStr: choices[x]})
        else:
            choiceCount.append(choices[x])

    # puts all single-object choices into the dictionary,
    # linking their string to the appropriate amount of the object
    choiceCount = list({i: choiceCount.count(i) for i in choiceCount}.items())
    for z in range(0, len(choiceCount)):
        objects = []
        for s in range(0, choiceCount[z][1]):
            objects.append(choiceCount[z][0])
        choiceDict.update({f"({choiceCount[z][1]}x) {str(choiceCount[z][0])}": objects})

    # lists their options
    while len(output) < num_of_choices:
        print("Choose one from: ")
        counter = 0
        for key in list(choiceDict.keys()):
            counter += 1
            print(str(counter) + ".\n" + key)

        nextAddition = Db.int_input(">") - 1
        if nextAddition < len(choiceDict.keys()):
            output.append(list(choiceDict.values())[nextAddition])
            choiceDict.pop(list(choiceDict.keys())[nextAddition])

    return output


def collect_race_option_data(race_name, chr_lvl, subrace_id=-1):
    """
    Extracts the race options data from the race database.
    :param race_name: the name of the race selected
    :type race_name: str
    :param chr_lvl: the level of the character being built
    :type chr_lvl: int
    :param subrace_id: the id of the subrace, if appropriate
    :type subrace_id: int, optional
    :return: three arrays holding the traits, proficiencies and languages
    """
    if subrace_id == -1:
        subraceStr = " IS NULL"
    else:
        subraceStr = "=" + str(subrace_id)

    spells, proficiencies, languages = [], [], []
    modUsed = ""
    Db.cursor.execute("SELECT raceOptionsId FROM RaceOptions WHERE raceId=" + str(Db.get_id(race_name, "Race"))
                      + " AND subraceId" + subraceStr)
    ids = Db.cursor.fetchall()
    Db.cursor.execute("SELECT raceOptionsId FROM RaceOptions WHERE raceId=" + str(Db.get_id(race_name, "Race")))
    for nextId in ids:
        metadata, options = DataExtractor.race_options_connections(nextId[0], subrace_id)
        if len(options) > 0:
            if metadata[1] == "proficiencies":
                proficiencies += make_choice(metadata[0], options, race_name)
            elif metadata[1] == "spells":
                spellNames = []
                for spell in options:
                    spellNames.append(spell[0])
                spells = make_choice(metadata[0], spellNames, race_name)
                spells = build_race_spells(options, spells, chr_lvl)
                modUsed = options[0][3]
            else:
                languages += make_choice(metadata[0], options, race_name)
    return spells, modUsed, proficiencies, languages


def build_race_spells(spells_data, spell_names, chr_lvl):
    """
    Builds the spells selected for the race alongside their additional data.
    :param spells_data: a 2D array, with arrays holding all data for each available spell
    :type spells_data: list
    :param spell_names: an array of all the names of spells selected
    :type spell_names: list
    :param chr_lvl: the current level of the character
    :type chr_lvl: int
    :return: an array of (spell object, spell cast level)
    """
    spellObjects = []
    for x in range(0, len(spell_names)):
        if spells_data[x][2] <= chr_lvl:
            spellObjects.append((Spell.get_spell(spell_names[x], chr_lvl), spells_data[x][1]))
    return spellObjects


def create_class_magic(class_name, class_lvl, subclass_name=""):
    """
    Creates the magic related to a class at a specified level.
    :param class_name: the class to create magic for
    :type class_name: str
    :param class_lvl: the level the class is at when gaining the magic object
    :type class_lvl: int
    :param subclass_name: the subclass to create magic for, if appropriate
    :type subclass_name: str, optional
    :return: an object representing all the magic in a class
    """
    # retrieves and sets up variables
    [cantripsKnown, amntKnown, spellsPrepared, knownCalc], spells, spellslots \
        = DataExtractor.create_class_magic(class_name, class_lvl, subclass_name)
    spellsPrepared = spellsPrepared == 1
    spellObjects, cantripObjects, selectedSpells = [], [], []
    if amntKnown is None:
        amntKnown = -1

    # creates spells
    for spell in spells:
        nextSpell = Spell.get_spell(spell, class_lvl)
        if nextSpell.level == 0:
            cantripObjects.append(nextSpell)
        else:
            spellObjects.append(nextSpell)

    # chooses spells
    if subclass_name != "":
        class_name = subclass_name
    selectedSpells = make_choice(cantripsKnown, cantripObjects, class_name)
    if spellsPrepared is False:
        selectedSpells += make_choice(amntKnown, spellObjects, class_name)
        params = [spellslots, False, amntKnown, selectedSpells]
    else:
        params = [spellslots, True, amntKnown, selectedSpells, knownCalc, spellObjects]
    return Magic.Magic(*params)


def collect_class_option_data(class_name, class_lvl, subclass_id=-1):
    """
    Extracts the class options data from the class database.
    :param class_name: the name of the class selected
    :type class_name: str
    :param class_lvl: the level to build the class at
    :type class_lvl: int
    :param subclass_id: the id of the subclass, if appropriate
    :type subclass_id: int, optional
    :return: three arrays holding the traits, proficiencies and languages
    """
    if subclass_id == -1:
        subclassStr = " IS NULL"
    else:
        subclassStr = "=" + str(subclass_id)

    traits, proficiencies, languages = [], [], []
    Db.cursor.execute("SELECT classOptionsId FROM ClassOptions WHERE classId=" + str(
        Db.get_id(class_name, "Class")) + " AND subclassId" + subclassStr)
    ids = Db.cursor.fetchall()
    for nextId in ids:
        metadata, options = DataExtractor.class_options_connections(nextId[0], subclass_id)
        if metadata[0] <= class_lvl:
            if metadata[2] == "traits":
                traits += make_choice(metadata[1], options, class_name)
                traits = choose_trait_option(traits, class_name)
            elif metadata[2] == "proficiencies":
                proficiencies += make_choice(metadata[1], options, class_name)
            else:
                languages += make_choice(metadata[1], options, class_name)
    return traits, proficiencies, languages


def choose_trait_option(traits, parent):
    """
    Goes through traits in order to make any trait choices required.
    :param traits: the list of traits, each being the format (name, desc)
    :type traits: list
    :param parent: the class or race(or other) that this trait is being received from
    :type parent: str
    :return: the updated list of traits
    """
    choices = []

    for x in range(0, len(traits)):
        Db.cursor.execute(f"SELECT optionDesc FROM TraitOption WHERE traitId={Db.get_id(traits[x][0], 'Trait')}")
        options = Db.cursor.fetchall()
        if len(options) > 0:
            for option in options:
                choices.append(option)
            selectedOption = make_choice(1, choices, parent)
            choices.clear()
            traits[x] = (traits[x][0], str(traits[x][1]) + " " + str(selectedOption[0][0]))
    return traits


def create_all_equipment():
    """
    Creates an object for each equipment item in the database.
    """
    equipmentData = DataExtractor.equipment_items()
    for equip in equipmentData:
        for x in range(0, len(equip)):
            if equip[x] == "":
                equip[x] = 0
        if type(equip[-1]) is list:
            Equipment.Equipment(*equip[:-1], item_range=equip[-1])
        else:
            Equipment.Equipment(*equip)


def create_equipment_option(option, class_name):
    """
    Creates a single equipment option set.
    :param option: a list of metadata and objects in the option,
                   in the layout [[isChoice boolean, [optional subsection]], [equipment objects]]
    :type option: list
    :param class_name: the name of the class this is being built for
    :type class_name: str
    :return: whether the option was a choice, and a list of the equipment objects selected
    """
    metadata, items = option
    itemChoices = items
    if len(metadata) > 1:
        for subsection in metadata[1:]:
            choice, subsectionVal = create_equipment_option(subsection, class_name)
            if choice is False:
                # flatten the list in such a way that it avoids requiring iterator overrides
                subsectionTempVal = subsectionVal
                subsectionVal = []
                for val in subsectionTempVal:
                    if type(val) is list:
                        for subval in subsectionTempVal:
                            subsectionVal.append(subval)
                    else:
                        subsectionVal.append(val)

            items += subsectionVal

    if metadata[0] is True:
        equipment = make_choice(1, itemChoices, class_name)
    else:
        equipment = items
    return metadata[0], equipment



def begin():
    """
    Begins the use of the data conversion.
    """
    return

