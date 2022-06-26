import numpy as np
import pandas as pd
import torch
from torch import nn, optim

class DQN(nn.Module):
    def __init__(self, inputs, outputs):
        super(DQN, self).__init__()
        self.liner1 = nn.Linear(inputs, 64)
        self.liner2 = nn.Linear(64, 64)
        self.liner3 = nn.Linear(64, outputs)

        def init_weights(m):
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=nn.init.calculate_gain('relu'))
                m.bias.data.fill_(0.01)

        self.fc = nn.Sequential(self.liner1, nn.ReLU(), self.liner2, nn.ReLU(), self.liner3)
        self.fc.apply(init_weights)

    def forward(self, x):
        return self.fc(x)


class Memory:
    def __init__(self, startAt):
        self.startAt = startAt
        self.state = None
        self.nextState = None
        self.reward1 = None
        self.reward2 = None
        self.reward3 = None
        self.action = -1
        self.done = 0

    def addState(self, state):
        self.state = list(state.values())

    def addNextState(self, nextState):
        self.nextState = list(nextState.values())

    def addAction(self, action):
        self.action = action

    def addReward(self, reward1=None, reward2=None, reward3=None):
        if not self.reward1:
            self.reward1 = reward1
        if not self.reward2:
            self.reward2 = reward2
        if not self.reward3:
            self.reward3 = reward3

    def isDone(self):
        self.nextState = self.state
        self.done = 1

    @property
    def r1(self):
        if self.reward1:
            return self.reward1

            # lambda1_list = [27.78739518528536, 38.182918274289726, 57.35820745216515, 59.71676026794776]
            # lambda1 = 1 / lambda1_list[self.action]
            # return (lambda1 - (lambda1 * np.exp(lambda1 * reward1)))
        return False

    @property
    def r2(self):
        if self.reward2:
            return self.reward2

            # lambda2 = 1 / 0.8055797891675754
            # return (lambda2 - (lambda2 * np.exp(lambda2 * reward2)))
        return False

    @property
    def r3(self):
        if self.reward3:
            return self.reward3

            # lambda3 = 1 / 6.34343874954562
            # return (lambda3 - (lambda3 * np.exp(lambda3 * reward3)))
        return False

    @property
    def reward(self):
        if self.reward1 and self.reward2:
            l = 1 / 7.775065368971529
            r = (self.r1 + self.r2)
            reward = 100 * np.exp(-l * r)
            return reward
        return -1

    @property
    def isAvailable(self):
        if self.state and self.nextState and self.reward != -1 and self.action != -1:
            return True
        return False

class MemoryManager:
    STEP_SIZE = 16
    memories = dict()
    histories = pd.DataFrame()
    target = -1

    @staticmethod
    def reset():
        MemoryManager.target = -1
        MemoryManager.memories = dict()
        MemoryManager.histories = pd.DataFrame()

    @staticmethod
    def addMemory(trayId, startAt):
        MemoryManager.memories[str(trayId)] = Memory(startAt)
        return

    @staticmethod
    def updateMemory(trayId, column, values):
        str_trayId = str(trayId)
        if str_trayId in MemoryManager.memories.keys():
            if column == "state":
                MemoryManager.memories[str_trayId].addState(values)
            if column == "nextState":
                MemoryManager.memories[str_trayId].addNextState(values)
            if column == "action":
                MemoryManager.memories[str_trayId].addAction(values)
            if column == "reward1":
                MemoryManager.memories[str_trayId].addReward(reward1=values)
            if column == "reward2":
                MemoryManager.memories[str_trayId].addReward(reward2=values)
            if column == "reward3":
                MemoryManager.memories[str_trayId].addReward(reward3=values)
            if column == "reward":
                MemoryManager.memories[str_trayId].addReward(values)
            if column == "done":
                MemoryManager.memories[str_trayId].isDone()

    @staticmethod
    def getAvailableMemories():
        memories = []
        for memory in MemoryManager.memories:
            if MemoryManager.memories[memory].isAvailable:
                memories.append(memory)
        return memories

    @staticmethod
    def addHistory(memory):
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
        MemoryManager.histories = MemoryManager.histories.append(data, ignore_index=True)

    @staticmethod
    def getMemories():
        availableMemories = MemoryManager.getAvailableMemories()
        memories = []
        size = MemoryManager.STEP_SIZE if len(availableMemories) > MemoryManager.STEP_SIZE else len(availableMemories)
        for memory in availableMemories[:size]:
            _memory = MemoryManager.memories.pop(memory)
            memories.append(_memory)
            MemoryManager.addHistory(_memory)

        return memories

