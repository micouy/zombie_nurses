from __future__ import division
from random import randint as rand, shuffle
from time import sleep
import pygame
import math
import os


clear = lambda: os.system('clear')


def get_distance(a, b):
	return math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2)


def get_time():
	return pygame.time.get_ticks()


class Vector(object):
	def __init__(self, x = 0, y = 0):
		self.x = x
		self.y = y


class Node(object):
	def __init__(self, x, y, value):
		self.x = x
		self.y = y
		self.value = value
		self.visited = False
		self.parent = None
		self.neighbors = None
			
	def reset(self):
		self.visited = False
		self.parent = None
		self.neighbors = None


class PathFinder(object):
	def __init__(self, sprite, level):
		self.sprite = sprite
		self.size = len(level) - 2
		self.all_nodes = [[Node(x, y, value) for x, value in enumerate(row)] for y, row in enumerate(level)]
		self.neighbors_positions = [
			Vector(0, -1),
			Vector(1, 0),
			Vector(0, 1),
			Vector(-1, 0),
		]
		self.visited_nodes = []
		self.current_path = []
		self.current_node = None
		self.found = False
		self.done = False

	def find_path(self, goal, start=None):
		self.goal = Vector(goal.x, goal.y)
		self.visited_nodes = []
		self.current_path = []
		self.found = False
		self.done = False

		for row in self.all_nodes:
			for node in row:
				node.reset()

		if self.sprite:
			self.current_node = self.all_nodes[self.sprite.y][self.sprite.x]
		elif start:
			self.current_node = self.all_nodes[start.y][start.x]
		else:
			return None
		self.current_path.append(self.current_node)

		while not (self.done or self.found):
			if self.current_node.x == self.goal.x and self.current_node.y == self.goal.y:
				self.found = True
				self.done = True
		
			self.current_node.neighbors = []
			for neighbor_position in self.neighbors_positions:
				position = Vector(self.current_node.x + neighbor_position.x, self.current_node.y + neighbor_position.y)
				if position.x < 0 or position.x > self.size + 1 or position.y < 0 or position.y > self.size + 1:
					break
				else:
					neighbor = self.all_nodes[position.y][position.x]
					if not (neighbor is self.current_node.parent or neighbor.visited or neighbor.value > 0 or neighbor in self.current_path):
						self.current_node.neighbors.append(neighbor)
		
			if len(self.current_node.neighbors) > 0:
				self.current_node.neighbors.sort(key=lambda node: get_distance(node, self.goal))
				previous = self.current_node
				self.current_node = self.current_node.neighbors[0]
				if self.current_node.parent is None:
					self.current_node.parent = previous
				self.current_path.append(self.current_node)
				if self.current_node.x == self.goal.x and self.current_node.y == self.goal.y:
					self.found = True
					self.done = True

					for node in self.current_path:
						neighbors_in_path = []
						for neighbor_position in self.neighbors_positions:
							position = Vector(node.x + neighbor_position.x, node.y + neighbor_position.y)
							if 0 <= position.x <= self.size + 1 and 0 <= position.y <= self.size + 1:
								neighbor = self.all_nodes[position.y][position.x]
					
							if neighbor in self.current_path and neighbor is not node.parent and node is not neighbor.parent:
								neighbors_in_path.append(neighbor)
						if len(neighbors_in_path):
							shuffle(neighbors_in_path)
							neighbors_in_path.sort(key=lambda node: self.current_path.index(node))
							del self.current_path[self.current_path.index(node) + 1 : self.current_path.index(neighbors_in_path[-1])]
			else:
				done = True
				for node in self.current_path:
					for neighbor in node.neighbors:
						if neighbor is not node.parent and node is not neighbor.parent and neighbor not in self.current_path:
							done = False
							break
					if not done:
						break
				if done:
					self.done = done			
					return
				while True:
					if len(self.current_node.neighbors) > 0:
						break
					self.current_node.visited = True
					self.visited_nodes.append(self.current_node)
					if self.current_node in self.current_path:
						self.current_path.remove(self.current_node)
					if self.current_node.parent is not None:
						if self.current_node in self.current_node.parent.neighbors:
							self.current_node.parent.neighbors.remove(self.current_node)
						self.current_node = self.current_node.parent
					else:
						self.done = True
		
		if self.found:
			return [Vector(node.x, node.y) for node in self.current_path]
		return None


class Sprite(object):
	def __init__(self, game):
		self.game = game
		if self not in self.game.sprites:
			self.game.sprites.append(self)
		self.level = self.game.level
		while True:
			self.x = rand(1, self.game.size)
			self.y = rand(1, self.game.size)
			if not self.level[self.y][self.x]:
				break
		self.new_position = Vector(self.x, self.y)

	def update(self):
		pass

	def draw(self):
		self.game.scene[self.y][self.x] = self.color

	def kill(self):
		self.game.sprites.remove(self)
		del self


