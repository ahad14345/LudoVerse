import math
import sys

import pygame

from game_state import GameState


WINDOW_WIDTH = 1120
WINDOW_HEIGHT = 800
BOARD_SIZE = 720
BOARD_OFFSET = 40
CELL = BOARD_SIZE // 15
PANEL_X = 790

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

PLAYER_COLORS = {
    "RED": RED,
    "GREEN": GREEN,
    "YELLOW": YELLOW,
    "BLUE": BLUE,
}
PLAYER_DARK_COLORS = {
    "RED": RED_DARK,
    "GREEN": GREEN_DARK,
    "YELLOW": YELLOW_DARK,
    "BLUE": BLUE_DARK,
}
BASE_ORIGINS = {
    "RED": (0, 0),
    "GREEN": (9, 0),
    "YELLOW": (0, 9),
    "BLUE": (9, 9),
}


def cell_rect(row, col):
    return pygame.Rect(
        BOARD_OFFSET + col * CELL,
        BOARD_OFFSET + row * CELL,
        CELL,
        CELL,
    )


def _base_rect_for_player(player):
    row, col = BASE_ORIGINS[player]
    return pygame.Rect(
        BOARD_OFFSET + col * CELL,
        BOARD_OFFSET + row * CELL,
        6 * CELL,
        6 * CELL,
    )


def _inner_base_rect(player):
    rect = _base_rect_for_player(player)
    inset = int(rect.width * 0.28)
    return rect.inflate(-inset * 2, -inset * 2)


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


def get_base_slot_center(player, piece_id):
    inner = _inner_base_rect(player)
    positions = (
        (inner.left + inner.width * 0.29, inner.top + inner.height * 0.29),
        (inner.right - inner.width * 0.29, inner.top + inner.height * 0.29),
        (inner.left + inner.width * 0.29, inner.bottom - inner.height * 0.29),
        (inner.right - inner.width * 0.29, inner.bottom - inner.height * 0.29),
    )
    cx, cy = positions[piece_id]
    return int(cx), int(cy)


def get_home_triangle_center(player, piece_id):
    center = BOARD_OFFSET + BOARD_SIZE // 2
    offsets = ((18, 18), (34, 18), (18, 34), (34, 34))
    x_offset, y_offset = offsets[piece_id]
    directions = {
        "RED": (-1, -1),
        "GREEN": (1, -1),
        "YELLOW": (-1, 1),
        "BLUE": (1, 1),
    }
    x_direction, y_direction = directions[player]
    return (
        center + x_direction * x_offset,
        center + y_direction * y_offset,
    )


def _piece_center(player, piece):
    if piece.state == "BASE":
        return get_base_slot_center(player, piece.piece_id)
    if piece.state == "HOME":
        return get_home_triangle_center(player, piece.piece_id)
    row, col = piece.get_board_coords()
    return cell_rect(row, col).center


