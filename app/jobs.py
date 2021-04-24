from flask_rq2 import RQ
from rq import get_current_job
import random
import consts

from allocation import *

rq = RQ()
rq.redis_url = 'redis://redis:6379/0'


# the timeout parameter specifies how long a job may take
# to execute before it is aborted and regardes as failed
@rq.job(timeout=180)
def approximate_pi(num_iterations):
    """ approximate Pi by using monte carlo method
    """

    # get a reference to the job we are currently in
    # to send back status reports
    self_job = get_current_job()

    inside = 0
    for i in range(1, num_iterations + 1):        # start from 1 to get round numbers in the progress information
        x, y = random.random(), random.random()
        dist = x**2 + y**2
        if dist <= 1.0:
            inside += 1

        # update meta information on every 1000 iterations
        if i % 1000 == 0:
            self_job.meta['progress'] = {'num_iterations': num_iterations, 'iteration': i, 'percent': i / num_iterations * 100}
            # save meta information to queue
            self_job.save_meta()

    pi = 4.0 * inside / num_iterations
    return pi

@rq.job(timeout=1000)
def run_allocation(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    ProjProfMap: Dict[ProjectID, ProfID],
    config: Config,
) -> Dict[StudentID, ProjectID]:
    costMap = getCostMap(studentPreferences)
    bestResult: Dict[StudentID, ProjectID] = {}
    bestCost: float = float("inf")

    self_job = get_current_job()

    for i in range(config.numRuns):
        defaultProjProfMap = defaultdict(int, ProjProfMap)
        res = allocate(studentPreferences, defaultProjProfMap, config, costMap)
        cost = sumCost(res, costMap)
        if cost < bestCost:
            bestCost = cost
            bestResult = res
        # update meta information on every iteration
        self_job.meta['progress'] = {'num_iterations': config.numRuns, 'iteration': i, 'percent': i / config.numRuns * 100}
        # save meta information to queue
        self_job.save_meta()
    return bestResult

