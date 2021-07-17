# a 2D array, storing all skills within their relative ability scores
character_skills = [["Athletics"],  # strength
                    ["Acrobatics", "Sleight of Hand", "Stealth"],  # dexterity
                    [],  # constitution(for iteration)
                    ["Arcana", "History", "Investigation", "Nature", "Religion"],  # intelligence
                    ["Animal Handling", "Insight", "Medicine", "Perception", "Survival"],  # wisdom
                    ["Deception", "Intimidation", "Performance", "Persuasion"]]               # charisma

# an array storing all the abilities' shortened names
character_abilities = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


class NPC:
    """A class representing all the data linked to a single NPC"""

    equipment = []

    def __init__(self, name, race, personality, appearance):
        """
        Initialises an NPC.
        :param name: the name of the character
        :type name: str
        :param race: the race that the character is
        :type race: class: `CharacterElements.Race`
        :param personality: the name of the character's personality traits, linked to a description
        :type personality: dict
        :param appearance: a collection of physical attributes linked to the characters description of these
        :type appearance: CharacterElements.NPC.Appearance
        """
        self.name = name
        self.race = race
        self.personality = personality
        self.appearance = appearance
