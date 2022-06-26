import json
from ._controller import RequestType

def isTrayByGDS(target, floor_):
    guide = [1, -2, 0, -1]
    for c in range(floor_.bays):
        for b in guide:
            cell = floor_.banks_[b].cells[c]
            if cell.tray:
                if cell.isAlloc:
                    if cell.tray.GDS == target.GDS:
                        return True

    return False


def getTargetLane(target, env):
    msc = env.msc
    value = -1
    result = -1
    max_command = 1
    for (lane, lane_) in enumerate(msc.lanes):
        _value = 0
        _isTray = False
        for (floor, floor_) in enumerate(lane_.floors_):
            _value += len(floor_.shuttle.commands)
            if isTrayByGDS(target, floor_):
                n_command = len(floor_.shuttle.commands)
                buffer = floor_.out_buffers_[-1]
                if n_command < max_command and not buffer.tray:
                    _isTray = True

        if _isTray:
            if value == -1 or _value < value:
                value = _value
                result = lane + 1

    return result

def getTargetFloor(target, env):
    msc = env.msc
    value = -1
    result = -1
    max_command = 1

    lane = target.lane
    lane_ = msc.lanes[lane - 1]
    for (floor, floor_) in enumerate(lane_.floors_):
        if isTrayByGDS(target, floor_):
            n_command = len(floor_.shuttle.commands)
            buffer = floor_.out_buffers_[-1]
            if n_command < max_command and not buffer.tray:
                if value == -1 or n_command < value:
                    value = n_command
                    result = floor + 1

    return result

def getTargetCell(target, env):
    floor_ = env.msc.lanes[target.lane - 1].floors_[target.floor - 1]
    guide = [1, -2, 0, -1]
    for c in range(floor_.bays):
        for b in guide:
            cell = floor_.banks_[b].cells[c]
            if cell.tray:
                if cell.isAlloc:
                    if cell.tray.GDS == target.GDS:
                        cell.activate()
                        return (b, c)

    return -1

"""
def isTrayByGDS(target, floor_):
    guide = [1, -2, 0, -1]
    for c in range(floor_.bays):
        for b in guide:
            cell = floor_.banks_[b].cells[c]
            if cell.tray:
                if cell.isAlloc:
                    if cell.tray.GDS == target.GDS:
                        return True
                if cell.tray.GDS == target.GDS:
                    return False

    return False

def getTargetLaneAndFloor(target, env):
    msc = env.msc
    value = -1
    max_command = 1
    for (lane, lane_) in enumerate(msc.lanes):
        for (floor, floor_) in enumerate(lane_.floors_):
            if isTrayByGDS(target, floor_):
                n_command = len(floor_.shuttle.commands)
                buffer = floor_.out_buffers_[-1]
                if n_command < max_command and not buffer.tray:
                    if value == -1 or n_command < value:
                        value = n_command
                        target.lane = lane + 1
                        target.floor = floor + 1

    if value != -1:
        target.cell = getTargetCell(target, env)
    else:
        target.cell = -1

    return target

def getTargetLane(target, env):
    storage = env.exportStorage()
    storageLanes = storage["storageOfLanes"]
    storageByTray = env.exportStorageByTray(target.GDS)
    storageLanesByTray = storageByTray["storageOfLanes"]
    result = 0
    for (lane, count) in enumerate(storageLanesByTray):
        if count > storageLanesByTray[result]:
            result = lane

        if count == storageLanesByTray[result] and storageLanes[lane] > storageLanes[result]:
            result = lane

    return result + 1

def getTargetFloor(target, env):
    storage = env.exportStorage()
    storageFloors = storage["storageOfFloors"][target.lane - 1]
    storageByTray = env.exportStorageByTray(target.GDS)
    storageFloorsByTray = storageByTray["storageOfFloors"][target.lane - 1]
    result = 0
    for (floor, count) in enumerate(storageFloorsByTray):
        if count > storageFloorsByTray[result]:
            result = floor

        if count == storageFloorsByTray[result] and storageFloors[floor] > storageFloors[result]:
            result = floor

    return result + 1

def getTargetCell(target, env):
    floor_ = env.msc.lanes[target.lane - 1].floors_[target.floor - 1]
    guide = [1, -2, 0, -1]
    for c in range(floor_.bays):
        for b in guide:
            cell = floor_.banks_[b].cells[c]
            if cell.tray:
                if cell.isAlloc:
                    if cell.tray.GDS == target.GDS:
                        cell.activate()
                        return (b, c)

    return -1
"""

def retrieval(request, env):
    (target, type) = request
    result = {
        "request": (target, type),
        "result": None}

    if type == RequestType.NONE:
        return result
    if type == RequestType.RETRIEVAL_SHUTTLE:
        target.lane = getTargetLane(target, env)
        if target.lane != -1:
            target.floor = getTargetFloor(target, env)
        else:
            target.floor = -1
        if target.floor != -1:
            target.cell = getTargetCell(target, env)
        else:
            target.cell = -1

    if target.cell == -1:
        return False

    result["result"] = target
    return result