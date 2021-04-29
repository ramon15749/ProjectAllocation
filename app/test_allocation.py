from app.allocation import *
import pytest
import numpy as np
from pprint import pprint
from scipy.optimize import linear_sum_assignment
import logging
import random
from app.test_util import randomPref, create_proj_prof

TestSet = NewType(
    "TestSet",
    Tuple[
        str,
        Dict[StudentID, List[Tuple[ProjectID, int]]],
        Dict[ProjectID, ProfID],
        Config,
    ],
)
Test: TestSet = namedtuple("TestSet", ["name", "pref", "proj_details", "defaultLoad"])


def test_costMap():
    input_dict = {1: [(1, 1), (2, 2)], 2: [(4, 1), (3, 2)]}
    ref = {(1, 1): 1, (1, 2): 2, (2, 4): 1, (2, 3): 2, (1, 0): 100, (2, 0): 100}
    mockProjProf = {ProjectID(i): ProfID(i) for i in range(1, 5)}
    costMap = getCostMap(input_dict)
    assert ref == costMap


def test_integration_linear_sum():
    numStudent = 50
    numProj = 70
    prefs = randomPref(numStudent, numProj)
    cost = np.full((numStudent, numProj + 1), 100)
    costMap = getCostMap(prefs)

    for (student, proj), value in costMap.items():
        cost[student - 1][proj] = value
    cost[::, 0] = 20
    expected_student, expected_rank = linear_sum_assignment(cost)
    expected = {a + 1: b for a, b in zip(expected_student, expected_rank)}

    mockProjProf = {ProjectID(i): ProfID(i) for i in range(1, numProj + 1)}
    studentProjectList = {
        student: [proj for proj, _ in projList] for student, projList in prefs.items()
    }
    result = allocate(studentProjectList, mockProjProf, Config(), costMap)
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
                [(i, i) for i in range(1, 5)],
                Config(forcedMatching={StudentID(1): ProjectID(4)}),
            ),
            lambda x: x[0][StudentID(1)] == ProjectID(4),
        ),
        (
            Test(
                "specialLoading is respected",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                [(1, 1), (2, 1), (3, 2)],
                Config(defaultLoad=2, specialLoading={ProfID(1): 1}),
            ),
            lambda x: getLoadMap(create_proj_prof([(1, 1), (2, 1), (3, 2)]), x[0])[
                ProfID(1)
            ]
            <= 1,
        ),
    ]
    for test, condition in testCases:
        r, costMap = driver(test)
        print(f"{test.name}: {sumCost(r, costMap)}")
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
                [(i, i) for i in range(1, 5)],
                Config(defaultLoad=5),
            ),
            4,
        ),
        (
            Test(
                "Non-restricted Loading Test",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                [(1, 1), (2, 1), (3, 2)],
                Config(defaultLoad=2),
            ),
            2,
        ),
        (
            Test(
                "Restricted Loading Test",
                {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
                [(1, 1), (2, 1), (3, 2)],
                Config(defaultLoad=1, numRuns=20),
            ),
            3,
        ),
    ]
    for test, expectedCost in testCases:
        r, costMap = driver(test)
        cost = sumCost(r, costMap)
        assert (
            cost == expectedCost
        ), f"{test.name} fails: get {cost} instead of {expectedCost}"


def driver(test_input: TestSet):
    name, pref, proj_details, config = test_input
    proj_prof = create_proj_prof(proj_details)
    stu_proj = {
        student: [proj for proj, _ in projList] for student, projList in pref.items()
    }
    costMap = getCostMap(pref, config.costUnalloc)
    r = bestAllocate(stu_proj, proj_prof, config, costMap)
    all_projects = list(filter((0).__ne__, list(r.values())))
    assert len(set(all_projects)) == len(
        all_projects
    ), f"{name} fails: project is assigned twice"
    # ensure that no project is assigned twice
    return r, costMap


test_property()