from enum import Enum
from ._static import Cell, Conveyor, Buffer, StationConveyor, LiftConveyor
from ._dynamic import Lift, Shuttle, Tray
from ._object import MSCObject, Command, Point
from _controller._controller import RequestType
from _util import Communicator, AppManager

def initalizeMSC(conveyors_map=None):
    if conveyors_map == None:
        conveyors_map = [
            [-1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, -2]
        ]
        """
        conveyors_map = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0],
            [-1, 1, 0, 0, 0, 0, 0, 0, 0, 1, -2],
        ]
        """

    def searchSource(conveyors_map):
        for row in range(map_nRows):
            for col in range(map_nCols):
                if conveyors_map[row][col] == -1:
                    return row, col

    def findConveyors(source, row, col, conveyors_map):
        D = [[-1, 0],
             [0, 1],
             [1, 0],
             [0, -1]]

        conveyor = source
        lanes = []
        while True:
            for d in D:
                _row = row + d[0]
                _col = col + d[1]
                if ((0 <= _row and _row < map_nRows)
                        and (0 <= _col and _col < map_nCols)):
                    if conveyors_map[_row][_col] > 1:
                        if conveyors_map[_row][_col] == 2:
                            isLeft = True
                        if conveyors_map[_row][_col] == 3:
                            isLeft = False

                        lane = Lane(laneId=len(lanes)+1, isLeft=isLeft)
                        lane.setLocation(Point(_col * 0.5, _row * 0.5))
                        lanes.append(lane)
                        _conveyor = StationConveyor(Point(_col * 0.5, _row * 0.5), lane.laneNum, lane.in_station.queues_[0],
                                                    lane.out_station.queues_[0])

                        _conveyor.setPrevious(conveyor)
                        conveyor.setNext(_conveyor)
                        conveyors_map[_row][_col] = 0
                        break

                    if conveyors_map[_row][_col] == 1:
                        _conveyor = Conveyor(location=Point(_col * 0.5, _row * 0.5))
                        _conveyor.setPrevious(conveyor)
                        conveyor.setNext(_conveyor)
                        conveyors_map[_row][_col] = 0
                        break

                    if conveyors_map[_row][_col] == -2:
                        _conveyor = Conveyor(location=Point(_col * 0.5, _row * 0.5))
                        _conveyor.setPrevious(conveyor)
                        conveyor.setNext(_conveyor)
                        conveyors_map[_row][_col] = 0
                        return MSC(lanes=lanes, source=source)

            conveyor = conveyor.next
            row = _row
            col = _col

    map_nRows = len(conveyors_map)
    map_nCols = len(conveyors_map[0])

    row, col = searchSource(conveyors_map)
    source = Conveyor(location=Point(col, row))

    return findConveyors(source, row, col, conveyors_map)

