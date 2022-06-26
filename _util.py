import datetime
import pandas as pd
import json
import pyodbc
from _getData import getRecordFloor, getRecordLane
from _env._object import DynamicObject, Command, DEVICE_TYPE
from _model._agent import LaneAgent, MemoryManager, FloorAgent
from _controller._controller import RequestType

class Communicator:
    requests = []

    @staticmethod
    def addRequest(request):
        Communicator.requests.append(request)

    @staticmethod
    def removeRequest(request):
        Communicator.requests.remove(request)
        (target, type) = request
        if type == RequestType.RETRIEVAL_SHUTTLE:
            AppManager.last_retrieval = AppManager.time

    @staticmethod
    def reset():
        Communicator.requests.clear()

class Caller:
    @staticmethod
    def transfer(sender, receiver):
        if sender:
            if sender.tray:
                if receiver:
                    if receiver.tray:
                        return False
                    else:
                        tray = sender.tray
                        if tray.status == DynamicObject.STATUS.STOP:
                            tray.setDestination(sender.position, receiver.position)
                            if (receiver.deviceType == DEVICE_TYPE.LIFT_CONVEYOR or
                                receiver.deviceType == DEVICE_TYPE.LIFT or
                                receiver.deviceType == DEVICE_TYPE.BUFFER or
                                receiver.deviceType == DEVICE_TYPE.SHUTTLE or
                                receiver.deviceType == DEVICE_TYPE.CELL):
                                tray.generatedLog(device=receiver.deviceType, deviceId=receiver.id)

                            if tray.isStorage:
                                if receiver.deviceType == DEVICE_TYPE.LIFT:
                                    tray.startAt = AppManager.time
                                    tray.reward1 = AppManager.time
                                if receiver.deviceType == DEVICE_TYPE.BUFFER:
                                    reward1 = (AppManager.time - tray.reward1).total_seconds()
                                    tray.reward1 = reward1
                                    AppManager.addReward1(tray.id, reward1)

                                    tray.reward2 = AppManager.time
                                if receiver.deviceType == DEVICE_TYPE.SHUTTLE:
                                    reward2 = (AppManager.time - tray.reward2).total_seconds()
                                    tray.reward2 = reward2
                                    AppManager.addReward2(tray.id, reward2)

                                    tray.reward3 = AppManager.time

                                if receiver.deviceType == DEVICE_TYPE.CELL:
                                    reward3 = (AppManager.time - tray.reward3).total_seconds()
                                    tray.reward3 = reward3
                                    AppManager.addReward3(tray.id, reward3)

                                    tray.reward3 = AppManager.time

                                    tray.endAt = AppManager.time
                                    endAtCell = tray.endAt
                                    elapseTimeForCell = (tray.endAt - tray.startAt).total_seconds()
                                    AppManager.updateStateLog(tray.id, endAtCell, elapseTimeForCell)

                            return False

                        if tray.status == DynamicObject.STATUS.MOVING:
                            tray.update()
                            return False

                        if tray.status == DynamicObject.STATUS.ARRIVED:
                            tray.setStop()
                            receiver.tray = tray
                            sender.tray = None
                            return True

    @staticmethod
    def delivery(deliver, deliver_location):
        if deliver.status == DynamicObject.STATUS.STOP:
            deliver.setDestination(deliver.location, deliver_location)
            return False

        if deliver.status == DynamicObject.STATUS.ARRIVED:
            return True


    @staticmethod
    def action(command, deliver, caller, deliver_position):
        if command.status == Command.STATUS.NONE:
            command.next()
            return True

        if command.status == Command.STATUS.SENDER:
            if Caller.delivery(deliver, deliver_position):
                if Caller.transfer(caller, deliver):
                    deliver.setStop()
                    command.next()
            else:
                if deliver.tray:
                    deliver.tray.location = deliver.position
            return True

        if command.status == Command.STATUS.RECEIVER:
            if Caller.delivery(deliver, deliver_position):
                if Caller.transfer(deliver, caller):
                    deliver.setStop()
                    return False
            else:
                if deliver.tray:
                    deliver.tray.location = deliver.position

        return True

