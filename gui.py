import os
import threading
import pygame
import chess
import chess.engine
import chess.pgn
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
        self.settings_options = ["Engines", "Toggle Coordinates", "Toggle Engine"]
        self.board_flipped = False
        self.show_coords = True
        self.engines = []
        self.engine = None
        self.engine_path = None
        self.engine_name = ""
        self.analysis_thread = None
        self.analysis_running = False
        self.analysis_info = {"line": "", "nodes": 0, "score": ""}
        # drag and drop state
        self.dragging = False
        self.drag_square = None
        self.dragged_piece = None
        self.drag_pos = (0, 0)
        self.load_textures()
        self.load_engine_path()

    def load_textures(self):
        self.pieces = {}
        for color in ['w', 'b']:
            for piece in ['p', 'n', 'b', 'r', 'q', 'k']:
                name = f"{color}{piece}.png"
                path = os.path.join('Textures', name)
                if os.path.exists(path):
                    image = pygame.image.load(path).convert_alpha()
                    self.pieces[color+piece] = image

    def pixel_to_square(self, pos):
        x, y = pos[0] // self.square_size, pos[1] // self.square_size
        if self.board_flipped:
            file = 7 - x
            rank = y
        else:
            file = x
            rank = 7 - y
        return chess.square(file, rank)

    def square_to_pixel(self, square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        if self.board_flipped:
            display_x = 7 - file
            display_y = rank
        else:
            display_x = file
            display_y = 7 - rank
        return display_x * self.square_size, display_y * self.square_size

    def draw_board(self):
        colors = [WHITE, GREEN]
        for display_y in range(8):
            for display_x in range(8):
                if self.board_flipped:
                    file = 7 - display_x
                    rank = display_y
                else:
                    file = display_x
                    rank = 7 - display_y
                square = chess.square(file, rank)
                rect = pygame.Rect(display_x*self.square_size, display_y*self.square_size,
                                   self.square_size, self.square_size)
                color = colors[(display_x+display_y) % 2]
                if self.selected_square == square:
                    color = SELECT
                pygame.draw.rect(self.screen, color, rect)

        if self.show_coords:
            self.draw_coordinates()

    def draw_coordinates(self):
        font = pygame.font.SysFont(None, 16)
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        for i in range(8):
            file_index = 7 - i if self.board_flipped else i
            rank_index = i if self.board_flipped else 7 - i
            file_text = font.render(files[file_index], True, (0, 0, 0))
            rank_text = font.render(ranks[rank_index], True, (0, 0, 0))
            self.screen.blit(file_text, (i * self.square_size + self.square_size - 12,
                                         self.board_size - 18))
            self.screen.blit(rank_text, (2, i * self.square_size + 2))
        
    def draw_pieces(self):
        for square in chess.SQUARES:
            if self.dragging and square == self.drag_square:
                continue
            piece = self.board.piece_at(square)
            if piece:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                if self.board_flipped:
                    display_x = 7 - file
                    display_y = rank
                else:
                    display_x = file
                    display_y = 7 - rank
                piece_code = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()
                img = self.pieces.get(piece_code)
                if img:
                    scaled = pygame.transform.smoothscale(img, (self.square_size, self.square_size))
                    rect = scaled.get_rect(topleft=(display_x*self.square_size, display_y*self.square_size))
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
        options = ["New Game", "Undo", "Flip Board", "Save Game", "Settings"]
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

        analysis_y = self.board_size - 80
        if self.engine:
            info_font = pygame.font.SysFont(None, 20)
            name = info_font.render(self.engine_name, True, (255, 255, 255))
            self.screen.blit(name, (self.board_size + 20, analysis_y))
            line = info_font.render(self.analysis_info.get("line", ""), True, (200, 200, 200))
            nodes = info_font.render(f"Nodes: {self.analysis_info.get('nodes', 0)}", True, (200, 200, 200))
            score = info_font.render(f"Score: {self.analysis_info.get('score', '')}", True, (200, 200, 200))
            self.screen.blit(line, (self.board_size + 20, analysis_y + 20))
            self.screen.blit(nodes, (self.board_size + 20, analysis_y + 40))
            self.screen.blit(score, (self.board_size + 20, analysis_y + 60))

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
        if self.engine:
            self.start_engine_analysis()

    def undo_move(self):
        if len(self.board.move_stack) > 0:
            self.board.pop()
            if self.move_history:
                self.move_history.pop()
        self.selected_square = None
        if self.engine:
            self.start_engine_analysis()

    def start_drag(self, pos):
        self.settings_open = False
        if pos[0] >= self.board_size or pos[1] >= self.board_size:
            return
        square = self.pixel_to_square(pos)
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
            square = self.pixel_to_square(pos)
            move = chess.Move(self.drag_square, square)
            if move in self.board.legal_moves:
                san = self.board.san(move)
                self.board.push(move)
                self.move_history.append(san)
                if self.engine:
                    self.start_engine_analysis()
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
                    elif name == "Toggle Coordinates":
                        self.show_coords = not self.show_coords
                    elif name == "Toggle Engine":
                        self.toggle_engine()
                    self.settings_open = False
                    return

        for name, rect in self.option_rects.items():
            if rect.collidepoint(pos):
                if name == "New Game":
                    self.reset_game()
                elif name == "Undo":
                    self.undo_move()
                elif name == "Flip Board":
                    self.board_flipped = not self.board_flipped
                elif name == "Save Game":
                    self.save_game()
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
                self.save_engine_path(path)
                self.start_engine_analysis(path)
                window.destroy()

        import_btn = tk.Button(window, text="Import Engine", command=import_engine)
        import_btn.pack(pady=5)

        close_btn = tk.Button(window, text="Close", command=window.destroy)
        close_btn.pack(pady=10)

        window.mainloop()

    def save_engine_path(self, path):
        try:
            with open("engine_path.txt", "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            print(f"Failed to save engine path: {e}")

    def load_engine_path(self):
        if os.path.exists("engine_path.txt"):
            try:
                with open("engine_path.txt", "r", encoding="utf-8") as f:
                    path = f.read().strip()
                if path:
                    self.start_engine_analysis(path)
            except Exception as e:
                print(f"Failed to load engine path: {e}")

    def save_game(self):
        path = filedialog.asksaveasfilename(defaultextension=".pgn",
                                            filetypes=[("PGN files", "*.pgn")])
        if not path:
            return
        game = chess.pgn.Game()
        node = game
        for move in self.board.move_stack:
            node = node.add_variation(move)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(game))

    def toggle_engine(self):
        if self.engine:
            self.stop_engine()
        else:
            self.start_engine_analysis()

    def start_engine_analysis(self, path=None):
        if path:
            self.engine_path = path
        if not self.engine_path:
            return
        if not self.engine or path:
            self.stop_engine()
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            except Exception as e:
                print(f"Failed to start engine: {e}")
                self.engine = None
                return
            self.engine_name = os.path.basename(self.engine_path)
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_running = False
            self.analysis_thread.join()
        self.analysis_running = True
        self.analysis_thread = threading.Thread(target=self.analysis_loop, daemon=True)
        self.analysis_thread.start()

    def stop_engine(self):
        self.analysis_running = False
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join()
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
            self.engine = None

    def analysis_loop(self):
        board_len = len(self.board.move_stack)
        while self.analysis_running and self.engine:
            analysis_board = self.board.copy()
            board_len = len(analysis_board.move_stack)
            try:
                with self.engine.analysis(analysis_board, chess.engine.Limit()) as analysis:
                    for info in analysis:
                        if not self.analysis_running:
                            analysis.stop()
                            break
                        if len(self.board.move_stack) != board_len:
                            analysis.stop()
                            break
                        pv = info.get("pv")
                        if pv:
                            temp_board = analysis_board.copy()
                            moves = []
                            for i, m in enumerate(pv):
                                if i >= 5:
                                    break
                                moves.append(temp_board.san(m))
                                temp_board.push(m)
                            line = " ".join(moves)
                        else:
                            line = self.analysis_info.get("line", "")
                        score = info.get("score")
                        if score is not None:
                            try:
                                cp = score.white().score(mate_score=100000)
                                score_text = f"{cp:+d}"
                            except Exception:
                                score_text = str(score)
                        else:
                            score_text = self.analysis_info.get("score", "")
                        nodes = info.get("nodes", self.analysis_info.get("nodes", 0))
                        self.analysis_info = {"line": line, "nodes": nodes, "score": score_text}
            except Exception as e:
                print("Engine analysis error:", e)
                break

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

        self.stop_engine()
        pygame.quit()


if __name__ == '__main__':
    ChessGUI().run()
