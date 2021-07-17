import itertools
import math
from collections import Counter

from Code.Database import CoreDatabase as Db, DataExtractor


def pull_generic_tag(tag_name, data, weight, archetype_tags, archetype_weight_dict):
    """
    Adjusts the inputted weighting dictionary based on the occurrences of archetype tags in the inputted data set.
    :param tag_name: the singular name of the type of item being pulled, such as Spell
    :type tag_name: str
    :param data: the names of all data pieces to pull tags from, with their relevant data values, in a 2D array
    :type data: list
    :param weight: the weighting to be applied to recorded occurrences of the tags
    :type weight: int
    :param archetype_tags: the tags that apply to the archetype(s) selected in creating the chromosome
    :type archetype_tags: set
    :param archetype_weight_dict: a dictionary, linking an archetype tag to the (weighted) occurences of it so far
    :type archetype_weight_dict: dict
    :return: the updated archetype weight dictionary
    """
    for dataPiece, dataValue in data:
        tags = DataExtractor.get_names_from_connector(tag_name, "GenericTag", input_name=dataPiece)
        tagAmnt = Counter(tags)
        for match in set(tags).intersection(archetype_tags):
            # calculates the weighted value of the match, based on it's amount of occurrences, and adds this
            # to the archetype weighting dictionaries current value
            weightedWorth = (tagAmnt[match] * (weight + dataValue))
            archetype_weight_dict.update({match: (archetype_weight_dict[match] + weightedWorth)})
    return archetype_weight_dict


