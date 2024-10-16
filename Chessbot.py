import chess
import chess.engine
piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}
def evaluate_board(board):
    value = 0
    for piece in chess.PIECE_TYPES:
        value += len(board.pieces(piece, chess.WHITE)) * piece_values[piece]
        value -= len(board.pieces(piece, chess.BLACK)) * piece_values[piece]
    return value
def get_bot_move(board):
    best_move = None
    best_value = -float('inf')
    for move in board.legal_moves:
        board.push(move)
        board_value = evaluate_board(board)
        board.pop()
        if board_value > best_value:
            best_value = board_value
            best_move = move
    return best_move
def play_game():
    board = chess.Board()
    while not board.is_game_over():
        print(board)
        if board.turn == chess.WHITE:
            user_move = input("Enter your move: ")
            try:
                move = chess.Move.from_uci(user_move)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Invalid move. Try again.")
            except:
                print("Invalid input. Please enter a move in UCI format (e.g., e2e4).")
        else:
            print("Bot is thinking...")
            bot_move = get_bot_move(board)
            board.push(bot_move)
            print(f"Bot plays: {bot_move}")
        
    print("Game Over!")
    print(board.result())
if __name__ == "__main__":
    play_game()
