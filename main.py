"""Run the game, or use --smoke-test for a finite headless startup check."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def main():
    parser = argparse.ArgumentParser(description="Glödsprång – ett plattformsspel i tre akter")
    parser.add_argument("--mute", action="store_true", help="Starta utan ljud")
    parser.add_argument("--headless", action="store_true", help="Använd SDL:s virtuella bild- och ljudenheter")
    parser.add_argument("--smoke-test", action="store_true", help="Rita meny och alla banor, kör simuleringen och avsluta")
    parser.add_argument("--screenshot", type=Path, help="Spara en bild av den sista ritade spelrutan")
    args = parser.parse_args()
    if args.headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    import pygame
    from audio import AudioManager
    from game import Game, InputState, WIDTH, HEIGHT
    from render import Renderer

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Glödsprång · Jakten på askkronan")
    canvas = pygame.Surface((WIDTH, HEIGHT))
    renderer = Renderer(canvas)
    audio = AudioManager()
    if args.mute or not audio.enabled:
        audio.toggle_mute()
    game = Game(audio=audio)
    clock = pygame.time.Clock()
    audio.start_music()

    if args.smoke_test:
        renderer.draw(game)
        game.start_new()
        for index in range(3):
            game.load_level(index, powered=True)
            for frame in range(180):
                game.update(1 / 120, InputState(right=True, jump_pressed=frame == 50,
                                               jump_held=50 <= frame < 95, shoot_held=True))
                renderer.draw(game)
            if index == 2:
                game.teleport_player(game.level.width - 800, 420)
                for _ in range(160):
                    game.update(1 / 120, InputState(shoot_held=True))
                    renderer.draw(game)
        for state in ("paused", "game_over", "victory"):
            game.state = state
            renderer.draw(game)
        game.state = "playing"
        renderer.draw(game)
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(canvas, str(args.screenshot))
        print("Smoke test OK: meny, tre banor, boss, projektiler och alla slutskärmar renderades.")
        pygame.quit()
        return 0

    running = True
    accumulator = 0.0
    jump_pending = shoot_pending = False

    def action(name):
        nonlocal running
        if name == "start":
            game.start_new()
        elif name == "resume":
            game.state = "playing"
        elif name == "pause":
            game.toggle_pause()
        elif name == "restart":
            if game.state == "victory":
                game.start_new()
            else:
                game.restart_checkpoint()
        elif name == "menu":
            game.state = "menu"
        elif name == "mute":
            audio.toggle_mute()
        elif name == "quit":
            running = False

    while running:
        elapsed = min(clock.tick(120) / 1000, .1)
        win_w, win_h = window.get_size()
        scale = min(win_w / WIDTH, win_h / HEIGHT)
        draw_size = (max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale)))
        offset = ((win_w - draw_size[0]) // 2, (win_h - draw_size[1]) // 2)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.WINDOWFOCUSLOST and game.state == "playing":
                game.state = "paused"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    action("mute")
                elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if game.state == "menu":
                        if event.key == pygame.K_ESCAPE:
                            running = False
                    else:
                        game.toggle_pause()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if game.state == "menu":
                        action("start")
                    elif game.state == "paused":
                        action("resume")
                    elif game.state in ("game_over", "victory"):
                        action("restart")
                elif event.key == pygame.K_r and game.state != "menu":
                    action("restart")
                elif event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    if game.state == "menu" and event.key == pygame.K_SPACE:
                        action("start")
                    else:
                        jump_pending = True
                elif event.key in (pygame.K_x, pygame.K_j):
                    shoot_pending = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                point = ((event.pos[0] - offset[0]) / scale, (event.pos[1] - offset[1]) / scale)
                for name, rect in renderer.buttons.items():
                    if rect.collidepoint(point):
                        action(name)
                        break
        keys = pygame.key.get_pressed()
        accumulator += elapsed
        while accumulator >= 1 / 120:
            game.update(1 / 120, InputState(
                left=keys[pygame.K_a] or keys[pygame.K_LEFT],
                right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
                jump_pressed=jump_pending,
                jump_held=keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP],
                shoot_pressed=shoot_pending,
                shoot_held=keys[pygame.K_x] or keys[pygame.K_j],
            ))
            jump_pending = shoot_pending = False
            accumulator -= 1 / 120
        mouse = pygame.mouse.get_pos()
        renderer.pointer = ((mouse[0] - offset[0]) / scale, (mouse[1] - offset[1]) / scale)
        renderer.draw(game)
        window.fill((12, 19, 31))
        if draw_size == (WIDTH, HEIGHT):
            window.blit(canvas, offset)
        else:
            window.blit(pygame.transform.smoothscale(canvas, draw_size), offset)
        pygame.display.flip()

    if args.screenshot:
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(canvas, str(args.screenshot))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
