import math
import time

from game_state import GameState
from heuristics import evaluate_state
from rules import apply_move, get_legal_moves, is_terminal


class MinimaxAgent:
    def __init__(self, max_depth=4, time_limit=1.0):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_explored = 0
        self.pruned_branches = 0
        self.last_score = 0.0

    def choose_move(self, state: GameState, player: str, dice_value: int):
        self.nodes_explored = 0
        self.pruned_branches = 0
        start_time = time.time()
        legal_moves = get_legal_moves(state, player, dice_value)

        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]

        best_move = legal_moves[0]
        best_score = -math.inf
        for piece_id in legal_moves:
            next_state = apply_move(state, player, piece_id, dice_value)
            score = self._alphabeta(
                next_state,
                self.max_depth - 1,
                -math.inf,
                math.inf,
                player,
                start_time,
            )
            if score > best_score:
                best_move = piece_id
                best_score = score

        self.last_score = best_score
        return best_move

    def _alphabeta(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        root_player: str,
        start_time: float,
    ) -> float:
        self.nodes_explored += 1
        if (
            depth <= 0
            or is_terminal(state)
            or time.time() - start_time > self.time_limit
        ):
            return evaluate_state(state, root_player)

        current_player = state.current_turn
        maximizing = current_player == root_player
        outcome_values = []

        for dice_value in (6, 4, 2):
            legal_moves = get_legal_moves(state, current_player, dice_value)
            if not legal_moves:
                next_state = apply_move(
                    state, current_player, None, dice_value
                )
                outcome_values.append(
                    self._alphabeta(
                        next_state,
                        depth - 1,
                        alpha,
                        beta,
                        root_player,
                        start_time,
                    )
                )
                continue

            value = -math.inf if maximizing else math.inf
            outcome_alpha = alpha
            outcome_beta = beta
            for piece_id in legal_moves:
                next_state = apply_move(
                    state, current_player, piece_id, dice_value
                )
                child_value = self._alphabeta(
                    next_state,
                    depth - 1,
                    outcome_alpha,
                    outcome_beta,
                    root_player,
                    start_time,
                )
                if maximizing:
                    value = max(value, child_value)
                    outcome_alpha = max(outcome_alpha, value)
                else:
                    value = min(value, child_value)
                    outcome_beta = min(outcome_beta, value)

                if outcome_beta <= outcome_alpha:
                    self.pruned_branches += 1
                    break

            outcome_values.append(value)

        return sum(outcome_values) / len(outcome_values)


class ExpectimaxAgent:
    def __init__(self, max_depth=2, time_limit=1.0):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_explored = 0
        self.last_score = 0.0

    def choose_move(self, state: GameState, player: str, dice_value: int):
        self.nodes_explored = 0
        start_time = time.time()
        legal_moves = get_legal_moves(state, player, dice_value)

        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]

        best_move = legal_moves[0]
        best_score = -math.inf
        for piece_id in legal_moves:
            next_state = apply_move(state, player, piece_id, dice_value)
            score = self._chance_node(
                next_state,
                self.max_depth - 1,
                player,
                start_time,
            )
            if score > best_score:
                best_move = piece_id
                best_score = score

        self.last_score = best_score
        return best_move

    def _chance_node(
        self,
        state: GameState,
        depth: int,
        root_player: str,
        start_time: float,
    ) -> float:
        self.nodes_explored += 1
        if (
            depth <= 0
            or is_terminal(state)
            or time.time() - start_time > self.time_limit
        ):
            return evaluate_state(state, root_player)

        return sum(
            self._decision_node(
                state,
                dice_value,
                depth,
                root_player,
                start_time,
            )
            for dice_value in range(1, 7)
        ) / 6.0

    def _decision_node(
        self,
        state: GameState,
        dice_value: int,
        depth: int,
        root_player: str,
        start_time: float,
    ) -> float:
        if (
            is_terminal(state)
            or time.time() - start_time > self.time_limit
        ):
            return evaluate_state(state, root_player)

        current_player = state.current_turn
        legal_moves = get_legal_moves(state, current_player, dice_value)
        if not legal_moves:
            next_state = apply_move(state, current_player, None, dice_value)
            return self._chance_node(
                next_state,
                depth - 1,
                root_player,
                start_time,
            )

        child_values = [
            self._chance_node(
                apply_move(state, current_player, piece_id, dice_value),
                depth - 1,
                root_player,
                start_time,
            )
            for piece_id in legal_moves
        ]
        if current_player == root_player:
            return max(child_values)
        return min(child_values)
