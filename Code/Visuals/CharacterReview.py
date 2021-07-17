from functools import partial

from PyQt5 import uic
import altair as alt
import pandas as pd
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel

from Code.Optimisation import ChromosomeController


class CharacterReview:
    """Sets up and runs the menu that allows the user to visually review a character."""

    controller = None
    selector = None
    chrComboBox = None
    data = None

    def __init__(self):
        """
        Sets up the selector menu visuals.
        """
        Form, Window = uic.loadUiType("Visuals/QtFiles/CharacterReview.ui")
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)
        self.centre = self.window.findChild(QWidget, "centralwidget")

    def begin(self, controller):
        """
        Begins the character review menu and visualises it.
        :param controller: the controller for the programs visuals
        :type controller: VisualsController
        """
        self.controller = controller
        self.chrComboBox = self.centre.findChild(QComboBox, "chrComboBox")
        self.define_data()

        self.load_all_graphs()
        viewSheetBtn = self.centre.findChild(QPushButton, "sheetBtn")
        viewSheetBtn.clicked.connect(partial(self.view_sheet))

        archText = ChromosomeController.constFilters.get("Secondary", "")
        if archText != "":
            archText = "/" + archText
        archText = ChromosomeController.constFilters["Primary"] + archText

        self.centre.findChild(QLabel, "archLabel").setText(archText)

    def define_data(self):
        """
        Defines the set of data for all charts to use.
        """
        headings = list()
        counter = 1
        for chromosome in ChromosomeController.nondominatedFront:
            name = str(counter) + ". " + chromosome.character.chrClass.name + " " + chromosome.character.race.name
            self.chrComboBox.addItem(name)
            for tag in [tuple(["Health"]) + tuple(chromosome.health), tuple(["Magic"]) + tuple(chromosome.magic)] \
                       + chromosome.tags:
                headings.append({"Character": name, "Tag": tag[0], "Weighting": tag[2]})
            counter += 1
        self.data = pd.DataFrame(headings)


    def view_sheet(self):
        """
        Allows the user to view a character sheet.
        """
        charName = self.chrComboBox.currentText()
        chromosome = ChromosomeController.nondominatedFront[int(charName.split(".")[0]) - 1]
        self.controller.load_character_sheet(chromosome)

    def create_web_view(self, widget):
        """
        Sets up a web view within a widget, and returns a pointer to it.
        :param widget: the widget for the view to be nested within
        :type widget: str
        :return: a pointer to the QWebEngineView
        """
        widget = self.centre.findChild(QWidget, widget)
        webview = QWebEngineView()
        hbox = QHBoxLayout()
        hbox.addWidget(webview)
        widget.setLayout(hbox)
        return webview

    def load_all_graphs(self):
        """
        Loads and organises all of the data graphs.
        """
        mainWidget = self.create_web_view("main")
        histogramWidget = self.create_web_view("histogram")

        bar_charts = alt.vconcat(self.chromosome_chart(), self.select_chromosome())
        result = alt.hconcat(bar_charts, self.slope_graph()).resolve_scale(color='independent')
        result = result.configure_view(fill='#C6EAF9').configure_legend(
            orient='left',
            padding=5, cornerRadius=5,
            strokeColor='black', fillColor='#BBBBBB', strokeWidth=2,
            labelColor='#1212DE', titleColor='#1212DE'
        )

        self.controller.load_chart(mainWidget, result)
        self.controller.load_chart(histogramWidget, self.histograms())

    def slope_graph(self):
        """
        Creates a slope graph of all the data.
        :return: the produced graph
        """
        chart = alt.Chart(self.data).mark_line(point=True).encode(
            x="Tag",
            y="Weighting",
            color="Character:N"
        ).properties(
            title="Characters Compared",
            width=350,
            height=350
        ).interactive()
        return chart

    def histograms(self):
        """
        Produces a histogram for every tag that has been optimised, laid out horizontally to each other.
        :return: the produced graph
        """
        allGraphs = self.histogram("Health")
        allGraphs = alt.hconcat(allGraphs, self.histogram("Magic"))
        for (tag, _, _) in ChromosomeController.nondominatedFront[0].tags:
            allGraphs = alt.hconcat(allGraphs, self.histogram(tag))
        allGraphs.properties(
            title="Histograms"
        )
        return allGraphs

    @staticmethod
    def histogram(tag):
        """
        Produces a single histogram for a tag.
        :param tag: the tag to use the data of for the histogram
        :type tag: str
        :return: the produced graph
        """
        data = []
        for chromosome in ChromosomeController.nondominatedFront:
            tags = [tuple(["Health"]) + tuple(chromosome.health), tuple(["Magic"]) + tuple(chromosome.magic)] \
                       + chromosome.tags
            tagIndex = chromosome.get_tag_index(tag) + 2
            if tag == "Health":
                tagIndex -= 1
            data.append({"Weighting": tags[tagIndex][2]})
        data = pd.DataFrame(data)
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X("Weighting", bin=alt.BinParams(maxbins=10, minstep=1)),
            y="count()",
        ).properties(
            title=tag,
            width=100,
            height=100
        )
        return chart

    def chromosome_chart(self):
        """
        Creates a bar chart for a chromosome.
        :return: the produced graph
        """
        chromosome = ChromosomeController.nondominatedFront[0]
        firstName = "1. " + chromosome.character.chrClass.name + " " + chromosome.character.race.name
        self.selector = alt.selection_single(encodings=['y'], init={'y': firstName})

        chart = alt.Chart(self.data).mark_bar(size=20, angle=20).encode(
            x="Tag",
            y="Weighting",
            color="Tag:N"
        ).properties(
            title="Character Tags",
            width=200,
            height=200
        ).transform_filter(self.selector)

        return chart

    def select_chromosome(self):
        """
        Creates a chart that allows you to select which chromosome to view the bar chart of.
        :return: the produced graph
        """
        chart = alt.Chart(self.data).mark_bar(size=20).encode(
            x="Weighting",
            y=alt.Y("Character:N", sort="-x"),
            color=alt.condition(self.selector, alt.value("Gold"), "Tag:N")
        ).add_selection(self.selector)

        return chart