class MSC:
    def __init__(self, lanes, source):
        self.lanes = lanes
        self.source = source

    def update(self):
        conveyor = self.source
        while conveyor.next:
            conveyor.update()
            conveyor = conveyor.next

        if conveyor.tray:
            conveyor.tray.generatedLog(device="DEVICE_TYPE.RETRIEVAL", deviceId=conveyor.id)
            conveyor.tray = None
            AppManager.retrieval += 1
            _n_retrieval = AppManager.retrieval
            _n_time = (AppManager.time - AppManager.startTime).total_seconds() / 60
            retrieval_rate = _n_retrieval / _n_time
            AppManager.retrieval_rate = retrieval_rate
            if _n_retrieval % 100 == 0:
                print("Retrieval", _n_retrieval, _n_time, retrieval_rate)

        for lane in self.lanes:
            lane.update()

    def addTray(self, tray):
        if self.source.tray:
            # print("Queueing...")
            return False
        else:
            self.source.tray = tray
            tray.generatedLog(device=self.source.deviceType, deviceId=self.source.id)
            tray.setLocation(self.source.location)
            tray.startAt = AppManager.time
            return True

    def action(self, action):
        def r2r(c, floor_):
            guide = [0, -1, 1, -2]
            for k in range(floor_.bays):
                if c - k >= 0:
                    for b in guide:
                        cell = floor_.banks_[b].cells[c - k]
                        if not cell.isAlloc:
                            if not cell.tray:
                                return (b, c - k)

                if c + k < floor_.bays:
                    for b in guide:
                        cell = floor_.banks_[b].cells[c + k]
                        if not cell.isAlloc:
                            if not cell.tray:
                                return (b, c + k)

        (target, type) = action
        if type == RequestType.RETRIEVAL_SHUTTLE:
            lane = target.lane
            floor = target.floor
            b, c = target.cell
            if b == 0 or b == -1:
                if b == 0:
                    _cell = self.lanes[lane - 1].floors_[floor - 1].banks_[1].cells[c]
                else:
                    _cell = self.lanes[lane - 1].floors_[floor - 1].banks_[-2].cells[c]

                if _cell.tray:
                    _b, _c = r2r(c, self.lanes[lane - 1].floors_[floor - 1])
                    cell = self.lanes[lane - 1].floors_[floor - 1].banks_[_b].cells[_c]
                    _cell.activate()
                    cell.disabled()
                    command = Command(_cell, cell, Command.TYPE.R2R)
                    shuttle = self.lanes[lane - 1].floors_[floor - 1].shuttle
                    shuttle.addCommand(command)
                    AppManager.r2r += 1

            shuttle = self.lanes[lane - 1].floors_[floor - 1].shuttle
            cell = self.lanes[lane - 1].floors_[floor - 1].banks_[b].cells[c]
            cell.tray.startRetrieval()
            buffer = self.lanes[lane - 1].floors_[floor - 1].out_buffers_[0]
            command = Command(cell, buffer, Command.TYPE.RETRIEVAL)
            shuttle.addCommand(command)

        if type == RequestType.RETRIEVAL_LIFT:
            lane = target.lane
            floor = target.floor
            lift = self.lanes[lane - 1].out_station.lift
            lift_queue = self.lanes[lane - 1].out_station.queues_[-1]
            buffer = self.lanes[lane - 1].floors_[floor - 1].out_buffers_[0]
            command = Command(buffer, lift_queue, Command.TYPE.STORAGE)
            lift.addCommand(command)

        if type == RequestType.STORAGE_LIFT:
            lane = target.lane
            floor = target.floor
            lift = self.lanes[lane - 1].in_station.lift
            lift_queue = self.lanes[lane - 1].in_station.queues_[-1]
            buffer = self.lanes[lane - 1].floors_[floor - 1].in_buffers_[0]
            command = Command(lift_queue, buffer, Command.TYPE.STORAGE)
            lift.addCommand(command)

            return True
        if type == RequestType.STORAGE_SHUTTLE:
            lane = target.lane
            floor = target.floor
            b, c = target.cell
            shuttle = self.lanes[lane - 1].floors_[floor - 1].shuttle
            cell = self.lanes[lane - 1].floors_[floor - 1].banks_[b].cells[c]
            buffer = self.lanes[lane - 1].floors_[floor - 1].in_buffers_[0]
            command = Command(buffer, cell, Command.TYPE.STORAGE)
            shuttle.addCommand(command)

            return True

    @property
    def trays_(self):
        trays_ = []
        conveyor = self.source
        while conveyor.next:
            if conveyor.tray:
                tray = conveyor.tray
                trays_.append(tray)
            conveyor = conveyor.next

        lanes = self.lanes
        for lane in lanes:
            trays_.extend(lane.trays_)

        return trays_

    @property
    def lifts_(self):
        lifts_ = []
        for lane in self.lanes:
            lifts_.append(lane.in_station.lift)
            lifts_.append(lane.out_station.lift)

        return lifts_

    @property
    def shuttles_(self):
        shuttles_ = []
        for lane in self.lanes:
            for floor in lane.floors_:
                shuttles_.append(floor.shuttle)

        return shuttles_

    @property
    def properties(self):
        conveyor_properties = []
        conveyor = self.source
        while conveyor.next:
            conveyor_properties.append(conveyor.properties)
            conveyor = conveyor.next

        return {
            "trays" : [tray.properties for tray in self.trays_],
            "lanes": [lane.properties for lane in self.lanes],
            "conveyors": conveyor_properties
        }

    @property
    def numOfLanes(self):
        return len(self.lanes)

    @property
    def numOfFloors(self):
        return self.lanes[0].floors


