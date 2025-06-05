import os
import pygame
import chess

# Constants
WIDTH, HEIGHT = 640, 640
SQUARE_SIZE = WIDTH // 8
FPS = 60

# Colors
WHITE = (245, 245, 220)
BROWN = (139, 69, 19)
HIGHLIGHT = (186, 202, 68)
SELECT = (246, 246, 105)


class ChessGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("THE Chess GUI")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.load_textures()

    def load_textures(self):
        self.pieces = {}
        for color in ['w', 'b']:
            for piece in ['p', 'n', 'b', 'r', 'q', 'k']:
                name = f"{color}{piece}.png"
                path = os.path.join('Textures', name)
                if os.path.exists(path):
                    image = pygame.image.load(path)
                    image = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
                    self.pieces[color+piece] = image

    def draw_board(self):
        colors = [WHITE, BROWN]
        for y in range(8):
            for x in range(8):
                rect = pygame.Rect(x*SQUARE_SIZE, y*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                color = colors[(x+y) % 2]
                if self.selected_square == chess.square(x, 7-y):
                    color = SELECT
                pygame.draw.rect(self.screen, color, rect)

                # highlight valid moves
                if self.selected_square is not None:
                    selected_piece = self.board.piece_at(self.selected_square)
                    if selected_piece and selected_piece.color == self.board.turn:
                        for move in self.board.legal_moves:
                            if move.from_square == self.selected_square and move.to_square == chess.square(x, 7-y):
                                pygame.draw.rect(self.screen, HIGHLIGHT, rect)
        
    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                x = chess.square_file(square)
                y = 7 - chess.square_rank(square)
                piece_code = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()
                img = self.pieces.get(piece_code)
                if img:
                    rect = img.get_rect(topleft=(x*SQUARE_SIZE, y*SQUARE_SIZE))
                    self.screen.blit(img, rect)

    def reset_game(self):
        self.board.reset()
        self.selected_square = None

    def handle_click(self, pos):
        x, y = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
        square = chess.square(x, 7 - y)
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.board.push(move)
            self.selected_square = None

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()

            self.draw_board()
            self.draw_pieces()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == '__main__':
    ChessGUI().run()
