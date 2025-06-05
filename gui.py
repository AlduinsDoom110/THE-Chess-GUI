import os
import pygame
import chess

# Constants
START_BOARD_SIZE = 640
SIDEBAR_WIDTH = 200
FPS = 60
WIDTH, HEIGHT = START_BOARD_SIZE + SIDEBAR_WIDTH, START_BOARD_SIZE

# Colors
WHITE = (245, 245, 220)
GREEN = (118, 150, 86)
HIGHLIGHT = (186, 202, 68)
SELECT = (246, 246, 105)


class ChessGUI:
    def __init__(self):
        pygame.init()
        self.width, self.height = WIDTH, HEIGHT
        self.board_size = START_BOARD_SIZE
        self.square_size = self.board_size // 8
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
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
                    image = pygame.image.load(path).convert_alpha()
                    self.pieces[color+piece] = image

    def draw_board(self):
        colors = [WHITE, GREEN]
        for y in range(8):
            for x in range(8):
                rect = pygame.Rect(x*self.square_size, y*self.square_size, self.square_size, self.square_size)
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
                    scaled = pygame.transform.smoothscale(img, (self.square_size, self.square_size))
                    rect = scaled.get_rect(topleft=(x*self.square_size, y*self.square_size))
                    self.screen.blit(scaled, rect)

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(self.board_size, 0, SIDEBAR_WIDTH, self.board_size)
        pygame.draw.rect(self.screen, (40, 40, 40), sidebar_rect)
        font = pygame.font.SysFont(None, 24)
        title = font.render("Options", True, (255, 255, 255))
        self.screen.blit(title, (self.board_size + 20, 20))
        options = ["New Game", "Undo", "Settings"]
        for i, text in enumerate(options):
            line = font.render(text, True, (200, 200, 200))
            self.screen.blit(line, (self.board_size + 20, 60 + i*30))

    def reset_game(self):
        self.board.reset()
        self.selected_square = None

    def handle_click(self, pos):
        if pos[0] >= self.board_size or pos[1] >= self.board_size:
            return
        x, y = pos[0] // self.square_size, pos[1] // self.square_size
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
                if event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.board_size = min(self.height, self.width - SIDEBAR_WIDTH)
                    self.square_size = self.board_size // 8
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

            self.draw_board()
            self.draw_pieces()
            self.draw_sidebar()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == '__main__':
    ChessGUI().run()