class Lane(MSCObject):
    def __init__(self, laneId, floors=4, bays=36, banks=4, level=1, buffers=1, isLeft=True):
        super().__init__()
        self.id = "{0:02d}".format(laneId)
        self.laneNum = laneId
        self.floors = floors
        self.bays = bays
        self.banks = banks
        self.level = level
        self.buffers = buffers
        self.isLeft = False

        self.floors_ = [Floor(id=self.id + "{0:02d}".format(floor+1), bays=bays, banks=banks, level=level, buffers=buffers) for floor in
                        range(self.floors)]
        self.in_station = Station(id=self.id + "01", type=Station.TYPE.INPUT)
        self.out_station = Station(id=self.id + "02", type=Station.TYPE.OUTPUT)

        self.initialize()

    def initialize(self):
        self.in_station.setLocation(Point(1, 1.4))
        self.out_station.setLocation(Point(3, 1.6))
        for f, floor in enumerate(self.floors_):
            floor.setLocation(Point(f * 5, 6))

        if self.isLeft:
            self.flipHorizontal()

    def flipHorizontal(self):
        self.in_station.setLocation(Point(2, 3))
        self.out_station.setLocation(Point(1, 1))
        self.in_station.flipHorizontal()
        self.out_station.flipHorizontal()
        for f, floor in enumerate(self.floors_):
            floor.flipHorizontal()

        self.setLocation(self.location.flipHorizontal())

    def update(self):
        self.in_station.update(self)
        self.out_station.update(self)
        for floor in self.floors_:
            floor.update()

    @property
    def trays_(self):
        trays_ = []
        trays_.extend(self.in_station.trays_)
        trays_.extend(self.out_station.trays_)
        for floor in self.floors_:
            trays_.extend(floor.trays_)

        return trays_


    @property
    def properties(self):
        return {
            "id": self.id,
            "floors": [floor.properties for floor in self.floors_],
            "in_lane": self.in_station.properties,
            "out_lane": self.out_station.properties
        }


class Floor(MSCObject):
    def __init__(self, id, bays, banks, level, buffers):
        self.id = id
        self.bays = bays
        self.banks = banks
        self.level = level
        self.buffers = buffers
        self.banks_ = [Bank(id=self.id+"{0:01d}".format(b + 1), bays=self.bays, level=self.level) for b in range(self.banks)]
        self.in_buffers_ = [Buffer(id=self.id+"01") for b in range(self.buffers)]
        self.out_buffers_ = [Buffer(id=self.id+"02") for b in range(self.buffers)]

        self.shuttle = Shuttle(id=self.id+"0001", location=Point(2, 0))

        self.initialize()

    def initialize(self):
        for b, buffer in enumerate(self.in_buffers_):
            buffer.setLocation(Point(1, b))
        for b, buffer in enumerate(self.out_buffers_):
            buffer.setLocation(Point(3, b))

        for b, bank in enumerate(self.banks_[:2]):
            bank.setLocation(Point(b, self.buffers))
        for b, bank in enumerate(self.banks_[2:]):
            bank.setLocation(Point(b + 3, self.buffers))

    def flipHorizontal(self):
        for b, bank in enumerate(self.banks_):
            bank.flipHorizontal()
        for b, buffer in enumerate(self.in_buffers_):
            buffer.flipHorizontal()
        for b, buffer in enumerate(self.out_buffers_):
            buffer.flipHorizontal()

        for b, buffer in enumerate(self.in_buffers_):
            buffer.setLocation(Point(b, 3))
        for b, buffer in enumerate(self.out_buffers_):
            buffer.setLocation(Point(b, 1))
        self.shuttle.flipHorizontal()

        self.setLocation(self.location.flipHorizontal())

    def setLocation(self, location):
        super().setLocation(location)
        for b, bank in enumerate(self.banks_):
            bank.setRelativity(location)
        for b, buffer in enumerate(self.in_buffers_):
            buffer.setRelativity(location)
        for b, buffer in enumerate(self.out_buffers_):
            buffer.setRelativity(location)
        self.shuttle.setRelativity(location)

    def setRelativity(self, relativity):
        super().setRelativity(relativity)
        for b, bank in enumerate(self.banks_):
            bank.setRelativity(self.position)
        for b, buffer in enumerate(self.in_buffers_):
            buffer.setRelativity(self.position)
        for b, buffer in enumerate(self.out_buffers_):
            buffer.setRelativity(self.position)
        self.shuttle.setRelativity(self.position)

    def update(self):
        self.shuttle.update()

        for b, bank in enumerate(self.banks_):
            bank.update()

        in_buffer = self.in_buffers_[0]
        if in_buffer.update():
            request = (in_buffer.tray, RequestType.STORAGE_SHUTTLE)
            Communicator.addRequest(request)

        out_buffer = self.out_buffers_[0]
        if out_buffer.update():
            request = (out_buffer.tray, RequestType.RETRIEVAL_LIFT)
            Communicator.addRequest(request)


    @property
    def trays_(self):
        trays_ = []

        if self.shuttle.tray:
            tray = self.shuttle.tray
            trays_.append(tray)

        for buffer in self.in_buffers_:
            if buffer.tray:
                tray = buffer.tray
                trays_.append(tray)

        for buffer in self.out_buffers_:
            if buffer.tray:
                tray = buffer.tray
                trays_.append(tray)

        for bank in self.banks_:
            for cell in bank.cells:
                if cell.tray:
                    tray = cell.tray
                    trays_.append(tray)

        return trays_


    @property
    def properties(self):
        return {
            "banks": [bank.properties for bank in self.banks_],
            "in_buffers": [buffer.properties for buffer in self.in_buffers_],
            "out_buffers": [buffer.properties for buffer in self.out_buffers_],
            "shuttle": self.shuttle.properties
        }


