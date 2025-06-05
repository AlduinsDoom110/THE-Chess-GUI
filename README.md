# THE-Chess-GUI

A simple chess interface written in Python. The GUI is powered by **pygame** and the chess rules are handled by **python-chess**. Piece graphics are loaded from the `Textures` folder.

## Features

- Click on a piece to select it and click on a valid destination to move.
- Highlights possible moves for the selected piece.
- Press **R** to reset the board at any time.
- Dark squares are now green.
- The board scales when resizing the window.
- Sidebar buttons for starting a new game, undoing moves, flipping the board and saving the game.
- Settings drop-down lets you import engines, toggle coordinates and toggle analysis.
- Optional board coordinates can be displayed around the board.
- Import an engine once and it will be reused on the next launch.
- The analysis display shows up to five half-moves from the engine's best line.

## Requirements

Install dependencies with pip:

```bash
pip install pygame python-chess
```

## Running

Execute the GUI with:

```bash
python gui.py
```

The selected engine path is stored in `engine_path.txt` so it is loaded
automatically on future runs.

Enjoy playing chess with custom piece textures!
