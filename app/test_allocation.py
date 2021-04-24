from allocation import *
import pytest
import numpy as np
from pprint import pprint
from scipy.optimize import linear_sum_assignment
import logging
from test_util import randomPref, create_proj_prof

TestSet = NewType(
    "TestSet",
    Tuple[
        str,
        Dict[StudentID, List[Tuple[ProjectID, int]]],
        Dict[ProjectID, ProfID],
        int,
        int,
    ],
)
Test: TestSet = namedtuple(
    "TestSet", ["name", "pref", "proj_details", "defaultLoad", "expectedCost"]
)


def test_costMap():
    input_dict = {1: [(1, 1), (2, 2)], 2: [(4, 1), (3, 2)]}
    ref = {(1, 1): 1, (1, 2): 2, (2, 4): 1, (2, 3): 2, (1, 0): 100, (2, 0): 100}
    mockProjProf = {ProjectID(i): ProfID(i) for i in range(1, 5)}
    costMap = getCostMap(input_dict)
    assert ref == costMap


def test_integration_linear_sum():
    numStudent = 5
    numProj = 7
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
    result = allocate(studentProjectList, mockProjProf, Config(defaultLoad=1), costMap)
    logging.debug(f"expected: {expected}")
    logging.debug(f"actual: {result}")
    assert sumCost(result, costMap) == cost[expected_student, expected_rank].sum()
    logging.debug(f"actual cost: {sumCost(result, costMap)}")
    logging.debug(f"expected cost: {cost[expected_student, expected_rank].sum()}")
    # assert expected == result


def test_integration_given_case_1():
    testCases = [
        Test(
            "Simple Case",
            {
                1: [(1, 1), (2, 2), (3, 3), (4, 4)],
                2: [(4, 1), (3, 2), (1, 3), (2, 4)],
                3: [(4, 1), (1, 2), (2, 3), (3, 4)],
            },
            [(i, i) for i in range(1, 5)],
            5,
            4,
        ),
        Test(
            "Non-restricted Loading Test",
            {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
            [(1, 1), (2, 1), (3, 2)],
            2,
            2,
        ),
        Test(
            "Restricted Loading Test",
            {1: [(1, 1), (2, 2), (3, 3)], 2: [(2, 1), (3, 2), (1, 3)]},
            [(1, 1), (2, 1), (3, 2)],
            1,
            3,
        ),
    ]
    driver(testCases)


def driver(test_inputs: List[TestSet]):
    for name, pref, proj_details, defaultLoad, resultCost in test_inputs:
        proj_prof = create_proj_prof(proj_details)
        stu_proj = {
            student: [proj for proj, _ in projList]
            for student, projList in pref.items()
        }
        costMap = getCostMap(pref)
        cost = 100
        result1 = None
        for i in range(5):
            r = allocate(stu_proj, proj_prof, Config(defaultLoad=defaultLoad), costMap)
            result1 = r if sumCost(r, costMap) < cost else result1
            cost = sumCost(r, costMap) if sumCost(r, costMap) < cost else cost
        assert cost == resultCost, f"{name} fails: get {cost} instead of {resultCost}"
