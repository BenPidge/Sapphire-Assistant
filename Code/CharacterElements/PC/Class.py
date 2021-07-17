import itertools

from Code.CharacterElements.PC import Character


class Class:
    """A python class representing a character's class."""
    def __init__(self, name, traits, proficiencies, equipment, main_ability, second_ability, saving_throws, hit_dice,
                 languages, level, magic=None, subclass=None):
        """
        Initialises the Class object with the appropriate variables.
        :param name: The name of the class
        :type name: str
        :param traits: The text-based traits the class grants in (name, description) pairs.
        :type traits: list
        :param proficiencies: The proficiencies gained from the class.
        :type proficiencies: list
        :param equipment: The equipment selected from the class-specific options.
        :type equipment: list
        :param main_ability: The main ability score used by the class.
        :type main_ability: str
        :param second_ability: The second most used ability score by the class.
        :type second_ability: str
        :param saving_throws: The two saving throws as a string of their first 3 caps characters, separated by a comma
        :type saving_throws: str
        :param hit_dice: The hit dice the class gains at every level, and therefore it's health increase per level.
        :type hit_dice: int
        :param magic: A Magic object representing all spell-related elements of the class.
        :type magic: class: `CharacterElements.Magic`, optional
        :param languages: The languages gained from the class.
        :type languages: list, optional
        :param level: The amount of levels the character currently has in this class.
        :type level: int, optional
        :param subclass: A Class object representing the subclass of the current class.
        :type subclass: Subclass, optional
        """
        if languages is None:
            languages = []
        self.name = name
        self.className = name  # this is used for retaining the class name in cases of subclasses
        self.traits = sorted(traits)
        self.proficiencies = sorted(proficiencies)
        self.equipment = sorted(equipment)
        self.mainAbility = main_ability
        self.secondAbility = second_ability
        self.savingThrows = saving_throws.split(", ")
        self.hitDice = hit_dice
        self.magic = magic
        self.languages = sorted(languages)
        self.level = level
        self.hasSubclass = (subclass is not None)
        self.subclassItems = dict()

        if subclass is not None:
            self.extract_subclass(subclass)

    def extract_subclass(self, subclass):
        """
        Extract and apply all subclass data to the class.
        :param subclass: The subclass of the current class selected.
        :type subclass: Subclass
        """
        self.name = subclass.name + " " + self.name
        self.subclassItems = subclass.get_data()
        for key in self.subclassItems.keys():
            attributeVal = getattr(self, key)
            # if its an array, merge the arrays
            if key in ["languages", "proficiencies", "traits"]:
                setattr(self, key, attributeVal + self.subclassItems[key])
            # if it's single value, update the attribute value
            else:
                setattr(self, key, self.subclassItems[key])

        if subclass.magic is not None:
            self.subclassItems["spells"] = subclass.magic.knownSpells + subclass.magic.preparedSpellOptions
            if self.magic is None:
                self.magic = subclass.magic
            else:
                self.magic.knownSpells += subclass.magic.knownSpells + subclass.magic.preparedSpellOptions

    def get_data(self):
        """
        Combines all non-null data into a dictionary for easy extraction.
        This only consists of data necessary for filter-based recreation.
        :return: a dictionary of all non-null class data.
        """
        # name, profs(skills), profs, langs, equip, spells

        potentialSkills = list(itertools.chain(*Character.character_skills))
        skills, proficiencies = [], []
        for nextProf in self.proficiencies:
            if nextProf in potentialSkills:
                skills.append(nextProf)
            else:
                proficiencies.append(nextProf)

        dataDict = {
            "name": self.className,
            "languages": self.languages,
            "skills": skills,
            "proficiencies": proficiencies,
            "equipment": [e.name for e in self.equipment],
        }
        if self.magic is not None:
            dataDict.update({"spells": [s.name for s in (self.magic.knownSpells + self.magic.preparedSpellOptions)]})

        # remove null data
        for key in dataDict.keys():
            if dataDict[key] is None:
                del dataDict[key]

        return dataDict

    def __eq__(self, other):
        """
        Compares the class object with another class.
        Note that this function could be condensed into one line, but is separated for the sake of clarity and potential
        error locating.
        Many comparisons in this method are unnecessary by default, but including these allows for the consistent easy
        addition of new elements to the database, without the risk of collision.
        :param other: the other class object to compare against
        :type other: Class
        :return: a boolean stating whether they're equal
        """
        # compares the basic-type class variables
        isEqual = self.name == other.name and self.mainAbility == other.mainAbility \
                    and self.secondAbility == other.secondAbility and self.hitDice == other.hitDice \
                    and self.level == other.level

        # compares the container class variables
        isEqual = isEqual and self.traits == other.traits and self.proficiencies == other.proficiencies \
                    and self.equipment == other.equipment and self.languages == other.languages \
                    and self.savingThrows == other.savingThrows

        # compares the CharacterElements object type class variable
        isEqual = isEqual and self.magic == other.magic

        return isEqual

    def __str__(self):
        """
        Converts the object to a string of it's content.
        :return: the objects relevant content, in a printable layout
        """
        output = f"This lvl{self.level} {self.name} uses {self.level}d{self.hitDice} hit dice, with ability priorities"\
                 f" of {self.mainAbility}, followed by {self.secondAbility}.\n" \
                 f"They have the saving throws {self.savingThrows[0]} and {self.savingThrows[1]}.\n" \
                 f"They have proficiency with {', '.join(self.proficiencies)}.\n"

        if len(self.languages) > 0:
            output += f"They can speak {', '.join(self.languages)}.\n"

        if len(self.traits) > 0:
            output += "They have the traits "
            for trait in self.traits:
                output += trait[0] + ", "
            output = output[:-2] + ".\n"

        output += "They own a "
        for x in range(0, len(self.equipment)):
            output += self.equipment[x].name + ", "
        output = output[:-2] + ".\n"

        output += str(self.magic)

        return output