class LaneAgent:
    def __init__(self):
        self.n_states = 92
        self.n_actions = 4

        self.discount_factor = 0.2
        self.learning_rate = 0.001
        self.epsilon = 1.0
        self.epsilon_decay = 0.998
        self.epsilon_min = 0.01
        self.batch_size = MemoryManager.STEP_SIZE

        self.network = DQN(self.n_states, self.n_actions)
        self.target_network = DQN(self.n_states, self.n_actions)

    def loadAgent(self, episodeNum):
        PATH = "./_model/_agent/laneAgent_{0:03d}.pth".format(episodeNum)
        self.network.load_state_dict(torch.load(PATH))
        self.update_target_model()
        self.epsilon = self.epsilon_min

    def saveAgent(self, episodeNum):
        PATH = "./_model/_agent/laneAgent_{0:03d}.pth".format(episodeNum)
        torch.save(self.network.state_dict(), PATH)

    def update_target_model(self):
        self.target_network.load_state_dict(self.network.state_dict())

    def select_action(self, state):
        with torch.no_grad():
            q_value = self.network(state)
            return q_value.numpy()
            # return np.argmax(q_value)

    def train_model(self):
        optimizer = optim.Adam(self.network.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        else:
            self.epsilon = self.epsilon_min

        memories = MemoryManager.getMemories()
        if not memories:
            return
        states = torch.tensor([memory.state for memory in memories])
        actions = torch.tensor([memory.action for memory in memories])
        rewards = torch.tensor([memory.reward for memory in memories])
        next_states = torch.tensor([memory.nextState for memory in memories])
        dones = torch.tensor([memory.done for memory in memories])

        for memory in memories:
            if memory.done == 1:
                print(memory.reward, self.network(states))

        # 현재 상태에 대한 모델의 큐함수
        state_action_values = self.network(states).gather(1, actions.view(-1, 1))

        # 다음 상태에 대한 타깃 모델의 큐함수
        next_state_values = self.target_network(next_states).max(1)[0].detach()

        # 벨만 최적 방정식을 이용한 업데이트 타깃
        expected_state_action_values = rewards + (1 - dones) * self.discount_factor * next_state_values

        # Huber 손실 계산
        loss = criterion(state_action_values.to(torch.float32), expected_state_action_values.unsqueeze(1).to((torch.float32)))

        # 모델 최적화
        optimizer.zero_grad()
        loss.backward()
        for param in self.network.parameters():
            param.grad.data.clamp_(-1, 1)
        optimizer.step()

class FloorAgent:
    def __init__(self):
        self.n_states = 16
        self.n_actions = 4

        self.discount_factor = 0.2
        self.learning_rate = 0.001
        self.epsilon = 1.0
        self.epsilon_decay = 0.998
        self.epsilon_min = 0.01
        self.batch_size = MemoryManager.STEP_SIZE

        self.network = DQN(self.n_states, self.n_actions)
        self.target_network = DQN(self.n_states, self.n_actions)

    def loadAgent(self, episodeNum):
        PATH = "./_model/_agent/floorAgent_{0:03d}.pth".format(episodeNum)
        self.network.load_state_dict(torch.load(PATH))
        self.update_target_model()
        self.epsilon = self.epsilon_min

    def saveAgent(self, episodeNum):
        PATH = "./_model/_agent/floorAgent_{0:03d}.pth".format(episodeNum)
        torch.save(self.network.state_dict(), PATH)

    def update_target_model(self):
        self.target_network.load_state_dict(self.network.state_dict())

    def select_action(self, state):
        with torch.no_grad():
            q_value = self.network(state)
            return q_value.numpy()
            # return np.argmax(q_value)

    def train_model(self):
        optimizer = optim.Adam(self.network.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        else:
            self.epsilon = self.epsilon_min

        memories = MemoryManager.getMemories()
        if not memories:
            return
        states = torch.tensor([memory.state for memory in memories])
        actions = torch.tensor([memory.action for memory in memories])
        rewards = torch.tensor([memory.reward for memory in memories])
        next_states = torch.tensor([memory.nextState for memory in memories])
        dones = torch.tensor([memory.done for memory in memories])

        for memory in memories:
            if memory.done == 1:
                print(memory.reward, self.network(states))

        # 현재 상태에 대한 모델의 큐함수
        state_action_values = self.network(states).gather(1, actions.view(-1, 1))

        # 다음 상태에 대한 타깃 모델의 큐함수
        next_state_values = self.target_network(next_states).max(1)[0].detach()

        # 벨만 최적 방정식을 이용한 업데이트 타깃
        expected_state_action_values = rewards + (1 - dones) * self.discount_factor * next_state_values

        # Huber 손실 계산
        loss = criterion(state_action_values.to(torch.float32), expected_state_action_values.unsqueeze(1).to((torch.float32)))

        # 모델 최적화
        optimizer.zero_grad()
        loss.backward()
        for param in self.network.parameters():
            param.grad.data.clamp_(-1, 1)
        optimizer.step()