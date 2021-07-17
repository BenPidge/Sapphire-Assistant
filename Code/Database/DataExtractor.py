from Code.CharacterElements import Equipment
import Code.Database.CoreDatabase as Db

# Represents the table(s) accessible from the input table using an intermediary table
# This excludes equipment due to the intermediary table holding extra information
INDIRECT_PATHS = {"Background": ["Proficiency", "Language"], "RaceOptions": ["Language", "Proficiency", "Spell"],
                  "ClassOptions": ["Proficiency", "Trait", "Language"], "Magic": ["Spell"], "Race": ["Trait"]}


def get_names_from_connector(start_table, end_table, input_id=-1, input_name=""):
    """
    Given two tables and an id or name, it gets all possible row names from the second table that are
    intermediately connected to the first row. This does not operate for EquipmentOption as the
    intermediary table has useful information.
    :param start_table: the name of the table the connection travels from
    :type start_table: str
    :param end_table: the name of the table the connection travels to
    :type end_table: str
    :param input_id: the id of the row to travel from in the start table. This or input_name must not be default
    :type input_id: int, optional
    :param input_name: the name of the row to travel from in the start table. This or input_id must not be default
    :type input_name: str, optional
    :return: an array of the names assigned within the rows pulled from the end table
    """
    # retrieves the id, if not provided
    if input_id == -1:
        input_id = Db.get_id(input_name, start_table)

    # determines the name of the intermediary table
    if start_table == "Magic":
        connTable = "ClassSpell"
    elif start_table == "Tag":
        connTable = "ArchTagConn"
    else:
        connTable = start_table.replace("Options", "") + end_table.replace("Generic", "")

    # determines the required variables for the sql call
    endId = Db.table_to_id(end_table)
    nameColumn = endId.replace("Id", "Name")
    startId = Db.table_to_id(start_table)

    # joins the tables to extract the names
    command = f"SELECT {nameColumn} FROM {connTable} INNER JOIN {start_table} ON {start_table}.{startId} = " \
              f"{connTable}.{startId} INNER JOIN {end_table} ON {end_table}.{endId} = {connTable}.{endId} " \
              f"WHERE {start_table}.{startId}={str(input_id)}"
    Db.cursor.execute(command)

    # converts the output into a cleaner, 1D array
    initOutput = Db.cursor.fetchall()
    output = []
    for item in initOutput:
        output.append(item[0])

    return output


def background_connections(background_name):
    """
    Returns the names of the options a background offers, as well as all the background information alongside.
    :param background_name: the name of the background to check
    :type background_name: str
    :return: 3 2D array - tools, skills and languages - holding the amount to pick and an array of the options
    """
    Db.cursor.execute(f"SELECT skillAmnt, toolAmnt, languageAmnt FROM Background "
                      f"WHERE backgroundName='{background_name}'")
    skillAmnt, toolAmnt, languageAmnt = Db.cursor.fetchone()
    proficiencies = get_names_from_connector("Background", "Proficiency", input_name=background_name)
    languages = get_names_from_connector("Background", "Language", input_name=background_name)

    for x in range(len(proficiencies)):
        proficiencies[x] = proficiencies[x].replace("'", "''")
    Db.cursor.execute("SELECT proficiencyName, proficiencyType FROM Proficiency WHERE proficiencyName IN ('"
                      + "', '".join(proficiencies) + "')")

    skills, tools = [], []
    for pair in Db.cursor.fetchall():
        if pair[1] == "Skill":
            skills.append(pair[0])
        else:
            tools.append(pair[0])

    return [toolAmnt, tools], [skillAmnt, skills], [languageAmnt, languages]


