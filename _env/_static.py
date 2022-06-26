from ._object import StaticObject, DEVICE_TYPE
from _util import Caller, AppManager

class Conveyor(StaticObject):
    ID = 0
    def __init__(self, id=None, location=None):
        if id:
            self.id = id
        else:
            Conveyor.ID = Conveyor.ID + 1
            self.id = "C{0:04d}".format(Conveyor.ID)

        super().__init__(location)
        self.deviceType = DEVICE_TYPE.CONVEYOR
        self.next = None
        self.previous = None
        self.tray = None

    def setNext(self, next):
        self.next = next

    def setPrevious(self, previous):
        self.previous = previous

    def update(self):
        if self.tray:
            if self.next:
                return Caller.transfer(self, self.next)

        return False

    @property
    def properties(self):
        return {
            "id": self.id,
            "tray": self.tray.properties if self.tray else None
        }


class Cell(StaticObject):
    def __init__(self, id, location=None):
        super().__init__(location)
        self.id = "F" + str(id)
        self.deviceType = DEVICE_TYPE.CELL
        self.tray = None
        self.isAlloc = False

    def disabled(self):
        self.isAlloc = True

    def activate(self):
        self.isAlloc = False

    def update(self):
        if self.tray:
            if self.tray.isStorage:
                self.tray.endStorage()

    @property
    def properties(self):
        return {
            "id": self.id,
            "tray": self.tray.properties if self.tray else None
        }


class StationConveyor(Conveyor):
    def __init__(self, location, laneId, in_station_coveyor, out_station_conveyor):
        super().__init__(location=location)
        self.laneId = laneId
        self.deviceType = DEVICE_TYPE.STATION_CONVEYOR
        self.in_station_coveyor = in_station_coveyor
        self.out_station_conveyor = out_station_conveyor

        self.priority = None

    def update(self):
        if self.tray:
            if self.tray.lane == self.laneId:
                if not self.in_station_coveyor.tray:
                    self.tray.location = self.in_station_coveyor.position
                    self.in_station_coveyor.tray = self.tray
                    self.tray = None
            else:
                if self.priority == "conveyor" or not self.priority:
                    self.priority = "conveyor"
                    if super().update():
                        if self.out_station_conveyor.tray:
                            self.priority = "station"
                        else:
                            self.priority = None
        else:
            if self.out_station_conveyor.tray:
                self.priority = "station"
            else:
                self.priority = None

        if self.out_station_conveyor.tray:
            if not self.next.tray:
                if self.priority == "station" or not self.priority:
                    self.priority = "station"
                    self.out_station_conveyor.tray.location = self.next.position
                    self.next.tray = self.out_station_conveyor.tray
                    self.out_station_conveyor.tray = None
                    if self.tray:
                        if self.tray.lane != self.laneId:
                            self.priority = "conveyor"
                        else:
                            self.priority = None
                    else:
                        self.priority = None
        else:
            if self.tray:
                if self.tray.lane != self.laneId:
                    self.priority = "conveyor"
                else:
                    self.priority = None
            else:
                self.priority = None

    @property
    def properties(self):
        return {
            "id": self.id,
            "laneId" : self.laneId,
            "tray": self.tray.properties if self.tray else None
        }


class LiftConveyor(Conveyor):
    def __init__(self, id, location):
        super().__init__(id=id, location=location)
        self.deviceType = DEVICE_TYPE.LIFT_CONVEYOR
        self.status = StaticObject.STATUS.NONE

    def update(self):
        super().update()
        if self.tray:
            if self.tray.floor:
                if self.status == StaticObject.STATUS.REQUEST:
                    self.status = StaticObject.STATUS.WAITING
                else:
                    self.status = StaticObject.STATUS.NONE
            else:
                if self.status == StaticObject.STATUS.NONE:
                    self.status = StaticObject.STATUS.REQUEST
                    return True

        return False

    @property
    def properties(self):
        return {
            "id": self.id,
            "tray": self.tray.properties if self.tray else None
        }


class Buffer(Cell):
    def __init__(self, id, location=None):
        super().__init__(id=id, location=location)
        self.id = "B" + str(id)
        self.deviceType = DEVICE_TYPE.BUFFER
        self.status = StaticObject.STATUS.NONE

    def update(self):
        if self.tray:
            if self.status == StaticObject.STATUS.NONE:
                self.status = StaticObject.STATUS.REQUEST
                return True
        else:
            self.status = StaticObject.STATUS.NONE

        return False

    @property
    def properties(self):
        return {
            "id": self.id,
            "tray": self.tray.properties if self.tray else None
        }