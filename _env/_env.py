import random
from _util import Communicator, AppManager
from _controller.storage_basic import storage
from _controller.retreival_basic import retrieval
from _controller._controller import RequestType
from ._dynamic import Tray
from ._object import Order
from _getData import getRecordFloor, getRecordLane
import json

lanes = 4
floors = 4
bays = 15
banks = 4
level = 1
n_storage = int(lanes * floors * bays * banks * level)
n_GDS = int(n_storage / 10)
count = [0 for gds in range(n_GDS)]

def initialize_Order(scenario):
    filename_ = "./scenario.config"
    with open(filename_, "r") as json_file:
        _order = json.load(json_file)

    scenario_type = "test"
    scenario_num = AppManager.episode % 5
    orders_ = []
    for GDS in _order[scenario_type][scenario_num]["STORAGE"]:
        orders_.append(Order(GDS, Order.Type.STORAGE))
    for GDS in _order[scenario_type][scenario_num]["RETRIEVAL"]:
        orders_.append(Order(GDS, Order.Type.RETRIEVAL))

    return orders_

def initialize_Store(msc):
    filename_ = "./scenario.config"
    with open(filename_, "r") as json_file:
        _order = json.load(json_file)
    _msc = _order["initial"]
    guide = [0, -1, 1, -2]
    for (lane, lane_) in enumerate(msc.lanes):
        for (floor, floor_) in enumerate(lane_.floors_):
            trays = _msc[lane][floor]
            for c in range(floor_.bays):
                if not trays:
                    break
                for b in guide:
                    if not trays:
                        break
                    tray = Tray(trays.pop(0))
                    tray.lane = lane + 1
                    tray.floor = floor + 1
                    tray.cell = (b, c)

                    cell = floor_.banks_[b].cells[c]
                    cell.tray = tray
                    cell.tray.location = cell.position
                    cell.disabled()

