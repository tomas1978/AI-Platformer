"""Three hand-built, traversable stages for Glödsprång.

Coordinates are world pixels. Ground blocks and ledges are ordinary solid
rectangles; collectible coordinates mark their centres. No assets are needed.
"""

from dataclasses import dataclass


TILE = 40
WORLD_HEIGHT = 640


@dataclass(frozen=True)
class LevelSpec:
    title: str
    subtitle: str
    width: int
    spawn: tuple[int, int]
    platforms: tuple[tuple[int, int, int, int], ...]
    coins: tuple[tuple[int, int], ...]
    powerups: tuple[tuple[int, int], ...]
    enemies: tuple[tuple[str, int, int], ...]
    goal_x: int
    palette: dict[str, tuple[int, int, int]]
    boss_spawn: tuple[int, int] | None = None


def _coins(x: int, y: int, count: int, spacing: int = 40) -> tuple[tuple[int, int], ...]:
    return tuple((x + i * spacing, y) for i in range(count))


LEVELS = (
    LevelSpec(
        title="1 · Vindängarna",
        subtitle="Hitta den blå skjutbonusen. Hoppa över hålen och följ mynten!",
        width=3600,
        spawn=(90, 514),
        platforms=(
            (0, 560, 760, 80),
            (880, 560, 640, 80),
            (1640, 560, 780, 80),
            (2540, 560, 1060, 80),
            (440, 480, 160, 80),
            (1040, 480, 160, 80),
            (1240, 400, 120, 24),
            (1780, 480, 160, 80),
            (2120, 470, 140, 90),
            (2740, 480, 160, 80),
            (2980, 400, 160, 24),
        ),
        coins=(
            _coins(240, 510, 3)
            + _coins(460, 440, 4)
            + ((750, 460), (810, 430), (870, 460))
            + _coins(1060, 440, 3)
            + _coins(1250, 360, 3)
            + ((1510, 460), (1570, 430), (1630, 460))
            + _coins(1800, 440, 3)
            + _coins(2130, 430, 3)
            + ((2410, 460), (2470, 430), (2530, 460))
            + _coins(2760, 440, 3)
            + _coins(3000, 360, 4)
            + _coins(3290, 510, 4)
        ),
        powerups=((290, 518), (1860, 438), (3280, 518)),
        enemies=(
            ("walker", 650, 526),
            ("walker", 1320, 526),
            ("armored", 2000, 526),
            ("spike", 2310, 526),
            ("walker", 2630, 526),
            ("armored", 3170, 526),
        ),
        goal_x=3480,
        palette={
            "sky_top": (36, 70, 112),
            "sky_bottom": (124, 190, 180),
            "far": (54, 105, 119),
            "near": (39, 92, 88),
            "ground": (89, 65, 62),
            "grass": (112, 196, 122),
            "accent": (255, 211, 123),
        },
    ),
    LevelSpec(
        title="2 · Bärnstensklyftan",
        subtitle="Pansarkryp tål hopp. Använd glöden och akta taggarna!",
        width=3920,
        spawn=(90, 514),
        platforms=(
            (0, 560, 640, 80),
            (760, 560, 640, 80),
            (1520, 560, 640, 80),
            (2280, 560, 560, 80),
            (2960, 560, 960, 80),
            (400, 480, 120, 80),
            (800, 480, 140, 80),
            (1000, 400, 160, 24),
            (1240, 480, 120, 80),
            (1610, 480, 140, 80),
            (1820, 400, 180, 24),
            (2010, 480, 120, 80),
            (2380, 480, 160, 80),
            (2620, 400, 160, 24),
            (3070, 480, 160, 80),
            (3310, 400, 160, 24),
        ),
        coins=(
            _coins(230, 510, 3)
            + _coins(420, 440, 3)
            + ((630, 460), (690, 430), (750, 460))
            + _coins(810, 440, 3)
            + _coins(1020, 360, 4)
            + _coins(1250, 440, 3)
            + ((1390, 460), (1450, 430), (1510, 460))
            + _coins(1630, 440, 3)
            + _coins(1840, 360, 4)
            + ((2150, 460), (2210, 430), (2270, 460))
            + _coins(2400, 440, 4)
            + _coins(2640, 360, 4)
            + ((2830, 460), (2890, 430), (2950, 460))
            + _coins(3090, 440, 4)
            + _coins(3330, 360, 4)
            + _coins(3610, 510, 4)
        ),
        powerups=((270, 518), (1690, 438), (3130, 438), (3650, 518)),
        enemies=(
            ("walker", 550, 526),
            ("spike", 1180, 526),
            ("armored", 1280, 446),
            ("walker", 1760, 526),
            ("armored", 2050, 446),
            ("spike", 2550, 526),
            ("walker", 3030, 526),
            ("armored", 3490, 526),
            ("spike", 3710, 526),
        ),
        goal_x=3800,
        palette={
            "sky_top": (82, 48, 102),
            "sky_bottom": (235, 150, 105),
            "far": (132, 79, 114),
            "near": (111, 63, 89),
            "ground": (123, 74, 71),
            "grass": (229, 161, 94),
            "accent": (255, 219, 145),
        },
    ),
    LevelSpec(
        title="3 · Glödens fäste",
        subtitle="Askkungen väntar. 15 glödskott eller 20 hopp besegrar honom.",
        width=4240,
        spawn=(90, 514),
        platforms=(
            (0, 560, 720, 80),
            (840, 560, 720, 80),
            (1680, 560, 640, 80),
            (2440, 560, 560, 80),
            (3120, 560, 1120, 80),
            (430, 480, 160, 80),
            (910, 480, 160, 80),
            (1150, 400, 160, 24),
            (1380, 480, 140, 80),
            (1750, 480, 160, 80),
            (1990, 400, 160, 24),
            (2170, 480, 120, 80),
            (2520, 480, 160, 80),
            (2760, 400, 160, 24),
            # These launch ledges make the 128 px tall boss stompable.
            (3360, 480, 220, 80),
            (3890, 480, 180, 80),
        ),
        coins=(
            _coins(220, 510, 3)
            + _coins(450, 440, 4)
            + ((710, 460), (770, 430), (830, 460))
            + _coins(930, 440, 4)
            + _coins(1170, 360, 4)
            + _coins(1390, 440, 3)
            + ((1550, 460), (1610, 430), (1670, 460))
            + _coins(1770, 440, 4)
            + _coins(2010, 360, 4)
            + ((2310, 460), (2370, 430), (2430, 460))
            + _coins(2540, 440, 4)
            + _coins(2780, 360, 4)
            + ((2990, 460), (3050, 430), (3110, 460))
            + _coins(3390, 440, 4)
            + _coins(3890, 440, 4)
        ),
        powerups=((270, 518), (1830, 438), (3260, 518), (3980, 438)),
        enemies=(
            ("walker", 640, 526),
            ("armored", 960, 446),
            ("spike", 1320, 526),
            ("walker", 1450, 446),
            ("armored", 1800, 446),
            ("spike", 2120, 526),
            ("walker", 2480, 526),
            ("armored", 2580, 446),
            ("spike", 2930, 526),
        ),
        goal_x=4120,
        boss_spawn=(3680, 432),
        palette={
            "sky_top": (27, 27, 52),
            "sky_bottom": (111, 53, 69),
            "far": (61, 43, 70),
            "near": (46, 35, 57),
            "ground": (65, 55, 74),
            "grass": (226, 113, 85),
            "accent": (255, 192, 106),
        },
    ),
)
