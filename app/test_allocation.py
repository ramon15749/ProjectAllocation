from app.allocation import *
import pytest
import numpy as np
from pprint import pprint
from scipy.optimize import linear_sum_assignment
import logging
import random
from app.test_util import randomPref, create_proj_staff
import math


TestSet = NewType(
    "TestSet",
    Tuple[
        str,
        Dict[StudentID, List[Tuple[ProjectID, int]]],
        Optional[Dict[ProjectID, List[Tuple[StudentID, int]]]],
        Dict[ProjectID, StaffID],
        Config,
    ],
)
Test: TestSet = namedtuple(
    "TestSet", ["name", "pref", "staffPref", "proj_details", "config"]
)


def createMockData(
    noStudent: int,
    tightness: float,
    stafftightness: float,
    num_choices: int,
    minStaff: int,
    ratioProjectStaff: float,
    ratioStudentGeneral: float,
    equalCloseness: float,
    scale: float,
):
    noProject = math.ceil(noStudent * tightness)
    noStaff = math.ceil((noProject * stafftightness) / minStaff)
    print(f"project: {noProject} staff:{noStaff}")
    projectPop = [np.random.normal(scale=1.0) for i in range(noProject)]
    staffPop = [np.random.normal(scale=ratioProjectStaff) for i in range(noStaff)]
    staffLoadInit = [abs(np.random.normal()) for i in range(noStaff)]
    staffLoad = [float(i) / sum(staffLoadInit) for i in staffLoadInit]
    staffProjMap = {}
    j = 1
    for s, l in enumerate(staffLoad):
        for i in range(math.ceil(l * noProject)):
            if len(staffProjMap) >= noProject:
                break
            staffProjMap[j] = s + 1
            j += 1
    studentPreferences = defaultdict(list)
    for i in range(noStudent):
        projectFit = [
            ratioStudentGeneral * np.random.normal(scale=1.0)
            for i in range(len(projectPop))
        ]
        staffFit = [
            ratioStudentGeneral * np.random.normal(scale=ratioProjectStaff)
            for i in range(len(staffPop))
        ]
        totalStaffPref = np.add(staffPop, staffFit)
        totalProjPref = np.add(projectPop, projectFit)
        finalPref = np.add(
            totalProjPref,
            [totalStaffPref[staffProjMap[i + 1]] for i in range(noProject)],
        )
        finalPref = np.array([x / sum(finalPref) for x in finalPref])
        selectedProject = np.argsort(-finalPref)[:num_choices]
        studentPreferences[i] += [(selectedProject[0].item() + 1, 1)]
        rank = 1
        for j, (proj, prev_proj) in enumerate(
            zip(selectedProject[1:], selectedProject)
        ):
            x = random.random()
            rank = rank if scale * math.exp(-x * equalCloseness) > j + 1 else j + 2
            studentPreferences[i] += [((proj.item() + 1), rank)]
            if len({staffProjMap[b] for b, _ in studentPreferences[i]}) >= minStaff:
                break
    return studentPreferences, staffProjMap


# def test_configHeuristic():
#     a, b = createMockData(150, 1.5, 1.5, 10, 3, 1.4, 1.24, 3, 8)
#     c = configHeuristic(a, b)
#     assert c == Config(maxDepth=10, numRuns=30, defaultLoad=2, maxRank=3)


def test_splitProject():
    pref = {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]}
    staffPref = {1: [(2, 1), (1, 3)], 2: [(2, 1)], 3: [(1, 1)]}
    projStaff = {1: 1, 2: 2, 3: 3}
    result = splitProject([1], pref, projStaff, staffPref)
    expected = (
        ({1: [(1, 1), (2, 2), (3, 3), (4, 1)], 2: [(2, 1), (3, 2), (1, 3), (4, 3)]}),
        {1: 1, 2: 2, 3: 3, 4: 1},
        ({1: [(2, 1), (1, 3)], 2: [(2, 1)], 3: [(1, 1)], 4: [(2, 1), (1, 3)]}),
    )
    assert result == expected, "project split incorrect"
    pref = {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]}
    staffPref = {1: [(2, 1), (1, 3)], 2: [(2, 1)], 3: [(1, 1)]}
    projStaff = {1: 1, 2: 2, 3: 3}
    result = splitProject([1, 2], pref, projStaff, staffPref)
    expected = (
        (
            {
                1: [(1, 1), (2, 2), (3, 3), (4, 1), (5, 2)],
                2: [(2, 1), (3, 2), (1, 3), (4, 3), (5, 1)],
            }
        ),
        {1: 1, 2: 2, 3: 3, 4: 1, 5: 2},
        (
            {
                1: [(2, 1), (1, 3)],
                2: [(2, 1)],
                3: [(1, 1)],
                4: [(2, 1), (1, 3)],
                5: [(2, 1)],
            }
        ),
    )
    assert result == expected, "project split incorrect"
    pref = {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]}
    projStaff = {1: 1, 2: 2, 3: 3}
    result = splitProject([1, 2], pref, projStaff)
    expected = (
        (
            {
                1: [(1, 1), (2, 2), (3, 3), (4, 1), (5, 2)],
                2: [(2, 1), (3, 2), (1, 3), (4, 3), (5, 1)],
            }
        ),
        {1: 1, 2: 2, 3: 3, 4: 1, 5: 2},
        None,
    )
    assert result == expected, "project split incorrect"


