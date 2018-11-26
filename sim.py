import math
from pprint import pprint
import random

def calculateDistance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

# Calculate the received bluetooth strength at node rx transmitted from node tx
def bluetoothRXPower(tx, rx):
    if tx.position == rx.position:
        return 0
    return -(40.04 + 10 * 3.71 * math.log10(calculateDistance(tx.position, rx.position)))

class Simulator(object):
    def __init__(self, areasize, gridsize, root_amount_nodes, queue):
        self.queue = queue
        self.groups = []
        self.gridsize = gridsize
        self.areasize = areasize
        self.num_nodes = int(root_amount_nodes) ** 2
        self.center = Node((areasize // 2, areasize // 2)) #central receiver node
        self.cost = 0
        self.nodes = [] # All nodes used in the simulation

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

        # pprint(self.groups)

        #For now, we simply give the first node a packet that should reach the central receiver node.
        # self.nodes[1].addPacket()
        # self.nodes[2].addPacket()
        self.packetsToTransmit = 1
        self.receivedPackets = 0

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

        # pprint({key: value for (key, value) in vars(self.nodes[0])})
        print("self: " + str(self.nodes[0]))
        pprint(vars(self.nodes[0]))
        input()

        #This assumes the receiver node is not in the nodes array!
        #Very important!
        # for node in self.nodes:
        #     if node.hasPackets():
        #         groupleader = node.leader == node
        #         #we have three options:
        #         #If this node is a group leader, and is in range of the center node,
        #         #transmit to the center node.
        #         if groupleader and (self.calculateDistance(node.position, self.center.position) < self.maxRange):
        #             #transmit to the center node
        #             self.transmit(node, self.center)
        #             self.receivedPackets += 1
        #             break
        #
        #         #If this node is a group leader but not in range, transmit to the group leader that is closer.
        #         if groupleader:
        #             #Find group leader to transmit to
        #             index = self.coordToIndex(node.position)
        #             dx = node.position[0] - self.center.position[0]
        #             dy = node.position[1] - self.center.position[1]
        #
        #             if dx > 100:
        #                 newIndex = (index[0] - 1, index[1])
        #             if dx < 100:
        #                 newIndex = (index[0] + 1, index[1])
        #             if dy > 100:
        #                 newIndex = (index[0], index[1] - 1)
        #             if dy < 100:
        #                 newIndex = (index[0], index[1] + 1)
        #             toNode = self.groups[newIndex[0]][newIndex[1]][0]
        #             self.transmit(node, toNode)
        #             break
        #
        #         #If this node is not a group leader, transmit to the group leader.
        #         self.transmit(node, node.leader)
        #
        # if self.receivedPackets < self.packetsToTransmit:
        #     self.simulate()
        # else:
        #     print('simulation ended with total cost being: ', self.cost)

    def coordToIndex(self, position):
        return (int(position[0] // self.gridsize), int(position[1] // self.gridsize))


class Node(object):
    def __init__(self, position):
        self.position = position
        self.energyUsed = 0
        self.signals = []
        self.transmitted = False

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
        self.signals = []

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
        print(self, "Transmitting BLE packet")
        self.energyUsed += 1
        for node in self.reachablesBLE:
            node.signals.append(self)
        self.transmitted = True

class Leader(Node):
    def __init__(self, position):
        super().__init__(position)
        self.receivedPackets = 0
        self.collisions = 0

    def __str__(self):
        return "Leader:" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def check(self):
        super().check()

    def update(self):
        super().update()

        signals = self.listenBLE()
        if signals:
            if signals is not True:
                self.receivedPackets += 1
            else:
                self.collisions += 1

    def reset(self):
        super().reset()

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
                print(self, "Oh no, someone is transmitting!")
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
