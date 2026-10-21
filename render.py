"""Original, asset-free artwork and Swedish interface for Glödsprång."""
from __future__ import annotations

import math
import pygame

WIDTH, HEIGHT = 960, 640
INK = (24, 29, 44)
CREAM = (255, 245, 215)
GOLD = (255, 203, 94)
TEAL = (83, 229, 199)


def mix(a, b, amount):
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


class Renderer:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = {}
        self.fonts = {}
        self.backgrounds = {}
        self.offset = pygame.Vector2()
        self.camera = 0.0
        self.clock = 0.0
        self.pointer = None

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            # Explicit bundled-system font paths keep Swedish glyphs portable.
            path = pygame.font.match_font("dejavusans", bold=bold)
            self.fonts[key] = pygame.font.Font(path, size)
        return self.fonts[key]

    def text(self, value, pos, size=20, color=CREAM, bold=False, center=False, shadow=False):
        font = self.font(size, bold)
        rendered = font.render(str(value), True, color)
        rect = rendered.get_rect(center=pos) if center else rendered.get_rect(topleft=pos)
        if shadow:
            dark = font.render(str(value), True, INK)
            self.surface.blit(dark, rect.move(0, 3))
        self.surface.blit(rendered, rect)
        return rect

    def panel(self, rect, color=(19, 30, 46, 228), radius=16, border=None):
        rect = pygame.Rect(rect)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, color, layer.get_rect(), border_radius=radius)
        if border:
            pygame.draw.rect(layer, border, layer.get_rect(), 1, border_radius=radius)
        self.surface.blit(layer, rect)

    def glow(self, center, radius, color, strength=55):
        radius = max(2, int(radius))
        layer = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        for i in range(4, 0, -1):
            r = max(1, int(radius * i / 4))
            pygame.draw.circle(layer, (*color[:3], int(strength / i)), (radius + 2, radius + 2), r)
        self.surface.blit(layer, (center[0] - radius - 2, center[1] - radius - 2))

    def world_rect(self, rect):
        return pygame.Rect(round(rect.x - self.camera + self.offset.x), round(rect.y + self.offset.y), rect.w, rect.h)

    def point(self, point):
        return pygame.Vector2(point[0] - self.camera + self.offset.x, point[1] + self.offset.y)

    def draw(self, game):
        self.buttons.clear()
        self.clock = game.time
        self.camera = game.camera_x
        shake = getattr(game, "shake", 0)
        self.offset.update(math.sin(self.clock * 83) * shake, math.cos(self.clock * 69) * shake * .55)
        self._background(game)
        self._world(game)
        if game.state == "menu":
            self._menu(game)
        else:
            self._hud(game)
            if game.state == "playing":
                self._level_title(game)
            elif game.state == "paused":
                self._pause(game)
            elif game.state == "game_over":
                self._ending(game, False)
            elif game.state == "victory":
                self._ending(game, True)

    def _background(self, game):
        p = game.level.palette
        key = (p["sky_top"], p["sky_bottom"])
        if key not in self.backgrounds:
            sky = pygame.Surface((WIDTH, HEIGHT))
            for y in range(HEIGHT):
                pygame.draw.line(sky, mix(key[0], key[1], y / HEIGHT), (0, y), (WIDTH, y))
            self.backgrounds[key] = sky
        self.surface.blit(self.backgrounds[key], (0, 0))
        if game.level_index == 2:
            for i in range(48):
                x = (i * 193 + 31 - self.camera * .08) % 1020 - 30
                y = 65 + (i * 79) % 280
                radius = 1 if i % 4 else 2
                pygame.draw.circle(self.surface, (255, 219, 155), (int(x), int(y)), radius)
            self.glow((755, 162), 92, (255, 134, 80), 24)
            pygame.draw.circle(self.surface, (255, 182, 119), (755, 162), 37)
            pygame.draw.circle(self.surface, p["sky_top"], (770, 148), 33)
        else:
            sun = (794 - self.camera * .025, 135)
            self.glow(sun, 110, (255, 231, 159), 35)
            pygame.draw.circle(self.surface, (255, 238, 181), sun, 43)
            for i in range(7):
                x = ((i * 211 - self.camera * .14 + self.clock * 2) % 1260) - 130
                y = 99 + (i * 61) % 165
                self._cloud(x, y, .65 + (i % 3) * .15, mix(p["sky_bottom"], CREAM, .55))
        # Two continuous, deterministic parallax ranges.
        for layer, (factor, color, base, height) in enumerate(((.14, p["far"], 483, 205), (.31, p["near"], 552, 137))):
            points = [(-40, HEIGHT)]
            for x in range(-60, WIDTH + 100, 40):
                wx = x + self.camera * factor
                y = base - height * (.5 + .32 * math.sin(wx / 169 + layer * 2) + .17 * math.sin(wx / 74))
                points.append((x, y))
            points.extend([(WIDTH + 80, HEIGHT), (-40, HEIGHT)])
            pygame.draw.polygon(self.surface, color, points)
        # Small silhouettes lend the near range scale.
        for i in range(12):
            x = (i * 157 - self.camera * .41) % 1200 - 100
            y = 449 + (i * 17) % 54
            color = mix(p["near"], p["ground"], .24)
            if game.level_index == 2:
                pygame.draw.rect(self.surface, color, (x, y - 80, 40, 150))
                for turret in range(3):
                    pygame.draw.rect(self.surface, color, (x + turret * 14, y - 92, 10, 15))
            else:
                pygame.draw.rect(self.surface, color, (x + 14, y, 8, 70))
                pygame.draw.polygon(self.surface, color, [(x - 14, y + 20), (x + 18, y - 47), (x + 49, y + 20)])
                pygame.draw.polygon(self.surface, color, [(x - 7, y - 5), (x + 18, y - 65), (x + 43, y - 5)])

    def _cloud(self, x, y, scale, color):
        for dx, dy, radius in ((0, 8, 23), (27, -5, 34), (63, 4, 25), (83, 13, 17)):
            pygame.draw.circle(self.surface, color, (round(x + dx * scale), round(y + dy * scale)), round(radius * scale))
        pygame.draw.rect(self.surface, color, (x, y + 5 * scale, 83 * scale, 24 * scale), border_radius=8)

    def _world(self, game):
        p = game.level.palette
        for platform in game.platforms:
            rect = self.world_rect(platform)
            if rect.right < -10 or rect.left > WIDTH + 10:
                continue
            pygame.draw.rect(self.surface, p["ground"], rect, border_radius=3)
            pygame.draw.rect(self.surface, mix(p["ground"], INK, .24), (rect.x, rect.y + 10, rect.w, 7))
            pygame.draw.rect(self.surface, p["grass"], (rect.x, rect.y, rect.w, 9), border_radius=3)
            pygame.draw.line(self.surface, mix(p["grass"], CREAM, .35), rect.topleft, (rect.right - 1, rect.y), 2)
            # Exposed edge and stone seams are world aligned, never flicker.
            for xx in range((platform.x // 40) * 40, platform.right, 40):
                sx = round(xx - self.camera + self.offset.x)
                if -40 <= sx <= WIDTH:
                    for yy in range(platform.y + 27, min(platform.bottom, HEIGHT + 30), 35):
                        stagger = 18 if (yy // 35) % 2 else 0
                        c = mix(p["ground"], CREAM, .10 if (xx // 40 + yy // 35) % 3 else .17)
                        pygame.draw.rect(self.surface, c, (sx + 7 + stagger, yy, 13, 5), border_radius=2)
            if game.level_index < 2:
                for xx in range(platform.x + 18, platform.right - 8, 93):
                    sx = round(xx - self.camera + self.offset.x)
                    if -10 < sx < WIDTH + 10:
                        pygame.draw.line(self.surface, p["grass"], (sx, rect.top), (sx - 3, rect.top - 8), 2)
                        pygame.draw.line(self.surface, p["grass"], (sx, rect.top), (sx + 5, rect.top - 5), 2)
                        if xx % 3 == 0:
                            pygame.draw.circle(self.surface, GOLD, (sx - 4, rect.top - 10), 3)
        for coin in game.coins:
            pos = self.point(coin)
            if -30 < pos.x < WIDTH + 30:
                stretch = max(3, round(8 * abs(math.cos(self.clock * 4 + coin.x * .02))))
                pygame.draw.ellipse(self.surface, (135, 89, 34), (pos.x - stretch, pos.y - 11, stretch * 2, 22))
                pygame.draw.ellipse(self.surface, GOLD, (pos.x - stretch, pos.y - 11, stretch * 2, 19))
                if stretch > 4:
                    pygame.draw.line(self.surface, (255, 246, 170), (pos.x - 2, pos.y - 6), (pos.x - 2, pos.y + 4), 2)
        for powerup in game.powerups:
            pos = self.point(powerup)
            pos.y += math.sin(self.clock * 3 + pos.x) * 4
            self._powerup(pos)
        self._goal(game)
        for enemy in game.enemies:
            if enemy.alive:
                rect = self.world_rect(enemy.rect)
                if -70 < rect.x < WIDTH + 70:
                    self._enemy(rect, enemy.kind, enemy.direction)
        if game.boss and game.boss.hp > 0:
            rect = self.world_rect(game.boss.rect)
            if -180 < rect.x < WIDTH + 160:
                self._boss(rect, game.boss.direction, game.boss.hurt_time > 0)
        for bullet in game.bullets:
            rect = self.world_rect(bullet.rect)
            self.glow(rect.center, 18, (115, 229, 255), 40)
            pygame.draw.ellipse(self.surface, (88, 188, 255), rect.inflate(5, 3))
            pygame.draw.ellipse(self.surface, (225, 255, 245), rect)
        for fire in game.fireballs:
            rect = self.world_rect(fire.rect)
            self.glow(rect.center, 30, (255, 119, 45), 45)
            direction = 1 if fire.vel.x < 0 else -1
            pygame.draw.polygon(self.surface, (238, 77, 40), [(rect.centerx + direction * 28, rect.y - 3), rect.bottomleft, rect.bottomright])
            pygame.draw.ellipse(self.surface, (255, 133, 51), rect.inflate(6, 6))
            pygame.draw.ellipse(self.surface, (255, 229, 132), rect.inflate(-5, -3))
        player = game.player
        if not (player.invulnerable > 0 and int(self.clock * 16) % 2):
            self._hero(self.world_rect(player.rect), player.facing, player.powered, player.grounded, abs(player.vel.x) > 5)
        for particle in game.particles:
            pos = self.point(particle.pos)
            fraction = max(0, min(1, particle.life / particle.max_life))
            pygame.draw.circle(self.surface, particle.color, (round(pos.x), round(pos.y)), max(1, round(particle.size * fraction)))
        for item in game.floating_texts:
            self.text(item.text, self.point(item.pos), 17, item.color, True, center=True, shadow=True)
        if game.level_index == 2:
            for i in range(15):
                x = (i * 149 + self.clock * (8 + i % 7) - self.camera * .3) % 1030 - 30
                y = 620 - (self.clock * 22 + i * 67) % 520
                pygame.draw.circle(self.surface, (245, 150 + i % 50, 64), (int(x), int(y)), 1 + i % 2)

    def _powerup(self, pos):
        self.glow(pos, 34, (97, 211, 255), 35)
        pygame.draw.circle(self.surface, (20, 88, 134), pos, 17)
        pygame.draw.circle(self.surface, (92, 217, 255), pos, 14)
        pygame.draw.polygon(self.surface, (235, 255, 252), [(pos.x + 2, pos.y - 11), (pos.x - 8, pos.y + 2), (pos.x - 1, pos.y + 2), (pos.x - 3, pos.y + 11), (pos.x + 8, pos.y - 3), (pos.x + 1, pos.y - 3)])
        pygame.draw.circle(self.surface, (223, 255, 255), pos, 17, 2)

    def _goal(self, game):
        x = game.level.goal_x - self.camera + self.offset.x
        if -100 <= x <= WIDTH + 100:
            y = 560 + self.offset.y
            pygame.draw.ellipse(self.surface, (24, 37, 42), (x - 24, y - 5, 48, 10))
            pygame.draw.rect(self.surface, (221, 212, 177), (x - 3, y - 139, 6, 139), border_radius=3)
            pygame.draw.circle(self.surface, GOLD, (round(x), round(y - 142)), 7)
            wave = math.sin(self.clock * 5) * 4
            color = TEAL if not game.boss or game.boss.hp <= 0 else (226, 103, 77)
            pygame.draw.polygon(self.surface, color, [(x + 3, y - 133), (x + 61, y - 125 + wave), (x + 48, y - 103 + wave), (x + 3, y - 109)])
            pygame.draw.polygon(self.surface, CREAM, [(x + 23, y - 127), (x + 26, y - 120), (x + 34, y - 119), (x + 28, y - 114), (x + 29, y - 107), (x + 23, y - 111), (x + 16, y - 107), (x + 18, y - 115), (x + 12, y - 120), (x + 20, y - 121)])

    def _hero(self, rect, facing=1, powered=False, grounded=True, moving=False):
        x, y, w, h = rect
        step = math.sin(self.clock * 16) * 3 if grounded and moving else 0
        if powered:
            self.glow(rect.center, 30, (75, 207, 255), 20)
        pygame.draw.ellipse(self.surface, (27, 46, 55), (x - 1, y + h - 4, w + 2, 8))
        # Boots, trousers, jacket, then scarf and face.
        pygame.draw.rect(self.surface, (30, 57, 76), (x + 6, y + 30, 9, 13 + step), border_radius=3)
        pygame.draw.rect(self.surface, (30, 57, 76), (x + 17, y + 30, 8, 13 - step), border_radius=3)
        pygame.draw.rect(self.surface, (57, 38, 45), (x + 3, y + 39 + step, 12, 7), border_radius=3)
        pygame.draw.rect(self.surface, (57, 38, 45), (x + 17, y + 39 - step, 12, 7), border_radius=3)
        pygame.draw.rect(self.surface, (24, 99, 104), (x + 3, y + 19, 25, 17), border_radius=6)
        pygame.draw.rect(self.surface, (48, 174, 163), (x + 5, y + 20, 19, 13), border_radius=4)
        arm_x = x + 23 if facing > 0 else x - 1
        pygame.draw.rect(self.surface, (58, 190, 177), (arm_x, y + 21, 9, 10), border_radius=4)
        pygame.draw.circle(self.surface, (255, 210, 153), (round(arm_x + 5), round(y + 29)), 4)
        tail = -facing
        pygame.draw.polygon(self.surface, (236, 106, 67), [(x + 13, y + 18), (x + 13 + tail * 20, y + 18), (x + 14 + tail * 18, y + 25), (x + 17, y + 23)])
        pygame.draw.rect(self.surface, (255, 149, 83), (x + 7, y + 18, 20, 5), border_radius=2)
        pygame.draw.rect(self.surface, (255, 213, 159), (x + 7, y + 3, 21, 16), border_radius=6)
        pygame.draw.rect(self.surface, (20, 68, 76), (x + 3, y, 25, 8), border_radius=4)
        pygame.draw.rect(self.surface, (38, 139, 143), (x + 5, y - 3, 18, 8), border_radius=4)
        pygame.draw.line(self.surface, (76, 206, 186), (x + 8, y - 2), (x + 18, y - 2), 2)
        eye = x + 22 if facing > 0 else x + 10
        pygame.draw.rect(self.surface, INK, (eye, y + 9, 3, 5), border_radius=1)
        pygame.draw.rect(self.surface, (255, 235, 188), (x + (27 if facing > 0 else 3), y + 11, 4, 5), border_radius=2)
        if powered:
            pygame.draw.circle(self.surface, (207, 251, 255), (round(arm_x + 5), round(y + 29)), 3)

    def _enemy(self, rect, kind, direction=1):
        x, y, w, h = rect
        bob = math.sin(self.clock * 7 + x * .02) * 1.5
        pygame.draw.ellipse(self.surface, (30, 40, 46), (x - 2, y + h - 4, w + 4, 8))
        if kind == "walker":
            pygame.draw.ellipse(self.surface, (79, 45, 55), (x + 1, y + h - 10, 14, 10))
            pygame.draw.ellipse(self.surface, (79, 45, 55), (x + w - 14, y + h - 10, 14, 10))
            pygame.draw.rect(self.surface, (157, 72, 66), (x + 3, y + 11 + bob, w - 6, h - 17), border_radius=9)
            pygame.draw.ellipse(self.surface, (238, 130, 93), (x - 2, y + 1 + bob, w + 4, 23))
            pygame.draw.ellipse(self.surface, (255, 178, 118), (x + 3, y + 3 + bob, w - 7, 9))
            for ex in (x + 10, x + w - 11):
                pygame.draw.rect(self.surface, INK, (ex, y + 15 + bob, 3, 5), border_radius=1)
        elif kind == "armored":
            pygame.draw.ellipse(self.surface, (48, 57, 73), (x - 2, y + 23, 15, 11))
            pygame.draw.ellipse(self.surface, (48, 57, 73), (x + w - 12, y + 23, 15, 11))
            pygame.draw.ellipse(self.surface, (73, 91, 116), (x, y + 2 + bob, w, h - 4))
            pygame.draw.ellipse(self.surface, (131, 153, 170), (x + 3, y + 3 + bob, w - 6, h - 13))
            pygame.draw.arc(self.surface, (200, 216, 214), (x + 6, y + 6 + bob, w - 12, h - 17), .3, 2.8, 2)
            pygame.draw.rect(self.surface, (45, 56, 78), (x + 5, y + 19 + bob, w - 10, 6), border_radius=3)
            for ex in (x + 10, x + w - 12):
                pygame.draw.rect(self.surface, (255, 194, 96), (ex, y + 20 + bob, 3, 3))
            pygame.draw.polygon(self.surface, (224, 222, 185), [(x + w / 2 - 4, y + 6), (x + w / 2, y - 5), (x + w / 2 + 4, y + 6)])
        else:
            pygame.draw.ellipse(self.surface, (98, 54, 113), (x + 2, y + 11, w - 4, h - 11))
            for i in range(5):
                xx = x - 2 + i * (w + 4) / 4
                pygame.draw.polygon(self.surface, (202, 167, 210), [(xx - 6, y + 18), (xx, y - (4 if i % 2 else 0)), (xx + 7, y + 18)])
                pygame.draw.line(self.surface, (247, 226, 229), (xx, y + 3), (xx + 3, y + 14), 2)
            pygame.draw.rect(self.surface, (50, 35, 66), (x + 8, y + 23, w - 16, 5), border_radius=2)
            pygame.draw.circle(self.surface, (247, 181, 212), (x + 12, y + 25), 2)
            pygame.draw.circle(self.surface, (247, 181, 212), (x + w - 12, y + 25), 2)

    def _boss(self, rect, direction=-1, hurt=False):
        margin = max(8, round(rect.w * .14))
        art = pygame.Surface((rect.w + margin * 2, rect.h + 10), pygame.SRCALPHA)
        target = self.surface
        self.surface = art
        self._boss_art(pygame.Rect(margin, 0, rect.w, rect.h), hurt)
        self.surface = target
        if direction > 0:
            art = pygame.transform.flip(art, True, False)
        self.surface.blit(art, (rect.x - margin, rect.y))

    def _boss_art(self, rect, hurt=False):
        x, y, w, h = rect
        sx, sy = w / 120, h / 128
        def r(xx, yy, ww, hh):
            return pygame.Rect(round(x + xx * sx), round(y + yy * sy), round(ww * sx), round(hh * sy))
        def points(seq):
            return [(x + xx * sx, y + yy * sy) for xx, yy in seq]
        shell = (159, 68, 77) if not hurt else (255, 227, 192)
        skin = (223, 145, 68) if not hurt else (255, 242, 200)
        pygame.draw.ellipse(self.surface, (32, 24, 42), r(0, 117, 123, 14))
        # Armored shell, horn ridge and blazing tail.
        tail = points([(88, 78), (130, 76), (113, 98), (80, 105)])
        pygame.draw.polygon(self.surface, (167, 80, 69), tail)
        for i in range(5):
            xx = 43 + i * 15
            yy = 37 + abs(i - 2) * 6
            pygame.draw.polygon(self.surface, (255, 219, 154), points([(xx - 8, yy), (xx + 1, yy - 25), (xx + 10, yy + 1)]))
        pygame.draw.ellipse(self.surface, (74, 44, 63), r(35, 35, 78, 81))
        pygame.draw.ellipse(self.surface, shell, r(36, 32, 73, 76))
        pygame.draw.ellipse(self.surface, (201, 109, 91) if not hurt else CREAM, r(46, 40, 51, 55), 3)
        pygame.draw.line(self.surface, (92, 44, 58), (x + 72 * sx, y + 34 * sy), (x + 71 * sx, y + 102 * sy), max(1, round(sx * 3)))
        pygame.draw.line(self.surface, (92, 44, 58), (x + 41 * sx, y + 70 * sy), (x + 103 * sx, y + 70 * sy), max(1, round(sx * 3)))
        pygame.draw.rect(self.surface, (129, 74, 51), r(21, 106, 33, 21), border_radius=8)
        pygame.draw.rect(self.surface, (129, 74, 51), r(77, 105, 33, 22), border_radius=8)
        pygame.draw.ellipse(self.surface, skin, r(17, 44, 58, 68))
        pygame.draw.ellipse(self.surface, (252, 199, 115), r(23, 58, 34, 47))
        for yy in (70, 82, 94):
            pygame.draw.line(self.surface, (205, 143, 77), (x + 29 * sx, y + yy * sy), (x + 53 * sx, y + yy * sy), 2)
        pygame.draw.ellipse(self.surface, skin, r(4, 23, 55, 46))
        pygame.draw.rect(self.surface, skin, r(-5, 43, 45, 28), border_radius=9)
        pygame.draw.rect(self.surface, (86, 41, 42), r(-1, 59, 33, 8), border_radius=4)
        for tooth in (3, 17):
            pygame.draw.polygon(self.surface, CREAM, points([(tooth, 59), (tooth + 4, 65), (tooth + 8, 59)]))
        pygame.draw.ellipse(self.surface, CREAM, r(11, 30, 18, 18))
        pygame.draw.rect(self.surface, INK, r(15, 33, 5, 12), border_radius=2)
        pygame.draw.line(self.surface, (82, 40, 44), (x + 8 * sx, y + 29 * sy), (x + 32 * sx, y + 35 * sy), max(2, round(4 * sx)))
        pygame.draw.polygon(self.surface, (255, 222, 163), points([(29, 28), (33, 5), (43, 29)]))
        pygame.draw.polygon(self.surface, (255, 222, 163), points([(7, 28), (8, 13), (18, 27)]))
        # An ash crown distinguishes this original boss.
        pygame.draw.polygon(self.surface, GOLD, points([(16, 22), (12, 9), (24, 14), (31, 0), (37, 14), (46, 8), (44, 25)]))
        pygame.draw.circle(self.surface, (238, 98, 69), (round(x + 30 * sx), round(y + 16 * sy)), max(2, round(3 * sx)))
        pygame.draw.ellipse(self.surface, skin, r(3, 75, 27, 18))
        pygame.draw.rect(self.surface, (79, 51, 58), r(15, 73, 10, 23), border_radius=3)
        for dy in (78, 88):
            pygame.draw.circle(self.surface, (224, 221, 203), (round(x + 20 * sx), round(y + dy * sy)), max(2, round(3 * sx)))

    def _heart(self, x, y, full=True):
        color = (255, 117, 112) if full else (75, 75, 88)
        pygame.draw.circle(self.surface, color, (x + 5, y + 5), 6)
        pygame.draw.circle(self.surface, color, (x + 15, y + 5), 6)
        pygame.draw.polygon(self.surface, color, [(x - 1, y + 7), (x + 21, y + 7), (x + 10, y + 20)])
        if full:
            pygame.draw.line(self.surface, (255, 190, 173), (x + 2, y + 2), (x + 6, y + 2), 2)

    def _hud(self, game):
        self.panel((18, 16, 924, 62), (20, 30, 44, 235), 15, (94, 118, 119, 120))
        self.text(f"BANA 0{game.level_index + 1}", (35, 27), 13, TEAL, True)
        self.text(game.level.title, (35, 45), 17, CREAM, True)
        for i in range(min(5, max(0, game.lives))):
            self._heart(266 + i * 29, 36)
        pygame.draw.circle(self.surface, GOLD, (461, 46), 9)
        pygame.draw.line(self.surface, (255, 247, 178), (459, 41), (459, 49), 2)
        self.text(f"{game.score:05d}", (481, 32), 23, CREAM, True)
        if game.player.powered:
            self.text("⚡ SKJUTBONUS", (625, 27), 13, (133, 226, 255), True)
            self.text("X / J  ·  skjut", (625, 47), 12, (173, 199, 211))
        else:
            self.text("HITTA BLÅ BONUS", (613, 27), 12, (172, 192, 202), True)
            self.text("Lås upp dina glödskott", (613, 47), 11, (152, 172, 185))
        self._button("pause", "Ⅱ", (866, 28, 29, 36), small=True)
        self._button("mute", "♫" if not game.audio.muted else "♪×", (901, 28, 29, 36), small=True)
        self.panel((180, 600, 600, 27), (18, 30, 44, 190), 8)
        self.text("A D / ← →   gå      MELLANSLAG   hoppa      X / J   skjut      ESC   paus", (480, 613), 12, (221, 231, 218), center=True)
        boss = game.boss
        if boss and boss.hp > 0 and abs(boss.rect.centerx - game.player.rect.centerx) < 1000:
            self.panel((235, 93, 490, 64), (30, 24, 40, 235), 12, (190, 97, 79, 180))
            self.text("ASKKUNGEN", (253, 101), 14, (255, 194, 123), True)
            # The remaining-hit hint is right aligned within the bar.
            hint = self.font(12).render(f"{math.ceil(boss.hp / 4)} skott / {math.ceil(boss.hp / 3)} hopp kvar", True, CREAM)
            pygame.draw.rect(self.surface, (30, 24, 40), (540, 99, 180, 22))
            self.surface.blit(hint, (706 - hint.get_width(), 103))
            pygame.draw.rect(self.surface, (71, 43, 55), (253, 128, 454, 12), border_radius=6)
            if boss.hp > 0:
                pygame.draw.rect(self.surface, (240, 109, 73), (253, 128, max(1, round(454 * boss.hp / boss.max_hp)), 12), border_radius=6)
        if game.checkpoint and game.level_time < 3:
            self.text("ELDARENAN · KONTROLLPUNKT", (480, 177), 15, GOLD, True, center=True, shadow=True)

    def _level_title(self, game):
        if game.level_time < 3.5:
            alpha = min(1, (3.5 - game.level_time) * 2)
            # Keep title below the HUD and leave the platforming lane clear.
            self.panel((170, 183, 620, 88), (19, 31, 45, int(218 * alpha)), 16)
            self.text(game.level.title, (480, 211), 27, CREAM, True, center=True, shadow=True)
            self.text(game.level.subtitle, (480, 247), 14, (225, 224, 201), center=True)

    def _veil(self, alpha=170):
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        layer.fill((10, 19, 34, alpha))
        self.surface.blit(layer, (0, 0))

    def _button(self, action, label, rect, primary=False, small=False):
        rect = pygame.Rect(rect)
        self.buttons[action] = rect
        pointer = pygame.mouse.get_pos()
        display = pygame.display.get_surface()
        if display:
            dw, dh = display.get_size()
            pointer = (pointer[0] * WIDTH / max(1, dw), pointer[1] * HEIGHT / max(1, dh))
        if self.pointer is not None:
            pointer = self.pointer
        hovered = rect.collidepoint(pointer)
        fill = (255, 203, 94) if primary else (52, 72, 86)
        if hovered:
            fill = mix(fill, CREAM, .18)
        pygame.draw.rect(self.surface, (10, 20, 30), rect.move(0, 4), border_radius=10)
        pygame.draw.rect(self.surface, fill, rect, border_radius=10)
        pygame.draw.rect(self.surface, mix(fill, CREAM, .24), rect, 1, border_radius=10)
        self.text(label, rect.center, 17 if not small else 16, INK if primary else CREAM, True, center=True)

    def _menu(self, game):
        self._veil(182)
        # Fine framing lines keep the title screen distinct from gameplay.
        pygame.draw.line(self.surface, (93, 124, 126), (46, 55), (914, 55))
        self.text("ETT EGET PLATTFORMSÄVENTYR", (48, 33), 12, TEAL, True)
        self.text("PYGAME  /  3 BANOR  /  1 ASKKUNG", (688, 34), 11, (175, 197, 202))
        self.text("GLÖDSPRÅNG", (42, 103), 64, GOLD, True, shadow=True)
        self.text("JAKTEN PÅ ASKKRONAN", (48, 184), 20, (245, 226, 188), True)
        self.text("Spring över raviner. Fånga glödens kraft.", (50, 229), 17, (201, 218, 221))
        self.text("Rädda dalen från den eldsprutande Askkungen.", (50, 255), 16, (201, 218, 221))
        self._button("start", "SPELA  →", (49, 310, 235, 52), primary=True)
        self.text("ENTER / MELLANSLAG", (55, 375), 11, (159, 186, 192), True)
        self._button("mute", "MUSIK  PÅ" if not game.audio.muted else "MUSIK  AV", (304, 310, 150, 52))
        # A little staged confrontation, drawn with the same game artwork.
        self.glow((758, 278), 155, (241, 146, 77), 20)
        pygame.draw.ellipse(self.surface, (19, 34, 44), (614, 389, 288, 32))
        pygame.draw.rect(self.surface, (88, 83, 88), (620, 399, 280, 17), border_radius=6)
        pygame.draw.rect(self.surface, (195, 142, 100), (620, 396, 280, 6), border_radius=3)
        self._boss(pygame.Rect(754, 227, 140, 170))
        self._hero(pygame.Rect(645, 335, 39, 60), 1, True, True, False)
        self._powerup(pygame.Vector2(688, 257 + math.sin(self.clock * 3) * 6))
        self.text("15 SKOTT", (836, 193), 12, GOLD, True, center=True)
        self.text("eller 20 hopp", (836, 211), 11, (214, 203, 190), center=True)
        for xx in (704, 723, 742):
            pygame.draw.circle(self.surface, (164, 234, 251), (xx, 360 - (xx - 704) // 4), 4)
        cards = (("walker", "SKOGSLUFSA", "Hoppa på eller skjut", (236, 149, 106)), ("armored", "PANSARKRYP", "Bara skott biter", (155, 187, 209)), ("spike", "TAGGVÄKTARE", "Odödlig · hoppa över", (214, 170, 226)))
        for i, (kind, name, hint, color) in enumerate(cards):
            x = 48 + i * 292
            self.panel((x, 442, 280, 79), (24, 42, 56, 236), 12, (89, 113, 121, 130))
            self._enemy(pygame.Rect(x + 17, 462, 34, 34), kind)
            self.text(name, (x + 67, 459), 13, color, True)
            self.text(hint, (x + 67, 482), 12, (218, 225, 218))
        self.panel((48, 543, 864, 55), (17, 31, 45, 220), 12)
        controls = ((71, "A D / ← →", "GÅ"), (263, "SPACE / W / ↑", "HOPPA"), (505, "X / J", "SKJUT"), (656, "ESC / P", "PAUS"), (827, "M", "LJUD"))
        for x, key, label in controls:
            self.text(key, (x, 551), 13, CREAM, True)
            self.text(label, (x, 575), 10, (137, 177, 184), True)
        self.text("Original grafik & musik • Tangentbord • Tre liv • Kontrollpunkt vid bossen", (480, 620), 11, (169, 193, 193), center=True)

    def _pause(self, game):
        self._veil(178)
        self.panel((260, 165, 440, 334), (24, 39, 55, 245), 23, (114, 149, 151, 180))
        self.text("TA ETT ANDETAG", (480, 210), 27, GOLD, True, center=True)
        self.text("Äventyret väntar på dig.", (480, 250), 16, (201, 217, 218), center=True)
        self._button("resume", "FORTSÄTT", (325, 291, 310, 48), primary=True)
        self._button("restart", "BÖRJA OM FRÅN KONTROLLPUNKT", (294, 352, 372, 44))
        self._button("menu", "TILL TITELSKÄRMEN", (325, 410, 310, 44))
        self.text("ESC / P för att fortsätta", (480, 478), 12, (156, 184, 191), center=True)

    def _ending(self, game, won):
        self._veil(180)
        self.panel((208, 137, 544, 372), (24, 39, 55, 245), 24, (137, 157, 148, 180))
        self.text("ASKKRONAN ÄR DIN!" if won else "GLÖDEN SLOCKNADE", (480, 194), 31, GOLD if won else (255, 155, 130), True, center=True)
        self.text("Dalen kan äntligen andas igen." if won else "Ett nytt försök. Ett nytt äventyr.", (480, 244), 17, CREAM, center=True)
        self.text(f"{game.score:05d} POÄNG", (480, 294), 31, TEAL, True, center=True)
        self._button("restart", "SPELA IGEN" if won else "FÖRSÖK IGEN", (325, 351, 310, 49), primary=True)
        self._button("menu", "TILL TITELSKÄRMEN", (325, 416, 310, 44))
        self.text("ENTER för att spela igen", (480, 487), 12, (156, 184, 191), center=True)