def test_ShiftLoadMap():
    SPalloc = {
        StudentID(1): ProjectID(1),
        StudentID(2): ProjectID(2),
        StudentID(3): ProjectID(3),
    }
    projStaff = create_proj_staff([(1, 1), (2, 2), (3, 3), (4, 2)])
    loadMap = getLoadMap(projStaff, SPalloc)
    moves = [
        (StudentID(1), ProjectID(2)),
        (StudentID(2), ProjectID(3)),
        (StudentID(3), ProjectID(4)),
    ]
    ref = 2.0
    res_loadMap, cost = ShiftLoadMap(SPalloc, loadMap, moves, projStaff)
    assert res_loadMap == {
        StaffID(1): 0,
        StaffID(2): 2,
        StaffID(3): 1,
    }
    assert cost == ref


def test_unfair():
    input_dict = {
        1: [(2, 1), (1, 2), (3, 3)],
        2: [(1, 1), (3, 2), (2, 3)],
        3: [(2, 1), (3, 1), (1, 2)],
    }
    costMap = getCostMap(input_dict)
    projPref = getProjectPreferences(costMap)
    assert getUnfair(StudentID(1), ProjectID(3), projPref, costMap) == 3


def test_costMap():
    input_dict = {1: [(1, 1), (2, 2)], 2: [(4, 1), (3, 2)]}
    ref = {(1, 1): 1, (1, 2): 2, (2, 4): 1, (2, 3): 2, (1, 0): 100, (2, 0): 100}
    mockProjStaff = {ProjectID(i): StaffID(i) for i in range(1, 5)}
    costMap = getCostMap(input_dict)
    assert ref == costMap


def test_integration_linear_sum():
    numStudent = 150
    numProj = 200
    prefs, staffProjMap = createMockData(
        numStudent, numProj / numStudent, 15, 10, 4, 1.4, 2, 3.2, 8
    )
    cost = np.full((numStudent, len(staffProjMap)), 100)
    costMap = getCostMap(prefs)

    for (student, proj), value in costMap.items():
        cost[student - 1][proj - 1] = value
    cost[::, 0] = 20
    expected_student, expected_rank = linear_sum_assignment(cost)
    expected = {a + 1: b for a, b in zip(expected_student, expected_rank)}
    result, _ = driver(
        Test(
            "linear sum",
            prefs,
            None,
            staffProjMap,
            config=Config(
                defaultLoad=100,
                weightStaff=0,
                weightUnfair=0,
                weightVarLoad=0,
                numRuns=10,
                maxDepth=10,
            ),
        ),
        bestAllocate,
    )
    logging.debug(f"expected: {expected}")
    logging.debug(f"actual: {result}")
    assert sumCost(result, costMap) == cost[expected_student, expected_rank].sum()
    logging.debug(f"actual cost: {sumCost(result, costMap)}")
    logging.debug(f"expected cost: {cost[expected_student, expected_rank].sum()}")
    # assert expected == result


