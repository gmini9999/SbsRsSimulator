import pygame
import sys
from _util import AppManager
from _env._object import Point

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
TARGET_FPS = 30

COLOR_BUFFER = YELLOW
COLOR_CELL = BLUE
COLOR_CONVEYOR = YELLOW
COLOR_SHUTTLE = WHITE
COLOR_LIFT = RED

CENTER_X = 100
CENTER_Y = 100

CONVEYOR_LENGTH = 80
UNIT_WIDTH = 10
UNIT_HEIGHT = 16

TRAY_SIZE = 10

SPAN_X = 5
SPAN_Y = 5

BAYS = 36
FLOORS = 4
BANKS = 2
FLOOR_WIDTH = (BANKS * 2 + 1) * (UNIT_WIDTH + SPAN_X)
FLOOR_HEIGHT = (BAYS + 1) * (UNIT_HEIGHT + SPAN_Y)

MSC_WIDTH = FLOOR_WIDTH * FLOORS
MSC_HEIGHT = FLOOR_HEIGHT


class MSC_Viewer:
    def __init__(self):
        pygame.init()
        self.size = (1920, 1080)
        self.background = None

        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill(BLACK)
        # Loop until the user clicks the close button.
        self.clock = pygame.time.Clock()

    def setBackground(self, env):
        self.background = pygame.Surface(self.size)
        self.background.fill(BLACK)

        msc = env.msc
        conveyor = msc.source
        while conveyor.next:
            previous_x = conveyor.location.x
            previous_y = conveyor.location.y
            next_x = conveyor.next.location.x
            next_y = conveyor.next.location.y
            pygame.draw.line(self.background, COLOR_CONVEYOR,
                             [CENTER_X + previous_x * CONVEYOR_LENGTH, CENTER_Y + previous_y * CONVEYOR_LENGTH],
                             [CENTER_X + next_x * CONVEYOR_LENGTH, CENTER_Y + next_y * CONVEYOR_LENGTH], 1)

            conveyor = conveyor.next

        for lane in msc.lanes:
            start_x = (lane.location.x) * CONVEYOR_LENGTH
            start_y = lane.location.y * CONVEYOR_LENGTH
            """
            start_x = (msc.location.x) * CONVEYOR_LENGTH
            start_y = msc.location.y * CONVEYOR_LENGTH - MSC_HEIGHT
            """

            for f in range(lane.floors - 1):
                previous_floor = lane.floors_[f].out_buffers_[0]
                next_floor = lane.floors_[f+1].in_buffers_[0]
                x = (previous_floor.position.x + next_floor.position.x) / 2
                y = previous_floor.position.y
                pygame.draw.line(self.background, COLOR_CONVEYOR,
                                 [CENTER_X + x * (UNIT_WIDTH + SPAN_X) + start_x, CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y],
                                 [CENTER_X + x * (UNIT_WIDTH + SPAN_X) + start_x, CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) + FLOOR_HEIGHT + start_y], 1)

            for floor_ in lane.floors_:
                for buffer in floor_.in_buffers_:
                    x = buffer.position.x
                    y = buffer.position.y
                    pygame.draw.rect(self.background, MAGENTA,
                                     [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + start_x,
                                      CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y,
                                      UNIT_WIDTH, UNIT_HEIGHT], 1)
                for buffer in floor_.out_buffers_:
                    x = buffer.position.x
                    y = buffer.position.y
                    pygame.draw.rect(self.background, CYAN,
                                     [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + start_x,
                                      CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y,
                                      UNIT_WIDTH, UNIT_HEIGHT], 1)

                for bank in floor_.banks_:
                    for cell in bank.cells:
                        position = cell.position
                        x = position.x
                        y = position.y
                        pygame.draw.rect(self.background, COLOR_CELL,
                                         [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + start_x,
                                          CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y,
                                          UNIT_WIDTH, UNIT_HEIGHT], 1)

            for queue in lane.in_station.queues_:
                if queue.next:
                    previous_x = queue.position.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X
                    previous_y = queue.position.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y
                    next_x = queue.next.position.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X
                    next_y = queue.next.position.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y
                    pygame.draw.line(self.background, MAGENTA, [previous_x, previous_y],
                                     [next_x, next_y], 1)

            for queue in lane.out_station.queues_:
                if queue.next:
                    previous_x = queue.position.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X
                    previous_y = queue.position.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y
                    next_x = queue.next.position.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X
                    next_y = queue.next.position.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y
                    pygame.draw.line(self.background, CYAN, [previous_x, previous_y],
                                     [next_x, next_y], 1)

            top = Point(lane.floors_[-1].in_buffers_[0].position.x, lane.in_station.lift.position.y)
            bottom = Point(lane.in_station.queues_[-1].position.x, lane.in_station.lift.position.y)
            pygame.draw.line(self.background, MAGENTA,
                             [bottom.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X,
                              bottom.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y],
                             [top.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X,
                              top.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y], 1)

            top = Point(lane.floors_[-1].out_buffers_[0].position.x, lane.out_station.lift.position.y)
            bottom = Point(lane.out_station.queues_[-1].position.x, lane.out_station.lift.position.y)
            pygame.draw.line(self.background, CYAN,
                             [bottom.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X,
                              bottom.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y],
                             [top.x * (UNIT_WIDTH + SPAN_X) + start_x + CENTER_X,
                              top.y * (UNIT_HEIGHT + SPAN_Y) + start_y + CENTER_Y], 1)

    def render(self, env):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

        pygame.display.flip()
        self.clock.tick(TARGET_FPS)
        self.screen.blit(self.background, (0, 0))

        msc = env.msc
        conveyor = msc.source
        while conveyor.next:
            if conveyor.tray:
                tray = conveyor.tray
                x = tray.position.x
                y = tray.position.y
                COLOR = COLOR_CONVEYOR
                if tray.isStorage:
                    COLOR = MAGENTA
                if tray.isRetrieval:
                    COLOR = CYAN
                pygame.draw.rect(self.screen, COLOR, [CENTER_X + x * CONVEYOR_LENGTH - (TRAY_SIZE * 0.5),
                                                      CENTER_Y + y * CONVEYOR_LENGTH - (TRAY_SIZE * 0.5),
                                                      10, 10], 0)

            conveyor = conveyor.next

        for lane in msc.lanes:
            start_x = (lane.location.x) * CONVEYOR_LENGTH
            start_y = lane.location.y * CONVEYOR_LENGTH
            """
            start_x = (msc.location.x) * CONVEYOR_LENGTH
            start_y = msc.location.y * CONVEYOR_LENGTH - MSC_HEIGHT
            """

            in_station = lane.in_station
            for queue in in_station.queues_:
                if queue.tray:
                    tray = queue.tray
                    x = tray.position.x
                    y = tray.position.y
                    COLOR = COLOR_CONVEYOR
                    if tray.isStorage:
                        COLOR = MAGENTA
                    if tray.isRetrieval:
                        COLOR = CYAN
                    pygame.draw.rect(self.screen, COLOR,
                                     [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (TRAY_SIZE * 0.5) + start_x,
                                      CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (TRAY_SIZE * 0.5) + start_y,
                                      TRAY_SIZE, TRAY_SIZE], 0)

            in_station_lift = in_station.lift
            x = in_station_lift.position.x
            y = in_station_lift.position.y
            pygame.draw.rect(self.screen, MAGENTA,
                             [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + start_x,
                              CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y,
                              UNIT_WIDTH, UNIT_HEIGHT], 0)
            if in_station_lift.tray:
                tray = in_station_lift.tray
                x = tray.position.x
                y = tray.position.y
                COLOR = COLOR_CONVEYOR
                if tray.isStorage:
                    COLOR = MAGENTA
                if tray.isRetrieval:
                    COLOR = CYAN
                pygame.draw.rect(self.screen, COLOR,
                                 [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (TRAY_SIZE * 0.5) + start_x,
                                  CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (TRAY_SIZE * 0.5) + start_y,
                                  TRAY_SIZE, TRAY_SIZE], 0)

            out_station = lane.out_station
            for queue in out_station.queues_:
                if queue.tray:
                    tray = queue.tray
                    x = tray.position.x
                    y = tray.position.y
                    COLOR = COLOR_CONVEYOR
                    if tray.isStorage:
                        COLOR = MAGENTA
                    if tray.isRetrieval:
                        COLOR = CYAN
                    pygame.draw.rect(self.screen, COLOR,
                                     [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (TRAY_SIZE * 0.5) + start_x,
                                      CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (TRAY_SIZE * 0.5) + start_y,
                                      TRAY_SIZE, TRAY_SIZE], 0)

            out_station_lift = out_station.lift
            x = out_station_lift.position.x
            y = out_station_lift.position.y
            pygame.draw.rect(self.screen, CYAN,
                             [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + start_x,
                              CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y,
                              UNIT_WIDTH, UNIT_HEIGHT], 0)
            if out_station_lift.tray:
                tray = out_station_lift.tray
                x = tray.position.x
                y = tray.position.y
                COLOR = COLOR_CONVEYOR
                if tray.isStorage:
                    COLOR = MAGENTA
                if tray.isRetrieval:
                    COLOR = CYAN
                pygame.draw.rect(self.screen, COLOR,
                                 [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (TRAY_SIZE * 0.5) + start_x,
                                  CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (TRAY_SIZE * 0.5) + start_y,
                                  TRAY_SIZE, TRAY_SIZE], 0)

            for floor_ in lane.floors_:
                shuttle = floor_.shuttle
                x = shuttle.position.x
                y = shuttle.position.y
                pygame.draw.rect(self.screen, COLOR_SHUTTLE,
                                 [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + start_x,
                                  CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + start_y,
                                  UNIT_WIDTH, UNIT_HEIGHT], 0)
                if shuttle.tray:
                    tray = shuttle.tray
                    x = tray.position.x
                    y = tray.position.y
                    COLOR = COLOR_CONVEYOR
                    if tray.isStorage:
                        COLOR = MAGENTA
                    if tray.isRetrieval:
                        COLOR = CYAN
                    pygame.draw.rect(self.screen, COLOR,
                                     [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + (
                                             (UNIT_WIDTH - TRAY_SIZE) * 0.5) + start_x,
                                      CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + (
                                              (UNIT_HEIGHT - TRAY_SIZE) * 0.5) + start_y,
                                      TRAY_SIZE, TRAY_SIZE], 0)

                for buffer in floor_.in_buffers_:
                    if buffer.tray:
                        tray = buffer.tray
                        x = tray.position.x
                        y = tray.position.y
                        COLOR = COLOR_CONVEYOR
                        if tray.isStorage:
                            COLOR = MAGENTA
                        if tray.isRetrieval:
                            COLOR = CYAN
                        pygame.draw.rect(self.screen, COLOR,
                                         [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + (
                                                     (UNIT_WIDTH - TRAY_SIZE) * 0.5) + start_x,
                                          CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + (
                                                      (UNIT_HEIGHT - TRAY_SIZE) * 0.5) + start_y,
                                          TRAY_SIZE, TRAY_SIZE], 0)

                for buffer in floor_.out_buffers_:
                    if buffer.tray:
                        tray = buffer.tray
                        x = tray.position.x
                        y = tray.position.y
                        COLOR = COLOR_CONVEYOR
                        if tray.isStorage:
                            COLOR = MAGENTA
                        if tray.isRetrieval:
                            COLOR = CYAN
                        pygame.draw.rect(self.screen, COLOR,
                                         [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + (
                                                     (UNIT_WIDTH - TRAY_SIZE) * 0.5) + start_x,
                                          CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + (
                                                      (UNIT_HEIGHT - TRAY_SIZE) * 0.5) + start_y,
                                          TRAY_SIZE, TRAY_SIZE], 0)

                for bank in floor_.banks_:
                    for cell in bank.cells:
                        if cell.tray:
                            tray = cell.tray
                            x = tray.position.x
                            y = tray.position.y
                            COLOR = COLOR_CONVEYOR
                            if tray.isStorage:
                                COLOR = MAGENTA
                            if tray.isRetrieval:
                                COLOR = CYAN
                            pygame.draw.rect(self.screen, COLOR,
                                             [CENTER_X + x * (UNIT_WIDTH + SPAN_X) - (UNIT_WIDTH * 0.5) + (
                                                     (UNIT_WIDTH - TRAY_SIZE) * 0.5) + start_x,
                                              CENTER_Y + y * (UNIT_HEIGHT + SPAN_Y) - (UNIT_HEIGHT * 0.5) + (
                                                      (UNIT_HEIGHT - TRAY_SIZE) * 0.5) + start_y,
                                              TRAY_SIZE, TRAY_SIZE], 0)

        return True
