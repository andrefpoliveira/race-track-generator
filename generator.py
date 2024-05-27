import math
import os
import pygame
import pickle

import numpy as np
import random as rn

from colorama import Fore
from scipy.spatial import ConvexHull
from scipy import interpolate

MIN_POINTS = 10
MAX_POINTS = 15
MARGIN = 100

GREEN = (87, 145, 60)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (110, 110, 110)


class RaceTrackGenerator:
	def __init__(self, window: pygame.Surface, display_checkpoints: bool = True, filename: str = "track"):
		self.window = window
		self.display_checkpoints = display_checkpoints
		self.filename = filename

		self._track = []
		self._checkpoints = []

	@property
	def track(self) -> list:
		return self._track

	@property
	def checkpoints(self) -> list:
		return self._checkpoints

	def load_track(self, filename: str) -> list:
		if not os.path.exists(filename):
			raise FileNotFoundError(Fore.RED + f"File {filename} not found. Verify the path introduced or generate a new track." + Fore.RESET)

		with open(filename, "rb") as file:
			self._track = pickle.load(file)
			self._checkpoints = self._track[::20]

		self.display_track()

	def generate_track(self) -> None:
		points = self._generate_points()

		for _ in range(3):
			self._push_points_apart(points)

		hull = ConvexHull(points)

		track = self._generate_perturbation_points([points[hull.vertices[i]] for i in range(len(hull.vertices))])

		for _ in range(10):
			self.fix_angles(track)
			self._push_points_apart(track)

		self._track = self._smooth_track(track)
		self._checkpoints = self._track[::20]

		with open(f"{self.filename}.pkl", "wb") as file:
			pickle.dump(self._track, file)

		self.display_track()
		self._save_track_image()


	def _generate_points(self, min_p: int = MIN_POINTS, max_p: int = MAX_POINTS, m: int = MARGIN) -> list:
		amount_points = rn.randint(min_p, max_p)
		points = []
		for _ in range(amount_points):
			x = rn.randint(0 + m, self.window.get_width() - m)
			y = rn.randint(0 + m, self.window.get_height() - m)
			points.append((x, y))
		return points


	def _generate_random_2d_vector(self, magnitude: int = 1) -> tuple:
		angle = rn.random() * 360
		return (-math.sin(math.radians(angle)) * magnitude, math.cos(math.radians(angle)) * magnitude)


	def _generate_perturbation_points(self, points: list, diffic: int = 0.5, max_disp: int = 30) -> list:
		_points = []
		for i in range(len(points)):
			dist = math.pow(rn.random(), diffic) * max_disp
			disp = [dist * i for i in self._generate_random_2d_vector()]

			_points.append(points[i])
			_points.append((
				(points[i][0] + points[(i + 1) % len(points)][0]) / 2 + disp[0],
				(points[i][1] + points[(i + 1) % len(points)][1]) / 2 + disp[1]
			))

		return _points


	def _smooth_track(self, points: list) -> list:
		x = np.array([p[0] for p in points])
		y = np.array([p[1] for p in points])

		x = np.r_[x, x[0]]
		y = np.r_[y, y[0]]

		tck, u = interpolate.splprep([x, y], s=0, per=True)

		xi, yi = interpolate.splev(np.linspace(0, 1, 1000), tck)
		return [(int(xi[i]), int(yi[i])) for i in range(len(xi))]


	def _push_points_apart(self, points: list, distance: int = 40) -> None:
		distance2 = distance * distance
		for i in range(len(points)):
			for j in range(i+1, len(points)):
				p_distance =  math.sqrt((points[i][0]-points[j][0])**2 + (points[i][1]-points[j][1])**2)
				if p_distance < distance:
					dx = points[j][0] - points[i][0]
					dy = points[j][1] - points[i][1]
					dl = math.sqrt(dx*dx + dy*dy)
					dx /= dl
					dy /= dl
					dif = distance - dl
					dx *= dif
					dy *= dif
					points[j] = (points[j][0] + dx, points[j][1] + dy)
					points[i] = (points[i][0] - dx, points[i][1] - dy)


	def fix_angles(self, dataset: list) -> None:
		for i in range(len(dataset)):
			previous, next = (i-1)%len(dataset), (i+1)%len(dataset)
			px, py = dataset[i][0] - dataset[previous][0], dataset[i][1] - dataset[previous][1]
			pl = math.sqrt(px*px + py*py)
			px /= pl
			py /= pl

			nx, ny = dataset[next][0] - dataset[i][0], dataset[next][1] - dataset[i][1]
			nl = math.sqrt(nx*nx + ny*ny)
			nx /= nl
			ny /= nl

			a = math.atan2(px * ny -py *nx, px * nx + py * ny)
			if abs(math.degrees(a)) <= 100:
				continue

			nA = math.radians(100 * np.sign(a))
			diff = nA - a
			cos = math.cos(diff)
			sin = math.sin(diff)
			new_x = (nx * cos - ny * sin) * nl
			new_y = (nx * sin + ny * cos) * nl
			dataset[next] = (dataset[i][0] + new_x, dataset[i][1] + new_y)


	def display_track(self) -> None:
		self.window.fill(GREEN)

		TRACK_WIDTH = 30
		radius = TRACK_WIDTH // 2
		chunk_dimensions = (radius * 2, radius * 2)

		for point in self._track:
			blit_pos = (point[0] - radius, point[1] - radius)
			track_chunk = pygame.Surface(chunk_dimensions, pygame.SRCALPHA)
			pygame.draw.circle(track_chunk, GRAY, (radius, radius), radius)
			self.window.blit(track_chunk, blit_pos)

		if self.display_checkpoints:
			pygame.draw.circle(self.window, YELLOW, self._track[0], 3)

			for id, p in enumerate(self.checkpoints[1:]):
				pygame.draw.circle(self.window, BLUE, p, 2)

	
	def _save_track_image(self) -> None:
		pygame.image.save(self.window, f"{self.filename}.png")
