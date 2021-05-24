from app.allocation import *

# for testing
def randomPref(
    numStudent: int, numProject: int
) -> Dict[StudentID, List[Tuple[ProjectID, int]]]:
    projectList = list()
    res = {}
    for i in range(numProject):
        projectList.append(ProjectID(i + 1))

    for i in range(numStudent):
        projectPref: List[Tuple[ProjectID, int]] = []
        j = 1
        for s in random.sample(projectList, 5):
            projectPref += [(s, j)]
            j = j + 1 if random.random() < 0.7 else j
        res[StudentID(i + 1)] = projectPref
    return res


def create_proj_staff(l_in):
    out = {}
    for (l, v) in l_in:
        out[ProjectID(l)] = StaffID(v)
    return out
