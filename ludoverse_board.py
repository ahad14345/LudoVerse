import math
import sys

import pygame

from game_state import GameState
from rules import SAFE_CELLS


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
PANEL_DARK = (30, 41, 59)
PANEL_TEXT = (15, 23, 42)
MUTED_TEXT = (100, 116, 139)
GOLD = (255, 191, 71)
LEGAL_HALO = (255, 159, 28)
PIP_RED = (185, 28, 28)
PIP_DARK = (127, 29, 29)

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
_PIECE_NUMBER_FONTS = {}


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
    inset = int(rect.width * 0.18)
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


def draw_piece(surface, row, col, color, dark, radius=None, piece_id=None):
    rect = cell_rect(row, col)
    cx = rect.centerx
    cy = rect.centery
    radius = radius or int(CELL * 0.40)
    _draw_piece_at(surface, (cx, cy), color, dark, radius, piece_id)


def draw_base(surface, rect, color, dark):
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, GRID, rect, 3)

    inset = int(rect.width * 0.18)
    inner = rect.inflate(-inset * 2, -inset * 2)
    pygame.draw.rect(
        surface,
        SHADOW,
        inner.move(0, 5),
        border_radius=22,
    )
    pygame.draw.rect(surface, PAPER, inner, border_radius=18)
    pygame.draw.rect(surface, SOFT_GRID, inner, 2, border_radius=18)

    positions = (
        (inner.left + inner.width * 0.29, inner.top + inner.height * 0.29),
        (inner.right - inner.width * 0.29, inner.top + inner.height * 0.29),
        (inner.left + inner.width * 0.29, inner.bottom - inner.height * 0.29),
        (inner.right - inner.width * 0.29, inner.bottom - inner.height * 0.29),
    )
    for cx, cy in positions:
        center = (int(cx), int(cy))
        pastel = tuple(
            int(channel * 0.2 + 255 * 0.8) for channel in color
        )
        pygame.draw.circle(surface, pastel, center, 13)
        pygame.draw.circle(surface, dark, center, 13, 2)


def draw_center(surface):
    left = BOARD_OFFSET + 6 * CELL
    top = BOARD_OFFSET + 6 * CELL
    right = BOARD_OFFSET + 9 * CELL
    bottom = BOARD_OFFSET + 9 * CELL
    center = (BOARD_OFFSET + int(7.5 * CELL),) * 2
    top_left = (left, top)
    top_right = (right, top)
    bottom_left = (left, bottom)
    bottom_right = (right, bottom)

    pygame.draw.polygon(surface, RED, [top_left, bottom_left, center])
    pygame.draw.polygon(surface, GREEN, [top_left, top_right, center])
    pygame.draw.polygon(surface, BLUE, [top_right, bottom_right, center])
    pygame.draw.polygon(surface, YELLOW, [bottom_left, bottom_right, center])
    pygame.draw.rect(
        surface,
        GRID,
        pygame.Rect(left, top, right - left, bottom - top),
        2,
    )
    for corner in (top_left, top_right, bottom_left, bottom_right):
        pygame.draw.line(surface, GRID, corner, center, 2)

    pygame.draw.circle(surface, PAPER, center, 10)
    pygame.draw.circle(surface, GOLD, center, 10, 2)
    draw_star(surface, center, 5, GOLD, YELLOW_DARK)


def _draw_launch_tile(surface, row, col, color, direction):
    rect = cell_rect(row, col)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, GRID, rect, 2)
    pygame.draw.rect(surface, PAPER, rect.inflate(-8, -8), 1)

    dx, dy = direction
    px, py = -dy, dx
    cx, cy = rect.center
    tip = (cx + dx * 14, cy + dy * 14)
    tail = (cx - dx * 12, cy - dy * 12)
    points = (
        tip,
        (cx + dx * 5 + px * 7, cy + dy * 5 + py * 7),
        (cx + dx * 5 + px * 3, cy + dy * 5 + py * 3),
        (tail[0] + px * 3, tail[1] + py * 3),
        (tail[0] - px * 3, tail[1] - py * 3),
        (cx + dx * 5 - px * 3, cy + dy * 5 - py * 3),
        (cx + dx * 5 - px * 7, cy + dy * 5 - py * 7),
    )
    pygame.draw.polygon(surface, PAPER, points)
    pygame.draw.polygon(surface, color, points, 1)


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
    for row, col in SAFE_CELLS:
        rect = cell_rect(row, col)
        pygame.draw.rect(surface, TRACK, rect)
        pygame.draw.rect(surface, SOFT_GRID, rect, 2)
        pygame.draw.circle(surface, PAPER, rect.center, int(CELL * 0.34))
        draw_star(surface, rect.center, int(CELL * 0.24), GOLD, YELLOW_DARK)

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

    start_cells = (
        (6, 1, RED, (1, 0)),
        (1, 8, GREEN, (0, 1)),
        (8, 13, BLUE, (-1, 0)),
        (13, 6, YELLOW, (0, -1)),
    )
    for row, col, color, direction in start_cells:
        _draw_launch_tile(surface, row, col, color, direction)

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


