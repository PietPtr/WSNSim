from math import log10, sqrt
from pprint import pprint
import random
import time

GATEWAY_HEIGHT = 30
C = 0 # for suburb
CARRIER_FREQ = 868
PACK_GEN_CHANCE = 0.001
LORA_ENERGY_PER_BYTE = (32.5 / 8) / 1e6 # joule per byte (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6068831/)
BLE_ENERGY_PER_BYTE = 0.405 * 1e-7 # based on http://www.ti.com/lit/an/swra347a/swra347a.pdf
FIXED_BLE_PACKET_SIZE = 10
FIXED_LORA_PACKET_SIZE = 60
BLE_LISTEN_COST = BLE_ENERGY_PER_BYTE * 40
# Assume that:
#   MCU used is STM32L0: https://www.st.com/en/microcontrollers/stm32l0-series.html?querycriteria=productId=SS1817
#   Em = (PON(fMCU) + Pm) · Tm, from the paper mentioned above
#   PON(fMCU) = 2.82 milliwatts, based on the microcontroller spec.
#   We could not find data on energy consumption during measuring, so we just take the controller as being not idle
#   For the time a measure cost we also are not sure, so we took 100ms, this way it is about similar to transmitting
LORA_LISTEN_COST = (0.00282) * 0.1

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

        self.nodes.append(Gateway((areasize//2, areasize//2)))

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

        print("Initializing nodes...")
        for node in self.nodes:
            node.initialize(self.nodes)

    def promoteToLeader(self, follower):
        leader = Leader(follower.position)
        leader.energyUsed = follower.energyUsed
        leader.signalsBLE = follower.signalsBLE
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
            input("step")
            # pprint([vars(node) for node in self.nodes if type(node) == Gateway])
        else:
            if self.settings["visualize_while_running"]:
                time.sleep(self.settings["time_delay"])
            if self.settings["run_until"](self):
                input("step")

        return True

    def printState(self):
        print(  "Collisions      :", self.countCollisions(),
              "\nPackets received:", self.countPackets(),
              "\nEnergy used     :", self.countEnergyUsed(),
              "\nGateway packs   :", self.countGatewayPackets())

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
                total += node.totalReceivedPackets + node.receivedPackets
        return total

    def countGatewayPackets(self):
        return [node.receivedPackets for node in self.nodes if type(node) == Gateway][0]

    def countEnergyUsed(self):
        total = 0
        for node in self.nodes:
            total += node.energyUsed
        return total


class Node(object):
    def __init__(self, position):
        self.position = position
        self.energyUsed = 0
        self.signalsBLE = []
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
        self.signalsBLE = []
        self.signalsLoRa = []

    def update(self):
        pass

    def listenBLE(self):
        self.energyUsed += BLE_LISTEN_COST
        if len(self.signalsBLE) > 1:
            return True
        elif len(self.signalsBLE) == 1:
            return self.signalsBLE[0]
        else:
            return False

    def transmitBLE(self):
        self.energyUsed += FIXED_BLE_PACKET_SIZE * BLE_ENERGY_PER_BYTE
        for node in self.reachablesBLE:
            node.signalsBLE.append(self)
        self.transmitted = True

    def listenLoRa(self):
        self.energyUsed += LORA_LISTEN_COST
        if len(self.signalsLoRa) > 1:
            return True
        elif len(self.signalsLoRa) == 1:
            return self.signalsLoRa[0]
        else:
            return False

    def transmitLoRa(self):
        self.energyUsed += FIXED_LORA_PACKET_SIZE * LORA_ENERGY_PER_BYTE
        for node in self.reachablesLoRA:
            node.signalsLoRa.append(self)
        self.transmittedLoRa = True

class Gateway(Node):
    def __init__(self, position):
        super().__init__(position)
        self.receivedPackets = 0
        self.collisions = 0

    def __str__(self):
        return "Gateway:\t" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def check(self):
        super().check()

    def reset(self):
        super().reset()

    def update(self):
        super().update()

        signals = self.listenLoRa()
        if signals:
            if signals is not True:
                self.receivedPackets += 1
            else:
                self.collisions += 1

class Leader(Node):
    def __init__(self, position):
        super().__init__(position)
        self.totalReceivedPackets = 0
        self.receivedPackets = 0
        self.collisions = 0

    def __str__(self):
        return "Leader:\t" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def initialize(self, allNodes):
        super().initialize(allNodes)
        self.reachablesLoRA = [node for node in allNodes if
                type(node) != Follower and loraRXPower(self, node) > -129]

    def check(self):
        super().check()
        if self.signalsLoRa == [self] and self.transmittedLoRa and self.receivedPackets > 5:
            self.totalReceivedPackets += self.receivedPackets
            self.receivedPackets = 0

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
            if self.listenLoRa() == False:
                self.transmitLoRa()


class Follower(Node):
    def __init__(self, position):
        super().__init__(position)
        self.packets = 0
        self.generatedPackets = 0

    def __str__(self):
        return "Follow:\t" + hex(int(str(id(self)).split(" ")[-1]))

    def __repr__(self):
        return self.__str__()

    def reset(self):
        super().reset()

    def check(self):
        super().check()
        if self.signalsBLE == [self] and self.transmitted and self.packets > 0:
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

        if random.random() < PACK_GEN_CHANCE:
            self.addPacket()


    def addPacket(self):
        self.packets += 1
        self.generatedPackets += 1

    def hasPackets(self):
        return self.packets > 0

    def removePacket(self):
        self.packets -= 1
