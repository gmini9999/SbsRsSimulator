from enum import Enum
from ._object import DynamicObject, Point, DEVICE_TYPE, Command
from _util import Caller, AppManager


# Conveyor 너무 빠름
# SHUTTLE 조금 빠름 #3배 느리게

SPEED = 5
SPEED_TRAY = (1 / (2/0.1)) * SPEED
SPEED_SHUTTLE = (1 / (0.3/0.1)) * SPEED
SPEED_LIFT = (5 / (1/0.1)) * SPEED

class Tray(DynamicObject):
    ID = 0
    class LOG:
        def __init__(self, device, deviceId, timestamp):
            self.device = device
            self.deviceId = deviceId
            self.timestamp = timestamp

    class COMMAND:
        NONE = 100
        STORAGE = 200
        RETRIEVAL = 300

    def __init__(self, GDS, location=None):
        Tray.ID = Tray.ID + 1
        super().__init__(location, speed=SPEED_TRAY)
        self.id = Tray.ID
        self.GDS = GDS
        self.lane = None
        self.floor = None
        self.cell = None
        self.command = Tray.COMMAND.NONE

        self.startAt = None
        self.endAt = None

        self.reward1 = 0
        self.reward2 = 0
        self.reward3 = 0

    def startStorage(self):
        self.command = Tray.COMMAND.STORAGE

    def endStorage(self):
        self.command = Tray.COMMAND.NONE

    def startRetrieval(self):
        self.command = Tray.COMMAND.RETRIEVAL

    def endRetrieval(self):
        self.command = Tray.STATUS.NONE

    def setAllocation(self, lane=None, floor=None, cell=None):
        if lane != None:
            self.lane = lane
        if floor != None:
            self.floor = floor
        if cell != None:
            self.cell = cell

    def generatedLog(self, device, deviceId):
        timestamp = AppManager.time
        AppManager.addTrayLog(self.id, device, deviceId, timestamp)
        # log = Tray.LOG(device, deviceId, timestamp)
        # self.logs.append(log)
        #
        # return log

    @property
    def isStorage(self):
        if self.command == Tray.COMMAND.STORAGE:
            return True
        return False

    @property
    def isRetrieval(self):
        if self.command == Tray.COMMAND.RETRIEVAL:
            return True
        return False

    @property
    def properties(self):
        return {
            "id": self.id,
            "lane": self.lane,
            "floor": self.floor,
            "cell": self.cell,
            "GDS": self.GDS,
            "isStorage": self.isStorage,
            "isRetrieval": self.isRetrieval
        }


class Lift(DynamicObject):
    class LOG:
        def __init__(self, command, timestamp):
            sender = command.sender
            receiver = command.receiver
            self.fromdevice = sender.deviceType
            self.fromdeviceId = sender.id
            self.todevice = receiver.deviceType
            self.todeviceId = receiver.id
            self.type = command.type
            self.timestamp = timestamp

    def __init__(self, id, location=None):
        self.id = "L" + str(id)
        super().__init__(location, speed=SPEED_LIFT)
        self.home_location = location
        self.deviceType = DEVICE_TYPE.LIFT
        self.tray = None
        self.status = DynamicObject.STATUS.STOP
        self.commands = []

    def addCommand(self, command):
        self.commands.append(command)

    def generatedLog(self, command):
        timestamp = AppManager.time
        sender = command.sender
        receiver = command.receiver
        fromDevice = sender.deviceType
        fromDeviceId = sender.id
        toDeivce = receiver.deviceType
        toDeviceId = receiver.id
        type = command.type

        AppManager.addLiftLog(self.id, fromDevice, fromDeviceId, toDeivce, toDeviceId, type, timestamp)
        # self.logs.append(Lift.LOG(command, timestamp))

    def update(self):
        super().update()
        if self.commands:
            command = self.commands[0]
            caller = command.caller
            deliver_position = Point(caller.position.x - self.relativity.x, self.location.y)

            if Caller.action(command, self, caller, deliver_position):
                return True
            else:
                self.generatedLog(command)
                del self.commands[0]

    @property
    def properties(self):
        direction = 0
        location = abs(self.location.x - self.home_location.x)
        if self.commands:
            if self.commands[0].status == Command.STATUS.SENDER:
                direction = 1
            if self.commands[0].status == Command.STATUS.RECEIVER:
                direction = 2

        returnTime = location / 5
        if self.commands:
            command = self.commands[0]
            sender = command.sender
            receiver = command.receiver
            sender_location = sender.position.x - self.relativity.x
            receiver_location = receiver.position.x - self.relativity.x
            if self.commands[0].status == Command.STATUS.SENDER:
                returnTime = (abs(receiver_location - sender_location) * 2 + location) / 5
            if self.commands[0].status == Command.STATUS.RECEIVER:
                returnTime = (abs(receiver_location - sender_location) * 2 - location) / 5

            if returnTime < 0:
                print("error")

        return {
            "id": self.id,
            "location": location,
            "direction": direction,
            "numOfCommand": len(self.commands),
            "returnTime": returnTime
        }


