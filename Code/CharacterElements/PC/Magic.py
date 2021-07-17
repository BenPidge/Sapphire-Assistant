
class Magic:
    """A class representing all details of magic that a character class might require."""

    preparedSpellAmnt = 0

    def __init__(self, spell_slot, are_spells_prepared, spell_amount=-1, known_spells=None,
                 prepared_spell_calculation=None, prepared_spell_options=None,
                 casting_abilities=None, known_secondary_spells=None):
        """
        Stores all the core information on a classes magic.
        :param spell_slot: The spell slot level, linked to the amount of these spell slots available at the class level.
        :type spell_slot: dict
        :param are_spells_prepared: Stating whether spells are prepared or selected at levels.
        :type are_spells_prepared: bool
        :param spell_amount: The amount of spells that the class should have at any one time, or -1 to show more info is
                             required to calculate this.
        :type spell_amount: int, optional
        :param known_spells: Spells that are always known at any one time.
        :type known_spells: list, optional
        :param prepared_spell_calculation: States how the spells are prepared.
        :type prepared_spell_calculation: str, optional
        :param prepared_spell_options: Spells that can be prepared and unprepared during long rests.
        :type prepared_spell_options: list, optional
        :param casting_abilities: A pair of the abilities used to cast spells.
        :type casting_abilities: tuple, optional
        :param known_secondary_spells: Spells that are known from a secondary source to the known_spells list
        :type known_secondary_spells: list, optional
        """
        if known_secondary_spells is None:
            known_secondary_spells = []
        if known_spells is None:
            known_spells = []
        if prepared_spell_options is None:
            prepared_spell_options = []

        self.spellAmount = spell_amount
        self.spellSlot = spell_slot
        self.knownSpells = sorted(list(set(known_spells + known_secondary_spells)))
        self.areSpellsPrepared = are_spells_prepared
        self.preparedSpellCalculation = prepared_spell_calculation
        self.preparedSpellOptions = prepared_spell_options

        self.spellcasting = dict()
        if casting_abilities is not None:
            if casting_abilities[0] == casting_abilities[1]:
                self.spellcasting.update({casting_abilities[0]: self.knownSpells.copy()})
            else:
                self.spellcasting.update({casting_abilities[0]: known_spells,
                                          casting_abilities[1]: sorted(known_secondary_spells)})

    def __eq__(self, other):
        """
        Compares the magic object with another magic.
        Note that this function could be condensed into one line, but is separated for the sake of clarity and potential
        error locating.
        Many comparisons in this method are unnecessary by default, but including these allows for the consistent easy
        addition of new elements to the database, without the risk of collision.
        :param other: the other magic object to compare against
        :type other: Magic
        :return: a boolean stating whether they're equal
        """
        # compares the non-container class variables
        isEqual = self.spellAmount == other.spellAmount and self.areSpellsPrepared == other.areSpellsPrepared \
                    and self.preparedSpellCalculation == other.preparedSpellCalculation \
                    and self.preparedSpellAmnt == other.preparedSpellAmnt

        # compares the container class variables
        isEqual = isEqual and self.spellSlot == other.spellSlot and self.spellcasting == other.spellcasting \
                    and self.knownSpells == other.knownSpells \
                    and sorted(self.preparedSpellOptions) == sorted(other.preparedSpellOptions)

        return isEqual

    def __str__(self):
        """
        Converts the object to a string of it's content.
        :return: the objects relevant content, in a printable layout
        """
        string = f"They have "
        for (level, amnt) in self.spellSlot.items():
            if level < 4:
                multiple = ["st", "nd", "rd"]
                multiple = multiple[level-1]
            else:
                multiple = "th"
            string += f"{str(amnt)} {str(level)}{multiple}-Level spellslots, "
        string = string[:-2] + "\n"

        string += "They know the cantrips: "
        for x in range(0, len(self.knownSpells)):
            if self.knownSpells[x].level == 0:
                string += self.knownSpells[x].name + ", "
        string = string[:-2] + ".\n"

        string += "They know the spells: "
        for x in range(0, len(self.knownSpells)):
            if self.knownSpells[x].level > 0:
                string += self.knownSpells[x].name + ", "
        string = string[:-2] + ".\n"

        if self.preparedSpellCalculation is not None:
            if self.spellAmount > -1:
                string += f"They know {self.spellAmount} spells.\n"
            else:
                string += "They known spells equal to " + self.preparedSpellCalculation + ".\n"
            string += "They can prepare the spells: "
            for x in range(0, len(self.preparedSpellOptions)):
                string += self.preparedSpellOptions[x].name + ", "
            string = string[:-2] + "."
        return string
