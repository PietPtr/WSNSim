

class Simulator(object):
    def __init__(self, areasize, gridsize, root_amount_nodes):
        self.groups = []
        self.gridsize = gridsize
        self.areasize = areasize
        self.num_nodes = int(root_amount_nodes) ** 2

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

    def coordToIndex(self, position):
        return (int(position[0] // self.gridsize), int(position[1] // self.gridsize))


class Node(object):
    def __init__(self, position):
        self.position = position
        self.leader = None

    def __str__(self):
        return str(self.position)