def _draw_piece_at(surface, center, color, dark, radius):
    cx, cy = center
    pygame.draw.circle(surface, SHADOW, (cx + 2, cy + 4), radius)
    pygame.draw.circle(surface, dark, (cx, cy), radius)
    pygame.draw.circle(surface, color, (cx, cy - 2), radius - 4)
    pygame.draw.circle(surface, PAPER, (cx - 5, cy - 7), max(3, radius // 5))


def _draw_legal_highlight(surface, center):
    cx, cy = center
    radius = 22
    rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    colors = (YELLOW_DARK, (255, 140, 0))
    for index in range(8):
        start_angle = math.radians(index * 45)
        end_angle = math.radians(index * 45 + 24)
        pygame.draw.arc(
            surface,
            colors[index % len(colors)],
            rect,
            start_angle,
            end_angle,
            3,
        )


def draw_dynamic_pieces(surface, game_state, legal_moves=None):
    for player in game_state.players:
        color = PLAYER_COLORS[player]
        dark = PLAYER_DARK_COLORS[player]
        for piece in game_state.pieces[player]:
            center = _piece_center(player, piece)
            if piece.state == "ACTIVE":
                row, col = piece.get_board_coords()
                draw_piece(surface, row, col, color, dark)
            else:
                radius = int(CELL * (0.22 if piece.state == "BASE" else 0.18))
                _draw_piece_at(surface, center, color, dark, radius)

            if (
                player == game_state.current_turn
                and legal_moves
                and piece.piece_id in legal_moves
            ):
                _draw_legal_highlight(surface, center)


def get_clicked_piece(mouse_pos, game_state, legal_moves):
    if not legal_moves:
        return None

    player = game_state.current_turn
    mouse_x, mouse_y = mouse_pos
    for piece in game_state.pieces[player]:
        if piece.piece_id not in legal_moves:
            continue
        center_x, center_y = _piece_center(player, piece)
        if (mouse_x - center_x) ** 2 + (mouse_y - center_y) ** 2 <= 24 ** 2:
            return piece.piece_id
    return None


def _ui_value(ui_state, *keys, default=None):
    for key in keys:
        if isinstance(ui_state, dict) and key in ui_state:
            return ui_state[key]
        if hasattr(ui_state, key):
            return getattr(ui_state, key)
    return default


def _draw_text(surface, text, font, color, position):
    surface.blit(font.render(str(text), True, color), position)


def _draw_wrapped_text(surface, text, font, color, x, y, max_width, line_height):
    lines = []
    current_line = ""
    for word in str(text).split():
        candidate = word if not current_line else current_line + " " + word
        if current_line and font.size(candidate)[0] > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = candidate
    if current_line:
        lines.append(current_line)

    for line in lines:
        surface.blit(font.render(line, True, color), (x, y))
        y += line_height


def _draw_die(surface, value, rect):
    pygame.draw.rect(surface, PAPER, rect, border_radius=12)
    pygame.draw.rect(surface, GRID, rect, 3, border_radius=12)
    if value not in range(1, 7):
        font = pygame.font.SysFont("Segoe UI", 44, bold=True)
        text = font.render("?", True, GRID)
        surface.blit(text, text.get_rect(center=rect.center))
        return

    left = rect.left + 25
    center_x = rect.centerx
    right = rect.right - 25
    top = rect.top + 25
    center_y = rect.centery
    bottom = rect.bottom - 25
    pips = {
        1: ((center_x, center_y),),
        2: ((left, top), (right, bottom)),
        3: ((left, top), (center_x, center_y), (right, bottom)),
        4: ((left, top), (right, top), (left, bottom), (right, bottom)),
        5: (
            (left, top),
            (right, top),
            (center_x, center_y),
            (left, bottom),
            (right, bottom),
        ),
        6: (
            (left, top),
            (right, top),
            (left, center_y),
            (right, center_y),
            (left, bottom),
            (right, bottom),
        ),
    }
    for pip in pips[value]:
        pygame.draw.circle(surface, GRID, pip, 6)


def draw_control_panel(surface, game_state, ui_state):
    panel = pygame.Rect(PANEL_X, 40, 300, 720)
    pygame.draw.rect(surface, PAPER, panel, border_radius=14)
    pygame.draw.rect(surface, SOFT_GRID, panel, 2, border_radius=14)

    title_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI", 12)
    label_font = pygame.font.SysFont("Segoe UI", 13, bold=True)
    body_font = pygame.font.SysFont("Segoe UI", 12)
    small_font = pygame.font.SysFont("Segoe UI", 11)

    _draw_text(surface, "LUDOVERSE", title_font, GRID, (810, 56))
    _draw_text(
        surface,
        "Intelligent Multi-Agent Ludo",
        subtitle_font,
        GRID,
        (810, 84),
    )
    pygame.draw.line(surface, SOFT_GRID, (810, 108), (1070, 108), 1)

    raw_mode = str(_ui_value(ui_state, "mode", default="AI vs AI"))
    human_mode = raw_mode.lower().replace(" ", "") in ("human", "humanvsai")
    mode = "Human vs AI" if human_mode else "AI vs AI"
    difficulty_value = str(
        _ui_value(ui_state, "difficulty", default="Medium")
    ).capitalize()
    if difficulty_value not in ("Easy", "Medium", "Hard"):
        difficulty_value = "Medium"
    _draw_text(surface, "Mode:", label_font, GRID, (810, 122))
    _draw_text(surface, mode, body_font, GRID, (866, 123))
    _draw_text(surface, "Difficulty:", label_font, GRID, (810, 146))
    _draw_text(surface, difficulty_value, body_font, GRID, (884, 147))

    current_player = game_state.current_turn
    badge_color = PLAYER_COLORS[current_player]
    turn_badge = pygame.Rect(810, 172, 260, 30)
    pygame.draw.rect(surface, badge_color, turn_badge, border_radius=8)
    pygame.draw.rect(
        surface,
        PLAYER_DARK_COLORS[current_player],
        turn_badge,
        2,
        border_radius=8,
    )
    turn_font = pygame.font.SysFont("Segoe UI", 13, bold=True)
    _draw_text(
        surface,
        "{} TURN".format(current_player),
        turn_font,
        PAPER,
        (turn_badge.x + 12, turn_badge.y + 7),
    )

    _draw_text(surface, "DICE", label_font, GRID, (810, 218))
    die_rect = pygame.Rect(890, 214, 100, 100)
    _draw_die(surface, game_state.dice_value, die_rect)

    telemetry = pygame.Rect(805, 330, 270, 250)
    pygame.draw.rect(surface, BG, telemetry, border_radius=10)
    pygame.draw.rect(surface, SOFT_GRID, telemetry, 1, border_radius=10)
    _draw_text(
        surface,
        "AI ENGINE TELEMETRY",
        label_font,
        GRID,
        (817, 341),
    )
    agent_one = "Human Player" if human_mode else "Minimax + Alpha-Beta"
    agent_two = (
        "Minimax + Alpha-Beta"
        if human_mode
        else "Expectimax (Chance Nodes)"
    )
    _draw_text(surface, "Agent 1 (RED)", small_font, RED_DARK, (817, 365))
    _draw_text(surface, agent_one, body_font, GRID, (817, 382))
    _draw_text(surface, "Agent 2 (BLUE)", small_font, BLUE_DARK, (817, 405))
    _draw_text(surface, agent_two, body_font, GRID, (817, 422))

    nodes = _ui_value(ui_state, "nodes_explored", "nodes", default=0)
    pruned = _ui_value(
        ui_state,
        "branches_pruned",
        "pruned_branches",
        "pruned",
        default=0,
    )
    heuristic = _ui_value(
        ui_state,
        "heuristic_score",
        "last_score",
        "score",
        default=0.0,
    )
    heuristic_text = (
        "{:.2f}".format(heuristic)
        if isinstance(heuristic, (int, float))
        else str(heuristic)
    )
    _draw_text(surface, "Nodes Explored: {}".format(nodes), body_font, GRID, (817, 450))
    _draw_text(surface, "Branches Pruned: {}".format(pruned), body_font, GRID, (817, 470))
    _draw_text(
        surface,
        "Heuristic Score: {}".format(heuristic_text),
        body_font,
        GRID,
        (817, 490),
    )
    _draw_text(surface, "Status:", small_font, GRID, (817, 515))
    status = _ui_value(
        ui_state,
        "status_message",
        "status",
        default="Ready",
    )
    _draw_wrapped_text(
        surface,
        status,
        body_font,
        GRID,
        817,
        533,
        244,
        16,
    )

    button_specs = (
        ("roll", "Roll Dice (SPACE)", GRID, PAPER),
        ("mode", "Switch Mode", BG, GRID),
        ("difficulty", "Difficulty: {}".format(difficulty_value), BG, GRID),
        ("reset", "Reset Game", (255, 224, 224), RED_DARK),
    )
    buttons = {}
    button_font = pygame.font.SysFont("Segoe UI", 13, bold=True)
    for index, (key, label, fill, text_color) in enumerate(button_specs):
        rect = pygame.Rect(810, 592 + index * 40, 260, 34)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, SOFT_GRID, rect, 1, border_radius=8)
        text = button_font.render(label, True, text_color)
        surface.blit(text, text.get_rect(center=rect.center))
        buttons[key] = rect

    return buttons


def main():
    pygame.init()
    pygame.display.set_caption("LudoVerse")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    game_state = GameState(num_players=2)
    ui_state = {
        "mode": "AI vs AI",
        "difficulty": "Medium",
        "nodes_explored": 0,
        "branches_pruned": 0,
        "heuristic_score": 0.0,
        "status_message": "Ready",
    }

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(BG)
        draw_board(screen)
        draw_dynamic_pieces(screen, game_state)
        draw_control_panel(screen, game_state, ui_state)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
