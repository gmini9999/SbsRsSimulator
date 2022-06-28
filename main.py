from _simulator import Simulator
from _util import AppManager
from _model._agent import MemoryManager
import pandas as pd
import time

num_episode = 5
AppManager.status = "rr1_4"
AppManager.initialize()
result = pd.DataFrame()
AppManager.status = "drl"
AppManager.initialize()
result = pd.DataFrame()
AppManager.laneAgent.loadAgent(959)
AppManager.floorAgent.loadAgent(299)
for episode in range(0, num_episode):
    AppManager.status = "rr1_4"
    AppManager.episode = episode
    AppManager.reset()
    print("{} Episode {}".format(AppManager.status, episode))
    simulator = Simulator()
    done = False
    start = time.time()
    while not done:
        done = simulator.run()

    if done == -1:
        print("Fail")
    else:
        done = 1
        print("True")

    memories = []
    availableMemories = MemoryManager.getAvailableMemories()
    for memory in availableMemories:
        _memory = MemoryManager.memories.pop(memory)
        memories.append(_memory)

    df = pd.DataFrame()
    for memory in memories:
        state = memory.state
        action = memory.action
        reward1 = memory.reward1
        reward2 = memory.reward2
        reward3 = memory.reward3
        reward = memory.reward
        next_state = memory.nextState
        done = memory.done

        data = dict()
        data["states"] = state
        data["actions"] = action
        data["rewards1"] = reward1
        data["rewards2"] = reward2
        data["rewards3"] = reward3
        data["rewards"] = reward
        data["nextStates"] = next_state
        data["dones"] = done
        df = df.append(data, ignore_index=True)

    df.to_csv("./data/data_{}.csv".format(episode))

    end = time.time()
    simulator_time = (end - start) / 60
    total_time = (AppManager.time - AppManager.startTime).total_seconds() / 60
    storage_rate = AppManager.storage_rate
    retrieval_rate = AppManager.retrieval_rate
    r2r_count = AppManager.r2r
    total_rate = (AppManager.storage + AppManager.retrieval) / total_time

    value = dict()
    value["Real"] = total_time
    value["Fake"] = simulator_time
    value["storage_rate"] = storage_rate
    value["retrieval_rate"] = retrieval_rate
    value["r2r_rate"] = r2r_count
    value["total_rate"] = total_rate
    value["done"] = done
    result = result.append(value, ignore_index=True)

    print("Episode {} Finish".format(episode))
    print("Episode {} total process time : {}m".format(episode, total_time))
    print("Episode {} total simulator time : {}m".format(episode, simulator_time))
    print("Episode {} storage rate : {}/m".format(episode, storage_rate))
    print("Episode {} retrieval rate : {}/m".format(episode, retrieval_rate))
    print("Episode {} r2r count : {}ea".format(episode, r2r_count))
    print("Episode {} total rate : {}/m".format(episode, total_rate))

    AppManager.laneAgent.saveAgent(episode)
    AppManager.commitDB()
    AppManager.reset()
    result.to_csv("./result.csv")

    del simulator

