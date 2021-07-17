class Equipment:
    """A class representing a piece of equipment."""

    # a static dictionary that stores all the equipment item names within their appropriate tags.
    tagGroups = {
        "Ammunition": [], "Arcane focus": [], "Armor": [], "Artisan's tools": [], "Bludgeoning": [],  "Combat": [],
        "Communication": [], "Consumable": [], "Container": [], "Control": [], "Currency": [], "Damage": [],
        "Deception": [], "Detection": [], "Druidic focus": [], "Exploration": [], "Finesse": [], "Gaming set": [],
        "Healing": [], "Heavy": [], "Heavy armor": [], "Holy symbol": [], "Light": [], "Light armor": [], "Loading": [],
        "Martial": [], "Medium armor": [], "Melee": [], "Metal": [], "Movement": [], "Outerwear": [], "Instrument": [],
        "Piercing": [], "Ranged": [], "Reach": [], "Simple": [], "Special": [], "Slashing": [], "Social": [],
        "Stealth disadv": [], "Str limit": [], "Thrown": [], "Two-handed": [], "Utility": [], "Versatile": [],
        "Warding": []
    }
    # a static array holding each equipment object, to avoid the need for repeated objects
    allEquipment = []

    def __init__(self, name, tags, description,
                 dice="d", armor_class=0, weight=0, value="0cp", str_limit=0, item_range=None):
        """
        Stores all the data for a piece of equipment.
        :param name: The name of the equipment.
        :type name: str
        :param tags: Tags applied to help identify the equipment.
        :type tags: list
        :param description: The description explaining the items purpose.
        :type description: str
        :param dice: The dice linked to the item, typically for damage, with the format "(num)d(sides)".
        :type dice: str, optional
        :param item_range: The normal and long range of a weapon, for thrown or ranged attacks.
        :type item_range: list, optional
        :param armor_class: The armor class provided by wearing or wielding the item.
        :type armor_class: int, optional
        :param str_limit: The strength score limit to use the item.
        :type str_limit: int, optional
        :param weight: How much the item weighs, in lb.
        :type weight: int, optional
        :param value: How much the item is worth. Represented using numbers and coin representations cp, sp, gp, pp.
        :type value: str, optional
        """
        if item_range is None:
            item_range = [5, 5]
        self.range = item_range
        self.name = name
        self.tags = tags
        self.description = description
        if dice != "d":
            self.dice = dice
        else:
            self.dice = None
        self.armorClass = armor_class
        if str(armor_class)[0] == "+":
            self.armorClass = int(armor_class[1:])
        self.strLimit = str_limit
        self.weight = weight
        self.value = value

        Equipment.allEquipment.append(self)
        self.sort_to_tags()

    def sort_to_tags(self):
        """
        Adds a pointer to the object in the tagGroups dictionaries array for each of the objects tags.
        """
        for tag in self.tags:
            Equipment.tagGroups[tag] = Equipment.tagGroups[tag] + [self.name]

    def setup_armor_class(self, dex):
        """
        Calculates the armor class based on the passed string and the character's dexterity.
        :param dex: the dexterity score of the character in possession of this item
        :type dex: int
        """
        try:
            self.armorClass = int(self.armorClass)
        except ValueError:
            self.armorClass = str(self.armorClass)
            if "MAX" in self.armorClass:
                self.armorClass = int(self.armorClass[:2]) + min(dex, int(self.armorClass[-2]))
            else:
                self.armorClass = int(self.armorClass[:2]) + dex


    def __eq__(self, other):
        """
        Compares the equipment object with another equipment.
        Note that this function could be condensed into one line, but is separated for the sake of clarity and potential
        error locating.
        Many comparisons in this method are unnecessary by default, but including these allows for the consistent easy
        addition of new elements to the database, without the risk of collision.
        :param other: the other equipment object to compare against
        :type other: Equipment
        :return: a boolean stating whether they're equal
        """
        isEqual = False
        # compares the basic-type class variables
        if type(other) is Equipment:
            isEqual = self.name == other.name and self.description == other.description and self.dice == other.dice \
                        and self.value == other.value and self.armorClass == other.armorClass \
                        and self.strLimit == other.strLimit and self.weight == other.weight
            # compares the container class variables
            isEqual = isEqual and sorted(self.tags) == sorted(other.tags) and self.range == other.range
        elif type(other) is str:
            isEqual = self.name == other

        return isEqual

    def __lt__(self, other):
        """
        Tests whether the current equipment is less than the passed equipment alphabetically.
        :param other: the other equipment to compare against
        :type other: Equipment
        :return: a boolean stating whether it's less than or not
        """
        return self.name < other.name

    def __str__(self):
        output = f"{self.name} is worth {self.value}, and weighs {self.weight}lb.\n" \
                 f"It has the tags: {', '.join(self.tags)}.\n"
        if self.description != 0:
            output += f"{self.description}\n"
        if self.dice is not None:
            output += f"Using it involves rolling {self.dice}."
        if self.armorClass != 0:
            output += f"It provides {self.armorClass}AC."
        if self.strLimit > 0:
            output += f"Using it without penalty requires a strength of {self.strLimit} or higher."
        if self.range != [5, 5]:
            output += f"It has a range of {self.range[0]}, or {self.range[1]} with disadvantage."
        return output

    def __hash__(self):
        """
        Hashes the object based on it's name and description.
        :return: the hashed value produced
        """
        return hash(str(self.name) + str(self.description))


def get_all_equipment():
    """
    Returns the allEquipment class variable
    :return an array of equipment objects
    """
    return Equipment.allEquipment


def get_equipment(equipment_name):
    """
    Returns the object of an equipment from it's name.
    :param equipment_name: the name of the equipment to return
    :type equipment_name: str
    :return: the equipment object matching the name
    """
    for equipment in Equipment.allEquipment:
        if equipment.name == equipment_name:
            return equipment
    return


def get_tag_group(tag):
    """
    Returns a specified tag array from the tagGroups class variable
    :param tag: the tag to get the group for
    :type tag: str
    :return an array of strings
    """
    return Equipment.tagGroups.get(tag)


def get_all_tags():
    """
    Returns all tags that have their grouped equipments stored.
    :return: an array of tag strings
    """
    return Equipment.tagGroups.keys()

