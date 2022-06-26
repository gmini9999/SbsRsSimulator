from enum import Enum
import math
import time

class Point:
    def __init__(self, x=None, y=None):
        self.x = 0 if x==None else x
        self.y = 0 if y==None else y

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return Point(x, y)

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return Point(x, y)

    def __mul__(self, other):
        x = self.x * other
        y = self.y * other
        return Point(x, y)

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False

    def flipHorizontal(self):
        return Point(self.x * -1, self.y)

class Command:
    class TYPE(Enum):
        STORAGE = 100
        RETRIEVAL = 200
        R2R = 300

    class STATUS(Enum):
        NONE = 0
        SENDER = 100
        RECEIVER = 200

    def __init__(self, sender, receiver, type):
        self.sender = sender
        self.receiver = receiver
        self.type = type
        self.status = Command.STATUS.NONE

    def next(self):
        if self.status == Command.STATUS.NONE:
            self.status = Command.STATUS.SENDER
        elif self.status == Command.STATUS.SENDER:
            self.status = Command.STATUS.RECEIVER

    @property
    def caller(self):
        if self.status == Command.STATUS.NONE:
            return DynamicObject()
        if self.status == Command.STATUS.SENDER:
            return self.sender
        if self.status == Command.STATUS.RECEIVER:
            return self.receiver

    @property
    def properties(self):
        return self.status

class DEVICE_TYPE(Enum):
    CONVEYOR = 0
    STATION_CONVEYOR = 100
    LIFT_CONVEYOR = 110
    SHUTTLE = 200
    LIFT = 300
    CELL = 400
    BUFFER = 410

class Order:
    class Type(Enum):
        STORAGE = 100
        RETRIEVAL = 200

    def __init__(self, GDS, type):
        self.GDS = GDS
        self.type = type

class MSCObject:
    def __init__(self, location=None, id=None):
        if id:
            self.id = id
        else:
            self.location = -1
        if location:
            self.location = location
        else:
            self.location = Point()
        self.relativity = Point()

    def flipHorizontal(self):
        self.setLocation(self.location.flipHorizontal())

    def setLocation(self, location):
        self.location = location

    def setRelativity(self, relativity):
        self.relativity = relativity

    def update(self):
        return

    @property
    def position(self):
        return self.location + self.relativity

    @property
    def properties(self):
        return {
            "id", self.id,
            "location", (self.location.x, self.location.y)
        }

class StaticObject(MSCObject):
    class STATUS(Enum):
        NONE = 0
        WAITING = 100
        REQUEST = 200
    def __init__(self, location):
        super().__init__(location)

class DynamicObject(MSCObject):
    class STATUS(Enum):
        STOP = 0
        MOVING = 100
        ARRIVED = 200

    def __init__(self, location=None, speed=None):
        super().__init__(location)
        self.direction = Point()
        self.endPosition = Point()
        if speed == None:
            self.speed = 0.3
        else:
            self.speed = speed

        self.status = DynamicObject.STATUS.STOP

    def setDirection(self, direction):
        SPEED = 0.8
        direction_x = direction.x
        direction_y = direction.y
        direction_v = math.sqrt(direction_x ** 2 + direction_y ** 2)
        if direction_v == 0:
            direction_v = 0
        else:
            direction_v = 1 / direction_v
        direction_v = direction_v * self.speed * SPEED
        self.direction = direction * direction_v

    def setDestination(self, startPosition, endPosition):
        self.location = startPosition
        self.endPosition = endPosition
        self.setDirection(endPosition - startPosition)
        self.status = DynamicObject.STATUS.MOVING

    def setStop(self):
        self.status = DynamicObject.STATUS.STOP
        self.direction = Point(0, 0)

    def update(self):
        if self.status == DynamicObject.STATUS.MOVING:
            self.location = self.location + self.direction
            if self.direction.x < 0 and self.location.x < self.endPosition.x:
                self.location.x = self.endPosition.x
            if self.direction.y < 0 and self.location.y < self.endPosition.y:
                self.location.y = self.endPosition.y
            if self.direction.x > 0 and self.location.x > self.endPosition.x:
                self.location.x = self.endPosition.x
            if self.direction.y > 0 and self.location.y > self.endPosition.y:
                self.location.y = self.endPosition.y

            if self.location == self.endPosition:
                self.status = DynamicObject.STATUS.ARRIVED