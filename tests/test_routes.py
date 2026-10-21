"""End-to-end terrain routes and boss ledge jumps using the real simulation.

The route driver deliberately removes enemies to isolate level geometry. Boss
checks retain boss patrol and collision behavior but suppress fire, so failures
identify inaccessible stomp routes rather than a combat controller's aim.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest

import pygame

from game import Game, InputState
from levels import LEVELS


DT = 1 / 120


class TerrainRouteTests(unittest.TestCase):
    def assert_terrain_route_completes(self, level_index):
        game = Game(seed=19)
        game.load_level(level_index)
        game.state = "playing"
        game.enemies.clear()
        if game.boss:
            game.boss.hp = 0  # Terrain only; the boss fight has separate checks.

        jump_count = 0
        for frame in range(5000):
            player = game.player
            # Look for a blocking wall or an actual hole. Looking down 200 px
            # avoids mistaking the drop from a raised ledge to the floor for a
            # hole and prematurely jumping into a later gap.
            front = pygame.Rect(player.rect.right + 8, player.rect.top,
                                30, player.rect.height - 4)
            below_ahead = pygame.Rect(player.rect.centerx + 40,
                                     player.rect.bottom + 1, 5, 200)
            wall = any(front.colliderect(rect) for rect in game.platforms)
            supported = any(below_ahead.colliderect(rect) for rect in game.platforms)
            jump = player.grounded and (wall or not supported)
            jump_count += int(jump)
            game.update(DT, InputState(right=True, jump_pressed=jump, jump_held=True))

            self.assertEqual(game.lives, 3,
                             f"Terrain caused damage/fall in level {level_index + 1}, "
                             f"frame {frame}, position {player.rect.topleft}")
            if game.level_index != level_index or game.state == "victory":
                self.assertGreater(jump_count, 0, "The route must exercise jumping")
                if level_index == len(LEVELS) - 1:
                    self.assertEqual(game.state, "victory")
                else:
                    self.assertEqual(game.level_index, level_index + 1)
                return
        self.fail(f"Terrain route stalled in level {level_index + 1} at "
                  f"{game.player.rect.topleft}")

    def test_first_level_full_terrain_route_without_enemies(self):
        self.assert_terrain_route_completes(0)

    def test_second_level_full_terrain_route_without_enemies(self):
        self.assert_terrain_route_completes(1)

    def test_third_level_full_terrain_route_without_enemies(self):
        self.assert_terrain_route_completes(2)


class BossLedgeRouteTests(unittest.TestCase):
    def assert_twenty_stomps_from_ledge(self, start_x, wait_for_right_patrol=False):
        game = Game(seed=19)
        game.load_level(2)
        game.state = "playing"
        game.enemies.clear()
        # Leave the moving boss, player physics, ledges and stomp collision
        # intact. Suppress only fire to isolate whether this route is possible.
        game.boss.fire_timer = 1000
        game.teleport_player(start_x, 434)  # Feet at the real ledge top, y480.

        if wait_for_right_patrol:
            for _ in range(1000):
                game.update(DT, InputState(jump_held=True))
                if game.boss.rect.left >= 3800:
                    break
            else:
                self.fail("The boss did not patrol toward the right launch ledge")

        for _ in range(20):
            game.update(DT, InputState(jump_held=True))
            if game.player.grounded:
                break
        self.assertTrue(game.player.grounded, "Player must begin on the launch ledge")
        previous_hp = game.boss.hp
        stomp_count = 0
        for frame in range(2400):
            offset = game.boss.rect.centerx - game.player.rect.centerx
            game.update(DT, InputState(left=offset < -12, right=offset > 12,
                                       jump_pressed=frame == 0, jump_held=True))
            self.assertEqual(game.lives, 3,
                             f"Ledge route from x{start_x} caused a side collision")
            self.assertFalse(game.bullets, "This route must use stomps exclusively")
            self.assertFalse(game.fireballs, "Fire is suppressed for this geometry check")
            if game.boss.hp < previous_hp:
                self.assertEqual(previous_hp - game.boss.hp, 3)
                self.assertLess(game.player.vel.y, 0, "Each stomp must bounce the player")
                stomp_count += 1
                previous_hp = game.boss.hp
            if game.boss.hp == 0:
                self.assertEqual(stomp_count, 20)
                return
        self.fail(f"Could not land 20 stomps from x{start_x}; "
                  f"boss retains {game.boss.hp} HP")

    def test_left_ledge_allows_twenty_stomps_on_moving_boss_with_fire_suppressed(self):
        self.assert_twenty_stomps_from_ledge(3520)

    def test_right_ledge_allows_twenty_stomps_on_moving_boss_with_fire_suppressed(self):
        self.assert_twenty_stomps_from_ledge(4000, wait_for_right_patrol=True)


if __name__ == "__main__":
    unittest.main()