class Chromosome:
    """A singular potential solution for the optimisation problem."""

    fitness = 0
    generic_tags = dict()

    def __init__(self, character, tags, magic_weight, health_weight, archs):
        """
        Initialises the chromosome with a provided character object and tags.
        This should be called primarily, if not completely, through the ChromosomeController.
        :param character: the character the chromosome will represent
        :type character: class: `Character.Character`
        :param tags: the tags that it's sorting will judge it off, in a [tag, weight] layout
        :type tags: list
        :param magic_weight: the weighting of how magic the chromosome is
        :type magic_weight: float
        :param health_weight: the weighting of how tanky the chromosome is
        :type health_weight: float
        :param archs: the archetypes this tuple is optimising
        :type archs: tuple
        """
        self.character = character
        self.health = [health_weight, (character.chrClass.hitDice - 6)/2 + character.ability_mod("CON")]
        self.archs = archs

        # calculates the magic weighting
        self.magic = [magic_weight, self.spellslots_value()]
        divisor = character.magic.preparedSpellAmnt
        if divisor != 0:
            self.magic[1] += len(character.magic.preparedSpellOptions)/divisor
        for (ability, spells) in character.magic.spellcasting.items():
            self.magic[1] += len(spells)

        # tags is a 2D array with nested array layouts of [tag, tags' weighting, tags' individual fitness]
        self.tags = []
        for (tag, weight) in sorted(tags):
            self.tags.append([tag, weight, 0])

        self.extract_tags()

    def get_tag_fitness_values(self):
        """
        Returns the tag fitness values in the order they're stored.
        :return: the tag fitness values, in a list
        """
        weights = [self.health[1], self.magic[1]]
        for (_, _, fitness) in self.tags:
            weights.append(fitness)
        return weights

    def calculate_fitness(self):
        """
        Sums the total of all tags' fitness values.
        """
        for (_, _, fitness) in self.tags:
            self.fitness += fitness

    def update_indiv_tag_fitness(self, tag, addition):
        """
        Updates the fitness value of a given tag.
        :param tag: the tag to update the fitness of
        :type tag: str
        :param addition: the amount to increase the tag fitness by
        :type addition: int
        """
        # flatten tagsFitness to get the tags' array index from the name
        index = int(list(itertools.chain(*self.tags)).index(tag) / 3)
        self.tags[index][2] = round(self.tags[index][2] + addition * self.tags[index][1], 2)

    def extract_tags(self):
        """
        Extracts the needed information from each tag.
        """
        self.ability_scores_tag()
        self.generic_tags = self.pull_generic_tags()
        for (tag, weight, fitness) in self.tags:
            self.update_indiv_tag_fitness(tag, self.get_tag_fitness(tag))
        self.calculate_fitness()

    def get_tag_fitness(self, tag):
        """
        Gets the unweighted fitness value of a tag relative to it's character.
        :param tag: the tag applying to the character
        :type tag: str
        :return: the integer weight
        """
        fitness = 0
        tagId = Db.get_id(tag, "Tag")
        fitness += self.proficiencies_total(tagId)
        Db.cursor.execute(f"SELECT genericTagName FROM GenericTag WHERE genericTagId IN "
                          f"(SELECT genericTagId FROM ArchTagConn WHERE tagId={Db.get_id(tag, 'Tag')})")
        for genericTag in list(itertools.chain(*Db.cursor.fetchall())):
            fitness += self.generic_tags[genericTag]

        return fitness

    def get_tag_index(self, tag_name):
        """
        Gets the index of a given tag within the tags array.
        :param tag_name: the name of the tag to find
        :type tag_name: str
        :return: the index int of the tag, or -1 if it doesn't exist
        """
        counter = 0
        for tagData in self.tags:
            if tagData[0] == tag_name:
                return counter
            else:
                counter += 1
        return -1

    def proficiencies_total(self, tag_id):
        """
        Counts how many proficiencies the character has that are appropriate to the given tag.
        :param tag_id: the id of the given tag to use for comparisons
        :type tag_id: int
        :return: the integer value of how many proficiencies are relevant
        """
        values = 0
        Db.cursor.execute("SELECT proficiencyId FROM TagProficiency WHERE tagId=" + str(tag_id))
        for pId in Db.cursor.fetchall():
            Db.cursor.execute("SELECT proficiencyName FROM Proficiency WHERE proficiencyId=" + str(pId[0]))
            try:
                prof = Db.cursor.fetchone()[0]
                if prof in self.character.proficiencies:
                    values += self.character.get_skill_value(prof)
            except TypeError:
                pass

        return values

    def spellslots_value(self):
        """
        Calculates the total magic value provided from the spellslots.
        :return: an integer value representing the spellslots' worth
        """
        value = 0
        for lvl, amnt in self.character.magic.spellSlot.items():
            value += lvl * amnt
        return value

    def ability_scores_tag(self):
        """
        Converts the current ability scores into one weighted integer, if they're related to tag.
        """
        # while it'll never be part of the intersect, health is kept in for tags-to-ability-score index consistency
        potentialTags = ["strong", "dexterous", "health", "wise", "knowledgeable", "charismatic"]
        # for every archetype-owned tag within potentialTags, ignoring casing
        for tag in list(set([x.lower() for x in potentialTags])
                        .intersection(set([x[0].lower() for x in self.tags]))):
            value = list(self.character.abilityScores.values())[potentialTags.index(tag)]
            self.update_indiv_tag_fitness(tag.title(), math.floor(value/2)-5)

    def pull_generic_tags(self):
        """
        Pulls all information linked to the GenericTag table from each archetype tag, and monitors how often
        it is used in the selected spells, equipment and traits.
        :return: the list information of all generic tags
        """
        # stores a set of the tags relevant to the selected archetype(s)
        archetypeTags = set()
        # stores a dictionary of (tag, value) pairs, where the pair is the weighted occurrences of the tag
        archetypeWeightDict = dict()
        # stores the weights of the generic tags, in [equipment, spell, trait] order
        weights = [1, 1, 1]

        # fills out the set and dictionary of the tags
        for tag in self.tags:
            archetypeTags.update(set(DataExtractor.get_names_from_connector("Tag", "GenericTag", input_name=tag[0])))
        for tag in archetypeTags:
            archetypeWeightDict.update({tag: 0})

        # prepares lists of the names of each data group, with their related data values
        # they have easily adjustable data value weightings, with the base values typically being
        # their maximum dice values, plus 1 for every dice above 1, to represent the benefit of more dice
        equipment, spells, traits = [], [], []
        for eq in set(self.character.chrClass.equipment):
            if eq.armorClass != 0:
                equipVal = (eq.armorClass - 10)/4.0
            elif eq.dice is not None:
                diceValues = eq.dice.split("d")
                equipVal = (int(diceValues[0]) * int(diceValues[1])) + (int(diceValues[0]) - 1)
                equipVal /= 6.0
            else:
                equipVal = 0
            equipment.append([eq.name, equipVal])

        for spell in (self.character.magic.knownSpells + self.character.magic.preparedSpellOptions):
            if spell.damage is None:
                spellDmg = 0
            else:
                spellDmgVals = spell.damage.split("d")
                spellDmg = (int(spellDmgVals[0]) * int(spellDmgVals[1])) + (int(spellDmgVals[0]) - 1)
                spellDmg /= 6.0
            spells.append([spell.name, spellDmg])

        for trait in self.character.traits:
            traits.append([trait[0], 0])

        archetypeWeightDict = pull_generic_tag("Equipment", equipment, weights[0], archetypeTags, archetypeWeightDict)
        archetypeWeightDict = pull_generic_tag("Spell", spells, weights[1], archetypeTags, archetypeWeightDict)
        archetypeWeightDict = pull_generic_tag("Trait", traits, weights[2], archetypeTags, archetypeWeightDict)

        return archetypeWeightDict

    def get_data_as_filters(self):
        """
        Retrieves the chromosome data that would be require to recreate it with the chromosome controller.
        :return: a dictionary of the filter data required
        """
        results = self.character.get_data_as_filters()
        results['Primary'] = self.archs[0]
        if self.archs[1] is not None:
            results['Secondary'] = self.archs[1]

        return results


    def __eq__(self, other):
        """
        Compares the chromosome object with another chromosome.
        Note that this function could be condensed into one line, but is separated for the sake of clarity and potential
        error locating.
        :param other: the other chromosome object to compare against
        :type other: Chromosome
        :return: a boolean stating whether they're equal
        """
        # compares the tags and fitness
        isEqual = self.fitness == other.fitness and self.generic_tags == other.generic_tags \
                                                and sorted(self.tags) == sorted(other.tags)

        # compares the health and magic
        isEqual = isEqual and self.health == other.health and self.magic == other.magic

        return isEqual

    def __str__(self):
        """
        Converts the chromosome into a string stating it's data.
        :return: the string of it's data
        """
        output = "This chromosome represents a " + self.character.race.name + " " + self.character.chrClass.name \
                 + " aiming to optimise for the current tags:\n"
        for tag in self.tags:
            output += str(tag[0]) + " with a weighting of " + str(tag[1]) \
                      + " and a fitness calculated as " + str(tag[2]) + "\n"
        output += "\nA health weighting of " + str(self.health[0]) + " with a fitness of " + str(self.health[1]) \
                  + " and a magic weighting of " + str(self.magic[0]) + " with a fitness of " + str(self.magic[1])
        return output