def test_custom_assert():
    testCases = [
        (
            Test(
                "cost Unalloc = 0 then everything is unalloc",
                {
                    1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                    2: [(4, 1), (3, 2), (1, 3), (2, 4)],
                    3: [(4, 1), (1, 2), (2, 3), (3, 4)],
                },
                None,
                [(i, i) for i in range(1, 5)],
                Config(costUnalloc=0),
            ),
            lambda x: sumCost(x[0], x[1]) == 0,
        ),
        (
            Test(
                "disallowed is not in alloc",
                {
                    1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                    2: [(4, 1), (3, 2), (1, 3), (2, 4)],
                    3: [(2, 1), (1, 2), (2, 3), (3, 4)],
                },
                None,
                [(i, i) for i in range(1, 5)],
                Config(disallowedMatching={StudentID(1): ProjectID(1)}),
            ),
            lambda x: x[0][StudentID(1)] != ProjectID(1),
        ),
        (
            Test(
                "forced is forced",
                {
                    1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                    2: [(4, 1), (3, 2), (1, 3), (2, 4)],
                    3: [(2, 1), (1, 2), (2, 3), (3, 4)],
                },
                None,
                [(i, i) for i in range(1, 5)],
                Config(forcedMatching={StudentID(1): ProjectID(4)}),
            ),
            lambda x: x[0][StudentID(1)] == ProjectID(4),
        ),
        (
            Test(
                "specialLoading is respected",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                None,
                [(1, 1), (2, 1), (3, 2)],
                Config(defaultLoad=2, specialLoading={StaffID(1): 1}),
            ),
            lambda x: getLoadMap(create_proj_staff([(1, 1), (2, 1), (3, 2)]), x[0])[
                StaffID(1)
            ]
            <= 1,
        ),
        (
            Test(
                "preferred is preferred",
                {
                    1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                    2: [(1, 1), (3, 2), (4, 3), (2, 4)],
                    3: [(2, 1), (1, 2), (4, 3), (3, 4)],
                },
                None,
                [(i, i) for i in range(1, 5)],
                Config(preferredStudent={StudentID(2): ProjectID(1)}),
            ),
            lambda x: x[0][StudentID(2)] == ProjectID(1),
        ),
        (
            Test(
                "preferred is preferred not forced",
                {
                    1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                    2: [(1, 1), (3, 2), (4, 3), (2, 4)],
                    3: [(2, 1), (1, 2), (4, 3), (3, 4)],
                },
                None,
                [(i, i) for i in range(1, 5)],
                Config(preferredStudent={StudentID(2): ProjectID(2)}),
            ),
            lambda x: x[0][StudentID(2)] != ProjectID(2),
        ),
    ]
    for test, condition in testCases:
        r, costMap = driver(test, bestAllocate)
        print(f"{test.name}: {r} {sumCost(r, costMap)}")
        assert condition((r, costMap)), f"{test.name} fails"


def test_integration_sumCost():
    testCases = [
        (
            Test(
                "Simple Case",
                {
                    1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                    2: [(4, 1), (3, 2), (1, 3), (2, 4)],
                    3: [(4, 1), (1, 2), (2, 3), (3, 4)],
                },
                None,
                [(i, i) for i in range(1, 5)],
                Config(defaultLoad=5),
            ),
            4,
        ),
        (
            Test(
                "Rotation Only Simple Case",
                {
                    1: [(1, 1), (2, 2), (3, 3)],
                    2: [(3, 1), (1, 2), (2, 3)],
                    3: [(1, 1), (2, 2), (3, 3)],
                },
                None,
                [(i, i) for i in range(1, 4)],
                Config(defaultLoad=5),
            ),
            4,
        ),
        (
            Test(
                "Non-restricted Loading Test",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                None,
                [(1, 1), (2, 1), (3, 2)],
                Config(defaultLoad=2),
            ),
            2,
        ),
        (
            Test(
                "Restricted Loading Test",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                None,
                [(1, 1), (2, 1), (3, 2)],
                Config(defaultLoad=1, numRuns=20),
            ),
            3,
        ),
        (
            Test(
                "Staff Preferences",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                {1: [(2, 1), (1, 3)], 2: [(2, 1)], 3: [(1, 1)]},
                [(1, 1), (2, 2), (3, 3)],
                Config(),
            ),
            4,
        ),
    ]
    for test, expectedCost in testCases:
        r, costMap = driver(test, bestAllocate)
        cost = sumCost(r, costMap)
        assert (
            cost == expectedCost
        ), f"bestAllocate {test.name} fails: get {cost} instead of {expectedCost}"
        r, costMap = driver(test, configSearch)
        cost = sumCost(r, costMap)
        assert (
            cost <= expectedCost
        ), f"configSearch {test.name} fails: get {cost} instead of {expectedCost}"


def driver(test_input: TestSet, function):
    print("test")
    name, pref, staff_pref, proj_details, config = test_input
    print(f"running test {name}")
    try:
        proj_staff = create_proj_staff(proj_details)
    except:
        proj_staff = proj_details
    costMap = getCostMap(pref, config=config)
    r = function(pref, proj_staff, staff_pref, config=config)
    if type(r) is tuple:
        _, r = r
    all_projects = list(filter((0).__ne__, list(r.values())))
    # ensure that no project is assigned twice
    assert len(set(all_projects)) == len(
        all_projects
    ), f"{name} fails: project is assigned twice"

    # ensure that there is no missing student
    assert set(pref.keys()) == set(r.keys())

    # ensure that the loading is followed
    assert checkload(getLoadMap(proj_staff, r), config)
    return r, costMap


test_custom_assert()