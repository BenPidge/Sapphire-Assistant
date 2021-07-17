class ChoiceStruct:
    contents = []

    def __init__(self, choices):
        """
        Initialises a ChoiceStruct to contain the appropriate choices.
        :param choices: the choices to be transformed into Choice objects
        :type choices: dict
        """
        if type(choices) is dict:
            for choice_type, (choice, subchoices) in choices.items():
                self.append(Choice(choice_type, choice, subchoices))

    def clear(self):
        """
        Clears the current contents
        """
        self.contents = []

    def get_from_name(self, name):
        """
        Gets a Choice object from it's name
        :param name: the name of the Choice
        :type name: str
        :return: the Choice object, or 0 if not found
        """
        for content in self.contents:
            if content.name == name:
                return content
            elif content.type == name:
                return content
        return 0

    def get_element(self, potential_choices, element):
        """
        Gets the element choice selected from a list of potential choices.
        :param potential_choices: the choices available
        :type potential_choices: list
        :param element: the element to search for these within
        :type element: str
        :return: the choice made, or 0 if none were found
        """
        elementObj = self.get_from_name(element)
        if elementObj != 0:
            for choice in potential_choices:
                if type(choice) is list or type(choice) is tuple:
                    if type(choice[0]) is str:
                        choiceName = choice[0]
                    else:
                        choiceName = choice[0].name
                elif type(choice) is not str:
                    choiceName = choice.name
                else:
                    choiceName = choice

                if choiceName in elementObj.elements:
                    elementObj.pop(choice)
                    return choice
                elif choiceName == elementObj.name:
                    return choice
        return 0

    def append(self, new_choice):
        """
        Adds a new Choice object to the struct.
        :param new_choice: the new Choice object to add
        :type new_choice: Choice
        """
        self.contents.append(new_choice)

    def __str__(self):
        """
        Converts the ChoiceStruct into an easily readable string representation
        :return: the string representation
        """
        output = "This ChoiceStruct holds the following elements:\n"
        for choiceObj in self.contents:
            output += str(choiceObj) + "\n"
        return output


class Choice:
    def __init__(self, elem_type, choice, subchoices):
        """
        Initialises a choice to contain the appropriate contents.
        :param elem_type: the type the element falls under, such as class or background
        :type elem_type: str
        :param choice: the choice to make for this element type
        :type choice: str
        :param subchoices: the subchoices to be made for this element
        :type subchoices: list
        """
        self.type = elem_type
        self.name = choice
        self.elements = subchoices

    def pop(self, element):
        """
        Checks for an element in the choice, removes it if so, and returns the success.
        :param element: the element to remove
        :type element: str
        """
        try:
            self.elements.remove(element)
            return 1
        except ValueError:
            return 0

    def __str__(self):
        """
        Converts the choice into a string output for easy reading.
        :return: the string output of the choice
        """
        output = f"This choice involves selecting {self.type} for {self.name}.\n" \
                 f"It takes the suboptions {self.elements}"
        return output

