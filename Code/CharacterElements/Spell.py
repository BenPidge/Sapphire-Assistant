from Code.Database import DataExtractor


class Spell:
    """A class used to represent a singular spell."""

    # all spells currently built in the system
    builtSpells = []

    def __init__(self, name, level, casting_time, duration, spell_range, components, school, tags, description,
                 damage=None, attack=None, save=None, area=None, chr_level=1):
        """
        Initialises the spell with all required information.
        :param name: The spells name.
        :type name: str
        :param level: The spells level, with 0 for cantrips.
        :type level: int
        :param casting_time: The spells casting time, including any ritual information.
        :type casting_time: str
        :param duration: The spells duration and if it requires concentration.
        :type duration: str
        :param spell_range: The range of the spell, in feet.
        :type spell_range: int
        :param components: The component tags the spell requires, and any non-foci materials.
        :type components: str
        :param school: The school of magic the spell is within.
        :type school: str
        :param tags: The tags applied to the spell, which help identify it's purpose.
        :type tags: list
        :param description: The description of the spell in its entirety.
        :type description: str
        :param damage: The damage it deals, typically represented as (num of dice)d(sides of dice), and the damage type.
        :type damage: str, optional
        :param attack: The attack type of the spell, such as melee or ranged.
        :type attack: str, optional
        :param save: The saving throw required against the spell.
        :type save: str, optional
        :param area: The area the spell covers in feet, and the shape of this area.
        :type area: str, optional
        :param chr_level: The level of the character, used for cantrip damages.
        :type chr_level: int, optional
        """

        self.name = name
        self.level = level
        self.castingTime = casting_time
        self.duration = duration
        self.range = spell_range
        self.description = description
        self.area = area
        self.components = components
        self.school = school
        self.tags = tags
        self.damage = damage
        self.attack = attack
        self.save = save
        self.__chrLevel = chr_level

        self.cantrip_damage()
        self.builtSpells.append(self)

    def update_chr_level(self, new_level):
        """
        Updates the characters level, and adjusts accordingly.
        :param new_level: the new level of the character
        :type new_level: int
        """
        self.__chrLevel = new_level
        self.cantrip_damage()

    def cantrip_damage(self):
        """Calculates the damage the spell does, providing it's a cantrip, based on the character level."""
        if self.level == 0 and self.damage is not None:
            if self.__chrLevel < 5:
                damage = 1
            elif 5 <= self.__chrLevel < 11:
                damage = 2
            elif 11 <= self.__chrLevel < 17:
                damage = 3
            else:
                damage = 4
            self.damage = str(damage) + self.damage[1:]

    def __eq__(self, other):
        """
        Compares the spell object with another spell.
        Note that this function could be condensed into one line, but is separated for the sake of clarity and potential
        error locating.
        Many comparisons in this method are unnecessary by default, but including these allows for the consistent easy
        addition of new elements to the database, without the risk of collision.
        :param other: the other spell object to compare against
        :type other: Spell
        :return: a boolean stating whether they're equal
        """
        isEqual = False
        if type(other) is Spell:
            isEqual = self.name == other.name and self.level == other.level and self.castingTime == other.castingTime \
                    and self.duration == other.duration and self.range == other.range \
                    and self.components == other.components and self.school == other.school \
                    and sorted(self.tags) == sorted(other.tags) and self.description == other.description \
                    and self.damage == other.damage and self.attack == other.attack and self.save == other.save \
                    and self.area == other.area and self.__chrLevel == other.__chrLevel
        elif type(other) is str:
            isEqual = self.name == other

        return isEqual

    def __lt__(self, other):
        """
        Tests whether the current spell is less than the passed spell alphabetically.
        :param other: the other spell to compare against
        :type other: Spell
        :return: a boolean stating whether it's less than or not
        """
        return self.name < other.name

    def __hash__(self):
        """
        Hashes the object based on it's name and description.
        :return: the hashed value produced
        """
        return hash(self.name + self.description)

    def __str__(self):
        """
        Returns the data of the spells as a string
        :return: a string stating the spell data
        """
        details = "{} - Level {} {} spell.\n" \
                  "{} \n\n" \
                  "It has a duration of {} and a casting time of {}, with a range of {}.\n" \
                  "It requires the components {} and has the tags: {}\n".format(self.name, self.level, self.school,
                                                                                self.description, self.duration,
                                                                                self.castingTime, self.range,
                                                                                self.components, self.tags)
        if self.area is not None:
            details += "It has an area of {}.".format(self.area)
        if self.damage is not None:
            if self.attack is not None:
                details += "It is a {} attack. ".format(self.attack)
            if self.save is not None:
                details += "It required a {} spell save. ".format(self.save)
            details += "It deals {} damage.\n".format(self.damage)
        return details


def get_spell(spell_name, chr_level=1):
    """
    Gets a specified spell from the array of built spells, or adds it if it currently isn't in there.
    This is done to save building a substantial amount of objects for each spell.
    :param spell_name: the name of the spell to return
    :type spell_name: str
    :param chr_level: the level of the current character, relevant for cantrips
    :type chr_level: int
    :return: the spell object, pointed to from the array
    """
    # determines if the spell is built
    spellIndex = -1
    spellArray = Spell.builtSpells
    for x in range(0, len(spellArray)):
        if spellArray[x].name == spell_name:
            spellIndex = x

    if spellIndex == -1:
        Spell.builtSpells.append(Spell(*DataExtractor.spell_info(spell_name, chr_level)))
        spellIndex = len(Spell.builtSpells) - 1

    return Spell.builtSpells[spellIndex]

