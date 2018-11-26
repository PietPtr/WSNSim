import sim
from threading import Thread
import renderer
from queue import Queue

queue = Queue()

render_thread = Thread(target=renderer.render, args=(queue,))
render_thread.start()

settings = {
    "interactive": True,
    "run_until": lambda packets, collisions: packets >= 1000
}

simulator = sim.Simulator(1000, 100, 45, queue, settings)

while simulator.simulate():
    print(simulator.printState())

print(simulator.printState())