class AppManager:
    time = datetime.datetime.now()
    startTime = time
    delta = datetime.timedelta(seconds=0.5)
    storage = 0
    retrieval = 0
    r2r = 0
    statue = ""
    storage_rate = 0
    retrieval_rate = 0
    rr = 0
    rr_ = [0, 0, 0, 0]

    @staticmethod
    def reset():
        AppManager.time = datetime.datetime.now()
        AppManager.startTime = AppManager.time
        AppManager.last_state_trayId = [None, None, None, None]
        AppManager.storage = 0
        AppManager.retrieval = 0
        AppManager.r2r = 0
        AppManager.rr = 0
        AppManager.rr_ = [0, 0, 0, 0]
        AppManager.last_retrieval = AppManager.time
        MemoryManager.reset()
        Communicator.reset()

    @staticmethod
    def initialize():
        AppManager.laneAgent = LaneAgent()
        AppManager.floorAgent = FloorAgent()
        AppManager.time = datetime.datetime.now()
        AppManager.startTime = AppManager.time
        AppManager.last_state_trayId = [None, None, None, None]
        AppManager.episode = 1
        AppManager.storage = 0
        AppManager.retrieval = 0
        AppManager.r2r = 0
        AppManager.rr = 0
        AppManager.rr_ = [0, 0, 0, 0]
        AppManager.last_retrieval = AppManager.time
        AppManager.conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=./log/msc.accdb;'
        )
        AppManager.connection = pyodbc.connect(AppManager.conn_str)
        AppManager.cursor = AppManager.connection.cursor()

        sql = "DELETE FROM lift"
        AppManager.cursor.execute(sql)

        sql = "DELETE FROM shuttle"
        AppManager.cursor.execute(sql)

        sql = "DELETE FROM tray"
        AppManager.cursor.execute(sql)

        sql = "DELETE FROM state"
        AppManager.cursor.execute(sql)

    @staticmethod
    def commitDB():
        AppManager.connection.commit()

    @staticmethod
    def initializeTime():
        AppManager.time = datetime.datetime.now()

    @staticmethod
    def updateTime():
        AppManager.time += AppManager.delta

    def default(o):
        if type(o) is datetime.date or type(o) is datetime.datetime:
            return o.isoformat()

    @staticmethod
    def addTrayLog(trayId, device, deviceId, timestamp):
        sql = "Insert into tray (episodeNum, trayId, device, deviceId, startAt) values ('{}', '{}', '{}', '{}', '{}')".format(AppManager.episode, trayId, device, deviceId, timestamp)
        AppManager.cursor.execute(sql)

    @staticmethod
    def addLiftLog(lifId, fromDevice, fromDeviceId, toDeivce, toDeviceId, type, timestamp):
        sql = "Insert into lift (episodeNum, liftId, fromDevice, fromDeviceId, toDevice, toDeviceId, type, startAt) values ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(AppManager.episode, lifId, fromDevice, fromDeviceId, toDeivce, toDeviceId, type, timestamp)
        AppManager.cursor.execute(sql)

    @staticmethod
    def addShuttleLog(ShuttleId, fromDevice, fromDeviceId, toDeivce, toDeviceId, type, timestamp):
        sql = "Insert into shuttle (episodeNum, ShuttleId, fromDevice, fromDeviceId, toDevice, toDeviceId, type, startAt) values ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
            AppManager.episode, ShuttleId, fromDevice, fromDeviceId, toDeivce, toDeviceId, type, timestamp)
        AppManager.cursor.execute(sql)

    @staticmethod
    def addStateLog(episodeNum, requestSequence, trayId, lane, startAt, record):
        sql = "Insert into state (episodeNum, requestSequence, trayId, lane, startAt"
        for key in record:
            sql = sql + ", {}".format(key)
        sql += ") values ('{}', '{}', '{}', '{}', '{}'".format(episodeNum, requestSequence, trayId, lane, startAt)
        for key in record:
            sql = sql + ", '{}'".format(record[key])
        sql += ")"
        AppManager.cursor.execute(sql)

    @staticmethod
    def updateStateLog(trayId, endAtLift, elapseTimeForLift):
        sql = "Update state set endAtLift='{}', elapseTimeForLift='{}' where episodeNum={} and trayId={}".format(
            endAtLift, elapseTimeForLift, AppManager.episode, trayId)
        AppManager.cursor.execute(sql)

    @staticmethod
    def addState(trayId, startAt, state, lane):
        if AppManager.last_state_trayId[lane - 1]:
            AppManager.addNextState(AppManager.last_state_trayId[lane - 1], state, lane)

        AppManager.last_state_trayId[lane - 1] = trayId
        record = getRecordFloor(state, lane)
        MemoryManager.addMemory(trayId, startAt)
        MemoryManager.updateMemory(trayId, "state", record)

    @staticmethod
    def addNextState(trayId, nextState, lane):
        record = getRecordFloor(nextState, lane)
        MemoryManager.updateMemory(trayId, "nextState", record)

    @staticmethod
    def addAction(trayId, action):
        MemoryManager.updateMemory(trayId, "action", action)

    @staticmethod
    def addReward1(trayId, reward1):
        MemoryManager.updateMemory(trayId, "reward1", reward1)

    @staticmethod
    def addReward2(trayId, reward2):
        MemoryManager.updateMemory(trayId, "reward2", reward2)

    @staticmethod
    def addReward3(trayId, reward3):
        MemoryManager.updateMemory(trayId, "reward3", reward3)

    @staticmethod
    def addReward(trayId, reward):
        MemoryManager.updateMemory(trayId, "reward", reward)

    @staticmethod
    def isDone(trayId):
        for trayId in AppManager.last_state_trayId:
            if trayId:
                MemoryManager.updateMemory(trayId, "done", 1)

    """
    @staticmethod
    def addState(trayId, startAt, state):
        record = getRecord(state)
        numOfConveyorForLane_1 = record["numOfConveyorForLane_1"]
        numOfWaitInStation_1 = record["numOfWaitInStation_1"]
        numOfWaitInLane_1 = record["numOfWaitInLane_1"]
        numOfWaitForLane_1 = record["numOfWaitForLane_1"]
        returnTimeInLift_1 = record["returnTimeInLift_1"]

        numOfConveyorForLane_2 = record["numOfConveyorForLane_2"]
        numOfWaitInStation_2 = record["numOfWaitInStation_2"]
        numOfWaitInLane_2 = record["numOfWaitInLane_2"]
        numOfWaitForLane_2 = record["numOfWaitForLane_2"]
        returnTimeInLift_2 = record["returnTimeInLift_2"]

        numOfConveyorForLane_3 = record["numOfConveyorForLane_3"]
        numOfWaitInStation_3 = record["numOfWaitInStation_3"]
        numOfWaitInLane_3 = record["numOfWaitInLane_3"]
        numOfWaitForLane_3 = record["numOfWaitForLane_3"]
        returnTimeInLift_3 = record["returnTimeInLift_3"]

        numOfConveyorForLane_4 = record["numOfConveyorForLane_4"]
        numOfWaitInStation_4 = record["numOfWaitInStation_4"]
        numOfWaitInLane_4 = record["numOfWaitInLane_4"]
        numOfWaitForLane_4 = record["numOfWaitForLane_4"]
        returnTimeInLift_4 = record["returnTimeInLift_4"]

        sql = "Insert into state (episodeNum, trayId, startAt, numOfConveyorForLane_1, numOfWaitInStation_1, numOfWaitInLane_1, numOfWaitForLane_1, returnTimeInLift_1, numOfConveyorForLane_2, numOfWaitInStation_2, numOfWaitInLane_2, numOfWaitForLane_2, returnTimeInLift_2, numOfConveyorForLane_3, numOfWaitInStation_3, numOfWaitInLane_3, numOfWaitForLane_3, returnTimeInLift_3, numOfConveyorForLane_4, numOfWaitInStation_4, numOfWaitInLane_4, numOfWaitForLane_4, returnTimeInLift_4) values ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
            AppManager.episode, trayId, startAt, numOfConveyorForLane_1, numOfWaitInStation_1, numOfWaitInLane_1, numOfWaitForLane_1, returnTimeInLift_1, numOfConveyorForLane_2, numOfWaitInStation_2, numOfWaitInLane_2, numOfWaitForLane_2, returnTimeInLift_2, numOfConveyorForLane_3, numOfWaitInStation_3, numOfWaitInLane_3, numOfWaitForLane_3, returnTimeInLift_3, numOfConveyorForLane_4, numOfWaitInStation_4, numOfWaitInLane_4, numOfWaitForLane_4, returnTimeInLift_4)
        AppManager.cursor.execute(sql)

    @staticmethod
    def getState(episodeNum):
        sql = "Select * from state where episodeNum = {} ORDER BY trayId".format(episodeNum)
        return pd.read_sql(sql, AppManager.connection)

    @staticmethod
    def getReward(episodeNum):
        sql = "Select trayId, startAt from tray where episodeNum = {} and device = 'DEVICE_TYPE.LIFT' ORDER BY trayId".format(episodeNum)
        return pd.read_sql(sql, AppManager.connection)

    @staticmethod
    def getAction(episodeNum):
        sql = "Select trayId, deviceId from tray where episodeNum = {} and device = 'DEVICE_TYPE.LIFT' ORDER BY trayId".format(episodeNum)
        df = pd.read_sql(sql, AppManager.connection)
        df["reward"] = df["deviceId"].str.slice(start=1, stop=2).astype(int)
        return pd.read_sql(sql, AppManager.connection)

    """
    @staticmethod
    def exportLog(log, filepath="./log/state/", filename="log.json"):
        filename_ = filepath + filename
        with open(filename_, "w") as json_file:
            json.dump(log, json_file, default=AppManager.default)

    @staticmethod
    def exportLogOfTrays(env, filepath="./log/object"):
        df = pd.DataFrame()
        logs = env.exportLogOfTrays()
        for log in logs:
            df = df.append(log, ignore_index=True)

        filename_ = filepath + "/" + "_trays.csv"
        df.to_csv(filename_)
        return

    @staticmethod
    def exportLogOfLifts(env, filepath="./log/object"):
        df = pd.DataFrame()
        logs = env.exportLogOfLifts()
        for log in logs:
            df = df.append(log, ignore_index=True)

        filename_ = filepath + "/" + "_lifts.csv"
        df.to_csv(filename_)
        return

    @staticmethod
    def exportLogOfShuttles(env, filepath="./log/object"):
        df = pd.DataFrame()
        logs = env.exportLogOfShuttles()
        for log in logs:
            df = df.append(log, ignore_index=True)

        filename_ = filepath + "/" + "_shuttles.csv"
        df.to_csv(filename_)
        return

    @staticmethod
    def exportEnv(env, filepath="./_log"):
        df = pd.DataFrame()
        history = env.exportHistory()
        idx = 0
        for (msc, timestamp) in history:
            log = msc.properties
            log["timestamp"] = str(timestamp)
            idx = idx + 1
            filename_ = filepath + "/log_" + str(idx) + ".json"
            value = dict()
            value["timestamp"] = str(timestamp)
            for lane in log["lanes"]:
                for floor in lane["floors"]:
                    shuttle = floor["shuttle"]
                    value[str(shuttle["id"]) + "shuttle_numOfCommand"] = shuttle["numOfCommand"]
                    value[str(shuttle["id"]) + "shuttle_location"] = shuttle["location"]

                in_lift = lane["in_station"]["lift"]
                value[str(in_lift["id"]) + "in_lift_numOfCommand"] = in_lift["numOfCommand"]
                value[str(in_lift["id"]) + "in_lift_location"] = in_lift["location"]

                out_lift = lane["out_station"]["lift"]
                value[str(out_lift["id"]) + "out_lift_numOfCommand"] = out_lift["numOfCommand"]
                value[str(out_lift["id"]) + "out_lift_location"] = out_lift["location"]

            df = df.append(value, ignore_index=True)

            with open(filename_, "w") as json_file:
                json.dump(log, json_file, default=AppManager.default)

        df.to_csv("./_log/_log.csv")

    @staticmethod
    def importEnv(env, filename):
        with open(filename, "r") as json_file:
            log = json.load(filename)

        return env