from enum import Enum

class Agent:
    def __init__(self, storageController=None, retrievalController=None):
        self.storageController = storageController
        self.retrievalController = retrievalController

    def importStorageController(self, controller):
        return

    def importRetrievalController(self, controller):
        return

    async def requestStorage(self, target, env):
        return await self.storageController.run(target, env)

    async def requestRetrieval(self, target, env):
        return await self.retrievalController.run(target, env)


class RequestType(Enum):
    NONE = -1
    STORAGE_LANE = 101
    STORAGE_LIFT = 102
    STORAGE_SHUTTLE = 103
    RETRIEVAL_LANE = 201
    RETRIEVAL_LIFT = 202
    RETRIEVAL_SHUTTLE = 203


class ControllerInterface:
    async def run(self, type: RequestType) -> dict:
        pass
