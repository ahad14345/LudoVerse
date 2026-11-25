import pygame
import math
from array import array

from ai_agents import ExpectimaxAgent, MinimaxAgent
from game_state import GameState
from ludoverse_board import (
    BG,
    BOARD_OFFSET,
    BOARD_SIZE,
    GRID,
    PAPER,
    PLAYER_COLORS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    draw_board,
    draw_control_panel,
    draw_dynamic_pieces,
    draw_game_background,
    draw_selection_popup,
    get_clicked_piece,
)
from rules import apply_move, get_legal_moves, get_winner, is_terminal


MODES = ["AI vs AI", "Human vs AI"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
DEFAULT_MODE = "AI vs AI"
DEFAULT_DIFFICULTY = "Medium"
STEP_DELAY_MS = 450


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.effects = {}
        if not pygame.mixer.get_init():
            return

        pygame.mixer.set_num_channels(8)
        self.effects = {
            "button": self._make_tone((520, 620), 0.07),
            "dice": self._make_sequence(((480, 0.04), (560, 0.04), (640, 0.05))),
            "move": self._make_tone((360, 500), 0.10),
            "capture": self._make_tone((170, 95), 0.22),
            "skip": self._make_tone((220, 180), 0.12),
            "win": self._make_sequence(
                ((440, 0.16), (554, 0.16), (659, 0.16), (880, 0.36))
            ),
        }

    def _make_tone(self, frequencies, duration, volume=0.28):
        sample_rate = 44100
        frame_count = int(sample_rate * duration)
        start_frequency, end_frequency = frequencies
        samples = array("h")

        for frame in range(frame_count):
            progress = frame / max(1, frame_count - 1)
            frequency = start_frequency + (end_frequency - start_frequency) * progress
            envelope = min(1.0, frame / 800.0) * min(1.0, (frame_count - frame) / 1200.0)
            phase = 2 * math.pi * frequency * frame / sample_rate
            value = int(32767 * volume * envelope * math.sin(phase))
            samples.append(value)
            samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _make_sequence(self, notes, volume=0.28):
        sample_rate = 44100
        samples = array("h")

        for frequency, duration in notes:
            frame_count = int(sample_rate * duration)
            for frame in range(frame_count):
                progress = frame / max(1, frame_count - 1)
                envelope = min(1.0, frame / 600.0) * min(1.0, (frame_count - frame) / 900.0)
                phase = 2 * math.pi * frequency * frame / sample_rate
                value = int(32767 * volume * envelope * math.sin(phase))
                samples.append(value)
                samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.enabled:
            effect = self.effects.get(name)
            if effect is not None:
                effect.play()

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()
        return self.enabled


_sounds = SoundManager.__new__(SoundManager)
_sounds.enabled = True
_sounds.effects = {}


def create_agents(mode, difficulty):
    if mode not in MODES:
        raise ValueError("mode must be AI vs AI or Human vs AI")
    if difficulty not in DIFFICULTIES:
        raise ValueError("difficulty must be Easy, Medium, or Hard")

    depths = {
        "Easy": (2, 1),
        "Medium": (4, 2),
        "Hard": (6, 3),
    }
    minimax_depth, expectimax_depth = depths[difficulty]

    if mode == "AI vs AI":
        return {
            "RED": MinimaxAgent(max_depth=minimax_depth),
            "BLUE": ExpectimaxAgent(max_depth=expectimax_depth),
        }

    return {
        "RED": None,
        "BLUE": MinimaxAgent(max_depth=minimax_depth),
    }


def _agent_label(player, mode):
    if mode == "Human vs AI" and player == "RED":
        return "Human Player"
    if mode == "AI vs AI" and player == "BLUE":
        return "Expectimax (Chance Nodes)"
    return "Minimax + Alpha-Beta"


def _sync_agent_labels(ui_state):
    ui_state["agent1"] = _agent_label("RED", ui_state["mode"])
    ui_state["agent2"] = _agent_label("BLUE", ui_state["mode"])


def _clear_telemetry(ui_state):
    ui_state["nodes"] = 0
    ui_state["pruned"] = 0
    ui_state["score"] = 0.0


def _roll_dice(state, ui_state):
    player = state.current_turn
    dice_value = state.roll_dice()
    _sounds.play("dice")
    legal_moves = get_legal_moves(state, player, dice_value)
    if legal_moves:
        ui_state["status"] = "{} rolled {}!".format(
            player.title(),
            dice_value,
        )
    else:
        ui_state["status"] = (
            "{} rolled {} - No legal moves (Skip)".format(
                player.title(),
                dice_value,
            )
        )


def _apply_selected_move(state, player, piece_id, dice_value, ui_state):
    before = {
        opponent: sum(
            piece.state == "ACTIVE"
            for piece in state.pieces[opponent]
        )
        for opponent in state.players
        if opponent != player
    }
    next_state = apply_move(state, player, piece_id, dice_value)
    captured_players = [
        opponent
        for opponent, active_count in before.items()
        if sum(
            piece.state == "ACTIVE"
            for piece in next_state.pieces[opponent]
        ) < active_count
    ]

    if captured_players:
        _sounds.play("capture")
        ui_state["status"] = "{} captured {}!".format(
            player.title(),
            ", ".join(opponent.title() for opponent in captured_players),
        )
    else:
        _sounds.play("move")
        ui_state["status"] = "{} moved piece {}.".format(
            player.title(),
            piece_id + 1,
        )
    return next_state


def _advance_game(state, agents, ui_state, now, last_step_time):
    if is_terminal(state):
        return state, last_step_time
    if (
        ui_state["mode"] == "AI vs AI"
        and ui_state.get("paused", False)
    ):
        return state, last_step_time
    if now - last_step_time < STEP_DELAY_MS:
        return state, last_step_time

    player = state.current_turn
    if state.dice_value is None:
        if agents[player] is not None:
            _roll_dice(state, ui_state)
            return state, now
        return state, last_step_time

    dice_value = state.dice_value
    legal_moves = get_legal_moves(state, player, dice_value)
    if not legal_moves:
        _sounds.play("skip")
        ui_state["status"] = (
            "{} rolled {} - No legal moves (Skip)".format(
                player.title(),
                dice_value,
            )
        )
        return (
            apply_move(state, player, None, dice_value),
            now,
        )

    agent = agents[player]
    if agent is None:
        return state, last_step_time

    chosen_piece = agent.choose_move(state, player, dice_value)
    ui_state["nodes"] = agent.nodes_explored
    ui_state["pruned"] = getattr(agent, "pruned_branches", 0)
    ui_state["score"] = agent.last_score
    return (
        _apply_selected_move(state, player, chosen_piece, dice_value, ui_state),
        now,
    )


def _apply_mode_selection(selected_mode, state, agents, difficulty, ui_state):
    agents = create_agents(selected_mode, difficulty)
    state = GameState(num_players=2)
    ui_state["mode"] = selected_mode
    ui_state["paused"] = False
    ui_state["status"] = "Mode changed to {}.".format(selected_mode)
    _clear_telemetry(ui_state)
    _sync_agent_labels(ui_state)
    return state, agents


def _apply_difficulty_selection(
    selected_difficulty,
    state,
    agents,
    mode,
    ui_state,
):
    agents = create_agents(mode, selected_difficulty)
    state = GameState(num_players=2)
    ui_state["difficulty"] = selected_difficulty
    ui_state["paused"] = False
    ui_state["status"] = "Difficulty set to {}. New game started.".format(
        selected_difficulty
    )
    _clear_telemetry(ui_state)
    return state, agents


def _draw_terminal_banner(surface, winner):
    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    overlay.fill((GRID[0], GRID[1], GRID[2], 150))
    surface.blit(overlay, (BOARD_OFFSET, BOARD_OFFSET))

    banner = pygame.Rect(BOARD_OFFSET + 110, BOARD_OFFSET + 270, 500, 180)
    pygame.draw.rect(surface, PAPER, banner, border_radius=16)
    pygame.draw.rect(surface, PLAYER_COLORS[winner], banner, 4, border_radius=16)

    title_font = pygame.font.SysFont("Segoe UI", 34, bold=True)
    prompt_font = pygame.font.SysFont("Segoe UI", 17)
    title = title_font.render("{} Wins!".format(winner.title()), True, GRID)
    prompt = prompt_font.render(
        "Ready for another game?",
        True,
        GRID,
    )
    surface.blit(title, title.get_rect(center=(banner.centerx, banner.y + 62)))
    surface.blit(prompt, prompt.get_rect(center=(banner.centerx, banner.y + 104)))
    reset_rect = pygame.Rect(banner.centerx - 90, banner.bottom - 42, 180, 34)
    pygame.draw.rect(surface, PLAYER_COLORS[winner], reset_rect, border_radius=17)
    pygame.draw.rect(surface, GRID, reset_rect, 1, border_radius=17)
    reset_font = pygame.font.SysFont("Segoe UI", 15, bold=True)
    reset_text = reset_font.render("Play Again", True, PAPER)
    surface.blit(reset_text, reset_text.get_rect(center=reset_rect.center))
    return reset_rect


def _logical_viewport(window_size):
    scale = min(
        window_size[0] / WINDOW_WIDTH,
        window_size[1] / WINDOW_HEIGHT,
    )
    width = max(1, int(WINDOW_WIDTH * scale))
    height = max(1, int(WINDOW_HEIGHT * scale))
    return (
        scale,
        (window_size[0] - width) // 2,
        (window_size[1] - height) // 2,
        (width, height),
    )


def _to_logical_position(position, window_size):
    scale, offset_x, offset_y, _ = _logical_viewport(window_size)
    return (
        int((position[0] - offset_x) / scale),
        int((position[1] - offset_y) / scale),
    )


def _reset_game(ui_state):
    ui_state["paused"] = False
    ui_state["status"] = "Game reset."
    _clear_telemetry(ui_state)
    _sounds.play("button")
    return GameState(num_players=2)


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    global _sounds
    _sounds = SoundManager()
    pygame.display.set_caption("LudoVerse | F11: Fullscreen")
    screen = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        pygame.RESIZABLE,
    )
    canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    mode = DEFAULT_MODE
    difficulty = DEFAULT_DIFFICULTY
    state = GameState(num_players=2)
    agents = create_agents(mode, difficulty)
    ui_state = {
        "mode": mode,
        "difficulty": difficulty,
        "agent1": "",
        "agent2": "",
        "nodes": 0,
        "pruned": 0,
        "score": 0.0,
        "status": "Ready",
        "auto_play": True,
        "paused": False,
        "sound_enabled": True,
        "popup": None,
    }
    _sync_agent_labels(ui_state)

    last_step_time = pygame.time.get_ticks()
    win_played = False
    button_rects = {}
    popup_rects = {}
    popup_close_rect = None
    terminal_reset_rect = None
    fullscreen = False
    windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    running = True
    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if ui_state["popup"] is not None:
                        ui_state["popup"] = None
                    else:
                        running = False
                elif event.key == pygame.K_m:
                    ui_state["sound_enabled"] = _sounds.toggle()
                    ui_state["status"] = (
                        "Sound enabled"
                        if ui_state["sound_enabled"]
                        else "Sound muted"
                    )
                    if ui_state["sound_enabled"]:
                        _sounds.play("button")
                elif event.key == pygame.K_F11:
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            windowed_size,
                            pygame.RESIZABLE,
                        )
                        fullscreen = False
                    else:
                        windowed_size = screen.get_size()
                        screen = pygame.display.set_mode(
                            (0, 0),
                            pygame.FULLSCREEN,
                        )
                        fullscreen = True
                elif ui_state["popup"] is not None:
                    options = (
                        MODES
                        if ui_state["popup"] == "mode"
                        else DIFFICULTIES
                    )
                    for index, option in enumerate(options, start=1):
                        if event.key == getattr(pygame, "K_" + str(index)):
                            if ui_state["popup"] == "mode":
                                mode = option
                                state, agents = _apply_mode_selection(
                                    mode,
                                    state,
                                    agents,
                                    difficulty,
                                    ui_state,
                                )
                            else:
                                difficulty = option
                                state, agents = _apply_difficulty_selection(
                                    difficulty,
                                    state,
                                    agents,
                                    mode,
                                    ui_state,
                                )
                            ui_state["popup"] = None
                            win_played = False
                            _sounds.play("button")
                            last_step_time = pygame.time.get_ticks()
                            break
                elif (
                    event.key == pygame.K_p
                    and ui_state["mode"] == "AI vs AI"
                    and not is_terminal(state)
                ):
                    ui_state["paused"] = not ui_state.get("paused", False)
                    ui_state["status"] = (
                        "Game Paused - Press P or Resume to continue"
                        if ui_state["paused"]
                        else "Game Resumed"
                    )
                    if not ui_state["paused"]:
                        last_step_time = pygame.time.get_ticks()
                elif (
                    event.key == pygame.K_SPACE
                    and state.dice_value is None
                    and not is_terminal(state)
                    and not (
                        mode == "AI vs AI"
                        and ui_state.get("paused", False)
                    )
                ):
                    _roll_dice(state, ui_state)
                    last_step_time = pygame.time.get_ticks()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                position = _to_logical_position(event.pos, screen.get_size())
                if ui_state["popup"] is not None:
                    if popup_close_rect and popup_close_rect.collidepoint(position):
                        ui_state["popup"] = None
                    else:
                        selected = next(
                            (
                                option
                                for option, rect in popup_rects.items()
                                if rect.collidepoint(position)
                            ),
                            None,
                        )
                        if selected is not None:
                            if ui_state["popup"] == "mode":
                                mode = selected
                                state, agents = _apply_mode_selection(
                                    mode,
                                    state,
                                    agents,
                                    difficulty,
                                    ui_state,
                                )
                                last_step_time = pygame.time.get_ticks()
                                win_played = False
                                _sounds.play("button")
                            else:
                                difficulty = selected
                                state, agents = _apply_difficulty_selection(
                                    difficulty,
                                    state,
                                    agents,
                                    mode,
                                    ui_state,
                                )
                                last_step_time = pygame.time.get_ticks()
                                win_played = False
                                _sounds.play("button")
                            ui_state["popup"] = None
                        elif not pygame.Rect(350, 250, 420, 300).collidepoint(position):
                            ui_state["popup"] = None
                elif (
                    is_terminal(state)
                    and terminal_reset_rect
                    and terminal_reset_rect.collidepoint(position)
                ):
                    state = _reset_game(ui_state)
                    win_played = False
                    last_step_time = pygame.time.get_ticks()
                elif button_rects.get("sound") and button_rects["sound"].collidepoint(position):
                    ui_state["sound_enabled"] = _sounds.toggle()
                    ui_state["status"] = (
                        "Sound enabled"
                        if ui_state["sound_enabled"]
                        else "Sound muted"
                    )
                    if ui_state["sound_enabled"]:
                        _sounds.play("button")
                elif button_rects.get("mode") and button_rects["mode"].collidepoint(position):
                    ui_state["popup"] = "mode"
                    _sounds.play("button")
                elif (
                    button_rects.get("difficulty")
                    and button_rects["difficulty"].collidepoint(position)
                ):
                    ui_state["popup"] = "difficulty"
                    _sounds.play("button")
                elif (
                    button_rects.get("reset")
                    and button_rects["reset"].collidepoint(position)
                ):
                    state = _reset_game(ui_state)
                    win_played = False
                    last_step_time = pygame.time.get_ticks()
                elif (
                    button_rects.get("exit")
                    and button_rects["exit"].collidepoint(position)
                ):
                    running = False
                elif (
                    button_rects.get("roll")
                    and button_rects["roll"].collidepoint(position)
                    and state.dice_value is None
                    and not is_terminal(state)
                    and not (
                        mode == "AI vs AI"
                        and ui_state.get("paused", False)
                    )
                ):
                    _roll_dice(state, ui_state)
                    last_step_time = pygame.time.get_ticks()
                elif (
                    button_rects.get("pause")
                    and button_rects["pause"].collidepoint(position)
                    and ui_state["mode"] == "AI vs AI"
                    and not is_terminal(state)
                ):
                    ui_state["paused"] = not ui_state.get("paused", False)
                    _sounds.play("button")
                    ui_state["status"] = (
                        "Game Paused - Press P or Resume to continue"
                        if ui_state["paused"]
                        else "Game Resumed"
                    )
                    if not ui_state["paused"]:
                        last_step_time = pygame.time.get_ticks()
                elif (
                    mode == "Human vs AI"
                    and state.current_turn == "RED"
                    and state.dice_value is not None
                    and not is_terminal(state)
                ):
                    legal_moves = get_legal_moves(
                        state,
                        state.current_turn,
                        state.dice_value,
                    )
                    piece_id = get_clicked_piece(
                        position,
                        state,
                        legal_moves,
                    )
                    if piece_id is not None:
                        state = _apply_selected_move(
                            state,
                            state.current_turn,
                            piece_id,
                            state.dice_value,
                            ui_state,
                        )
                        last_step_time = pygame.time.get_ticks()

        now = pygame.time.get_ticks()
        if ui_state["popup"] is None:
            state, last_step_time = _advance_game(
                state,
                agents,
                ui_state,
                now,
                last_step_time,
            )
        winner = get_winner(state)
        if winner is not None and not win_played:
            _sounds.play("win")
            win_played = True

        mouse_position = _to_logical_position(
            pygame.mouse.get_pos(),
            screen.get_size(),
        )
        draw_game_background(canvas)
        draw_board(canvas)
        legal_moves = (
            get_legal_moves(state, state.current_turn, state.dice_value)
            if state.dice_value is not None and not is_terminal(state)
            else []
        )
        draw_dynamic_pieces(canvas, state, legal_moves)
        button_rects = draw_control_panel(
            canvas,
            state,
            ui_state,
            mouse_pos=mouse_position,
        )
        if is_terminal(state):
            terminal_reset_rect = _draw_terminal_banner(canvas, get_winner(state))
        else:
            terminal_reset_rect = None
        if ui_state["popup"] is not None:
            popup_rects, popup_close_rect = draw_selection_popup(
                canvas,
                ui_state["popup"],
                mode if ui_state["popup"] == "mode" else difficulty,
                mouse_pos=mouse_position,
            )
        screen.fill(BG)
        _, offset_x, offset_y, viewport_size = _logical_viewport(screen.get_size())
        scaled_canvas = pygame.transform.scale(canvas, viewport_size)
        screen.blit(scaled_canvas, (offset_x, offset_y))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