class Subclass:
    """A class representing all details of one subclass"""
    def __init__(self, name, class_name, second_ability, traits=None, magic=None, languages=None, proficiencies=None):
        """
        Initialises the subclass object.
        :param name: the name of the subclass
        :type name: str
        :param class_name: the name of the class it extends
        :type class_name: str
        :param second_ability: the second most important ability to the subclass
        :type second_ability: str
        :param traits: an array of trait (name, desc) pairs
        :type traits: list
        :param magic: a magic object, representing their magic capabilities
        :type magic: class: `CharacterElements.Magic`
        :param languages: an array of language names
        :type languages: list
        :param proficiencies: an array of proficiency names
        :type proficiencies: list
        """
        self.name = name
        self.className = class_name
        self.traits = traits
        self.magic = magic
        self.languages = languages
        self.proficiencies = proficiencies
        self.secondAbility = second_ability

    def get_data(self):
        """
        Combines all non-null data into a dictionary for easy extraction.
        :return: a dictionary of all non-null class data.
        """
        dataDict = {
            "name": self.name,
            "languages": self.languages,
            "proficiencies": self.proficiencies,
            "traits": self.traits,
            "secondAbility": self.secondAbility
        }

        # remove null data
        for key in dataDict.keys():
            if dataDict[key] is None:
                del dataDict[key]

        return dataDict

    def __str__(self):
        """
        Converts the object to a string of it's content.
        :return: the objects relevant content, in a printable layout
        """
        output = f"This {self.name} {self.className} subclass gains the proficiencies: {', '.join(self.proficiencies)}.\n"

        if len(self.languages) > 0:
            output += f"They can additionally speak {', '.join(self.languages)}.\n"

        if len(self.traits) > 0:
            output += "They gain the traits "
            for trait in self.traits:
                output += trait[0] + ", "
            output = output[:-2] + ".\n"

        output += str(self.magic)

        return output

