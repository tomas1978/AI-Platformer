"""Game rules and fixed-step physics for Glödsprång.

The simulation does not require a window or an audio device, so the same rules
can be exercised by the headless test suite and the interactive game.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

import pygame

from levels import LEVELS

WIDTH, HEIGHT = 960, 640
PLAYER_SPEED = 285.0
JUMP_SPEED = 650.0
GRAVITY = 1750.0
MAX_FALL_SPEED = 900.0


class SilentAudio:
    muted = True

    def play(self, name):
        pass

    def start_music(self):
        pass

    def toggle_mute(self):
        return True


@dataclass
class InputState:
    left: bool = False
    right: bool = False
    jump_pressed: bool = False
    jump_held: bool = False
    shoot_pressed: bool = False
    shoot_held: bool = False


@dataclass
class Player:
    rect: pygame.Rect
    pos: pygame.Vector2
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)
    facing: int = 1
    grounded: bool = False
    powered: bool = False
    invulnerable: float = 0.0
    coyote: float = 0.0
    jump_buffer: float = 0.0
    shoot_cooldown: float = 0.0


@dataclass
class Enemy:
    kind: str
    rect: pygame.Rect
    pos: pygame.Vector2
    direction: int = -1
    alive: bool = True
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)

    def can_be_defeated(self, attack: str) -> bool:
        return self.kind == "walker" or (self.kind == "armored" and attack == "shot")


@dataclass
class Projectile:
    rect: pygame.Rect
    pos: pygame.Vector2
    vel: pygame.Vector2
    life: float = 2.2


@dataclass
class Boss:
    rect: pygame.Rect
    pos: pygame.Vector2
    hp: int = 60
    max_hp: int = 60
    direction: int = -1
    hurt_time: float = 0.0
    fire_timer: float = 1.0

    def take_hit(self, attack: str) -> bool:
        """Fifteen shots or twenty stomps defeat the boss; attacks can mix."""
        if self.hp <= 0:
            return False
        if attack not in ("shot", "stomp"):
            raise ValueError(f"Unknown attack: {attack}")
        self.hp = max(0, self.hp - (4 if attack == "shot" else 3))
        self.hurt_time = 0.18
        return self.hp == 0


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    color: tuple[int, int, int]
    life: float
    max_life: float
    size: float


@dataclass
class FloatingText:
    pos: pygame.Vector2
    text: str
    color: tuple[int, int, int]
    life: float = 1.3


def move_actor(pos, rect, velocity, dt, solids):
    """Resolve each axis separately; keep subpixel movement between steps."""
    hit_wall = grounded = False
    pos.x += velocity.x * dt
    rect.x = round(pos.x)
    for solid in solids:
        if rect.colliderect(solid):
            if velocity.x > 0:
                rect.right = solid.left
            elif velocity.x < 0:
                rect.left = solid.right
            pos.x = rect.x
            hit_wall = True
    pos.y += velocity.y * dt
    rect.y = round(pos.y)
    for solid in solids:
        if rect.colliderect(solid):
            if velocity.y > 0:
                rect.bottom = solid.top
                grounded = True
            elif velocity.y < 0:
                rect.top = solid.bottom
            pos.y = rect.y
            velocity.y = 0
    return hit_wall, grounded


class Game:
    def __init__(self, audio=None, seed=7):
        self.audio = audio or SilentAudio()
        self.rng = random.Random(seed)
        self.state = "menu"
        self.time = 0.0
        self.level_time = 0.0
        self.score = 0
        self.lives = 3
        self.level_start_score = 0
        self.checkpoint = False
        self.load_level(0, powered=False)

    def start_new(self):
        self.score = 0
        self.level_start_score = 0
        self.lives = 3
        self.checkpoint = False
        self.load_level(0, powered=False)
        self.state = "playing"
        self.audio.start_music()

    def load_level(self, index, powered=None, at_checkpoint=False):
        if powered is None:
            powered = self.player.powered if hasattr(self, "player") else False
        self.level_index = index
        self.level = LEVELS[index]
        self.platforms = [pygame.Rect(p) for p in self.level.platforms]
        spawn = self.level.spawn
        if at_checkpoint and self.level.boss_spawn:
            spawn = (self.level.width - 955, 514)
            powered = True
        self.player = Player(pygame.Rect(*spawn, 30, 46), pygame.Vector2(spawn), powered=powered)
        self.enemies = [Enemy(k, pygame.Rect(x, y, 34, 34), pygame.Vector2(x, y))
                        for k, x, y in self.level.enemies]
        self.coins = [pygame.Vector2(p) for p in self.level.coins]
        self.powerups = [pygame.Vector2(p) for p in self.level.powerups]
        self.bullets = []
        self.fireballs = []
        self.particles = []
        self.floating_texts = []
        self.boss = None
        if self.level.boss_spawn:
            x, y = self.level.boss_spawn
            self.boss = Boss(pygame.Rect(x, y, 120, 128), pygame.Vector2(x, y))
        self.camera_x = max(0.0, min(float(self.level.width - WIDTH), spawn[0] - 280.0))
        self.shake = 0.0
        self.level_time = 0.0
        self.checkpoint = at_checkpoint

    def restart_checkpoint(self):
        self.score = self.level_start_score
        self.lives = 3
        self.load_level(self.level_index, at_checkpoint=self.checkpoint)
        self.state = "playing"
        self.audio.start_music()

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"

    def teleport_player(self, x, y):
        """Synchronize float and collision positions (also useful for tooling)."""
        self.player.pos.update(x, y)
        self.player.rect.topleft = round(x), round(y)
        self.player.vel.update(0, 0)
        self.player.grounded = False

    def burst(self, position, color, count=12, speed=150):
        for _ in range(count):
            a = self.rng.uniform(0, math.tau)
            life = self.rng.uniform(0.25, 0.65)
            velocity = pygame.Vector2(math.cos(a), math.sin(a)) * self.rng.uniform(speed * .3, speed)
            self.particles.append(Particle(pygame.Vector2(position), velocity, color, life, life,
                                           self.rng.uniform(2, 5)))

    def label(self, position, text, color=(255, 221, 120)):
        self.floating_texts.append(FloatingText(pygame.Vector2(position), text, color))

    def update(self, dt, controls=None):
        dt = max(0.0, min(dt, 1 / 30))
        self.time += dt
        if self.state != "playing":
            return
        self.level_time += dt
        self.shake = max(0, self.shake - dt * 18)
        controls = controls or InputState()
        p = self.player
        p.invulnerable = max(0, p.invulnerable - dt)
        p.shoot_cooldown = max(0, p.shoot_cooldown - dt)
        p.coyote = .1 if p.grounded else max(0, p.coyote - dt)
        p.jump_buffer = .12 if controls.jump_pressed else max(0, p.jump_buffer - dt)
        direction = int(controls.right) - int(controls.left)
        target = direction * PLAYER_SPEED
        acceleration = 2400 if p.grounded else 1700
        p.vel.x += max(-acceleration * dt, min(acceleration * dt, target - p.vel.x))
        if direction:
            p.facing = direction
        if p.jump_buffer > 0 and p.coyote > 0:
            p.vel.y = -JUMP_SPEED
            p.jump_buffer = p.coyote = 0
            p.grounded = False
            self.audio.play("jump")
            self.burst(p.rect.midbottom, (183, 224, 187), 5, 90)
        if not controls.jump_held and p.vel.y < -250:
            p.vel.y += GRAVITY * dt * .9
        p.vel.y = min(MAX_FALL_SPEED, p.vel.y + GRAVITY * dt)
        previous_bottom = p.rect.bottom
        near_solids = [r for r in self.platforms if r.right > p.rect.left - 24 and r.left < p.rect.right + 24]
        _, p.grounded = move_actor(p.pos, p.rect, p.vel, dt, near_solids)
        if p.rect.left < 0:
            p.rect.left = 0
            p.pos.x = 0
        if p.rect.right > self.level.width:
            p.rect.right = self.level.width
            p.pos.x = p.rect.x
        if (controls.shoot_held or controls.shoot_pressed) and p.powered and p.shoot_cooldown <= 0:
            center = pygame.Vector2(p.rect.centerx + p.facing * 20, p.rect.centery + 2)
            rect = pygame.Rect(0, 0, 14, 8)
            rect.center = round(center.x), round(center.y)
            self.bullets.append(Projectile(rect, pygame.Vector2(rect.topleft), pygame.Vector2(p.facing * 650, 0)))
            p.shoot_cooldown = .23
            self.audio.play("shoot")
            self.burst(center, (110, 226, 255), 3, 75)
        if p.rect.top > HEIGHT + 120:
            self._fall()
            return
        self._collect_items()
        self._update_enemies(dt, previous_bottom)
        self._update_boss(dt, previous_bottom)
        self._update_projectiles(dt)
        self._update_effects(dt)
        if self.state != "playing":
            return
        if p.rect.centerx >= self.level.goal_x and (self.boss is None or self.boss.hp <= 0):
            self._complete_level()
            return
        target_camera = max(0, min(self.level.width - WIDTH, p.rect.centerx - WIDTH * .38))
        self.camera_x += (target_camera - self.camera_x) * min(1, dt * 7)

    def _collect_items(self):
        p = self.player
        for coin in self.coins[:]:
            if p.rect.colliderect(pygame.Rect(coin.x - 11, coin.y - 11, 22, 22)):
                self.coins.remove(coin)
                self.score += 10
                self.audio.play("pickup")
                self.burst(coin, (255, 214, 90), 8, 110)
        for item in self.powerups[:]:
            if p.rect.colliderect(pygame.Rect(item.x - 17, item.y - 17, 34, 34)):
                self.powerups.remove(item)
                p.powered = True
                self.audio.play("pickup")
                self.label(item, "SKJUTBONUS!", (116, 234, 255))
                self.burst(item, (86, 223, 255), 24, 180)

    def _defeat_enemy(self, enemy, attack):
        if not enemy.alive or not enemy.can_be_defeated(attack):
            return False
        enemy.alive = False
        self.score += 100
        self.audio.play("stomp" if attack == "stomp" else "enemy_die")
        self.burst(enemy.rect.center, (255, 171, 100), 16, 170)
        self.label(enemy.rect.midtop, "+100")
        return True

    def _update_enemies(self, dt, previous_bottom):
        p = self.player
        for e in self.enemies:
            if not e.alive:
                continue
            speed = {"walker": 64, "armored": 48, "spike": 82}[e.kind]
            foot_probe = pygame.Rect(e.rect.centerx + e.direction * 25, e.rect.bottom + 1, 5, 8)
            has_ground = any(foot_probe.colliderect(r) for r in self.platforms)
            if e.vel.y == 0 and not has_ground:
                e.direction *= -1
            e.vel.x = e.direction * speed
            e.vel.y = min(MAX_FALL_SPEED, e.vel.y + GRAVITY * dt)
            solids = [r for r in self.platforms if r.right > e.rect.left - 10 and r.left < e.rect.right + 10]
            wall, _ = move_actor(e.pos, e.rect, e.vel, dt, solids)
            if wall:
                e.direction *= -1
            if e.rect.top > HEIGHT + 100:
                e.alive = False
            if e.alive and p.rect.colliderect(e.rect):
                stomp = p.vel.y > 0 and previous_bottom <= e.rect.top + 13
                if stomp and self._defeat_enemy(e, "stomp"):
                    p.rect.bottom = e.rect.top
                    p.pos.y = p.rect.y
                    p.vel.y = -470
                else:
                    self._hurt_player(e.rect.centerx)

    def _boss_hit(self, attack):
        if self.boss is None or self.boss.hp <= 0:
            return
        died = self.boss.take_hit(attack)
        self.audio.play("boss_hit")
        self.shake = 5
        self.burst(self.boss.rect.center, (255, 196, 106), 14, 210)
        if died:
            self.score += 1500
            self.fireballs.clear()
            self.audio.play("victory")
            self.label(self.boss.rect.midtop, "ASKKRONAN ÄR DIN!")
            self.burst(self.boss.rect.center, (255, 214, 93), 80, 310)

    def _update_boss(self, dt, previous_bottom):
        boss = self.boss
        if boss is None:
            return
        boss.hurt_time = max(0, boss.hurt_time - dt)
        if boss.hp <= 0:
            return
        p = self.player
        if p.rect.centerx < self.level.width - 1040:
            return
        if not self.checkpoint:
            self.checkpoint = True
            self.label((self.level.width - 950, 460), "KONTROLLPUNKT", (119, 241, 213))
        boss.pos.x += boss.direction * 68 * dt
        if boss.pos.x < self.level.width - 630:
            boss.pos.x = self.level.width - 630
            boss.direction = 1
        if boss.pos.x > self.level.width - 420:
            boss.pos.x = self.level.width - 420
            boss.direction = -1
        boss.rect.x = round(boss.pos.x)
        boss.fire_timer -= dt
        if boss.fire_timer <= 0:
            boss.fire_timer = 1.75 if boss.hp > 24 else 1.25
            facing = -1 if p.rect.centerx < boss.rect.centerx else 1
            origin = pygame.Vector2(boss.rect.centerx + facing * 53, boss.rect.top + 72)
            aim = pygame.Vector2(p.rect.center) - origin
            if aim.length_squared() < 1:
                aim = pygame.Vector2(facing, 0)
            aim = aim.normalize() * 290
            for angle in (-12, 0, 12):
                rect = pygame.Rect(0, 0, 22, 22)
                rect.center = round(origin.x), round(origin.y)
                self.fireballs.append(Projectile(rect, pygame.Vector2(rect.topleft), aim.rotate(angle), 3.1))
            self.audio.play("fire")
            self.burst(origin, (255, 130, 62), 12, 120)
        if p.rect.colliderect(boss.rect):
            if p.vel.y > 0 and previous_bottom <= boss.rect.top + 16:
                p.rect.bottom = boss.rect.top
                p.pos.y = p.rect.y
                p.vel.y = -560
                self._boss_hit("stomp")
                self.audio.play("stomp")
            else:
                self._hurt_player(boss.rect.centerx)

    def _update_projectiles(self, dt):
        for bullet in self.bullets[:]:
            bullet.life -= dt
            bullet.pos += bullet.vel * dt
            bullet.rect.topleft = round(bullet.pos.x), round(bullet.pos.y)
            consumed = bullet.life <= 0 or any(bullet.rect.colliderect(r) for r in self.platforms)
            if not consumed:
                for e in self.enemies:
                    if e.alive and bullet.rect.colliderect(e.rect):
                        self._defeat_enemy(e, "shot")
                        if e.kind == "spike":
                            self.burst(bullet.rect.center, (194, 188, 227), 5, 80)
                        consumed = True
                        break
            if not consumed and self.boss and self.boss.hp > 0 and bullet.rect.colliderect(self.boss.rect):
                self._boss_hit("shot")
                consumed = True
            if consumed:
                self.bullets.remove(bullet)
        for fire in self.fireballs[:]:
            fire.life -= dt
            fire.pos += fire.vel * dt
            fire.rect.topleft = round(fire.pos.x), round(fire.pos.y)
            consumed = fire.life <= 0 or any(fire.rect.colliderect(r) for r in self.platforms)
            if not consumed and fire.rect.colliderect(self.player.rect.inflate(-8, -6)):
                self._hurt_player(fire.rect.centerx)
                consumed = True
            if consumed:
                self.fireballs.remove(fire)

    def _hurt_player(self, source_x):
        p = self.player
        if p.invulnerable > 0 or self.state != "playing":
            return
        self.lives -= 1
        p.invulnerable = 1.6
        p.vel.update(-240 if source_x > p.rect.centerx else 240, -310)
        self.shake = 8
        self.audio.play("hurt")
        self.burst(p.rect.center, (255, 111, 115), 18, 190)
        if self.lives <= 0:
            self.state = "game_over"

    def _fall(self):
        self.lives -= 1
        self.audio.play("hurt")
        if self.lives <= 0:
            self.state = "game_over"
            return
        remaining = self.lives
        power = self.player.powered
        checkpoint = self.checkpoint
        self.score = self.level_start_score
        self.load_level(self.level_index, powered=power, at_checkpoint=checkpoint)
        self.lives = remaining
        self.player.invulnerable = 1.6

    def _complete_level(self):
        self.score += 500
        self.audio.play("level_complete")
        if self.level_index == len(LEVELS) - 1:
            self.state = "victory"
            self.audio.play("victory")
        else:
            power = self.player.powered
            self.level_start_score = self.score
            self.lives = 3
            self.load_level(self.level_index + 1, powered=power)

    def _update_effects(self, dt):
        for particle in self.particles[:]:
            particle.life -= dt
            particle.vel.y += 300 * dt
            particle.pos += particle.vel * dt
            if particle.life <= 0:
                self.particles.remove(particle)
        for text in self.floating_texts[:]:
            text.life -= dt
            text.pos.y -= 30 * dt
            if text.life <= 0:
                self.floating_texts.remove(text)
