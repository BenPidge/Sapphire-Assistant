class Race:
    """A class representing a character's race."""

    def __init__(self, name, languages, proficiencies, ability_scores, traits, speed=30, size="Medium",
                 darkvision=False, spells=None, spell_modifier=None, resistance=None, subrace=None):
        """
        Initialise the race with all the necessary information to properly model it.
        :param name: The name of the race.
        :type name: str
        :param languages: The language or languages that the character knows from racial features.
        :type languages: list
        :param proficiencies: The proficiencies that the character knows from racial features.
        :type proficiencies: list
        :param ability_scores: The ability score improvements gained from the race, in an ability-to-value dictionary.
        :type ability_scores: dict
        :param traits: The racial traits gained that don't directly impact other racial data.
        :type traits: list
        :param speed: The walking speed, in feet, of the race.
        :type speed: int, optional
        :param size: The creature size of members of the race.
        :type size: str, optional
        :param darkvision: Whether this race grants darkvision or not.
        :type darkvision: bool, optional
        :param spells: Any spells that can be cast from a racial trait, as pairs (spell, spellLvl).
        :type spells: list, optional
        :param spell_modifier: The ability score modifier used to cast the racial spells
        :type spell_modifier: str, optional
        :param resistance: The damage type that this race grants resistance to.
        :type resistance: str, optional
        :param subrace: The subrace of this race that was selected.
        :type subrace: Race, optional
        """

        self.name = name
        self.raceName = name  # this is used for retaining the race name in cases of subraces
        self.languages = languages
        self.proficiencies = proficiencies
        self.abilityScores = ability_scores
        self.traits = traits
        self.speed = speed
        self.size = size
        self.darkvision = darkvision
        self.spellMod = spell_modifier
        self.resistance = resistance
        self.hasSubrace = (subrace is not None)

        if spells is None:
            self.spells = []
        else:
            self.spells = spells

        if subrace is not None:
            self.name = subrace.name
            self.extract_subrace(subrace)

    def extract_subrace(self, subrace):
        """
        Extract and apply all subrace data to the race.
        :param subrace: The subrace of this race that was selected.
        :type subrace: Race
        """
        subraceDict = subrace.get_data()
        subraceDict["spells"] = sorted(subrace.spells)
        for key in subraceDict.keys():
            attributeVal = getattr(self, key)
            # if its an array, merge the arrays
            if key in ["languages", "proficiencies", "traits",  "spells"]:
                setattr(self, key, attributeVal + subraceDict[key])
            # if it's a dictionary, merge the dictionaries
            elif key == "abilityScores":
                self.abilityScores = {**self.abilityScores, **subraceDict[key]}
            # if it's single value, update the attribute value
            else:
                setattr(self, key, subraceDict[key])

    def get_data(self):
        """
        Combines all non-null data into a dictionary for easy extraction.
        :return: a dictionary of all non-null racial data.
        """
        dataDict = {
            "name": self.name,
            "languages": sorted(self.languages),
            "proficiencies": sorted(self.proficiencies),
            "abilityScores": self.abilityScores,
            "traits": sorted(self.traits),
            "speed": self.speed,
            "size": self.size,
            "darkvision": self.darkvision,
            "resistance": self.resistance,
            "spells": sorted([s for (s, l) in self.spells]),
            "spellMod": self.spellMod
        }

        # remove null data
        tempDataDict = dataDict.copy()
        for key in tempDataDict.keys():
            if dataDict[key] is None or dataDict[key] is False:
                del dataDict[key]

        return dataDict

    def __eq__(self, other):
        """
        Compares the race object with another race.
        :param other: the other race object to compare against
        :type other: Race
        :return: a boolean stating whether they're equal
        """
        return self.get_data() == other.get_data()

    def __str__(self):
        """
        Converts the object to a string of it's content.
        :return: the objects relevant content, in a printable layout
        """
        output = f"This {self.name} has a speed of {self.speed}ft and is of {self.size} size.\n" \
                 f"They can speak {', '.join(self.languages)}.\n"

        if self.darkvision is True:
            output += "They are capable of seeing in darkness."
        if self.resistance is not None and self.resistance != "":
            output += f"They have resistance to {self.resistance} damage."
        output += "\n"

        for ability, addition in self.abilityScores.items():
            output += f"They gain +{addition} to their {ability} ability score. "
        output += "\n"

        if len(self.proficiencies) > 0:
            output += "\nThey have proficiency with "
            for proficiency in self.proficiencies:
                output += proficiency + ", "
            output = output[:-2] + ".\n"

        if len(self.traits) > 0:
            output += "\nThey have the traits "
            for trait in self.traits:
                output += trait[0] + ", "
            output = output[:-2] + ".\n"

        if len(self.spells) > 0:
            output += f"Using {self.spellMod} as their spellcasting ability, they can cast "
            for spell in self.spells:
                output += f"{spell[0].name} as if using a spellslot of level {spell[1]}, "
            output = output[:-2] + ".\n"

        return output