class Environment:
    def __init__(self, msc):
        self.msc = msc
        self.scenario = 0
        self.orders_ = initialize_Order(scenario=self.scenario)
        self.storage_ = []
        self.retrieval_ = []

        initialize_Store(self.msc)
        while self.orders_:
            order = self.orders_[0]
            if order.type == Order.Type.STORAGE:
                self.storage_.append(Tray(order.GDS))
            if order.type == Order.Type.RETRIEVAL:
                self.retrieval_.append(order.GDS)
            del self.orders_[0]

    def wait_request(self):
        for request in Communicator.requests:
            (tray, type) = request
            if type == RequestType.RETRIEVAL_LANE or type == RequestType.RETRIEVAL_LIFT or type == RequestType.RETRIEVAL_SHUTTLE:
                result = retrieval(request, self)
                if result:
                    Communicator.removeRequest(request)
                    (target, type) = request
                    result = result["result"]
                    if type == RequestType.RETRIEVAL_SHUTTLE:
                        target = result
                    if type == RequestType.RETRIEVAL_LIFT:
                        target = result

                    action = (target, type)
                    self.msc.action(action)
                """
                else:
                    print("Abnormal termination...")
                    return False
                """

            else:
                result = storage(request, self)
                if result:
                    Communicator.removeRequest(request)
                    (target, type) = request
                    result = result["result"]
                    if type == RequestType.STORAGE_LANE:
                        target.lane = result
                        self.exportState(request, result, target.lane)
                    if type == RequestType.STORAGE_LIFT:
                        target.floor = result
                        self.exportState(request, result, target.lane)
                        AppManager.addAction(target.id, result - 1)
                    if type == RequestType.STORAGE_SHUTTLE:
                        target.cell = result

                    action = (target, type)
                    self.msc.action(action)

                else:
                    print("Abnormal termination...")
                    return False
        return True

    def isFinish(self):
        for tray in self.msc.trays_:
            if tray.isStorage or tray.isRetrieval:
                return False

        if self.storage_:
            return False
        if self.retrieval_:
            return False
        if self.orders_:
            return False

        return True

    def Storage(self):
        if self.storage_:
            tray = self.storage_[0]
            tray.startStorage()
            if self.msc.addTray(tray):
                request = (tray, RequestType.STORAGE_LANE)
                Communicator.addRequest(request)
                AppManager.storage += 1
                del self.storage_[0]

            return True

    def Retrieval(self):
        if self.retrieval_:
            interval = 4
            time = (AppManager.time - AppManager.last_retrieval).total_seconds()
            if time < interval:
                return False

            for request in Communicator.requests:
                (tray, type) = request
                if type == RequestType.RETRIEVAL_LANE or type == RequestType.RETRIEVAL_LIFT or type == RequestType.RETRIEVAL_SHUTTLE:
                    return False

            GDS = self.retrieval_[0]
            target = Tray(GDS)
            request = (target, RequestType.RETRIEVAL_SHUTTLE)
            Communicator.addRequest(request)
            del self.retrieval_[0]

            return True

    def update(self):
        self.Storage()
        self.Retrieval()

        self.msc.update()
        if not self.wait_request():
            return -1

        if self.isFinish():
            return True
        else:
            return False

    @property
    def state_(self):
        state = getRecordLane(self.msc.properties)
        return state

    def state_floor_(self, lane):
        state = getRecordFloor(self.msc.properties, lane)
        return state

    def exportState(self, request, result, lane):
        (target, type) = request
        if type == RequestType.STORAGE_LANE:
            _n_storage = AppManager.storage
            _n_time = (AppManager.time - AppManager.startTime).total_seconds() / 60
            _n_storage_rate = _n_storage / _n_time
            AppManager.storage_rate = _n_storage_rate

            if _n_storage % 100 == 0:
                print("STORAGE", _n_storage, _n_time, _n_storage_rate)

            if not self.storage_:
                print("done")
                AppManager.isDone(target.id)

        if type == RequestType.STORAGE_LIFT:
            AppManager.addState(target.id, AppManager.time, self.msc.properties, lane)
            AppManager.addStateLog(AppManager.episode, AppManager.storage, target.id, result, AppManager.time,
                                   self.state_)

    """
    def exportLog(self, request, result):
        (target, type) = request
        filename = ""
        if type == RequestType.STORAGE_LANE:
            filename = "state_lane" + "{0:04d}".format(target.id)
            _log = self.msc.properties
        if type == RequestType.STORAGE_LIFT:
            filename = "state_lift" + "{0:04d}".format(target.id)
            _log = self.msc.lanes[target.lane - 1].properties
        if type == RequestType.STORAGE_SHUTTLE:
            filename = "state_shuttle" + "{0:04d}".format(target.id)
            _log = self.msc.lanes[target.lane - 1].floors_[target.floor - 1].properties

        log = {
            "timestamp": AppManager.time,
            "trayId": target.id,
            "result": result["result"],
            "state": _log
        }

        AppManager.exportLog(log=log, filename=filename + ".json")
    """

    def exportStorageLog(self, request):
        (target, type) = request
        _log = self.exportStorageByTray(target.GDS)
        filename = ""
        if type == RequestType.STORAGE_LANE:
            filename = "storage_lane" + "{0:04d}".format(target.id)
        elif type == RequestType.STORAGE_LIFT:
            filename = "storage_lane" + "{0:04d}".format(target.id)
        else:
            return
        log = {
            "timestamp": AppManager.time,
            "trayId": target.id,
            "GDS": target.GDS,
            "storage": _log
        }
        AppManager.exportLog(log=log, filepath="./log/storage/", filename=filename + ".json")

    def exportStorage(self):
        lanes = self.msc.numOfLanes
        floors = self.msc.numOfFloors
        storageOfLanes = [0 for lane in range(lanes)]
        storageOfFloors = [[0 for floor in range(floors)] for lane in range(lanes)]
        for tray in self.msc.trays_:
            if not tray.isRetrieval:
                if tray.lane:
                    storageOfLanes[tray.lane - 1] += 1
                    if tray.floor:
                        storageOfFloors[tray.lane - 1][tray.floor - 1] += 1

        return {"storageOfLanes": storageOfLanes,
                "storageOfFloors": storageOfFloors}

    def exportStorageByTray(self, GDS):
        lanes = self.msc.numOfLanes
        floors = self.msc.numOfFloors
        storageOfLanes = [0 for lane in range(lanes)]
        storageOfFloors = [[0 for floor in range(floors)] for lane in range(lanes)]
        for tray in self.msc.trays_:
            if not tray.isRetrieval:
                if tray.GDS == GDS:
                    if tray.lane:
                        storageOfLanes[tray.lane - 1] += 1
                        if tray.floor:
                            storageOfFloors[tray.lane - 1][tray.floor - 1] += 1

        return {"storageOfLanes": storageOfLanes,
                "storageOfFloors": storageOfFloors}

    def importEnv(self, filename):
        return
