import math
import sys

import pygame


WINDOW_SIZE = 800
BOARD_SIZE = 720
BOARD_OFFSET = (WINDOW_SIZE - BOARD_SIZE) // 2
CELL = BOARD_SIZE // 15

BG = (244, 246, 250)
PAPER = (255, 255, 255)
TRACK = (250, 251, 252)
GRID = (55, 65, 75)
SOFT_GRID = (190, 198, 207)
SHADOW = (210, 216, 224)

RED = (220, 68, 68)
RED_DARK = (171, 43, 43)
GREEN = (57, 181, 94)
GREEN_DARK = (38, 139, 68)
YELLOW = (244, 196, 48)
YELLOW_DARK = (196, 151, 26)
BLUE = (58, 122, 214)
BLUE_DARK = (40, 86, 166)


def cell_rect(row, col):
    return pygame.Rect(
        BOARD_OFFSET + col * CELL,
        BOARD_OFFSET + row * CELL,
        CELL,
        CELL,
    )


def draw_star(surface, center, radius, color, outline=None):
    cx, cy = center
    points = []
    for index in range(10):
        angle = math.radians(-90 + index * 36)
        distance = radius if index % 2 == 0 else radius * 0.42
        points.append(
            (
                cx + math.cos(angle) * distance,
                cy + math.sin(angle) * distance,
            )
        )
    pygame.draw.polygon(surface, color, points)
    if outline:
        pygame.draw.lines(surface, outline, True, points, 2)


