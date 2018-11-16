import math

class Simulator(object):
    def __init__(self, areasize, gridsize, root_amount_nodes):
        self.groups = []
        self.gridsize = gridsize
        self.areasize = areasize
        self.num_nodes = int(root_amount_nodes) ** 2
        self.center = Node((areasize //2, areasize //2)) #central receiver node
        self.cost = 0
        self.maxRange = 130 # max range!

        for x in range(0, areasize // gridsize):
            self.groups.append([])
            for y in range(0, areasize // gridsize):
                self.groups[x].append([])

        self.nodes = []

        node_space = areasize / root_amount_nodes
        for x in range(root_amount_nodes):
            for y in range(root_amount_nodes):
                self.nodes.append(Node((x * node_space, y * node_space)))

        for node in self.nodes:
            indices = self.coordToIndex(node.position)
            self.groups[indices[0]][indices[1]].append(node)

        for groupx in self.groups:
            for group in groupx:
                for node in group:
                    node.leader = group[0]

        #For now, we simply give the first node a packet that should reach the central receiver node.
        self.nodes[0].addPacket()
        self.packetsToTransmit = 1
        self.receivedPackets = 0
        #For now, we simulate until self.receivedPackets >= self.packetsToTransmit


    def simulate(self):
        #This assumes the receiver node is not in the nodes array!
        #Very important!!!!!!!1
        for node in self.nodes:
            if node.hasPackets():
                groupleader = node.leader == node
                #we have three options:
                #If this node is a group leader, and is in range of the center node, 
                #transmit to the center node.
                if groupleader and (self.calculateDistance(node.position, self.center.position) < self.maxRange):
                    #transmit to the center node
                    self.transmit(node, self.center)
                    self.receivedPackets += 1
                    break

                #If this node is a group leader but not in range, transmit to the group leader that is closer.
                if groupleader:
                    #Find group leader to transmit to
                    index = self.coordToIndex(node.position)
                    dx = node.position[0] - self.center.position[0]
                    dy = node.position[1] - self.center.position[1]

                    if dx > 100:
                        newIndex = (index[0] - 1, index[1])
                    if dx < 100:
                        newIndex = (index[0] + 1, index[1])
                    if dy > 100:
                        newIndex = (index[0], index[1] - 1)
                    if dy < 100:
                        newIndex = (index[0], index[1] + 1)
                    toNode = self.groups[newIndex[0]][newIndex[1]][0]
                    self.transmit(node, toNode)
                    break

                #If this node is not a group leader, transmit to the group leader.
                self.transmit(node, node.leader)

        if self.receivedPackets < self.packetsToTransmit:
            self.simulate()    
        else:
            print('simulation ended with total cost being: ', self.cost)

    def coordToIndex(self, position):
        return (int(position[0] // self.gridsize), int(position[1] // self.gridsize))

    def transmit(self, fromNode, toNode):
       self.cost += self.calculateCost(self.calculateDistance(fromNode.position, toNode.position))
       fromNode.removePacket()
       toNode.addPacket()

    def calculateDistance(self, pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) 

    #To add: formula from lecture slides.
    def calculateCost(self, distance):
        return distance

class Node(object):
    def __init__(self, position):
        self.position = position
        self.leader = None
        self.packets = 0

    def __str__(self):
        return str((self.position, self.packets))

    def addPacket(self):
        self.packets += 1

    def hasPackets(self):
        return self.packets > 0

    def removePacket(self):
        self.packets -= 1



    