class Shuttle(DynamicObject):
    class LOG:
        def __init__(self, command, timestamp):
            sender = command.sender
            receiver = command.receiver
            self.fromdevice = sender.deviceType
            self.fromdeviceId = sender.id
            self.todevice = receiver.deviceType
            self.todeviceId = receiver.id
            self.type = command.type
            self.timestamp = timestamp

    def __init__(self, id, location=None):
        super().__init__(location, speed=SPEED_SHUTTLE)
        self.id = "S" + str(id)
        self.home_location = location
        self.deviceType = DEVICE_TYPE.SHUTTLE
        self.tray = None
        self.status = DynamicObject.STATUS.STOP
        self.commands = []

    def addCommand(self, command):
        self.commands.append(command)

    def generatedLog(self, command):
        timestamp = AppManager.time
        sender = command.sender
        receiver = command.receiver
        fromDevice = sender.deviceType
        fromDeviceId = sender.id
        toDeivce = receiver.deviceType
        toDeviceId = receiver.id
        type = command.type

        AppManager.addShuttleLog(self.id, fromDevice, fromDeviceId, toDeivce, toDeviceId, type, timestamp)
        # self.logs.append(Shuttle.LOG(command, timestamp))


    def update(self):
        super().update()
        if self.commands:
            command = self.commands[0]
            caller = command.caller
            deliver_position = Point(self.location.x, caller.position.y - self.relativity.y)

            if Caller.action(command, self, caller, deliver_position):
                return True
            else:
                self.generatedLog(command)
                del self.commands[0]

    @property
    def properties(self):
        direction = 0
        location = abs(self.location.y - self.home_location.y)
        if self.commands:
            if self.commands[0].status == Command.STATUS.SENDER:
                direction = 1
            if self.commands[0].status == Command.STATUS.RECEIVER:
                direction = 2

        returnTime = location
        if self.commands:
            command = self.commands[0]
            sender = command.sender
            receiver = command.receiver
            sender_location = sender.position.y - self.relativity.y
            receiver_location = receiver.position.y - self.relativity.y
            if command.type == Command.TYPE.R2R:
                if command.status == Command.STATUS.SENDER:
                    returnTime = abs(receiver_location - sender_location) * 2 + abs(receiver_location - location)
                if command.status == Command.STATUS.RECEIVER:
                    returnTime = abs(receiver_location - sender_location) * 2 - abs(receiver_location - location)
                last_location = receiver_location

                if returnTime < 0:
                    print(location, sender_location, receiver_location, returnTime)
                    print("error")

                command = self.commands[1]
                sender = command.sender
                receiver = command.receiver
                sender_location = sender.position.y - self.relativity.y
                receiver_location = receiver.position.y - self.relativity.y
                returnTime += (abs(receiver_location - sender_location) * 2 + last_location)
            else:
                if command.status == Command.STATUS.SENDER:
                    returnTime = (abs(receiver_location - sender_location) * 2 + location)
                if command.status == Command.STATUS.RECEIVER:
                    returnTime = (abs(receiver_location - sender_location) * 2 - location)

            if returnTime < 0:
                print(location, sender_location, receiver_location, returnTime)
                print("error2")

        return {
            "id": self.id,
            "location": abs(self.location.x - self.home_location.x) / 5,
            "direction": direction,
            "numOfCommand": len(self.commands),
            "returnTime": returnTime
        }