def draw_piece(surface, row, col, color, dark, radius=None):
    rect = cell_rect(row, col)
    cx = rect.centerx
    cy = rect.centery
    radius = radius or int(CELL * 0.31)
    pygame.draw.circle(surface, SHADOW, (cx + 2, cy + 4), radius)
    pygame.draw.circle(surface, dark, (cx, cy), radius)
    pygame.draw.circle(surface, color, (cx, cy - 2), radius - 4)
    pygame.draw.circle(surface, (255, 255, 255), (cx - 5, cy - 7), max(3, radius // 5))


def draw_base(surface, rect, color, dark):
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, GRID, rect, 3)

    inset = int(rect.width * 0.28)
    inner = rect.inflate(-inset * 2, -inset * 2)
    pygame.draw.rect(surface, PAPER, inner, border_radius=18)
    pygame.draw.rect(surface, dark, inner, 3, border_radius=18)

    positions = (
        (inner.left + inner.width * 0.29, inner.top + inner.height * 0.29),
        (inner.right - inner.width * 0.29, inner.top + inner.height * 0.29),
        (inner.left + inner.width * 0.29, inner.bottom - inner.height * 0.29),
        (inner.right - inner.width * 0.29, inner.bottom - inner.height * 0.29),
    )
    for cx, cy in positions:
        pygame.draw.circle(surface, SHADOW, (int(cx + 2), int(cy + 3)), int(CELL * 0.27))
        pygame.draw.circle(surface, dark, (int(cx), int(cy)), int(CELL * 0.27))
        pygame.draw.circle(surface, color, (int(cx), int(cy - 2)), int(CELL * 0.21))
        pygame.draw.circle(
            surface,
            (255, 255, 255),
            (int(cx - 5), int(cy - 7)),
            max(3, int(CELL * 0.06)),
        )


def draw_center(surface):
    center = BOARD_OFFSET + BOARD_SIZE // 2
    half = 3 * CELL

    top = (center, BOARD_OFFSET + 6 * CELL)
    left = (BOARD_OFFSET + 6 * CELL, center)
    right = (BOARD_OFFSET + 9 * CELL, center)
    bottom = (center, BOARD_OFFSET + 9 * CELL)
    middle = (center, center)

    pygame.draw.polygon(surface, GREEN, [top, middle, right])
    pygame.draw.polygon(surface, YELLOW, [left, middle, bottom])
    pygame.draw.polygon(surface, RED, [top, left, middle])
    pygame.draw.polygon(surface, BLUE, [right, middle, bottom])

    pygame.draw.polygon(surface, GRID, [top, left, middle], 3)
    pygame.draw.polygon(surface, GRID, [top, middle, right], 3)
    pygame.draw.polygon(surface, GRID, [left, middle, bottom], 3)
    pygame.draw.polygon(surface, GRID, [right, middle, bottom], 3)

    pygame.draw.circle(surface, PAPER, (center, center), int(CELL * 0.19))
    pygame.draw.circle(surface, GRID, (center, center), int(CELL * 0.19), 3)


def draw_board(surface):
    board_rect = pygame.Rect(BOARD_OFFSET, BOARD_OFFSET, BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(surface, SHADOW, board_rect.inflate(12, 12), border_radius=10)
    pygame.draw.rect(surface, PAPER, board_rect)
    pygame.draw.rect(surface, GRID, board_rect, 4)

    # Draw the complete 15 x 15 grid first.
    for row in range(15):
        for col in range(15):
            rect = cell_rect(row, col)
            pygame.draw.rect(surface, TRACK, rect)

    # Corner base zones.
    draw_base(
        surface,
        pygame.Rect(
            BOARD_OFFSET,
            BOARD_OFFSET,
            6 * CELL,
            6 * CELL,
        ),
        RED,
        RED_DARK,
    )
    draw_base(
        surface,
        pygame.Rect(
            BOARD_OFFSET + 9 * CELL,
            BOARD_OFFSET,
            6 * CELL,
            6 * CELL,
        ),
        GREEN,
        GREEN_DARK,
    )
    draw_base(
        surface,
        pygame.Rect(
            BOARD_OFFSET,
            BOARD_OFFSET + 9 * CELL,
            6 * CELL,
            6 * CELL,
        ),
        YELLOW,
        YELLOW_DARK,
    )
    draw_base(
        surface,
        pygame.Rect(
            BOARD_OFFSET + 9 * CELL,
            BOARD_OFFSET + 9 * CELL,
            6 * CELL,
            6 * CELL,
        ),
        BLUE,
        BLUE_DARK,
    )

    # Red home column: left side, leading upward toward the center.
    for row in range(6, 9):
        for col in range(1, 6):
            rect = cell_rect(row, col)
            pygame.draw.rect(surface, (255, 224, 224) if row == 7 else PAPER, rect)
    for col in range(1, 7):
        rect = cell_rect(7, col)
        if col < 6:
            pygame.draw.rect(surface, RED, rect)
            pygame.draw.rect(surface, SOFT_GRID, rect, 2)

    # Green home column: top side.
    for row in range(1, 7):
        rect = cell_rect(row, 7)
        pygame.draw.rect(surface, GREEN, rect)
        pygame.draw.rect(surface, SOFT_GRID, rect, 2)

    # Yellow home column: bottom-left arm.
    for row in range(8, 14):
        rect = cell_rect(row, 7)
        pygame.draw.rect(surface, YELLOW if row < 14 else TRACK, rect)
        pygame.draw.rect(surface, SOFT_GRID, rect, 2)

    # Blue home column: bottom-right arm.
    for col in range(8, 14):
        rect = cell_rect(7, col)
        pygame.draw.rect(surface, BLUE if col < 14 else TRACK, rect)
        pygame.draw.rect(surface, SOFT_GRID, rect, 2)

    # Red column must remain red across the middle arm; show all six visually.
    for col in range(1, 7):
        rect = cell_rect(7, col)
        pygame.draw.rect(surface, RED if col < 6 else RED, rect)
        pygame.draw.rect(surface, SOFT_GRID, rect, 2)

    # Star-marked safe zones.
    safe_cells = {(6, 2), (2, 6), (8, 12), (12, 8), (6, 6), (8, 8)}
    for row, col in safe_cells:
        rect = cell_rect(row, col)
        pygame.draw.rect(surface, TRACK, rect)
        pygame.draw.rect(surface, SOFT_GRID, rect, 2)
        pygame.draw.circle(surface, PAPER, rect.center, int(CELL * 0.34))
        draw_star(surface, rect.center, int(CELL * 0.27), YELLOW_DARK)

    # Start squares.
    start_cells = (
        (6, 1, RED),
        (1, 8, GREEN),
        (13, 6, YELLOW),
        (8, 13, BLUE),
    )
    for row, col, color in start_cells:
        rect = cell_rect(row, col)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, GRID, rect, 2)

    # The main grid borders over all cells, except colored home zones stay bordered.
    for row in range(15):
        for col in range(15):
            rect = cell_rect(row, col)
            if not (
                row < 6 and col < 6
                or row < 6 and col >= 9
                or row >= 9 and col < 6
                or row >= 9 and col >= 9
            ):
                pygame.draw.rect(surface, SOFT_GRID, rect, 1)

    draw_center(surface)

    # Sample active pieces on the track.
    draw_piece(surface, 6, 1, RED, RED_DARK)
    draw_piece(surface, 2, 8, GREEN, GREEN_DARK)
    draw_piece(surface, 8, 13, BLUE, BLUE_DARK)
    draw_piece(surface, 13, 6, YELLOW, YELLOW_DARK)
    draw_piece(surface, 6, 4, RED, RED_DARK)
    draw_piece(surface, 8, 11, BLUE, BLUE_DARK)

    # Sample pieces inside home columns.
    draw_piece(surface, 7, 2, RED, RED_DARK)
    draw_piece(surface, 3, 7, GREEN, GREEN_DARK)
    draw_piece(surface, 11, 7, YELLOW, YELLOW_DARK)
    draw_piece(surface, 7, 10, BLUE, BLUE_DARK)


def draw_title(surface):
    font = pygame.font.SysFont("Segoe UI", 30, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI", 14)
    title = font.render("LudoVerse", True, (33, 42, 54))
    subtitle = subtitle_font.render("Intelligent Multi-Agent Ludo", True, (115, 126, 140))
    title_rect = title.get_rect(center=(WINDOW_SIZE // 2, 20))
    subtitle_rect = subtitle.get_rect(center=(WINDOW_SIZE // 2, 49))
    surface.blit(title, title_rect)
    surface.blit(subtitle, subtitle_rect)


def main():
    pygame.init()
    pygame.display.set_caption("LudoVerse")
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    clock = pygame.time.Clock()

    screen.fill(BG)

    # Reserve a little breathing room above the board while keeping it centered.
    global BOARD_OFFSET
    BOARD_OFFSET = 50

    draw_board(screen)

    # Board title in the lower margin if needed for a clean presentation.
    title_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
    title = title_font.render("LUDOVERSE", True, (49, 59, 69))
    subtitle_font = pygame.font.SysFont("Segoe UI", 13)
    subtitle = subtitle_font.render("INTELLIGENT MULTI-AGENT LUDO", True, (120, 130, 142))
    screen.blit(title, title.get_rect(center=(WINDOW_SIZE // 2, 25)))
    screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE // 2, 769)))

    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
