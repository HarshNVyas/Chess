# Chess — Terminal Edition

> A fully-featured, two-player chess game playable right in your terminal — no GUI required.

![chess_set](https://upload.wikimedia.org/wikipedia/commons/6/6f/ChessSet.jpg)

---

## Features

- **Complete chess rules** — castling, en-passant-style pawn kills, pawn promotion, and check/checkmate detection
- **Check warnings** — the game alerts you to threats by direction (diagonal, perpendicular, knight, pawn)
- **Auto-move assistance** — pawns auto-advance when no decision is needed; kill options surface only when an enemy is in range
- **Illegal move tracking** — each player gets 3 chances before forfeiting on repeated bad moves
- **Available in Java and Python** — play with `chess.java` (compile + run) or `chess.py` (Python 3)

---

## How to Play

### Python
```bash
python3 chess.py
```

### Java
```bash
javac chess.java
java chess
```

> **Note:** Must be run in an interactive terminal (not piped/redirected). Python version will warn you if it detects a non-interactive shell.

---

## Piece Naming (Cookies)

Every piece on the board is a 3-character code:

| Code | Piece | Hindi Name |
|------|-------|------------|
| `WR1` / `BR2` | Rook | Hathi |
| `WK1` / `BK2` | Knight | Ghoda |
| `WB1` / `BB2` | Bishop | Vazir |
| `WLn` / `BLn` | King | Raja |
| `WQn` / `BQn` | Queen | Rani |
| `WP1`–`WP8` | Pawn | Sipahi |

- First letter: **W** (White) or **B** (Black)
- Second letter: piece type
- Third: number to distinguish identical pieces (`n` for unique pieces like King/Queen)

![cookie_info](https://images.creativemarket.com/0.1.0/ps/299465/910/607/m1/fpnw/wm0/1410.m00.i103.n006.s.c12.chess-set-with-chess-names-.jpg?1421047171&s=8340fbc93b8aa0a5079d061bb5485519)

---

## Input Format

At the `Enter a cookie :` prompt, type the exact piece code as shown on the board — case-sensitive.

```
Enter a cookie : WP3     ✓ correct
Enter a cookie : wp3     ✗ invalid
Enter a cookie : Wp3     ✗ invalid
```

Then enter the target row and column when prompted.

---

## Special Moves

| Move | How to trigger |
|------|----------------|
| **Castling** | Select your Rook, then enter your King's position as the destination |
| **Pawn promotion** | Move a pawn to the last rank — choose your replacement piece from the menu |
| **Pawn kill** | Kill options appear automatically when an enemy is diagonally adjacent |

---

## Rules & Precautions

1. Castling is initiated by selecting the **Rook**, not the King.
2. The board displays X (columns) and Y (rows) axes at the edges — double-check coordinates before entering.
3. **3 illegal/invalid moves = forfeit.** Think before you type.
4. If your King is under two simultaneous threats, only King moves are allowed.

---

## Learn Chess

New to chess? Check out the official rules:
[https://en.wikipedia.org/wiki/Rules_of_chess](https://en.wikipedia.org/wiki/Rules_of_chess)

---

## Project Structure

```
Chess-in-Java/
├── chess.java   # Original Java implementation
├── chess.py     # Python rewrite (optimised, bug-fixed)
└── README.md
```

---

*Built for fun. Forks welcome.*