class DoorKey(Sprite):
	def __init__(self, game):
		super(DoorKey, self).__init__(game)
		self.path_finder = PathFinder(self, self.level)
		self.player = self.game.player
		self.color = 4

		while True:
			self.x = rand(1, self.game.size + 1)
			self.y = rand(1, self.game.size + 1)
			if self.level[self.y][self.x]:
				continue
			path_to_player = self.path_finder.find_path(self.player)
			if self.path_finder.found:
				break

	def update(self):
		if self.x == self.player.x and self.y == self.player.y:
			self.game.sprites.remove(self)
			del self	


class Zombie(Sprite):
	def __init__(self, game):
		super(Zombie, self).__init__(game)
		self.player = self.game.player
		self.game.enemies.append(self)
		while True:
			self.x = rand(1, self.game.size + 1)
			self.y = rand(1, self.game.size + 1)
			if not self.level[self.y][self.x]:
				if get_distance(self, self.player) > 3:
					break
		self.color = 3
		self.cooldown = 1500
		self.last_move = 0
		self.movement_map = [[0 for i in range(self.game.size + 2)] for j in range(self.game.size + 2)]
		self.neighbors_positions = [
			[0, -1],
			[1, 0],
			[0, 1],
			[-1, 0],
		]
		self.path_finder = PathFinder(self, self.game.level)
		self.path_to_player = []
		self.last_player_position = Vector()
		shuffle(self.neighbors_positions)

	def update(self):
		if get_time() > self.last_move + self.cooldown:
			#if self.player.x == self.x and not any(row[self.x] for row in self.level[min(self.y, self.player.y):max(self.y, self.player.y)]):				
			#	distance = self.player.y - self.y
			#	if distance:				
			#		self.new_position.y = self.y + int(distance / abs(distance))
			#elif self.player.y == self.y and not any(cell for cell in self.level[self.y][min(self.x, self.player.x):max(self.x, self.player.x)]):
			#	distance = self.player.x - self.x
			#	if distance:
			#		self.new_position.x = self.x + int(distance / abs(distance))
			if get_distance(self, self.player) < 4:
				if self.last_player_position.x != self.player.x or self.last_player_position.y != self.player.y:
					self.path_to_player = self.path_finder.find_path(self.player)
					self.last_player_position.x = self.player.x
					self.last_player_position.y = self.player.y
				if self.path_to_player is not None and len(self.path_to_player):
					self.new_position.x = self.path_to_player[0].x
					self.new_position.y = self.path_to_player[0].y
					del self.path_to_player[0]
			else:
				neighbors = []
				for neighbor_position in self.neighbors_positions:
					x = self.x + neighbor_position[0]
					y = self.y + neighbor_position[1]
					if 0 <= x <= self.game.size + 1 and 0 <= y <= self.game.size + 1 and not self.level[y][x]:
						neighbors.append([x, y, self.movement_map[y][x]])
				if len(neighbors):
					neighbors.sort(key=lambda neighbor: neighbor[2])
					self.new_position.x = neighbors[0][0]
					self.new_position.y = neighbors[0][1]
					self.movement_map[self.new_position.y][self.new_position.x] += 1
			self.x = self.new_position.x
			self.y = self.new_position.y
			print 'zombie pos ', self.x, self.y
			self.last_move = get_time()
			self.cooldown = rand(1000, 2000)


class Bullet(Sprite):
	def __init__(self, game, sprite, direction):
		super(Bullet, self).__init__(game)
		self.x = sprite.x
		self.y = sprite.y
		self.color = 5
		self.sprite = sprite
		self.sprite.bullets.append(self)
		self.direction = direction
		self.last_move = 0
	
	def update(self):
		if get_time() > self.last_move + 300:
			self.x += self.direction[0]
			self.y += self.direction[1]
			self.last_move = get_time()
	
		for sprite in self.game.enemies:
			if sprite is self.sprite or sprite is self:
				continue
			
			if self.x == sprite.x and self.y == sprite.y:
				print sprite.__class__.__name__
				sprite.kill()
				self.kill()
	
		if self.level[self.y][self.x]:
			self.sprite.bullets.remove(self)
			self.kill()