def race_options_connections(race_options_id, subrace_id=-1):
    """
    Returns the names of the options that RaceOptions offers, and RaceOptions data.
    :param race_options_id: the id of the race option to extract
    :type race_options_id: int
    :param subrace_id: the id of the subrace of the option to extract
    :type subrace_id: int, optional
    :return: [any spells], the amount to choose, [choices]
    """
    # retrieve all data related to the RaceOptions
    if subrace_id > -1:
        subclassCall = "=" + str(subrace_id)
    else:
        subclassCall = " IS NULL"
    Db.cursor.execute("SELECT amntToChoose FROM RaceOptions WHERE raceOptionsId="
                      + str(race_options_id) + " AND subraceId" + subclassCall)
    try:
        amntToChoose = Db.cursor.fetchone()[0]
    except TypeError:
        amntToChoose = -1

    # gets data from other methods
    languages = list(set(get_names_from_connector("RaceOptions", "Language", race_options_id)))
    proficiencies = list(set(get_names_from_connector("RaceOptions", "Proficiency", race_options_id)))

    # gets all spells info
    spells = []
    Db.cursor.execute("SELECT * FROM RaceSpell WHERE raceOptionsId=" + str(race_options_id))
    spellsInfo = Db.cursor.fetchall()
    for spellInfo in spellsInfo:
        Db.cursor.execute("SELECT spellName FROM Spell WHERE spellId=" + str(spellInfo[1]))
        name = Db.cursor.fetchone()[0]
        # sets missing spell info to its default value
        spellInfo = list(spellInfo)
        if spellInfo[2] is None:
            Db.cursor.execute("SELECT spellLevel FROM Spell WHERE spellName='" + name + "'")
            spellInfo[2] = Db.cursor.fetchone()[0]
        if spellInfo[3] is None:
            spellInfo[3] = 1
        info = [name] + list(spellInfo[2:])
        spells.append(info)

    # converts this data into an array
    output = []
    classOption = ["languages", "proficiencies", "spells"]
    metadata = [amntToChoose]
    counter = 0
    for data in [languages, proficiencies, spells]:
        if len(data) > 0:
            output += data
            metadata += [classOption[counter]]
        counter += 1

    if metadata[0] == -1 or metadata[0] is None:
        metadata[0] = len(output)
    # if the RaceOptions holds no information connections, it was saved during an insert that failed,
    # so thus deletes the row
    if len(output) == 0:
        Db.cursor.execute("DELETE FROM RaceOptions WHERE raceOptionsId=" + str(race_options_id))
    return metadata, output


def create_class_magic(class_name, class_lvl, subclass_name=""):
    """
    Retrieves the magic associated with a class at a given level.
    :param class_name: the name of the class to create the magic for
    :type class_name: str
    :param class_lvl: the level to get the classes magic at
    :type class_lvl: int
    :param subclass_name: the name of the subclass to receive magic for
    :type subclass_name: str, optional
    :return: the data required to choose all of the classes magic, in 2 arrays & a dictionary, with the format:
    [no of cantrips, no of spells, spells prepared boolean, amount of spells known calculation],
    [spell names], (spellslot level: num of spellslot) dictionary
    """
    if subclass_name != "":
        subclassCall = "=" + str(Db.get_id(subclass_name, 'Subclass'))
    else:
        subclassCall = " IS NULL"

    Db.cursor.execute(f"SELECT magicId, spellsPrepared, knownCalc, amntKnown, cantripsKnown FROM Magic WHERE "
                      f"classId={Db.get_id(class_name, 'Class')} AND lvl={class_lvl} AND subclassId{subclassCall}")
    magicId, spellsPrepared, knownCalc, amntKnown, cantripsKnown = Db.cursor.fetchone()
    if subclass_name != "":
        spellsPrepared = False

    Db.cursor.execute(f"SELECT spellslotLvl, amount FROM ClassSpellslot WHERE magicId={str(magicId)}")
    spellslots = dict()
    for pair in Db.cursor.fetchall():
        spellslots.update({pair[0]: pair[1]})

    spells = get_names_from_connector("Magic", "Spell", magicId)
    return [cantripsKnown, amntKnown, spellsPrepared, knownCalc], spells, spellslots


def class_options_connections(class_options_id, subclass_id=-1):
    """
    Returns the names of the options that the ClassOptions offers, and ClassOptions data.
    :param class_options_id: the id of the ClassOptions to pull data from
    :type class_options_id: int
    :param subclass_id: the id of the subclass to include checks for, if appropriate
    :type subclass_id: int, optional
    :return: the level required and amount to choose in an array, and an array of the choices
    """
    # retrieve all data related to the ClassOptions
    if subclass_id > -1:
        subclassCall = "=" + str(subclass_id)
    else:
        subclassCall = " IS NULL"

    Db.cursor.execute("SELECT lvlRequired, amntToChoose FROM ClassOptions WHERE classOptionsId="
                      + str(class_options_id) + " AND subclassId" + subclassCall)
    metadata = list(Db.cursor.fetchone())
    languages = get_names_from_connector("ClassOptions", "Language", class_options_id)
    proficiencies = get_names_from_connector("ClassOptions", "Proficiency", class_options_id)
    traits = get_names_from_connector("ClassOptions", "Trait", class_options_id)

    newTraits = []
    for trait in traits:
        Db.cursor.execute("SELECT traitDescription FROM Trait WHERE traitName='" + trait.replace("'", "''") + "'")
        desc = Db.cursor.fetchone()[0]
        newTraits.append((trait, desc))
    traits = newTraits

    # converts all the data into two arrays
    output = []
    classOption = ["languages", "proficiencies", "traits"]
    counter = 0
    for data in [languages, proficiencies, traits]:
        if len(data) > 0:
            output += data
            metadata += [classOption[counter]]
        counter += 1
    if metadata[0] is None:
        metadata[0] = 1
    if metadata[1] is None:
        metadata[1] = len(output)

    # if the ClassOptions holds no information connections, it was saved during an insert that failed,
    # so thus deletes the row
    if len(output) == 0:
        Db.cursor.execute("DELETE FROM ClassOptions WHERE classOptionsId=" + str(class_options_id))
    return metadata, output


