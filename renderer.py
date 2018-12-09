import pygame
from sim import *

black = 0, 0, 0
darkgray = 57, 57, 57
lightgray = 78, 78, 78
white = 255, 255, 255
blue = 0, 100, 255

def render(queue):
    print("renderer was started")
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
            line_color = 64, 64, 64
            dot_color = 255, 255, 255
            radius = 0
            if type(node) is Leader:
                dot_color = 255, 0, 0
                line_color = dot_color
                radius = 2
            elif type(node) is Follower:
                if node.packets >= 1:
                    dot_color = 0, 255, 0
                    line_color = dot_color
                    radius = 2
            elif type(node) is Gateway:
                dot_color = 0, 100, 255
                line_color = dot_color
                radius = 4

            pygame.draw.circle(screen, lightgray, (int(node.position[0]), int(node.position[1])), radius)

            for sig in node.signalsBLE:
                pygame.draw.line(screen, darkgray, (node.position), (sig.position))
                pygame.draw.circle(screen, dot_color, (int(node.position[0]), int(node.position[1])), radius)

            if type(node) is Leader:
                for sig in node.signalsLoRa:
                    pygame.draw.line(screen, darkgray, (node.position), (sig.position))
            if type(node) is Gateway:
                for sig in node.signalsLoRa:
                    pygame.draw.line(screen, blue, (node.position), (sig.position), 4)



        pygame.display.flip()
