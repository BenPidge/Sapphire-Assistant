from io import StringIO

from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect

from Code.Visuals import SelectorMenu, AdvancedFiltersMenu, ConfirmationScreen, CharacterReview, CharacterSheet, \
    MainMenu, VisualDatabase, DataPiece


class VisualsController:
    """Controls all visual elements of the program."""

    advancedFiltersUsed = False
    filters = None

    app = QApplication([])
    mainMenu = None
    selectorMenu = None
    advancedFiltersMenu = None
    confirmationScreen = None
    characterReview = None
    visualDatabase = None

    thread = None
    loading = None
    character_review = None

    def begin(self):
        """
        Begins the program visuals.
        """
        # the declarations are done here for the potential future use of resets
        self.mainMenu = MainMenu.MainMenu()
        self.selectorMenu = SelectorMenu.SelectorMenu()
        self.advancedFiltersMenu = AdvancedFiltersMenu.AdvancedFiltersMenu()
        self.confirmationScreen = ConfirmationScreen.ConfirmationScreen()
        self.characterReview = CharacterReview.CharacterReview()
        self.visualDatabase = VisualDatabase.VisualDatabase()
        self.advancedFiltersUsed = False
        self.filters = dict()
        self.mainMenu.begin(self)
        self.app.exec_()

    def return_to_main_menu(self):
        """Returns to the main menu."""
        self.visualDatabase.window.hide()
        self.selectorMenu.window.hide()
        self.mainMenu.window.show()

    def start_selector_menu(self):
        """Starts up the selector menu."""
        self.mainMenu.window.hide()
        self.selectorMenu.begin(self)

    def start_database_menu(self):
        self.mainMenu.window.hide()
        self.visualDatabase.begin(self)

    def show_selector_menu(self):
        """Shows the selector menu, when returned to from the confirmation screen"""
        self.selectorMenu.window.show()
        self.confirmationScreen.window.hide()
        self.mainMenu.window.hide()

    def start_advanced_filters_menu(self):
        """
        Starts up the advanced filters menu window.
        """
        self.advancedFiltersMenu.begin(self)
        self.selectorMenu.window.hide()
        self.advancedFiltersUsed = True

    def stop_advanced_filters_menu(self):
        """
        Visually stops the advanced filters menu window.
        """
        self.advancedFiltersMenu.window.hide()
        self.selectorMenu.window.show()

    def retrieve_filters(self):
        """
        Retrieves the filters applied into a dictionary.
        """
        self.filters.clear()
        self.filters.update(self.selectorMenu.get_filters())
        if self.advancedFiltersUsed:
            self.filters.update(self.advancedFiltersMenu.get_filters())
        for (tag, item) in self.filters.items():
            if type(item) is list:
                self.filters[tag].sort()

    def show_loading_screen(self):
        """
        Displays the loading screen while the optimisation occurs.
        """
        self.retrieve_filters()
        self.confirmationScreen.begin(self)
        self.selectorMenu.window.hide()
        self.confirmationScreen.window.show()

    def load_character_review(self):
        """
        Starts up the character review menu.
        """
        self.characterReview.begin(self)
        self.confirmationScreen.window.hide()
        self.characterReview.window.show()

    def load_character_sheet(self, chromosome):
        """
        Loads up a character sheet in a new window.
        :param chromosome: the character for the sheet to visualise
        :type chromosome: class: `CharacterElements.Chromosome`
        """
        CharacterSheet.CharacterSheet(self, chromosome)

    def open_view_popup(self, info, table):
        """
        Loads up a piece of data from the database in a new window.
        :param info: the info to be visualised
        :type info: list
        :param table: the table the info is from
        :type table: str
        """
        DataPiece.DataPiece(self, info, table)

    def data_piece_deleted(self):
        """
        Updates the visual database view segment upon a piece being deleted.
        """
        self.visualDatabase.reset_view()

    @staticmethod
    def setup_shadows(centre, shadow_items):
        """
        Sets up the shadows for all widgets passed through.
        :param shadow_items: a name:type dictionary of widgets to give shadows
        :type shadow_items: dict
        :param centre: the centre widget that the passed widgets rest on
        :type centre: widget
        :return: the modified centre
        """
        for item, obj in shadow_items.items():
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            centre.findChild(obj, item).setGraphicsEffect(shadow)
        return centre

    @staticmethod
    def load_chart(widget, chart):
        """
        Loads a pulled chart into a Qt widget.
        :param widget: the widget to place the chart within
        :type widget: class: `QtWebEngineWidgets.QWebEngineView`
        :param chart: the chart to insert into the widget
        :type chart: class: `altair.Chart`
        """
        html = StringIO()
        chart.save(html, "html")
        widget.setHtml(html.getvalue())

