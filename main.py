import pygame

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
    get_clicked_piece,
)
from rules import apply_move, get_legal_moves, get_winner, is_terminal


MODES = ["AI vs AI", "Human vs AI"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
DEFAULT_MODE = "AI vs AI"
DEFAULT_DIFFICULTY = "Medium"
STEP_DELAY_MS = 450


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
        ui_state["status"] = "{} captured {}!".format(
            player.title(),
            ", ".join(opponent.title() for opponent in captured_players),
        )
    else:
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
        "Click Reset Game to play again",
        True,
        GRID,
    )
    surface.blit(title, title.get_rect(center=(banner.centerx, banner.y + 62)))
    surface.blit(prompt, prompt.get_rect(center=(banner.centerx, banner.y + 118)))


def main():
    pygame.init()
    pygame.display.set_caption("LudoVerse")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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
    }
    _sync_agent_labels(ui_state)

    last_step_time = pygame.time.get_ticks()
    button_rects = {}
    running = True
    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
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
                position = event.pos
                if button_rects.get("mode") and button_rects["mode"].collidepoint(position):
                    mode = MODES[(MODES.index(mode) + 1) % len(MODES)]
                    agents = create_agents(mode, difficulty)
                    state = GameState(num_players=2)
                    ui_state["mode"] = mode
                    ui_state["paused"] = False
                    ui_state["status"] = "Mode changed to {}.".format(mode)
                    _clear_telemetry(ui_state)
                    _sync_agent_labels(ui_state)
                    last_step_time = pygame.time.get_ticks()
                elif (
                    button_rects.get("difficulty")
                    and button_rects["difficulty"].collidepoint(position)
                ):
                    difficulty = DIFFICULTIES[
                        (DIFFICULTIES.index(difficulty) + 1)
                        % len(DIFFICULTIES)
                    ]
                    agents = create_agents(mode, difficulty)
                    ui_state["difficulty"] = difficulty
                    ui_state["status"] = "Difficulty set to {}.".format(
                        difficulty
                    )
                    _clear_telemetry(ui_state)
                elif (
                    button_rects.get("reset")
                    and button_rects["reset"].collidepoint(position)
                ):
                    state = GameState(num_players=2)
                    ui_state["paused"] = False
                    ui_state["status"] = "Game reset."
                    _clear_telemetry(ui_state)
                    last_step_time = pygame.time.get_ticks()
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
        state, last_step_time = _advance_game(
            state,
            agents,
            ui_state,
            now,
            last_step_time,
        )

        screen.fill(BG)
        draw_board(screen)
        legal_moves = (
            get_legal_moves(state, state.current_turn, state.dice_value)
            if state.dice_value is not None and not is_terminal(state)
            else []
        )
        draw_dynamic_pieces(screen, state, legal_moves)
        button_rects = draw_control_panel(screen, state, ui_state)
        if is_terminal(state):
            _draw_terminal_banner(screen, get_winner(state))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
