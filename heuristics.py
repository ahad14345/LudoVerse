from game_state import GameState, MAIN_TRACK, Piece, START_INDEX
from rules import SAFE_CELLS


WEIGHT_HOME = 100
WEIGHT_CAPTURE = 50
WEIGHT_ACTIVE = 30
WEIGHT_SAFE = 20
WEIGHT_STEP = 1
WEIGHT_RISK = -40


def is_piece_at_risk(state: GameState, player: str, piece: Piece) -> bool:
    if (
        piece.state != "ACTIVE"
        or not 0 <= piece.step_count <= 50
        or piece.get_board_coords() in SAFE_CELLS
    ):
        return False

    piece_track_index = (
        START_INDEX[player] + piece.step_count
    ) % len(MAIN_TRACK)

    for opponent in state.players:
        if opponent == player:
            continue
        for opponent_piece in state.pieces[opponent]:
            if (
                opponent_piece.state != "ACTIVE"
                or not 0 <= opponent_piece.step_count <= 50
            ):
                continue

            opponent_track_index = (
                START_INDEX[opponent] + opponent_piece.step_count
            ) % len(MAIN_TRACK)
            distance = (
                piece_track_index - opponent_track_index
            ) % len(MAIN_TRACK)
            if 1 <= distance <= 6:
                return True

    return False


def calculate_player_score(state: GameState, player: str) -> int:
    score = 0

    for piece in state.pieces[player]:
        if piece.state == "HOME":
            score += WEIGHT_HOME + 56 * WEIGHT_STEP
        elif piece.state == "ACTIVE":
            score += WEIGHT_ACTIVE + piece.step_count * WEIGHT_STEP

        if piece.get_board_coords() in SAFE_CELLS:
            score += WEIGHT_SAFE
        if is_piece_at_risk(state, player, piece):
            score += WEIGHT_RISK

    for opponent in state.players:
        if opponent == player:
            continue
        score += sum(
            WEIGHT_CAPTURE
            for piece in state.pieces[opponent]
            if piece.state == "BASE"
        )

    return score


def evaluate_state(state: GameState, player: str) -> float:
    if state.winner == player:
        return 100000.0
    if state.winner is not None:
        return -100000.0

    my_score = calculate_player_score(state, player)
    opponent_scores = [
        calculate_player_score(state, opponent)
        for opponent in state.players
        if opponent != player
    ]
    return my_score - (max(opponent_scores) if opponent_scores else 0)
