import pandas as pd
import json
import datetime

def getDistanceToLane(conveyors, laneId):
    count = 0
    for conveyor in conveyors:
        count += 1
        if 'laneId' in conveyor:
            if conveyor["laneId"] == laneId:
                return count

def getNumTrayMovingForLane(conveyors, laneId):
    count = 0
    for conveyor in conveyors:
        if conveyor["tray"]:
            count += 1
        if 'laneId' in conveyor:
            if conveyor["laneId"] == laneId:
                return count


def getNumTrayAsgnToLane(conveyors, laneId):
    count = 0
    for conveyor in conveyors:
        if conveyor["tray"]:
            if conveyor["tray"]["lane"] == laneId:
                count += 1
        if 'laneId' in conveyor:
            if conveyor["laneId"] == laneId:
                return count

def getNumTrayStation(station):
    count = 0
    for conveyor in station["queues"]:
        if conveyor["tray"]:
            count += 1

    return count

def getNumTrayBuffer(buffers):
    count = 0
    for buffer in buffers:
        if buffer["tray"]:
            count += 1

    return count

def getRecordFloor(state, lane):
    record = {}
    for floor in range(1, 5):
        record["numTray_InBuffer_{}_{}".format(lane, floor)] = getNumTrayBuffer(state["lanes"][lane - 1]["floors"][floor - 1]["in_buffers"]) / len(state["lanes"][lane - 1]["floors"][floor - 1]["in_buffers"])
        record["numTray_OutBuffer_{}_{}".format(lane, floor)] = getNumTrayBuffer(state["lanes"][lane - 1]["floors"][floor - 1]["out_buffers"]) / len(state["lanes"][lane - 1]["floors"][floor - 1]["in_buffers"])
        record["waitingTime_Shuttle_{}_{}".format(lane, floor)] = state["lanes"][lane - 1]["floors"][floor - 1]["shuttle"]["returnTime"] / (36 * 2)
        record["numCommand_Shuttle_{}_{}".format(lane, floor)] = state["lanes"][lane - 1]["floors"][floor - 1]["shuttle"]["numOfCommand"] / 2
    return record

def getRecordLane(state):
    record = {}
    for lane in range(1, 5):
        record["distanceToLane_{}".format(lane)] = getDistanceToLane(state["conveyors"], lane) / len(state["conveyors"])
        record["numTrayMovingForLane_{}".format(lane)] = getNumTrayMovingForLane(state["conveyors"], lane) / len(state["conveyors"])
        record["numTrayAsgnToLane_{}".format(lane)] = getNumTrayAsgnToLane(state["conveyors"], lane) / len(state["conveyors"])
        record["numTray_InStation_{}".format(lane)] = getNumTrayStation(state["lanes"][lane - 1]["in_lane"]) / len(state["lanes"][lane - 1]["in_lane"])
        record["numTray_OutStation_{}".format(lane)] = getNumTrayStation(state["lanes"][lane - 1]["out_lane"]) / len(state["lanes"][lane - 1]["out_lane"])
        record["waitingTime_InLift_{}".format(lane)] = state["lanes"][lane - 1]["in_lane"]["lift"]["returnTime"] / (3 * 2 * 5)
        record["waitingTime_OutLift_{}".format(lane)] = state["lanes"][lane - 1]["out_lane"]["lift"]["returnTime"] / (3 * 2 * 5)
        for floor in range(1, 5):
            record["numTray_InBuffer_{}_{}".format(lane, floor)] = getNumTrayBuffer(state["lanes"][lane - 1]["floors"][floor - 1]["in_buffers"]) / len(state["lanes"][lane - 1]["floors"][floor - 1]["in_buffers"])
            record["numTray_OutBuffer_{}_{}".format(lane, floor)] = getNumTrayBuffer(state["lanes"][lane - 1]["floors"][floor - 1]["out_buffers"]) / len(state["lanes"][lane - 1]["floors"][floor - 1]["in_buffers"])
            record["waitingTime_Shuttle_{}_{}".format(lane, floor)] = state["lanes"][lane - 1]["floors"][floor - 1]["shuttle"]["returnTime"] / (36 * 2)
            record["numCommand_Shuttle_{}_{}".format(lane, floor)] = state["lanes"][lane - 1]["floors"][floor - 1]["shuttle"]["numOfCommand"] / 2
    return record

"""
def getRecord_ETC(trayId, lane, startAt, state):
    record = {
        "trayId": trayId,
        "lane": lane,
        "startAt": startAt,
        "numOfCoveyorForLane": getCountConveyor(state["conveyors"], lane),
        "numOfWaitInStation": getTraysForStation(state["lanes"][lane - 1]["in_lane"]),
        "numOfWaitInLane": getTraysForLaneToLane(state["conveyors"], lane),
        "numOfWaitForLane": getTraysForLane(state["conveyors"], lane),
        "distanceInLift": state["lanes"][lane - 1]["in_lane"]["lift"]["location"],
        "directionInLift": state["lanes"][lane - 1]["in_lane"]["lift"]["direction"]
    }
    return record
"""

"""
def getRecord(state):
    record = {}
    for lane in range(1, 5):
        record["distanceToLane_{}".format(lane)] = getDistanceToLane(state["trays"], lane) / (36 * 4 * 4)
        record["numTrayMovingForLane_{}".format(lane)] = getNumTrayMovingForLane(state["conveyors"], lane) / len(state["conveyors"])
        record["numTrayAsgnToLane_{}".format(lane)] = getNumTrayAsgnToLane(state["conveyors"], lane) / len(state["conveyors"])
        record["numTray_InStation_{}".format(lane)] = getNumTrayStation(state["lanes"][lane - 1]["in_lane"]) / len(state["lanes"][lane - 1]["in_lane"])
        record["numTray_OutStation_{}".format(lane)] = getNumTrayStation(state["lanes"][lane - 1]["out_lane"]) / len(state["lanes"][lane - 1]["out_lane"])
        record["waitingTime_InLift_{}".format(lane)] = state["lanes"][lane - 1]["in_lane"]["lift"]["returnTime"] / (3 * 3 + 2 * 2)
        record["waitingTime_OutLift_{}".format(lane)] = state["lanes"][lane - 1]["out_lane"]["lift"]["returnTime"] / (3 * 3 + 2 * 2)
        for floor in range(1, 5):
            record["numTray_InBuffer_{}_{}".format(lane, floor)] = getNumTrayBuffer(state["lanes"][lane - 1][floor - 1]["in_buffers"]) / len(state["lanes"][lane - 1][floor - 1]["in_buffers"])
            record["numTray_OutBuffer_{}_{}".format(lane, floor)] = getNumTrayBuffer(state["lanes"][lane - 1][floor - 1]["out_buffers"]) / len(state["lanes"][lane - 1][floor - 1]["out_buffers"])
            record["waitingTime_Shuttle_{}_{}".format(lane, floor)] = state["lanes"][lane - 1][floor - 1]["shuttle"]["returnTime"] / (3 * 3 + 2 * 2)
            record["numCommand_Shuttle_{}_{}".format(lane, floor)] = state["lanes"][lane - 1][floor - 1]["shuttle"]["numOfCommand"] / (3 * 3 + 2 * 2)
                        3 * 3 + 2 * 2)
    return record
"""
