import os
import pygame
import chess
import tkinter as tk
from tkinter import filedialog

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
        self.move_history = []
        self.option_rects = {}
        self.dropdown_rects = {}
        self.settings_open = False
        self.settings_options = ["Engines"]
        self.engines = []
        # drag and drop state
        self.dragging = False
        self.drag_square = None
        self.dragged_piece = None
        self.drag_pos = (0, 0)
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

                # valid move highlighting removed for cleaner look
        
    def draw_pieces(self):
        for square in chess.SQUARES:
            if self.dragging and square == self.drag_square:
                continue
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

        if self.dragging and self.dragged_piece:
            piece_code = ("w" if self.dragged_piece.color == chess.WHITE else "b") + self.dragged_piece.symbol().lower()
            img = self.pieces.get(piece_code)
            if img:
                scaled = pygame.transform.smoothscale(img, (self.square_size, self.square_size))
                rect = scaled.get_rect(center=self.drag_pos)
                self.screen.blit(scaled, rect)

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(self.board_size, 0, SIDEBAR_WIDTH, self.board_size)
        pygame.draw.rect(self.screen, (40, 40, 40), sidebar_rect)
        font = pygame.font.SysFont(None, 24)
        title = font.render("Options", True, (255, 255, 255))
        self.screen.blit(title, (self.board_size + 20, 20))
        options = ["New Game", "Undo", "Settings"]
        mouse_pos = pygame.mouse.get_pos()
        for i, text in enumerate(options):
            button_rect = pygame.Rect(self.board_size + 10, 60 + i*30, SIDEBAR_WIDTH - 20, 25)
            hover = button_rect.collidepoint(mouse_pos)
            color = (70, 70, 70) if hover else (50, 50, 50)
            pygame.draw.rect(self.screen, color, button_rect)
            line = font.render(text, True, (200, 200, 200))
            text_rect = line.get_rect(center=button_rect.center)
            self.option_rects[text] = button_rect
            self.screen.blit(line, text_rect.topleft)

        if self.settings_open:
            self.draw_settings_dropdown(font)

        # draw move history below the options
        moves_font = pygame.font.SysFont(None, 20)
        y_offset = 60 + len(options) * 30 + 20
        for i, line_text in enumerate(self.format_move_history()):
            move_line = moves_font.render(line_text, True, (255, 255, 255))
            self.screen.blit(move_line, (self.board_size + 20, y_offset + i * 20))

    def draw_settings_dropdown(self, font):
        base_rect = self.option_rects.get("Settings")
        if not base_rect:
            return
        self.dropdown_rects = {}
        for i, name in enumerate(self.settings_options):
            rect = pygame.Rect(base_rect.left, base_rect.bottom + i * 28, base_rect.width, 25)
            pygame.draw.rect(self.screen, (60, 60, 60), rect)
            text = font.render(name, True, (220, 220, 220))
            text_rect = text.get_rect(center=rect.center)
            self.dropdown_rects[name] = rect
            self.screen.blit(text, text_rect.topleft)

    def format_move_history(self):
        lines = []
        for i in range(0, len(self.move_history), 2):
            number = i // 2 + 1
            white = self.move_history[i]
            black = self.move_history[i + 1] if i + 1 < len(self.move_history) else ""
            lines.append(f"{number}. {white} {black}")
        return lines

    def reset_game(self):
        self.board.reset()
        self.selected_square = None
        self.move_history = []

    def undo_move(self):
        if len(self.board.move_stack) > 0:
            self.board.pop()
            if self.move_history:
                self.move_history.pop()
        self.selected_square = None

    def start_drag(self, pos):
        self.settings_open = False
        if pos[0] >= self.board_size or pos[1] >= self.board_size:
            return
        x, y = pos[0] // self.square_size, pos[1] // self.square_size
        square = chess.square(x, 7 - y)
        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn:
            self.dragging = True
            self.drag_square = square
            self.dragged_piece = piece
            self.drag_pos = pos
            self.selected_square = square

    def update_drag(self, pos):
        if self.dragging:
            self.drag_pos = pos

    def end_drag(self, pos):
        if not self.dragging:
            return
        if pos[0] < self.board_size and pos[1] < self.board_size:
            x, y = pos[0] // self.square_size, pos[1] // self.square_size
            square = chess.square(x, 7 - y)
            move = chess.Move(self.drag_square, square)
            if move in self.board.legal_moves:
                san = self.board.san(move)
                self.board.push(move)
                self.move_history.append(san)
        self.dragging = False
        self.drag_square = None
        self.dragged_piece = None
        self.selected_square = None


    def handle_sidebar_click(self, pos):
        if self.settings_open:
            for name, rect in self.dropdown_rects.items():
                if rect.collidepoint(pos):
                    if name == "Engines":
                        self.open_engines_window()
                    self.settings_open = False
                    return

        for name, rect in self.option_rects.items():
            if rect.collidepoint(pos):
                if name == "New Game":
                    self.reset_game()
                elif name == "Undo":
                    self.undo_move()
                elif name == "Settings":
                    self.settings_open = not self.settings_open
                return

        self.settings_open = False

    def open_engines_window(self):
        window = tk.Tk()
        window.title("Engine Settings")
        window.geometry("300x150")

        label = tk.Label(window, text="Manage Chess Engines", font=("Arial", 12))
        label.pack(pady=10)

        def import_engine():
            path = filedialog.askopenfilename(title="Select Engine")
            if path:
                self.engines.append(path)

        import_btn = tk.Button(window, text="Import Engine", command=import_engine)
        import_btn.pack(pady=5)

        close_btn = tk.Button(window, text="Close", command=window.destroy)
        close_btn.pack(pady=10)

        window.mainloop()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[0] >= self.board_size:
                        self.handle_sidebar_click(event.pos)
                    else:
                        self.start_drag(event.pos)
                if event.type == pygame.MOUSEMOTION:
                    self.update_drag(event.pos)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.end_drag(event.pos)
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