class Bank(MSCObject):
    def __init__(self, id, bays, level):
        self.id = id
        self.bays = bays
        self.level = level
        self.cells = [Cell(id=self.id+"{0:01d}{0:02d}".format(1, x+1), location=Point(0, x)) for x in range(self.bays)]

    def flipHorizontal(self):
        for cell in self.cells:
            cell.flipHorizontal()

        self.setLocation(self.location.flipHorizontal())

    def setLocation(self, location):
        super().setLocation(location)
        for cell in self.cells:
            cell.setRelativity(location)

    def setRelativity(self, relativity):
        super().setRelativity(relativity)
        for cell in self.cells:
            cell.setRelativity(self.position)

    def update(self):
        for cell in self.cells:
            cell.update()

    @property
    def properties(self):
        return {
            "cells": [cell.properties for cell in self.cells]
        }


class Station(MSCObject):
    class TYPE(Enum):
        INPUT = 100
        OUTPUT = 200

    def __init__(self, id, queues=3, type=TYPE.INPUT):
        self.id = id
        self.queues = queues
        self.type = type
        self.queues_ = [Conveyor(id=self.id + "{0:04d}".format(q+1), location=Point(0, q)) for q in range(self.queues-1)]
        self.queues_.append(LiftConveyor(id=self.id + "{0:04d}".format(self.queues), location=Point(0, self.queues-1)))

        if type == Station.TYPE.INPUT:
            for q in range(0, self.queues-1):
                self.queues_[q].setNext(self.queues_[q + 1])
            for q in range(1, self.queues):
                self.queues_[q].setPrevious(self.queues_[q-1])

        else:
            for q in range(0, self.queues-1):
                self.queues_[q].setPrevious(self.queues_[q + 1])
            for q in range(1, self.queues):
                self.queues_[q].setNext(self.queues_[q-1])

        self.lift = Lift(id=self.id, location=Point(0, self.queues))

    def flipHorizontal(self):
        for queue in self.queues_:
            queue.flipHorizontal()
        self.lift.flipHorizontal()

        self.setLocation(self.location.flipHorizontal())

    def setLocation(self, location):
        super().setLocation(location)
        for queue in self.queues_:
            queue.setRelativity(location)
        self.lift.setRelativity(location)

    def setRelativity(self, relativity):
        super().setRelativity(relativity)
        for queue in self.queues_:
            queue.setRelativity(self.position)
        self.lift.setRelativity(self.position)

    def update(self, msc):
        for queue in self.queues_[:-1]:
            queue.update()

        lift_queue = self.queues_[-1]
        if lift_queue.update():
            request = (lift_queue.tray, RequestType.STORAGE_LIFT)
            Communicator.addRequest(request)

        self.lift.update()

    @property
    def trays_(self):
        trays = []

        if self.lift.tray:
            tray = self.lift.tray
            trays.append(tray)

        for queue in self.queues_:
            if queue.tray:
                tray = queue.tray
                trays.append(tray)

        return trays


    @property
    def properties(self):
        return {
            "lift": self.lift.properties,
            "queues": [queue_.properties for queue_ in self.queues_]
        }
