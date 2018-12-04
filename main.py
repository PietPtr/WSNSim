import sim
from threading import Thread
import renderer
from queue import Queue

queue = Queue()

settings = {
    "interactive": False,
    "run_until": lambda simulation: simulation.countGatewayPackets() >= 1000,
    "visualize_while_running": False,
    "time_delay": 0.2
}

simulator = sim.Simulator(1000, 100, 45, queue, settings)

render_thread = Thread(target=renderer.render, args=(queue,))
render_thread.start()

while simulator.simulate():
    print(simulator.printState())

print(simulator.printState())
