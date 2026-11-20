from game_state import GameState, HOME_COLUMNS, MAIN_TRACK, START_INDEX


SAFE_CELLS = {
    (6, 1),
    (1, 8),
    (8, 13),
    (13, 6),
    (6, 2),
    (2, 6),
    (8, 12),
    (12, 8),
    (6, 6),
    (8, 8),
}


def _validate_player_and_dice(state, player, dice_value):
    if player not in state.players:
        raise ValueError("player must be part of this game")
    if dice_value not in range(1, 7):
        raise ValueError("dice_value must be between 1 and 6")


def get_legal_moves(state: GameState, player: str, dice_value: int) -> list:
    _validate_player_and_dice(state, player, dice_value)
    legal_moves = []

    for piece in state.pieces[player]:
        if piece.state == "BASE" and piece.step_count == -1 and dice_value == 6:
            legal_moves.append(piece.piece_id)
        elif (
            piece.state == "ACTIVE"
            and piece.step_count + dice_value <= 56
        ):
            legal_moves.append(piece.piece_id)
        elif piece.state not in ("BASE", "ACTIVE", "HOME"):
            raise ValueError("piece state must be BASE, ACTIVE, or HOME")

    return legal_moves


def _next_player(state, player):
    player_index = state.players.index(player)
    return state.players[(player_index + 1) % len(state.players)]


def apply_move(
    state: GameState,
    player: str,
    piece_id: int,
    dice_value: int,
) -> GameState:
    new_state = state.clone()
    _validate_player_and_dice(new_state, player, dice_value)
    legal_moves = get_legal_moves(new_state, player, dice_value)

    if piece_id is None:
        if legal_moves:
            raise ValueError("cannot skip a turn when a legal move exists")
        new_state.current_turn = _next_player(new_state, player)
        new_state.consecutive_sixes = 0
        new_state.dice_value = None
        return new_state

    if piece_id not in legal_moves:
        raise ValueError("piece_id must identify a legal move")

    piece = new_state.pieces[player][piece_id]
    if piece.state == "BASE":
        piece.state = "ACTIVE"
        piece.step_count = 0
    else:
        piece.step_count += dice_value
        if piece.step_count == 56:
            piece.state = "HOME"

    captured = False
    if piece.state == "ACTIVE" and 0 <= piece.step_count <= 50:
        coords = piece.get_board_coords()
        if coords not in SAFE_CELLS:
            for opponent in new_state.players:
                if opponent == player:
                    continue
                for opponent_piece in new_state.pieces[opponent]:
                    if (
                        opponent_piece.state == "ACTIVE"
                        and opponent_piece.get_board_coords() == coords
                    ):
                        opponent_piece.state = "BASE"
                        opponent_piece.step_count = -1
                        captured = True

    if all(piece.state == "HOME" for piece in new_state.pieces[player]):
        new_state.winner = player

    if new_state.consecutive_sixes >= 3:
        new_state.current_turn = _next_player(new_state, player)
        new_state.consecutive_sixes = 0
    elif dice_value == 6 or captured:
        new_state.current_turn = player
    else:
        new_state.current_turn = _next_player(new_state, player)

    new_state.dice_value = None
    return new_state


def is_terminal(state: GameState) -> bool:
    return get_winner(state) is not None


def get_winner(state: GameState):
    if state.winner is not None:
        return state.winner

    for player in state.players:
        if all(piece.state == "HOME" for piece in state.pieces[player]):
            return player
    return None
