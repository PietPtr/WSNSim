import pygame
from sim import *

black = 0, 0, 0
darkgray = 57, 88, 85
lightgray = 78, 104, 83
white = 255, 255, 255

def render(queue):
    pygame.init()

    size = width, height = 1000, 1000

    screen = pygame.display.set_mode(size)
    screen.fill(black)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    zoom *= 1.1
                if event.button == 5:
                    zoom /= 1.1

        data = queue.get()
        if data == None:
            continue

        screen.fill(black)

        for node in data:
            color = white
            radius = 0
            if type(node) is Leader:
                color = 255, 0, 0
                radius = 2
            elif type(node) is Follower:
                if node.packets >= 1:
                    color = 0, 255, 0
                    radius = 2
            pygame.draw.circle(screen, color, (int(node.position[0]), int(node.position[1])), radius)

            for sig in node.signals:
                pygame.draw.line(screen, color, (node.position), (sig.position))

        pygame.display.flip()
