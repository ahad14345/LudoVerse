import random


MAIN_TRACK = [
    (6, 1),
    (6, 2),
    (6, 3),
    (6, 4),
    (6, 5),
    (5, 6),
    (4, 6),
    (3, 6),
    (2, 6),
    (1, 6),
    (0, 6),
    (0, 7),
    (0, 8),
    (1, 8),
    (2, 8),
    (3, 8),
    (4, 8),
    (5, 8),
    (6, 9),
    (6, 10),
    (6, 11),
    (6, 12),
    (6, 13),
    (6, 14),
    (7, 14),
    (8, 14),
    (8, 13),
    (8, 12),
    (8, 11),
    (8, 10),
    (8, 9),
    (9, 8),
    (10, 8),
    (11, 8),
    (12, 8),
    (13, 8),
    (14, 8),
    (14, 7),
    (14, 6),
    (13, 6),
    (12, 6),
    (11, 6),
    (10, 6),
    (9, 6),
    (8, 5),
    (8, 4),
    (8, 3),
    (8, 2),
    (8, 1),
    (8, 0),
    (7, 0),
    (6, 0),
]

START_INDEX = {
    "RED": 0,
    "GREEN": 13,
    "BLUE": 26,
    "YELLOW": 39,
}

HOME_COLUMNS = {
    "RED": [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],
    "GREEN": [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)],
    "BLUE": [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)],
    "YELLOW": [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)],
}

ALL_PLAYERS = ("RED", "GREEN", "BLUE", "YELLOW")


class Piece:
    def __init__(self, player, piece_id, state="BASE", step_count=-1):
        if player not in ALL_PLAYERS:
            raise ValueError("player must be RED, GREEN, BLUE, or YELLOW")
        if piece_id not in range(4):
            raise ValueError("piece_id must be between 0 and 3")
        if state not in ("BASE", "ACTIVE", "HOME"):
            raise ValueError("state must be BASE, ACTIVE, or HOME")
        if state == "BASE" and step_count != -1:
            raise ValueError("BASE pieces must have a step_count of -1")
        if state == "ACTIVE" and not 0 <= step_count <= 55:
            raise ValueError("ACTIVE pieces must have a step_count between 0 and 55")
        if state == "HOME" and step_count != 56:
            raise ValueError("HOME pieces must have a step_count of 56")

        self.player = player
        self.piece_id = piece_id
        self.state = state
        self.step_count = step_count

    def get_board_coords(self):
        if self.state == "BASE":
            return None
        if self.state == "HOME":
            return HOME_COLUMNS[self.player][-1]
        if self.state != "ACTIVE":
            raise ValueError("state must be BASE, ACTIVE, or HOME")

        if 0 <= self.step_count <= 50:
            track_index = (START_INDEX[self.player] + self.step_count) % len(MAIN_TRACK)
            return MAIN_TRACK[track_index]
        if 51 <= self.step_count <= 55:
            return HOME_COLUMNS[self.player][self.step_count - 51]
        raise ValueError("ACTIVE pieces must have a step_count between 0 and 55")


class GameState:
    def __init__(self, num_players=4):
        if num_players == 2:
            self.players = ["RED", "BLUE"]
        elif num_players == 4:
            self.players = list(ALL_PLAYERS)
        else:
            raise ValueError("num_players must be 2 or 4")

        self.num_players = num_players
        self.pieces = {
            player: [Piece(player, piece_id) for piece_id in range(4)]
            for player in self.players
        }
        self.current_turn = self.players[0]
        self.dice_value = None
        self.consecutive_sixes = 0
        self.winner = None

    def roll_dice(self):
        self.dice_value = random.randint(1, 6)
        if self.dice_value == 6:
            self.consecutive_sixes += 1
        else:
            self.consecutive_sixes = 0
        return self.dice_value

    def clone(self):
        cloned_state = object.__new__(GameState)
        cloned_state.players = self.players.copy()
        cloned_state.num_players = self.num_players
        cloned_state.pieces = {
            player: [
                Piece(piece.player, piece.piece_id, piece.state, piece.step_count)
                for piece in pieces
            ]
            for player, pieces in self.pieces.items()
        }
        cloned_state.current_turn = self.current_turn
        cloned_state.dice_value = self.dice_value
        cloned_state.consecutive_sixes = self.consecutive_sixes
        cloned_state.winner = self.winner
        return cloned_state