def equipment_connections(class_id):
    """
    Pulls the data of all available equipment options in a class.
    :param class_id: the class to get the equipment for
    :type class_id: int
    :return:
    """
    Db.cursor.execute("SELECT equipOptionId, hasChoice FROM EquipmentOption WHERE classId=" + str(class_id)
                      + " AND suboption IS NULL")
    equipmentPoints = Db.cursor.fetchall()
    options = []
    for option in equipmentPoints:
        options.append(equipment_point(*option))
    return options


def equipment_point(option_id, has_choice):
    """
    Pulls the data of all available equipment options for a single option.
    :param option_id: the id of the option to use
    :param has_choice: whether the option involves selecting one or receiving all items in it
    :return:
    """
    Db.cursor.execute("SELECT equipmentId, amnt FROM EquipmentIndivOption WHERE equipmentOptionId=" + str(option_id))
    indivOption = Db.cursor.fetchall()
    items = []
    for (equipmentId, amnt) in indivOption:
        Db.cursor.execute("SELECT equipmentName FROM Equipment WHERE equipmentId=" + str(equipmentId))
        item = Db.cursor.fetchone()[0]
        equipment = Equipment.get_equipment(item)
        for x in range(0, amnt):
            items.append(equipment)
    metadata = [has_choice == 1]
    Db.cursor.execute("SELECT equipOptionId, hasChoice FROM EquipmentOption WHERE suboption=" + str(option_id))
    suboption = Db.cursor.fetchall()
    if len(suboption) > 0:
        for (newOptionId, hasChoice) in suboption:
            metadata.append(equipment_point(newOptionId, hasChoice))
    return [metadata, items]


def equipment_items():
    """
    Pulls the needed information of each equipment item.
    :return: an array with an index for each item
    """
    Db.cursor.execute("SELECT * FROM Equipment")
    allData = Db.cursor.fetchall()
    allEquipment = []
    for (eId, name, desc, diceSides, diceNum, armorClass, weight, value) in allData:
        tags = []
        Db.cursor.execute("SELECT genericTagId FROM EquipmentTag WHERE equipmentId=" + str(eId))
        for tag in Db.cursor.fetchall():
            Db.cursor.execute("SELECT genericTagName FROM GenericTag where genericTagId=" + str(tag[0]))
            tags.append(Db.cursor.fetchone()[0])

        equip = [name, tags, desc, str(diceNum) + "d" + str(diceSides), armorClass, weight, value]
        allEquipment.append(equip)
    return allEquipment


def spell_info(spell_name, chr_level=1):
    """
    Get all the appropriate info for a spell from the name.
    :param spell_name: the name of the spell to fetch
    :type spell_name: str
    :param chr_level: the level of the character, relevant for cantrips, and 1 by default
    :type chr_level: int, optional
    :return: all the required data for a spell object, in parameter order
    """
    Db.cursor.execute("SELECT * FROM Spell WHERE spellName='" + spell_name.replace("'", "''") + "'")
    lvl, castingTime, duration, sRange, area, components, atOrSave, school, damOrEffect, desc = Db.cursor.fetchone()[2:]
    damage, attack, save = None, None, None

    # gets the spells' tags
    tags = []
    Db.cursor.execute("SELECT genericTagId FROM SpellTag WHERE spellId=" + str(Db.get_id(spell_name, "Spell")))
    for tag in Db.cursor.fetchall():
        Db.cursor.execute("SELECT genericTagName FROM GenericTag where genericTagId=" + str(tag[0]))
        tags.append(Db.cursor.fetchone()[0])

    # separates atOrSave into it's appropriate variable
    if "Save" in atOrSave:
        save = atOrSave
    elif atOrSave is not None:
        attack = atOrSave

    return spell_name, lvl, castingTime, duration, sRange, components, school,\
        tags, desc, damage, attack, save, area, chr_level



def begin():
    """
    Begins the use of the data extraction.
    """

    Db.cursor.execute("SELECT * FROM Magic WHERE subclassId=" + str(Db.get_id("Nature Domain", "Subclass")))
    print(Db.cursor.fetchall())
    Db.cursor.execute("SELECT classOptionsId, amntToChoose FROM ClassOptions WHERE subclassId="
                      + str(Db.get_id("Nature Domain", "Subclass")))
    res = Db.cursor.fetchall()
    print(res)
    call = "SELECT proficiencyName FROM Proficiency WHERE proficiencyId IN " \
           "(SELECT proficiencyId FROM ClassProficiency WHERE classOptionsId IN ("
    for r in res:
        call += str(r[0]) + ", "
    call = call[:-2] + "))"
    Db.cursor.execute(call)
    print(Db.cursor.fetchall())

