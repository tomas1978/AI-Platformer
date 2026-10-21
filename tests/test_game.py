"""Headless gameplay checks; run with ``python -m unittest discover -s tests -v``."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest

import pygame

from game import Enemy, Game, HEIGHT, InputState, PLAYER_SPEED, Projectile
from levels import LEVELS


DT = 1 / 120


class GameRulesTests(unittest.TestCase):
    def make_game(self, level=0, flat=True):
        game = Game(seed=4)
        game.start_new()
        if level:
            game.load_level(level)
        game.enemies.clear()
        game.coins.clear()
        game.powerups.clear()
        if flat:
            game.platforms = [pygame.Rect(0, 560, game.level.width, 80)]
        return game

    def enemy(self, game, kind, x=400, y=526):
        enemy = Enemy(kind, pygame.Rect(x, y, 34, 34), pygame.Vector2(x, y))
        game.enemies.append(enemy)
        return enemy

    def projectile(self, center, velocity=(0, 0), size=(14, 8)):
        rect = pygame.Rect(0, 0, *size)
        rect.center = center
        return Projectile(rect, pygame.Vector2(rect.topleft), pygame.Vector2(velocity))

    def shoot_until_hit(self, game, enemy):
        game.player.powered = True
        game.update(DT, InputState(shoot_pressed=True))
        self.assertEqual(len(game.bullets), 1)
        for _ in range(100):
            game.update(DT)
            if not game.bullets:
                break
        self.assertFalse(game.bullets, "The fired shot must reach its target")

    def test_shooting_requires_collecting_a_powerup(self):
        game = self.make_game()
        for _ in range(10):
            game.update(DT, InputState(shoot_held=True))
        self.assertFalse(game.bullets)
        game.powerups.append(pygame.Vector2(game.player.rect.center))
        game.update(DT)
        self.assertTrue(game.player.powered)
        self.assertFalse(game.powerups)
        game.update(DT, InputState(shoot_pressed=True))
        self.assertEqual(len(game.bullets), 1)
        first_x = game.bullets[0].rect.x
        game.update(DT, InputState(shoot_held=True))
        self.assertEqual(len(game.bullets), 1, "Holding fire respects its cooldown")
        self.assertGreater(game.bullets[0].rect.x, first_x)

    def test_real_shots_defeat_walker_and_armored_but_not_spike(self):
        for kind in ("walker", "armored", "spike"):
            with self.subTest(kind=kind):
                game = self.make_game()
                enemy = self.enemy(game, kind, x=280)
                self.shoot_until_hit(game, enemy)
                self.assertEqual(enemy.alive, kind == "spike")
                self.assertEqual(game.score, 0 if kind == "spike" else 100)
                self.assertEqual(game.lives, 3)

    def test_stomping_walker_bounces_but_other_enemies_hurt(self):
        for kind in ("walker", "armored", "spike"):
            with self.subTest(kind=kind):
                game = self.make_game()
                enemy = self.enemy(game, kind)
                game.teleport_player(402, enemy.rect.top - game.player.rect.height)
                game.player.vel.y = 230
                game.update(DT, InputState(jump_held=True))
                if kind == "walker":
                    self.assertFalse(enemy.alive)
                    self.assertEqual(game.lives, 3)
                    self.assertLess(game.player.vel.y, 0)
                    self.assertEqual(game.player.rect.bottom, enemy.rect.top)
                    self.assertEqual(game.score, 100)
                else:
                    self.assertTrue(enemy.alive)
                    self.assertEqual(game.lives, 2)
                    self.assertGreater(game.player.invulnerable, 0)

    def test_side_contact_hurts_for_all_enemy_types(self):
        for kind in ("walker", "armored", "spike"):
            with self.subTest(kind=kind):
                game = self.make_game()
                enemy = self.enemy(game, kind)
                game.teleport_player(375, 514)
                game.update(DT)
                self.assertEqual(game.lives, 2)
                self.assertTrue(enemy.alive)

    def test_fireball_hurts_and_grants_temporary_invulnerability(self):
        game = self.make_game()
        game.fireballs.append(self.projectile(game.player.rect.center, size=(22, 22)))
        game.update(DT)
        self.assertEqual(game.lives, 2)
        self.assertFalse(game.fireballs)
        game.fireballs.append(self.projectile(game.player.rect.center, size=(22, 22)))
        game.update(DT)
        self.assertEqual(game.lives, 2)
        self.assertFalse(game.fireballs)

    def test_boss_takes_exactly_fifteen_projectile_hits(self):
        game = self.make_game(level=2)
        for hit in range(1, 16):
            game.bullets.append(self.projectile(game.boss.rect.center))
            game.update(DT)
            self.assertEqual(game.boss.hp, 60 - hit * 4)
            self.assertFalse(game.bullets)
            if hit < 15:
                self.assertEqual(game.score, 0)
        self.assertEqual(game.score, 1500)
        self.assertEqual(game.state, "playing", "Defeating the boss still requires reaching the exit")

    def test_boss_takes_exactly_twenty_real_stomps(self):
        game = self.make_game(level=2)
        for hit in range(1, 21):
            game.teleport_player(game.boss.rect.x + 25, game.boss.rect.top - game.player.rect.height)
            game.player.vel.y = 230
            game.update(DT, InputState(jump_held=True))
            self.assertEqual(game.boss.hp, 60 - hit * 3)
            self.assertLess(game.player.vel.y, 0)
            self.assertEqual(game.lives, 3)
        self.assertEqual(game.score, 1500)
        self.assertFalse(game.fireballs)

    def test_boss_accepts_mixed_shot_and_stomp_damage(self):
        game = self.make_game(level=2)
        for _ in range(3):
            game.bullets.append(self.projectile(game.boss.rect.center))
            game.update(DT)
        self.assertEqual(game.boss.hp, 48)
        for _ in range(16):
            game.teleport_player(game.boss.rect.x + 25, game.boss.rect.top - game.player.rect.height)
            game.player.vel.y = 230
            game.update(DT, InputState(jump_held=True))
        self.assertEqual(game.boss.hp, 0)
        self.assertEqual(game.score, 1500)
        self.assertEqual(game.lives, 3)

    def test_boss_wakes_near_arena_fires_and_creates_checkpoint(self):
        game = self.make_game(level=2)
        for _ in range(150):
            game.update(DT)
        self.assertFalse(game.fireballs)
        self.assertFalse(game.checkpoint)
        game.teleport_player(game.level.width - 940, 514)
        for _ in range(121):
            game.update(DT)
        self.assertTrue(game.checkpoint)
        self.assertEqual(len(game.fireballs), 3)
        self.assertTrue(all(fire.vel.x < 0 for fire in game.fireballs))
        self.assertEqual(game.lives, 3)

    def test_all_three_levels_and_boss_gate_lead_to_victory(self):
        game = self.make_game()
        game.player.powered = True
        for index in (0, 1):
            self.assertEqual(game.level_index, index)
            game.teleport_player(game.level.goal_x, 514)
            game.update(DT)
            self.assertEqual(game.level_index, index + 1)
            self.assertEqual(game.state, "playing")
            self.assertTrue(game.player.powered)
        game.teleport_player(game.level.goal_x, 514)
        game.update(DT)
        self.assertEqual(game.state, "playing")
        self.assertEqual(game.level_index, 2)
        for _ in range(15):
            game.bullets.append(self.projectile(game.boss.rect.center))
            game.update(DT)
        self.assertEqual(game.boss.hp, 0)
        self.assertEqual(game.state, "victory")

    def test_falling_uses_lives_respawns_and_eventually_ends_game(self):
        game = self.make_game()
        game.player.powered = True
        game.score = 80
        for remaining in (2, 1, 0):
            game.teleport_player(780, HEIGHT + 121)
            game.update(DT)
            self.assertEqual(game.lives, remaining)
            if remaining:
                self.assertEqual(game.state, "playing")
                self.assertEqual(game.player.rect.topleft, game.level.spawn)
                self.assertTrue(game.player.powered)
                self.assertEqual(game.score, game.level_start_score)
            else:
                self.assertEqual(game.state, "game_over")

    def test_checkpoint_fall_restarts_boss_arena_with_powerup(self):
        game = self.make_game(level=2)
        game.teleport_player(game.level.width - 940, 514)
        game.update(DT)
        self.assertTrue(game.checkpoint)
        game.teleport_player(3300, HEIGHT + 121)
        game.update(DT)
        self.assertEqual(game.lives, 2)
        self.assertTrue(game.checkpoint)
        self.assertTrue(game.player.powered)
        self.assertGreater(game.player.rect.x, 3000)
        self.assertEqual(game.boss.hp, game.boss.max_hp)

    def test_pause_freezes_gameplay_and_resumes(self):
        game = self.make_game()
        game.player.powered = True
        game.update(DT, InputState(right=True, shoot_pressed=True))
        game.toggle_pause()
        player = game.player.rect.copy()
        bullet = game.bullets[0].rect.copy()
        level_time = game.level_time
        for _ in range(120):
            game.update(DT, InputState(right=True, jump_pressed=True, shoot_held=True))
        self.assertEqual(game.player.rect, player)
        self.assertEqual(game.bullets[0].rect, bullet)
        self.assertEqual(game.level_time, level_time)
        game.toggle_pause()
        for _ in range(12):
            game.update(DT, InputState(right=True))
        self.assertGreater(game.player.rect.x, player.x)
        self.assertGreater(game.level_time, level_time)

    def test_every_ground_gap_can_be_cleared_with_normal_jump(self):
        for index, level in enumerate(LEVELS):
            ground = sorted((pygame.Rect(p) for p in level.platforms if p[1] == 560), key=lambda r: r.x)
            for left, right in zip(ground, ground[1:]):
                if right.left <= left.right:
                    continue
                with self.subTest(level=index + 1, gap=(left.right, right.left)):
                    game = self.make_game(level=index, flat=False)
                    game.boss = None
                    game.teleport_player(left.right - 30, 514)
                    game.player.grounded = True
                    game.player.vel.x = PLAYER_SPEED
                    game.update(DT, InputState(right=True, jump_pressed=True, jump_held=True))
                    landed = False
                    for _ in range(150):
                        game.update(DT, InputState(right=True, jump_held=True))
                        if game.player.grounded and game.player.rect.left >= right.left - 30:
                            landed = True
                            break
                        if game.lives < 3:
                            break
                    self.assertTrue(landed, "A running jump must reach the opposite side")
                    self.assertEqual(game.lives, 3)


if __name__ == "__main__":
    unittest.main()
