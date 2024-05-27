from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from generator import RaceTrackGenerator

WIDTH = 700
HEIGHT = 700

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Race Track Generator")

g = RaceTrackGenerator(window)
g.generate_track()