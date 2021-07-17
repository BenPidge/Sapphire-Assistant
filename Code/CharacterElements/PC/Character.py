import itertools
import math

from Code.CharacterElements import Equipment
from Code.CharacterElements.PC import Magic

# a 2D array, storing all skills within their relative ability scores
character_skills = [["Athletics"],  # strength
                    ["Acrobatics", "Sleight of Hand", "Stealth"],  # dexterity
                    [],  # constitution(for iteration)
                    ["Arcana", "History", "Investigation", "Nature", "Religion"],  # intelligence
                    ["Animal Handling", "Insight", "Medicine", "Perception", "Survival"],  # wisdom
                    ["Deception", "Intimidation", "Performance", "Persuasion"]]               # charisma

# an array storing all the abilities' shortened names
character_abilities = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


class Character:
    """A class representing a built character."""

    armorClass = 0
    health = 0

    def __init__(self, race, chr_class, background, ability_scores):
        """
        Stores up the key elements of the character.
        :param race: The characters race, stored as a Race object.
        :type race: class: `CharacterElements.Race`
        :param chr_class: The characters class, stored as a Class object.
        :type chr_class: class: `CharacterElements.Class`
        :param background: The characters background, stored as a Background object.
        :type background: class: `CharacterElements.Background`
        :param ability_scores: The ability scores of the character.
        :type ability_scores: dict
        """
        self.race = race
        self.chrClass = chr_class
        self.background = background
        self.proficiencyBonus = 2

        self.abilityScores = self.setup_ability_scores(ability_scores)
        self.languages = race.languages + chr_class.languages + background.languages
        self.traits = race.traits + chr_class.traits
        self.proficiencies = self.setup_proficiencies()
        self.magic = self.setup_magic()

        # calculates the characters armor class and health
        self.setup_armor_class()
        self.setup_health()

    def setup_health(self):
        """
        Calculates the amount of health the character would have.
        """
        constMod = self.abilityScores["CON"]//2 - 5
        self.health = self.chrClass.hitDice + constMod
        self.health += (self.chrClass.hitDice/2 + 1 + constMod) * (self.chrClass.level - 1)

    def setup_armor_class(self):
        """
        Calculates the armor class of the character, based on their equipment and dexterity modifier
        """
        for eq in self.chrClass.equipment:
            if eq.armorClass != 0:
                if "Shield" in eq.name:
                    self.armorClass += eq.armorClass
                else:
                    eq.setup_armor_class(self.abilityScores["DEX"] // 2 - 5)
                    self.armorClass = eq.armorClass
        if self.armorClass == 0:
            self.armorClass = 10 + self.abilityScores["DEX"]//2 - 5

    def setup_ability_scores(self, ability_scores):
        """
        Adds the racial ability score increases to the inputted ability scores.
        :param ability_scores: each ability score, linked as a key to it's current value.
        :type ability_scores: dict
        :return: a set of complete ability scores for a character
        """
        raceAbilities = self.race.abilityScores.keys()
        for ability in ability_scores.keys():
            if ability in raceAbilities:
                ability_scores[ability] = ability_scores[ability] + self.race.abilityScores[ability]
        return ability_scores

    def get_skill_value(self, skill):
        """
        Gets a single skills' value.
        :param skill: the name of the skill to get the value for
        :type skill: str
        :return: an integer of the value
        """
        value = 0
        if skill in self.proficiencies:
            value += self.proficiencyBonus
        for x in range(0, len(character_skills)):
            if skill in character_skills[x]:
                value += self.abilityScores.get(character_abilities[x])
                break
        return value

    def setup_proficiencies(self):
        """
        For every proficiency gained from any source, sort it into one of four categories:
        armor, weapons, tools, saving throws. Connect these categories and proficiencies with a dictionary of arrays.
        :return: a dictionary, connecting a key for each category with an array of all applicable proficiencies.
        """
        armor, weapons, tools, saving_throws, skills = [], [], [], [], []
        for proficiency in (self.race.proficiencies + self.chrClass.proficiencies + self.background.proficiencies):
            if proficiency in character_abilities:
                saving_throws.append(proficiency)
            elif "armor" in proficiency or proficiency.lower() == "shield":
                armor.append(proficiency)
            elif proficiency in Equipment.get_tag_group("Martial") + Equipment.get_tag_group("Simple"):
                weapons.append(proficiency)
            elif proficiency in itertools.chain(*skills):
                skills.append(proficiency)
            else:
                tools.append(proficiency)

        return {"Armor": sorted(armor), "Weapons": sorted(weapons),
                "Tools": sorted(tools), "Saving throws": sorted(saving_throws),
                "Skills": sorted(skills)}

    def setup_magic(self):
        """
        Sets up the character's magic.
        :return: the magic object created to represent this
        """
        raceSpells = []
        for spell in self.race.spells:
            # defensive code to avoid potential errors
            if type(spell) is tuple:
                raceSpells.append(spell[0])
            else:
                raceSpells.append(spell)

        if self.chrClass.mainAbility in ["INT", "WIS", "CHA"]:
            abilities = (self.chrClass.mainAbility, self.race.spellMod)
        else:
            abilities = (self.chrClass.secondAbility, self.race.spellMod)

        magic = self.chrClass.magic
        if magic is not None:
            elements = [magic.spellSlot, magic.areSpellsPrepared,
                        magic.spellAmount, magic.knownSpells,
                        magic.preparedSpellCalculation, magic.preparedSpellOptions]

        else:
            elements = [{1: 0}, False, 0, [], "ALL", []]

        newMagic = Magic.Magic(elements[0], elements[1], elements[2], elements[3], elements[4], elements[5],
                               abilities, raceSpells)
        if magic is not None and magic.areSpellsPrepared:
            newMagic.preparedSpellAmnt = self.ability_mod(magic.preparedSpellCalculation[:3]) + self.chrClass.level

        return newMagic

    def ability_mod(self, ability_score):
        """
        Calculates the ability modifier value, given an ability score name.
        :param ability_score: the name of the ability score to convert
        :type ability_score: str
        :return: the ability modifier value
        """
        return math.floor(self.abilityScores[ability_score] / 2) - 5

    def get_data_as_filters(self):
        """
        Returns the characters data in a layout matching the filters passed to create a chromosome.
        :return: the characters data, as a dict
        """
        results = dict()

        # gets basic information
        results.update({'Race': self.race.raceName, 'Class': self.chrClass.className,
                        'Background': self.background.name, 'Languages': self.languages})

        # gets equipment and spells
        results['Equipment'] = [e.name for e in self.chrClass.equipment]
        results['Spells'] = [s.name for s in (self.magic.knownSpells + self.magic.preparedSpellOptions)]

        # gets all proficiencies/skills
        profLayout = []
        for profType, proficiencies in self.proficiencies.items():
            if profType == "Skills":
                results['Skills'] = proficiencies
            else:
                profLayout += proficiencies
        results['Proficiencies'] = profLayout

        # converts the layout of ability scores, then adds them
        abilityLayout = dict()
        for ability, score in self.abilityScores.items():
            abilityLayout.update({ability: [score, 17]})
        results['Abilities'] = abilityLayout

        # gets optional information when appropriate
        if self.race.hasSubrace:
            results['Subrace'] = self.race.name
        if self.chrClass.hasSubclass:
            results['Subclass'] = self.chrClass.name

        return results

    def __eq__(self, other):
        """
        Compares the character object with another character.
        Note that this function could be condensed into one line, but is separated for the sake of clarity and potential
        error locating.
        :param other: the other character object to compare against
        :type other: Character
        :return: a boolean stating whether they're equal
        """
        # compares the base-type class variables
        isEqual = self.proficiencyBonus == other.proficiencyBonus \
                    and sorted(self.proficiencies) == sorted(other.proficiencies) and \
                    sorted(self.traits) == sorted(other.traits) and sorted(self.languages) == sorted(other.languages) \
                    and self.abilityScores == other.abilityScores

        # compares the class variables that are objects of types within the CharacterElements package
        isEqual = isEqual and self.magic == other.magic and self.background == other.background and \
                    self.race == other.race and self.chrClass == other.chrClass

        return isEqual

    def __str__(self):
        """
        Converts the object to a string of it's content.
        :return: the objects relevant content, in a printable layout
        """
        output = f"This lvl{self.chrClass.level} {self.race.name} {self.chrClass.name} uses " \
                 f"{self.chrClass.level}d{self.chrClass.hitDice} hit dice, with ability priorities of " \
                 f"{self.chrClass.mainAbility}, followed by {self.chrClass.secondAbility}.\n"  \
                 f"They have the saving throws {self.chrClass.savingThrows[0]} and {self.chrClass.savingThrows[1]}.\n" \
                 f"They have proficiency with {', '.join(list(itertools.chain(*self.proficiencies.values())))}.\n" \
                 f"They can speak {', '.join(self.languages)}.\n"

        output += "They have "
        abilityScores = list(self.abilityScores.items())
        for x in range(0, 6):
            output += f"{str(abilityScores[x][1])} {abilityScores[x][0]}, "
        output = output[:-2] + ".\n"

        if len(self.traits) > 0:
            output += "They have the traits "
            for trait in self.traits:
                output += trait[0] + ", "
            output = output[:-2] + ".\n"

        output += "They own a "
        for x in range(0, len(self.chrClass.equipment)):
            output += self.chrClass.equipment[x].name + ", "
        output = output[:-2] + ".\n"

        output += str(self.magic)

        return output

