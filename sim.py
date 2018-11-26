from math import log10, sqrt
from pprint import pprint
import random

GATEWAY_HEIGHT = 30
C = 0 # for suburb
CARRIER_FREQ = 868


def calculateDistance(pos1, pos2):
    return sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

# Calculate the received bluetooth strength at node rx transmitted from node tx
def bluetoothRXPower(tx, rx):
    if tx.position == rx.position:
        return 0
    return -(40.04 + 10 * 3.71 * log10(calculateDistance(tx.position, rx.position)))

def loraRXPower(tx, rx):
    if tx.position == rx.position:
        return 0

    d = calculateDistance(tx.position, rx.position) / 1000
    f = CARRIER_FREQ
    hB = GATEWAY_HEIGHT
    hR = 0

    a = (1.1 * log10(f) - 0.7) * hR - (1.56 * log10(f) - 0.8)

    L = 46.3 + 33.9 * log10(f) - 13.82 * log10(hB) - a + (44.9 - 6.55 * log10(hB)) * log10(d) + C

    return -L

class Simulator(object):
    def __init__(self, areasize, gridsize, root_amount_nodes, queue, settings):
        self.queue = queue
        self.groups = []
        self.gridsize = gridsize
        self.areasize = areasize
        self.num_nodes = int(root_amount_nodes) ** 2
        self.cost = 0
        self.nodes = [] # All nodes used in the simulation
        self.settings = settings

        print("Generating groups...")
        for x in range(0, areasize // gridsize):
            self.groups.append([])
            for y in range(0, areasize // gridsize):
                self.groups[x].append([])

        node_space = areasize / root_amount_nodes
        for x in range(root_amount_nodes):
            for y in range(root_amount_nodes):
                self.nodes.append(Follower((x * node_space, y * node_space)))

        print("Generating nodes...")
        for node in self.nodes:
            indices = self.coordToIndex(node.position)
            self.groups[indices[0]][indices[1]].append(node)

        print("Assigning leaders...")
        for groupx in self.groups:
            for group in groupx:
                for node_i in range(len(group)):
                    if node_i == 0:
                        nodes_index = self.nodes.index(group[node_i])
                        self.nodes[nodes_index] = self.promoteToLeader(group[node_i])
                    else:
                        group[node_i].leader = group[0]

        print("Initializing nodes...")
        for node in self.nodes:
            node.initialize(self.nodes)

    def promoteToLeader(self, follower):
        leader = Leader(follower.position)
        leader.energyUsed = follower.energyUsed
        leader.signals = follower.signals
        return leader

    def simulate(self):
        for node in self.nodes:
            node.check()
        for node in self.nodes:
            node.reset()
        for node in self.nodes:
            node.update()

        self.queue.put(self.nodes)

        if self.settings["interactive"]:
            command = input("step")
        else:
            if self.settings["run_until"](self.countPackets(), self.countCollisions()):
                return False

        return True

    def printState(self):
        print("Collisions:", self.countCollisions(),
              "Packets received:", self.countPackets(),
              "Energy used: ", self.countEnergyUsed())

    def coordToIndex(self, position):
        return (int(position[0] // self.gridsize), int(position[1] // self.gridsize))

    def countCollisions(self):
        total = 0
        for node in self.nodes:
            if type(node) == Leader:
                total += node.collisions
        return total

    def countPackets(self):
        total = 0
        for node in self.nodes:
            if type(node) == Leader:
                total += node.receivedPackets
        return total

    def countEnergyUsed(self):
        total = 0
        for node in self.nodes:
            total += node.energyUsed
        return total


class Node(object):
    def __init__(self, position):
        self.position = position
        self.energyUsed = 0
        self.signals = []
        self.signalsLoRa = []
        self.transmitted = False
        self.transmittedLoRa = False

    def initialize(self, allNodes):
        self.reachablesBLE = [node for node in allNodes if bluetoothRXPower(self, node) > -116]

    def __str__(self):
        return "Node:" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def check(self):
        pass

    def reset(self):
        self.transmitted = False
        self.transmittedLoRa = False
        self.signals = []
        self.signalsLoRa = []

    def update(self):
        pass
        # if self.leader == self:
        #     print(self.signals)
        #     data = self.listenBLE()
        #     if data is not True and data is not False:
        #

    def listenBLE(self):
        self.energyUsed += 1
        if len(self.signals) > 1:
            return True
        elif len(self.signals) == 1:
            return self.signals[0]
        else:
            return False

    def transmitBLE(self):
        self.energyUsed += 1
        for node in self.reachablesBLE:
            node.signals.append(self)
        self.transmitted = True

    def transmitLoRa(self):
        self.energyUsed += 1
        for node in self.reachablesLoRA:
            node.signalsLoRa.append(self)
        self.transmittedLoRa = True

# class Gateway(Node):
#     def __init__(self, position):
#         self.receivedPackets = 0
#         self.collisions = 0
#         self.loraSignals = []

class Leader(Node):
    def __init__(self, position):
        super().__init__(position)
        self.receivedPackets = 0
        self.collisions = 0

    def __str__(self):
        return "Leader:" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def initialize(self, allNodes):
        super().initialize(allNodes)
        self.reachablesLoRA = [node for node in allNodes if
                type(node) == Leader and loraRXPower(self, node) > -127]

    def check(self):
        super().check()

    def reset(self):
        super().reset()

    def update(self):
        super().update()

        signals = self.listenBLE()
        if signals:
            if signals is not True:
                self.receivedPackets += 1
            else:
                self.collisions += 1

        if self.receivedPackets > 5:
            self.transmitLoRa()




class Follower(Node):
    def __init__(self, position):
        super().__init__(position)
        self.packets = 0
        self.leader = None
        self.generatedPackets = 0

    def __str__(self):
        return "Follow:" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def reset(self):
        super().reset()

    def check(self):
        super().check()
        if self.signals == [self] and self.transmitted and self.packets > 0:
            # There was no collision so our packet was sent
            self.removePacket()

    def update(self):
        super().update()
        if self.packets >= 1:
            # listen to the network
            if self.listenBLE():
                pass # someone is transmitting, so shut up
            else:
                self.transmitBLE()

        if random.random() < 0.005:
            self.addPacket()


    def addPacket(self):
        self.packets += 1
        self.generatedPackets += 1

    def hasPackets(self):
        return self.packets > 0

    def removePacket(self):
        self.packets -= 1
