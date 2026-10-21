"""Original, procedurally composed music and effects. No audio assets are needed.

Everything is synthesized with the Python standard library. Audio is optional:
machines without a sound device can still run and test the game normally.
"""

from __future__ import annotations

from array import array
import io
import math
import sys
import wave

import pygame


class AudioManager:
    """Small, resilient mixer facade with independent music and effect channels."""

    def __init__(self, enabled: bool = True):
        self.enabled = False
        self.muted = False
        self.music = None
        self.effects: dict[str, pygame.mixer.Sound] = {}
        self._music_channel = None
        self._music_wanted = False
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.rate, self._format, self._channels = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(1)
            self._music_channel = pygame.mixer.Channel(0)
            self.music = self._sound(self._compose())
            self.music.set_volume(0.46)
            self._make_effects()
            self.enabled = True
        except (pygame.error, OSError, ValueError):
            # Audio hardware is not a prerequisite for the game.
            self.enabled = False
            self.music = None
            self.effects.clear()

    def _sound(self, mono: array) -> pygame.mixer.Sound:
        """Encode signed PCM; WAV conversion also supports existing mixer formats."""
        if self._format == -16:
            samples = mono
            if self._channels == 2:
                samples = array("h", (v for sample in mono for v in (sample, sample)))
            return pygame.mixer.Sound(buffer=samples.tobytes())
        samples = array("h", mono)
        if sys.byteorder != "little":
            samples.byteswap()
        stream = io.BytesIO()
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.rate)
            wav.writeframes(samples.tobytes())
        stream.seek(0)
        return pygame.mixer.Sound(file=stream)

    def _tone(self, hz: float, count: int, volume: float, kind: str = "lead") -> array:
        """Rounded pulse and triangle voices with short, click-free envelopes."""
        out = array("h")
        if hz == 0:
            return array("h", [0]) * count
        step = hz / self.rate
        attack = max(1, int(self.rate * 0.006))
        release = max(1, int(self.rate * 0.045))
        for i in range(count):
            phase = (i * step) % 1.0
            triangle = 1.0 - 4.0 * abs(phase - 0.5)
            if kind == "bass":
                sample = triangle
            else:
                # A soft pulse retains a playful, handheld-console character.
                sample = 0.62 * triangle + 0.38 * (1.0 if phase < 0.4 else -1.0)
            envelope = min(1.0, i / attack, (count - 1 - i) / release)
            out.append(int(sample * envelope * volume * 32767))
        return out

    def _compose(self) -> array:
        # Eight original bars in C major, at 144 BPM. Each entry is an eighth
        # note; the last bar resolves directly into the first for a clean loop.
        melody = (
            (76, 79, 81, 79, 76, 74, 72, 74),
            (76, 79, 84, 83, 81, 79, 76, 0),
            (77, 81, 84, 81, 77, 76, 74, 76),
            (79, 83, 86, 84, 83, 81, 79, 0),
            (81, 84, 88, 86, 84, 81, 79, 76),
            (77, 81, 84, 86, 84, 81, 77, 0),
            (79, 83, 86, 83, 79, 77, 74, 71),
            (72, 76, 79, 84, 79, 76, 74, 71),
        )
        roots = (48, 48, 53, 55, 57, 53, 55, 48)
        length = round(self.rate * 60 / 144 / 2)
        cache: dict[tuple[int, str], array] = {}

        def note(midi: int, kind: str) -> array:
            key = (midi, kind)
            if key not in cache:
                hz = 0 if midi == 0 else 440 * 2 ** ((midi - 69) / 12)
                cache[key] = self._tone(hz, length, 0.17 if kind == "lead" else 0.13, kind)
            return cache[key]

        # A quiet kick and short noise brush make the rhythm audible without
        # competing with the firing and jumping cues.
        kick = array("h", [0]) * length
        brush = array("h", [0]) * length
        phase = 0.0
        noise = 91
        for i in range(min(length, int(self.rate * 0.09))):
            t = i / self.rate
            phase += 2 * math.pi * (46 + 85 * math.exp(-t * 45)) / self.rate
            kick[i] = int(math.sin(phase) * math.exp(-t * 38) * 1900)
            noise = (1664525 * noise + 1013904223) & 0xFFFFFFFF
            brush[i] = int(((noise / 0xFFFFFFFF) * 2 - 1) * math.exp(-t * 100) * 430)

        result = array("h")
        for bar, notes in enumerate(melody):
            for beat, midi in enumerate(notes):
                lead = note(midi, "lead")
                bass_midi = roots[bar] + (12 if beat % 4 == 2 else 7 if beat % 4 == 3 else 0)
                bass = note(bass_midi, "bass")
                if beat % 2 == 0:
                    result.extend(a + b + k + n for a, b, k, n in zip(lead, bass, kick, brush))
                else:
                    result.extend(a + b + n for a, b, n in zip(lead, bass, brush))
        return result

    def _sweep(self, start: float, end: float, seconds: float, volume: float = 0.28,
               noise: float = 0.0) -> array:
        count = int(self.rate * seconds)
        out = array("h")
        phase = 0.0
        seed = 123
        for i in range(count):
            fraction = i / max(1, count - 1)
            hz = start + (end - start) * fraction
            phase = (phase + hz / self.rate) % 1.0
            triangle = 1.0 - 4.0 * abs(phase - 0.5)
            seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
            random_sample = seed / 0xFFFFFFFF * 2 - 1
            envelope = min(1.0, i / max(1, self.rate * 0.004)) * (1 - fraction) ** 0.6
            sample = (triangle * (1 - noise) + random_sample * noise) * envelope
            out.append(int(sample * volume * 32767))
        return out

    def _jingle(self, notes: tuple[int, ...], duration: float = 0.09) -> array:
        result = array("h")
        for midi in notes:
            result.extend(self._tone(440 * 2 ** ((midi - 69) / 12), int(self.rate * duration), 0.25))
        return result

    def _make_effects(self) -> None:
        pcm = {
            "jump": self._sweep(240, 790, 0.14),
            "shoot": self._sweep(1100, 180, 0.10, 0.24, 0.08),
            "pickup": self._jingle((76, 79, 84, 88)),
            "stomp": self._sweep(220, 65, 0.10, 0.32),
            "hurt": self._sweep(340, 70, 0.30, 0.27, 0.18),
            "enemy_die": self._sweep(520, 100, 0.16, 0.24),
            "level_complete": self._jingle((72, 76, 79, 84), 0.14),
            "victory": self._jingle((72, 76, 79, 84, 79, 84, 88, 91, 96), 0.16),
            "fire": self._sweep(170, 55, 0.36, 0.20, 0.80),
            "boss_hit": self._sweep(175, 65, 0.20, 0.32, 0.15),
        }
        self.effects = {name: self._sound(samples) for name, samples in pcm.items()}

    def start_music(self) -> None:
        self._music_wanted = True
        if self.enabled and not self.muted and self._music_channel and self.music:
            if not self._music_channel.get_busy():
                self._music_channel.play(self.music, loops=-1)

    def stop_music(self) -> None:
        self._music_wanted = False
        if self._music_channel:
            self._music_channel.stop()

    def play(self, name: str) -> None:
        if not self.enabled or self.muted:
            return
        sound = self.effects.get(name)
        if sound is not None:
            channel = pygame.mixer.find_channel()
            if channel is not None:
                channel.play(sound)

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        if self.enabled:
            if self.muted:
                # Do not use mixer.stop(): channel ownership remains explicit.
                for index in range(pygame.mixer.get_num_channels()):
                    pygame.mixer.Channel(index).stop()
            elif self._music_wanted:
                self.start_music()
        return self.muted