class Player(Sprite):
	def __init__(self, game):
		super(Player, self).__init__(game)
		self.color = 2
		self.keys = {
			'w': False,
			's': False,
			'a': False,
			'd': False
		}
		self.hp = 2
		self.bullets_left = 3
		self.bullets = []
		self.last_shot = 0
		self.last_hit = 0
		self.direction = [1, 0]

	def update(self):
		keys = pygame.key.get_pressed()
		self.new_position.x = self.x
		self.new_position.y = self.y
		
		if keys[pygame.K_w]:
			if not self.keys['w']:
				self.new_position.y = self.y - 1
				self.direction[0] = 0
				self.direction[1] = -1
			self.keys['w'] = True
		else:
			self.keys['w'] = False
			if keys[pygame.K_s]:
				if not self.keys['s']:
					self.new_position.y = self.y + 1
					self.direction[0] = 0
					self.direction[1] = 1
				self.keys['s'] = True
			else:
				self.keys['s'] = False
				if keys[pygame.K_a]:
					if not self.keys['a']:
						self.new_position.x = self.x - 1
						self.direction[0] = -1
						self.direction[1] = 0
					self.keys['a'] = True
				else:
					self.keys['a'] = False
					if keys[pygame.K_d]:
						if not self.keys['d']:
							self.new_position.x = self.x + 1
							self.direction[0] = 1
							self.direction[1] = 0
						self.keys['d'] = True
					else:
						self.keys['d'] = False
		
		if keys[pygame.K_SPACE] and get_time() > self.last_shot + 500:
			if self.bullets_left > 0:
				self.shoot()
				self.last_shot = get_time()
				self.bullets_left -= 1
		if (self.new_position.x < 0 or self.new_position.x > self.game.size + 1
			or self.new_position.y < 0 or self.new_position.y > self.game.size + 1):
			self.game.start_game()
		else:
			if not self.level[self.new_position.y][self.new_position.x]:
				self.x = self.new_position.x
				self.y = self.new_position.y

			if get_time() > self.last_hit + 500:
				for enemy in self.game.enemies:
					if self.x == enemy.x and self.y == enemy.y:
						print 'hit by:', enemy.__class__.__name__, 'no.', self.game.enemies.index(enemy), 'at', (enemy.x, enemy.y), (self.x, self.y)						
						self.hp -= 1
						self.last_hit = get_time()
						break

			if self.hp <= 0:
				self.hp = 0	
			#	exit()

	def shoot(self):
		self.bullets.append(Bullet(self.game, self, list(self.direction)))


class Game(object):
	def __init__(self):
		self.size = 25
		self.tile_size = 18
		self.screen = pygame.display.set_mode(((self.size + 2) * self.tile_size, (self.size + 4) * self.tile_size))
		self.clock = pygame.time.Clock()
		self.start_game()

	def start_game(self):
		self.sprites = []
		self.enemies = []	
		self.level = [[0 if (i != 0 and i != self.size + 1 and j != 0 and j != self.size + 1) else 1 for i in range(self.size + 2)] for j in range(self.size + 2)]
		for i in range(int(self.size ** 2 * 0.35)):
			self.level[rand(1, self.size)][rand(1, self.size)] = 1
		
		self.path_finder = PathFinder(None, self.level)
		self.player = Player(self)
		
		while True:
			position = [rand(1, self.size + 1) for i in range(2)]
			position[rand(0, 1)] = rand(0, 1) * (self.size + 1)
			if self.path_finder.find_path(start=Vector(position[0], position[1]), goal=self.player) is not None:
				self.level[position[1]][position[0]] = 0
				print position
				break
		self.add_sprite(Zombie, 15)
		self.add_sprite(DoorKey, 3)
		print len(self.enemies)
		print '\n'.join([str(sprite.__class__.__name__) for sprite in self.sprites])
					
	def add_sprite(self, class_name, amount=1):
		for i in range(amount):
			class_name(self)

	def update(self):
		for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit()

		for sprite in self.sprites:
			sprite.update()

	def draw(self):
		self.scene = [list(row) for row in self.level]
		
		self.screen.fill(color_table[0])

		for sprite in self.sprites:
			sprite.draw()

		for y, row in enumerate(self.scene):
			for x, cell in enumerate(row):
				if cell:
					pygame.draw.rect(self.screen, color_table[cell], (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size))
	
		for hp in range(self.player.hp):
			if hp % 2:
				color = (200, 25, 25)
			else:
				color = (225, 15, 15)
			pygame.draw.rect(self.screen, color, ((self.size + 1 - hp) * self.tile_size, (self.size + 3) * self.tile_size, self.tile_size, self.tile_size))

		for bullet in range(self.player.bullets_left):
			if bullet % 2:
				color = (200, 200, 0)
			else:
				color = (225, 225, 0)
			pygame.draw.rect(self.screen, color, (bullet * self.tile_size, (self.size + 3) * self.tile_size, self.tile_size, self.tile_size))
		#scene = [[0 for i in range(self.size + 2)] for j in range(self.size + 2)]
		#for enemy in self.enemies:
		#	for y, row in enumerate(enemy.movement_map):
		#		for x, cell in enumerate(row):
		#			scene[y][x] += cell
		#for y, row in enumerate(scene):
		#	for x, cell in enumerate(row):
		#		if cell*5 > 255:
		#			cell = 255/5
		#		pygame.draw.rect(self.screen, (cell*5, cell*5, cell*5), (x*self.tile_size, y*self.tile_size, self.tile_size, self.tile_size))

		#clear()
		#print '\n'.join([''.join([str(cell) for cell in row]) for row in self.enemies[0].movement_map])
		
		pygame.display.update()

	def run(self):
		while True:
			self.update()
			self.draw()
			self.clock.tick(25)

color_table = [
	(15, 15, 15),		# 0.
	(75, 75, 65),		# 1. - wall
	(175, 175, 200),	# 2. - player
	(150, 225, 50),		# 3. - zombie
	(250, 175, 0),		# 4. - key
	(225, 225, 0),		# 5. - bullet
	(255, 0, 0),		# 6. - marked zombie
]

game = Game()
game.run()













	