def _draw_piece_at(surface, center, color, dark, radius, piece_id=None):
    cx, cy = center
    pygame.draw.circle(surface, PANEL_DARK, (cx + 3, cy + 5), radius + 3)
    pygame.draw.circle(surface, PANEL_DARK, (cx, cy), radius)
    pygame.draw.circle(surface, dark, (cx, cy), max(1, radius - 2))
    pygame.draw.circle(surface, color, (cx, cy - 1), max(1, radius - 4))
    pygame.draw.circle(surface, PAPER, (cx, cy), max(2, radius - 7), 2)
    dome_color = tuple(
        min(255, int(channel * 0.62 + 255 * 0.38))
        for channel in color
    )
    pygame.draw.circle(
        surface,
        dome_color,
        (cx, cy - 2),
        max(2, radius - 10),
    )
    pygame.draw.circle(
        surface,
        PAPER,
        (cx - max(3, radius // 3), cy - max(3, radius // 3)),
        max(2, radius // 5),
    )
    if piece_id is not None:
        font_size = max(8, int(radius * 0.68))
        if font_size not in _PIECE_NUMBER_FONTS:
            _PIECE_NUMBER_FONTS[font_size] = pygame.font.SysFont(
                "Segoe UI",
                font_size,
                bold=True,
            )
        font = _PIECE_NUMBER_FONTS[font_size]
        number = str(piece_id + 1)
        shadow = font.render(number, True, PANEL_DARK)
        text = font.render(number, True, PAPER)
        shadow_rect = shadow.get_rect(center=(cx + 1, cy + 1))
        text_rect = text.get_rect(center=(cx, cy))
        surface.blit(shadow, shadow_rect)
        surface.blit(text, text_rect)


def _draw_legal_highlight(surface, center):
    cx, cy = center
    pulse = int((math.sin(pygame.time.get_ticks() / 180) + 1) * 1.5)
    radius = int(CELL * 0.42) + pulse
    pygame.draw.circle(surface, (255, 225, 171), center, radius + 4, 6)
    pygame.draw.circle(surface, LEGAL_HALO, center, radius, 3)
    pygame.draw.circle(surface, GOLD, center, radius + 7, 1)


def draw_dynamic_pieces(surface, game_state, legal_moves=None):
    for player in game_state.players:
        color = PLAYER_COLORS[player]
        dark = PLAYER_DARK_COLORS[player]
        for piece in game_state.pieces[player]:
            center = _piece_center(player, piece)
            if piece.state == "ACTIVE":
                row, col = piece.get_board_coords()
                draw_piece(
                    surface,
                    row,
                    col,
                    color,
                    dark,
                    piece_id=piece.piece_id,
                )
            else:
                radius = int(CELL * (0.40 if piece.state == "BASE" else 0.18))
                _draw_piece_at(
                    surface,
                    center,
                    color,
                    dark,
                    radius,
                    piece.piece_id,
                )

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
    pygame.draw.rect(surface, SHADOW, rect.move(2, 4), border_radius=14)
    pygame.draw.rect(surface, PAPER, rect, border_radius=14)
    pygame.draw.rect(surface, SOFT_GRID, rect, 2, border_radius=14)
    if value not in range(1, 7):
        font = pygame.font.SysFont("Segoe UI", 42, bold=True)
        text = font.render("?", True, PIP_DARK)
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
        pygame.draw.circle(surface, PIP_DARK, (pip[0] + 1, pip[1] + 2), 7)
        pygame.draw.circle(surface, PIP_RED, pip, 6)


def draw_control_panel(surface, game_state, ui_state):
    panel = pygame.Rect(PANEL_X, 40, 300, 720)
    pygame.draw.rect(surface, PAPER, panel, border_radius=14)
    header = pygame.Rect(PANEL_X, 40, 300, 96)
    pygame.draw.rect(surface, PANEL_DARK, header, border_radius=14)
    title_font = pygame.font.SysFont("Segoe UI", 23, bold=True)
    subtitle_font = pygame.font.SysFont("Segoe UI", 12, bold=True)
    label_font = pygame.font.SysFont("Segoe UI", 12, bold=True)
    body_font = pygame.font.SysFont("Segoe UI", 12)
    small_font = pygame.font.SysFont("Segoe UI", 10)

    _draw_text(surface, "LUDOVERSE", title_font, PAPER, (810, 58))
    _draw_text(
        surface,
        "Where Luck Meets Intelligence",
        subtitle_font,
        GOLD,
        (810, 91),
    )

    raw_mode = str(_ui_value(ui_state, "mode", default="AI vs AI"))
    human_mode = raw_mode.lower().replace(" ", "") in ("human", "humanvsai")
    mode = "Human vs AI" if human_mode else "AI vs AI"
    difficulty_value = str(
        _ui_value(ui_state, "difficulty", default="Medium")
    ).capitalize()
    if difficulty_value not in ("Easy", "Medium", "Hard"):
        difficulty_value = "Medium"
    _draw_text(surface, "MODE", small_font, MUTED_TEXT, (810, 147))
    _draw_text(surface, mode, label_font, PANEL_TEXT, (810, 160))
    _draw_text(surface, "DIFFICULTY", small_font, MUTED_TEXT, (947, 147))
    _draw_text(surface, difficulty_value, label_font, PANEL_TEXT, (947, 160))

    current_player = game_state.current_turn
    badge_color = PLAYER_COLORS[current_player]
    turn_badge = pygame.Rect(810, 188, 260, 30)
    pygame.draw.rect(surface, badge_color, turn_badge, border_radius=8)
    pygame.draw.rect(
        surface,
        PLAYER_DARK_COLORS[current_player],
        turn_badge,
        2,
        border_radius=8,
    )
    turn_font = pygame.font.SysFont("Segoe UI", 12, bold=True)
    _draw_text(
        surface,
        "ACTIVE TURN  |  {}".format(current_player),
        turn_font,
        PAPER,
        (turn_badge.x + 10, turn_badge.y + 8),
    )

    dice_card = pygame.Rect(805, 232, 270, 132)
    pygame.draw.rect(
        surface,
        SHADOW,
        dice_card.move(0, 4),
        border_radius=14,
    )
    pygame.draw.rect(surface, BG, dice_card, border_radius=14)
    pygame.draw.rect(surface, SOFT_GRID, dice_card, 1, border_radius=14)
    _draw_text(surface, "DICE ROLL", label_font, PANEL_DARK, (817, 240))
    die_rect = pygame.Rect(817, 256, 100, 100)
    _draw_die(surface, game_state.dice_value, die_rect)
    if game_state.dice_value is None:
        _draw_text(
            surface,
            "Roll Dice",
            pygame.font.SysFont("Segoe UI", 17, bold=True),
            PANEL_DARK,
            (935, 275),
        )
        _draw_text(
            surface,
            "Press SPACE",
            body_font,
            MUTED_TEXT,
            (935, 302),
        )
    else:
        _draw_text(
            surface,
            "RESULT",
            small_font,
            MUTED_TEXT,
            (935, 274),
        )
        _draw_text(
            surface,
            str(game_state.dice_value),
            pygame.font.SysFont("Segoe UI", 22, bold=True),
            PIP_DARK,
            (935, 290),
        )
        _draw_text(
            surface,
            "Good luck!",
            body_font,
            MUTED_TEXT,
            (935, 322),
        )

    telemetry = pygame.Rect(805, 376, 270, 204)
    pygame.draw.rect(surface, BG, telemetry, border_radius=12)
    pygame.draw.rect(surface, SOFT_GRID, telemetry, 1, border_radius=12)
    _draw_text(
        surface,
        "AI ENGINE TELEMETRY",
        pygame.font.SysFont("Segoe UI", 12, bold=True),
        PANEL_DARK,
        (817, 386),
    )
    agent_one = _ui_value(
        ui_state,
        "agent1",
        default="Human Player" if human_mode else "Minimax + Alpha-Beta",
    )
    agent_two = _ui_value(
        ui_state,
        "agent2",
        default=(
            "Minimax + Alpha-Beta"
            if human_mode
            else "Expectimax (Chance Nodes)"
        ),
    )
    _draw_text(surface, "Agent 1 (RED)", small_font, RED_DARK, (817, 407))
    _draw_text(surface, agent_one, body_font, PANEL_TEXT, (817, 420))
    _draw_text(surface, "Agent 2 (BLUE)", small_font, BLUE_DARK, (817, 443))
    _draw_text(surface, agent_two, body_font, PANEL_TEXT, (817, 456))

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
    metric_labels = ("Nodes\nExplored", "Branches\nPruned", "Heuristic\nScore")
    metric_values = (nodes, pruned, heuristic_text)
    metric_label_font = pygame.font.SysFont("Segoe UI", 9, bold=True)
    metric_value_font = pygame.font.SysFont("Consolas", 14, bold=True)
    for index, (metric_label, metric_value) in enumerate(
        zip(metric_labels, metric_values)
    ):
        rect = pygame.Rect(813 + index * 84, 480, 80, 61)
        pygame.draw.rect(surface, PAPER, rect, border_radius=9)
        pygame.draw.rect(surface, SOFT_GRID, rect, 1, border_radius=9)
        for line_index, line in enumerate(metric_label.splitlines()):
            _draw_text(
                surface,
                line,
                metric_label_font,
                MUTED_TEXT,
                (rect.x + 6, rect.y + 4 + line_index * 10),
            )
        value_text = str(metric_value)
        value_surface = metric_value_font.render(value_text, True, PANEL_DARK)
        surface.blit(
            value_surface,
            value_surface.get_rect(
                midleft=(rect.x + 6, rect.y + 47)
            ),
        )

    _draw_text(surface, "STATUS", small_font, MUTED_TEXT, (817, 548))
    status = _ui_value(
        ui_state,
        "status_message",
        "status",
        default="Ready",
    )
    _draw_wrapped_text(
        surface,
        status,
        pygame.font.SysFont("Segoe UI", 10),
        PANEL_TEXT,
        866,
        547,
        194,
        13,
    )

    button_specs = (
        ("roll", "Roll Dice (SPACE)", PANEL_DARK, PAPER, GOLD, PANEL_DARK),
        ("mode", "Switch Mode", BG, PANEL_TEXT, (226, 232, 240), PANEL_DARK),
        (
            "difficulty",
            "Difficulty: {}".format(difficulty_value),
            BG,
            PANEL_TEXT,
            (226, 232, 240),
            PANEL_DARK,
        ),
        (
            "reset",
            "Reset Game",
            (254, 226, 226),
            RED_DARK,
            (254, 202, 202),
            RED_DARK,
        ),
    )
    buttons = {}
    button_font = pygame.font.SysFont("Segoe UI", 13, bold=True)
    mouse_pos = pygame.mouse.get_pos()
    for index, (key, label, fill, text_color, hover_fill, hover_text) in enumerate(
        button_specs
    ):
        rect = pygame.Rect(810, 590 + index * 40, 260, 34)
        hovered = rect.collidepoint(mouse_pos)
        current_fill = hover_fill if hovered else fill
        current_text = hover_text if hovered else text_color
        pygame.draw.rect(surface, SHADOW, rect.move(0, 3), border_radius=17)
        pygame.draw.rect(surface, current_fill, rect, border_radius=17)
        pygame.draw.rect(
            surface,
            LEGAL_HALO if hovered else SOFT_GRID,
            rect,
            2 if hovered else 1,
            border_radius=17,
        )
        text = button_font.render(label, True, current_text)
        surface.blit(text, text.get_rect(center=rect.center))
        buttons[key] = rect

    pygame.draw.rect(surface, SOFT_GRID, panel, 1, border_radius=14)
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
