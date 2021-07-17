import itertools

from pymoo.algorithms.nsga2 import NSGA2
from pymoo.factory import np
from pymoo.optimize import minimize

from Code.Database import CharacterBuilder, DataConverter, CoreDatabase as Db
from Code.Optimisation.Chromosome import Chromosome
from Code.Optimisation.PymooOverwrites import ChrMutation, ChrCrossover, ChrSampling, ChrDuplicates, ChrProblem

currentGen = []
nondominatedFront = []
constFilters = dict()


def set_const_filters(filters):
    """
    Sets the constant filters to be used regardless of chromosome being built.
    :param filters: the filters to be the new constant filters
    :type filters: dict
    """
    global constFilters
    constFilters = filters


def build_chromosome(filters):
    """
    Builds a chromosome and adds it to the list of current chromosomes.
    :param filters: the filters to use to build the chromosome
    :type filters: dict
    :return: The created chromosome object
    """
    # retrieves the needed filters for building a chr
    convertedFilters = []
    for heading, elements in filters.items():
        choiceType = heading[:-1]
        whereFrom = ["Background", "ClassOptions", "RaceOptions"]
        if heading in ("Proficiencies", "Skills"):
            choiceType = "Proficiency"
        elif heading == "Spells":
            whereFrom = ["Race", "Class"]
        elif heading == "Equipment":
            choiceType = "Equipment"
            whereFrom = ["Class"]
        elif heading in ("Background", "Class", "Race"):
            choiceType = heading
            whereFrom = [heading]
            elements = [elements]
        elif heading in ("Subrace", "Subclass"):
            choiceType = heading
            whereFrom = [heading.replace("Sub", "").capitalize()]
            elements = [elements]
        elif heading != "Languages":
            choiceType = ""

        if choiceType != "":
            for element in elements:
                if type(element) is not str:
                    element = element.name
                convertedFilters.append([element, choiceType, whereFrom])

    # builds a character
    convertedFilters = CharacterBuilder.take_choices(convertedFilters)
    abilities = filters.get("Abilities", dict())
    for ability, [min_val, max_val] in constFilters.get("Abilities", dict()).items():
        currentAbilityFilter = abilities.get(ability, [min_val, max_val])
        if currentAbilityFilter[0] < min_val:
            abilities[ability][0] = min_val

        if currentAbilityFilter[1] > max_val:
            abilities[ability][1] = max_val
        elif currentAbilityFilter[1] < min_val:
            abilities[ability][1] = min_val
    newChr = DataConverter.create_character(1, convertedFilters, abilities)

    # extracts the tags for the selected archetypes
    primaryArch = filters["Primary"]
    try:
        secondaryArch = filters["Secondary"]
    except KeyError:
        secondaryArch = None
    healthWeight, magicWeight, tags = extract_tags(primaryArch, secondaryArch)

    # combines it all to make a chromosome
    tags = [[i, j] for (i, j) in tags.items()]
    chromosome = Chromosome(newChr, tags, magicWeight, healthWeight, (primaryArch, secondaryArch))
    currentGen.append(chromosome)
    return chromosome


def extract_tags(primary_arch, secondary_arch=None):
    """
    Extracts the tags and their calculated weighting from archetypes.
    :param primary_arch: the name of the primary archetype
    :type primary_arch: str
    :param secondary_arch: the name of the secondary archetype
    :type secondary_arch: str
    :return: The health weighting, the magic weighting, and a dictionary linking tags to their weights
    """
    archWeights = (2, 1)
    tags = dict()
    healthWeight = 0
    magicWeight = 0
    if secondary_arch is None:
        secondary_arch = primary_arch

    archCount = 0
    for arch in [primary_arch, secondary_arch]:
        Db.cursor.execute(f"SELECT archetypeId, healthWeighting, magicWeighting FROM Archetype "
                          f"WHERE archetypeName='{arch}'")

        for (archId, healthWeighting, magicWeighting) in Db.cursor.fetchall():
            healthWeight += healthWeighting * archWeights[archCount]
            magicWeight += magicWeighting * archWeights[archCount]

            Db.cursor.execute(f"SELECT tagName, tagId FROM Tag WHERE tagId IN ("
                              f"SELECT tagId FROM ArchetypeTag WHERE archetypeId={str(archId)})")
            for (name, tagId) in Db.cursor.fetchall():
                Db.cursor.execute(f"SELECT weighting FROM ArchetypeTag WHERE tagId={str(tagId)}")
                if name in tags.keys():
                    newVal = tags[name] + float(Db.cursor.fetchone()[0]) * archWeights[archCount]
                else:
                    newVal = float(Db.cursor.fetchone()[0]) * archWeights[archCount]
                tags.update({name: round(newVal, 2)})

        archCount += 1
    return round(healthWeight, 2), round(magicWeight, 2), tags


def begin_optimising():
    """
    Begins the optimisation process for the character requirements.
    """
    # gets the amount of unique tags that the primary - and secondary, if appropriate - archetype(s) optimise
    if constFilters.get('Secondary', []):
        Db.cursor.execute(f"SELECT COUNT(DISTINCT tagId) FROM ArchetypeTag "
                          f"WHERE archetypeId IN ({Db.get_id(constFilters['Primary'], 'Archetype')}, "
                          f"{Db.get_id(constFilters['Secondary'], 'Archetype')})")
        tag_num = int(Db.cursor.fetchone()[0])
    else:
        Db.cursor.execute(f"SELECT COUNT(DISTINCT tagId) FROM ArchetypeTag "
                          f"WHERE archetypeId={Db.get_id(constFilters['Primary'], 'Archetype')}")
        tag_num = int(Db.cursor.fetchone()[0])

    tag_num += 2  # for the magic and health tags
    algorithm = NSGA2(pop_size=10, sampling=ChrSampling.ChrSampling(), crossover=ChrCrossover.ChrCrossover(),
                      mutation=ChrMutation.ChrMutation(), eliminate_duplicates=ChrDuplicates.ChrDuplicates())
    results = minimize(ChrProblem.ChrProblem(tag_num), algorithm, ("n_gen", 20))
    nondominatedFront.clear()
    nondominatedFront.extend(list(itertools.chain(*results.X[np.argsort(results.F[:, 0])])))


def begin():
    constFilters.update({'Primary': 'Creator'})
    begin_optimising()
    print("\n\n\nComplete!")
    print(nondominatedFront)
    for element in nondominatedFront:
        print(element)

