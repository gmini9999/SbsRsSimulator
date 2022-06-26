import json
import random

from ._controller import RequestType
from _util import AppManager
import torch
import numpy as np

def getTargetLane(target, env):
    storage = env.exportStorage()
    storageLanes = np.array(storage["storageOfLanes"])
    max_storage = (36 * 4 * 4) * 0.9
    error_index = np.where(storageLanes >= max_storage)

    state = torch.tensor(list(env.state_.values()))
    value = AppManager.laneAgent.select_action(state)
    min_value = np.min(value)
    value[error_index] = min_value - 1.0
    result = np.argmax(value) + 1

    if 1 <= result and result <= 4:
        return result
    else:
        print(result)
        return -1

def getTargetFloor(target, env):
    lane = target.lane - 1
    storage = env.exportStorage()
    storageFloors = np.array(storage["storageOfFloors"][lane])
    max_storage = (36 * 4) * 0.95
    error_index = np.where(storageFloors >= max_storage)

    state = torch.tensor(list(env.state_floor_(lane + 1).values()))
    value = AppManager.floorAgent.select_action(state)
    min_value = np.min(value)
    value[error_index] = min_value - 1.0
    result = np.argmax(value) + 1

    if 1 <= result and result <= 4:
        return result
    else:
        print(result)
        return -1

def getTargetCell(target, env):
    floor_ = env.msc.lanes[target.lane - 1].floors_[target.floor - 1]
    guide = [0, -1, 1, -2]
    for c in range(floor_.bays):
        for b in guide:
            cell = floor_.banks_[b].cells[c]
            if not cell.isAlloc:
                if not cell.tray:
                    cell.disabled()
                    return (b, c)

    return -1


def storage(request, env):
    (target, type) = request
    result = {
        "request": (target, type),
        "result": None}

    if type == RequestType.NONE:
        return result
    if type == RequestType.STORAGE_LANE:
        result["result"] = getTargetLane(target, env)
        if result["result"] == -1:
            return False
    if type == RequestType.STORAGE_LIFT:
        result["result"] = getTargetFloor(target, env)
        if result["result"] == -1:
            return False
    if type == RequestType.STORAGE_SHUTTLE:
        result["result"] = getTargetCell(target, env)
        if result["result"] == -1:
            return False

    return result