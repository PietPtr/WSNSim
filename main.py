import sim
from threading import Thread
import renderer
from queue import Queue

queue = Queue()

render_thread = Thread(target=renderer.render, args=(queue,))
render_thread.start()

simulator = sim.Simulator(1000, 100, 45, queue)

while True:
    simulator.simulate()
