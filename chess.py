"""
Chess game - Python rewrite of chess.java with bug fixes.
"""

import sys

if not sys.stdin.isatty():
    print("\nERROR: This game requires an interactive terminal.")
    print("Open Terminal.app (or iTerm2) on your Mac and run:")
    print("\n    python3 ~/Documents/Projects/Chess/chess.py\n")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Board state
# ---------------------------------------------------------------------------

arr = [
    ["BR1", "BK1", "BB1", "BQn", "BLn", "BB2", "BK2", "BR2"],
    ["BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7", "BP8"],
    ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
    ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
    ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
    ["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "],
    ["WP1", "WP2", "WP3", "WP4", "WP5", "WP6", "WP7", "WP8"],
    ["WR1", "WK1", "WB1", "WQn", "WLn", "WB2", "WK2", "WR2"],
]

# Counters / flags
chance = 0          # even = White's turn, odd = Black's turn
illegal_W = 0
illegal_B = 0
castled_W = False
castled_B = False
castling_ok_W = True   # becomes False once White king or rook moves
castling_ok_B = True

# Pawn promotion counters
wq_count = 0
wb_count = 0
wk_count = 0
wr_count = 0
bq_count = 0
bb_count = 0
bk_count = 0
br_count = 0

# Track which pieces have moved (for pawn first-move and castling)
moved = set()

# Player names
player1_name = ""
player2_name = ""


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def inp_int(prompt=""):
    """Print prompt and read an integer, retrying on bad input."""
    while True:
        try:
            return int(input(prompt))
        except (ValueError, EOFError):
            print("Please enter a number.")


def add_illegal(color):
    global illegal_W, illegal_B
    if color == "W":
        illegal_W += 1
    else:
        illegal_B += 1


def search(piece):
    """Return (row, col) of piece, or (-1, -1) if not found."""
    for r in range(8):
        for c in range(8):
            if arr[r][c] == piece:
                return (r, c)
    return (-1, -1)


def path_clear(r1, c1, r2, c2):
    """
    Return True if all squares strictly between (r1,c1) and (r2,c2) are empty.
    Works for horizontal, vertical, and diagonal paths.
    """
    dr = 0 if r2 == r1 else (1 if r2 > r1 else -1)
    dc = 0 if c2 == c1 else (1 if c2 > c1 else -1)
    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2):
        if arr[r][c] != "   ":
            return False
        r += dr
        c += dc
    return True


def col_letter(c):
    return chr(ord('a') + c)


def col_index(letter):
    return ord(letter) - ord('a')


def in_bounds(r, c):
    return 0 <= r <= 7 and 0 <= c <= 7


# ---------------------------------------------------------------------------
# Check / threat detection
# ---------------------------------------------------------------------------

def threats_on_king(color):
    """
    Return the number of distinct pieces that currently threaten the king of
    *color*.  Uses clean loops; no recursion.
    """
    king_piece = "WLn" if color == "W" else "BLn"
    pos = search(king_piece)
    if pos == (-1, -1):
        return 0
    r, c = pos
    opp = "B" if color == "W" else "W"
    count = 0

    # ---- Straight lines (rook / queen) ----
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            sq = arr[nr][nc]
            if sq != "   ":
                if sq[0] == opp and sq[1] in ("R", "Q"):
                    count += 1
                break
            nr += dr
            nc += dc

    # ---- Diagonal lines (bishop / queen) ----
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            sq = arr[nr][nc]
            if sq != "   ":
                if sq[0] == opp and sq[1] in ("B", "Q"):
                    count += 1
                break
            nr += dr
            nc += dc

    # ---- Knights ----
    for dr, dc in [(-2, -1), (-2, 1), (2, -1), (2, 1),
                   (-1, -2), (-1, 2), (1, -2), (1, 2)]:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            sq = arr[nr][nc]
            if sq[0] == opp and sq[1] == "K":
                count += 1

    # ---- Pawns ----
    if color == "W":
        # White king threatened by Black pawns above it (row-1)
        for dc in [-1, 1]:
            nr, nc = r - 1, c + dc
            if in_bounds(nr, nc):
                sq = arr[nr][nc]
                if sq[0] == "B" and sq[1] == "P":
                    count += 1
    else:
        # Black king threatened by White pawns below it (row+1)
        for dc in [-1, 1]:
            nr, nc = r + 1, c + dc
            if in_bounds(nr, nc):
                sq = arr[nr][nc]
                if sq[0] == "W" and sq[1] == "P":
                    count += 1

    return count


def king_in_check(color):
    return threats_on_king(color) > 0


def print_check_warnings(color):
    """Print WARNING lines matching Java's check_W/check_B(count=0) output."""
    king_piece = "WLn" if color == "W" else "BLn"
    pos = search(king_piece)
    if pos == (-1, -1):
        return
    r, c = pos
    opp = "B" if color == "W" else "W"

    warn_pawn = warn_diag = warn_straight = warn_knight = False

    # Pawn attacks
    pawn_dr = -1 if color == "W" else 1
    for dc in [-1, 1]:
        nr, nc = r + pawn_dr, c + dc
        if in_bounds(nr, nc) and arr[nr][nc][0] == opp and arr[nr][nc][1] == "P":
            warn_pawn = True

    # Diagonal (bishop / queen)
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            sq = arr[nr][nc]
            if sq != "   ":
                if sq[0] == opp and sq[1] in ("B", "Q"):
                    warn_diag = True
                break
            nr += dr; nc += dc

    # Straight (rook / queen)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            sq = arr[nr][nc]
            if sq != "   ":
                if sq[0] == opp and sq[1] in ("R", "Q"):
                    warn_straight = True
                break
            nr += dr; nc += dc

    # Knight
    for dr, dc in [(-2, -1), (-2, 1), (2, -1), (2, 1),
                   (-1, -2), (-1, 2), (1, -2), (1, 2)]:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and arr[nr][nc][0] == opp and arr[nr][nc][1] == "K":
            warn_knight = True

    print()
    if warn_pawn:    print("WARNING: Check via Pawn")
    if warn_diag:    print("WARNING: Check via Diagonal")
    if warn_straight: print("WARNING: Check via Perpendicular")
    if warn_knight:  print("WARNING: Check via Knight")
    print()


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display():
    print()
    print("      |--------------------    X    ------------------|")
    print("         a     b     c     d     e     f     g     h  ")
    print("---    ----- ----- ----- ----- ----- ----- ----- -----")

    y_labels = {0: " |  1", 1: " |  2", 2: " |  3", 3: " |  4",
                4: "    5", 5: " Y  5", 6: " |  6", 7: " |  7", 8: " |  8"}
    # Row labels as displayed (row index -> display label)
    row_display = [
        " |  1",
        " |  2",
        " |  3",
        " |  4",
        "    5",
        " |  6",
        " |  7",
        " |  8",
    ]
    # The Java source has the Y label on row index 4 (display row 5)
    # and a special apostrophe on the separator after row index 5 (display row 6)

    labels = [" |  1", " |  2", " |  3", "    4", "    5", " |  6", " |  7", " |  8"]
    for i in range(8):
        cells = " | ".join(arr[i])
        print(f"{labels[i]} | {cells} |")
        if i < 7:
            if i == 3:
                sep = " Y     ----- ----- ----- ----- ----- ----- ----- -----"
            elif i == 5:
                sep = " |     ----- ----- ----- ----- ----- ----- ----- -----'"
            else:
                sep = " |     ----- ----- ----- ----- ----- ----- ----- -----"
            print(sep)

    print("---    ----- ----- ----- ----- ----- ----- ----- -----")
    print()


# ---------------------------------------------------------------------------
# Details / instructions
# ---------------------------------------------------------------------------

def details():
    print()
    print("=== CHESS INSTRUCTIONS ===")
    print("Pieces: P=Pawn  R=Rook  K=Knight  B=Bishop  Q=Queen  L=King")
    print("Colors: W=White  B=Black")
    print("Coordinates: X axis = a-h (columns), Y axis = 1-8 (rows, 1=Black side)")
    print()
    print("Movement prompts:")
    print("  Pawn  : choose kill or forward, then steps")
    print("  Rook/Bishop/Queen: enter Y (1-8) then X (a-h)")
    print("  King/Knight: choose direction 1-8")
    print()
    print("King directions  : 1=left 2=right 3=up 4=down 5=upleft 6=upright 7=downleft 8=downright")
    print("Knight directions: 1=UUL 2=UUR 3=DDL 4=DDR 5=LLU 6=LLD 7=RRU 8=RRD")
    print()
    print("Castling: move your rook onto your king's square (if neither has moved and path clear).")
    print()


# ---------------------------------------------------------------------------
# Victory check
# ---------------------------------------------------------------------------

def victory():
    global illegal_W, illegal_B, chance
    wl = search("WLn")
    bl = search("BLn")
    if wl == (-1, -1) or bl == (-1, -1) or illegal_W >= 3 or illegal_B >= 3:
        print("\n" + "-" * 70)
        if wl == (-1, -1) or illegal_W >= 3:
            print(f"\t\tCongragulations {player2_name} Team.....!!!")
        else:
            print(f"\t\tCongragulations {player1_name}'s Team.....!!!")
        print("-" * 70)
        white_steps = chance // 2 + (chance % 2)
        black_steps = chance // 2
        print(f"\nTotal chances taken in the game are {chance}. "
              f"\nTotal steps taken by White team are {white_steps}. "
              f"\nTotal steps taken by Black team are {black_steps}.")
        input("\nHope You Enjoyed...!!! \nThank You for playing \nEnter '1' to Exit\nInput: ")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Pawn promotion
# ---------------------------------------------------------------------------

def pawn_promote(pos, piece):
    global wq_count, wb_count, wk_count, wr_count
    global bq_count, bb_count, bk_count, br_count

    color = piece[0]
    while True:
        try:
            num = int(input(
                "\nCongrats!!!\nYou can swap the pawn with of of the cookie's mentioned below:"
                "\n1.Queen\n2.Bishop\n3.Knight\n4.Rook\nInput:\t"))
        except (ValueError, EOFError):
            num = -1
        if num in (1, 2, 3, 4):
            break
        print("Plss Don't confuse me...!!!\nTry input again")
    choice = str(num)

    r, c = pos
    if color == "W":
        if choice == "1":
            if wq_count == 0:
                # Rename existing WQn to WQ1
                qpos = search("WQn")
                if qpos != (-1, -1):
                    arr[qpos[0]][qpos[1]] = "WQ1"
                wq_count = 2
                arr[r][c] = "WQ2"
            else:
                wq_count += 1
                arr[r][c] = f"WQ{wq_count}"
        elif choice == "2":
            wb_count += 1
            arr[r][c] = f"WB{wb_count + 2}"   # original bishops are 1 and 2
        elif choice == "3":
            wk_count += 1
            arr[r][c] = f"WK{wk_count + 2}"
        elif choice == "4":
            wr_count += 1
            arr[r][c] = f"WR{wr_count + 2}"
    else:  # Black
        if choice == "1":
            if bq_count == 0:
                qpos = search("BQn")
                if qpos != (-1, -1):
                    arr[qpos[0]][qpos[1]] = "BQ1"
                bq_count = 2
                arr[r][c] = "BQ2"
            else:
                bq_count += 1
                arr[r][c] = f"BQ{bq_count}"
        elif choice == "2":
            bb_count += 1
            arr[r][c] = f"BB{bb_count + 2}"
        elif choice == "3":
            bk_count += 1
            arr[r][c] = f"BK{bk_count + 2}"
        elif choice == "4":
            br_count += 1
            arr[r][c] = f"BR{br_count + 2}"


# ---------------------------------------------------------------------------
# Move helpers
# ---------------------------------------------------------------------------

def _save_board():
    """Return a deep copy of the board."""
    return [row[:] for row in arr]


def _restore_board(saved):
    for r in range(8):
        for c in range(8):
            arr[r][c] = saved[r][c]


def get_destination(piece):
    """Prompt for Y (1-8) and X (a-h). Returns (row, col) 0-indexed, or None."""
    try:
        y_str = input("Enter the destination coordinates:\n1.Y coordinate :\t").strip()
        x_str = input("2.X coordinate :\t").strip().lower()
    except EOFError:
        return None

    try:
        row = int(y_str) - 1
    except ValueError:
        row = -1
    if not (0 <= row <= 7):
        print("Invalid First co-ordinate:\nEnter number in range '1' to '8' as input of Y coordinate")
        return None
    if x_str not in ("a", "b", "c", "d", "e", "f", "g", "h"):
        print("Invalid Second co-ordinate:\nEnter alphabet in range 'a' to 'h' as input of X coordinate")
        return None
    return (row, col_index(x_str))


# ---------------------------------------------------------------------------
# Pawn movement
# ---------------------------------------------------------------------------

def move_pawn(piece, color):
    """Pawn movement matching Java's pawn_p1/pawn_p2 logic exactly."""
    global illegal_W, illegal_B

    pos = search(piece)
    if pos == (-1, -1):
        add_illegal(color)
        return False
    r, c = pos

    direction = -1 if color == "W" else 1   # White→row 0, Black→row 7
    promo_row  =  0 if color == "W" else 7
    opp        = "B" if color == "W" else "W"
    nr         = r + direction               # square directly in front

    kill         = 2          # 2 = no kill/action yet, 1 = action already done
    killed_piece = "   "
    door         = 2
    cnt          = 0
    first_move   = piece not in moved

    saved = _save_board()

    # ── Auto-detect diagonal kill options and show the right prompt ───────
    if color == "W":
        # Java pawn_p1: checks left (c-1) first, then right (c+1)
        has_left  = (c > 0 and 0 <= nr < 8
                     and arr[nr][c-1] != "   " and arr[nr][c-1][0] == opp)
        has_right = (c < 7 and 0 <= nr < 8
                     and arr[nr][c+1] != "   " and arr[nr][c+1][0] == opp)

        if has_left and has_right:
            choice = inp_int(f"Enter :\n1.To kill {arr[nr][c-1]}\n2.To kill {arr[nr][c+1]}\n3.Move forward\nInput: ")
            if   choice == 1: killed_piece = arr[nr][c-1]; arr[nr][c-1] = piece; arr[r][c] = "   "
            elif choice == 2: killed_piece = arr[nr][c+1]; arr[nr][c+1] = piece; arr[r][c] = "   "
            elif choice == 3: arr[nr][c] = piece; arr[r][c] = "   "
            door = choice; kill = 1

        elif has_left:
            choice = inp_int(f"Enter :\n1.To kill {arr[nr][c-1]}\n2.Move forward\nInput: ")
            kill = choice
            if choice == 1: killed_piece = arr[nr][c-1]; arr[nr][c-1] = piece; arr[r][c] = "   "

        elif has_right:
            choice = inp_int(f"Enter :\n1.To kill {arr[nr][c+1]}\n2.Move forward\nInput: ")
            kill = choice
            if choice == 1: killed_piece = arr[nr][c+1]; arr[nr][c+1] = piece; arr[r][c] = "   "

    else:
        # Java pawn_p2: checks right (c+1) first, then left (c-1)
        has_right = (c < 7 and 0 <= nr < 8
                     and arr[nr][c+1] != "   " and arr[nr][c+1][0] == opp)
        has_left  = (c > 0 and 0 <= nr < 8
                     and arr[nr][c-1] != "   " and arr[nr][c-1][0] == opp)

        if has_right and has_left:
            choice = inp_int(f"Enter :\n1.To kill {arr[nr][c+1]}\n2.To kill {arr[nr][c-1]}\n3.Move forward\nInput: ")
            if   choice == 1: killed_piece = arr[nr][c+1]; arr[nr][c+1] = piece; arr[r][c] = "   "
            elif choice == 2: killed_piece = arr[nr][c-1]; arr[nr][c-1] = piece; arr[r][c] = "   "
            elif choice == 3: arr[nr][c] = piece; arr[r][c] = "   "
            door = choice; kill = 1

        elif has_right:
            choice = inp_int(f"Enter :\n1.To kill {arr[nr][c+1]}\n2.Move forward\nInput: ")
            kill = choice
            if choice == 1: killed_piece = arr[nr][c+1]; arr[nr][c+1] = piece; arr[r][c] = "   "

        elif has_left:
            choice = inp_int(f"Enter :\n1.To kill {arr[nr][c-1]}\n2.Move forward\nInput: ")
            kill = choice
            if choice == 1: killed_piece = arr[nr][c-1]; arr[nr][c-1] = piece; arr[r][c] = "   "

    # ── Forward movement ──────────────────────────────────────────────────
    if first_move and kill == 2:
        # First move: player chooses 1 or 2 steps
        if color == "W":
            prompt = "Enter:\n1 for moving 1 step forward\n2 for moving 2 steps forward\nInput:\t"
        else:
            prompt = "Enter:\n1 for moving 1 step forward\n2 to move 2 steps forward\nInput:\t"
        steps = inp_int(prompt)
        if steps == 2:
            dest_r = r + 2 * direction
            if not (0 <= dest_r < 8) or arr[dest_r][c] != "   ":
                print("Place already occupied, try some other move:")
                _restore_board(saved)
                add_illegal(color)
                return False
            arr[dest_r][c] = piece; arr[r][c] = "   "
            cnt = 1
        elif steps == 1:
            if not (0 <= nr < 8) or arr[nr][c] != "   ":
                print("Place already occupied, try some other move:")
                _restore_board(saved)
                add_illegal(color)
                return False
            arr[nr][c] = piece; arr[r][c] = "   "
            cnt = 1
        else:
            print("Enter valid move:")
            _restore_board(saved)
            add_illegal(color)
            return False

    elif not first_move and kill == 2:
        # Already moved before — auto-advance 1 step, no prompt
        if not (0 <= nr < 8) or arr[nr][c] != "   ":
            print("Place already occupied, try some other move:")
            _restore_board(saved)
            add_illegal(color)
            return False
        arr[nr][c] = piece; arr[r][c] = "   "

    elif kill != 1 and kill != 2:
        # Invalid choice in a 1-or-2 prompt
        print("Kill or not?? You Kept me in confusion...!!!\nTry again: ")
        _restore_board(saved)
        add_illegal(color)
        return False

    # ── Check validation ──────────────────────────────────────────────────
    if threats_on_king(color) > 0:
        _restore_board(saved)
        print("Check not resolved!!! Also you made an invalid move:")
        add_illegal(color)
        return False

    moved.add(piece)

    new_pos = search(piece)
    if new_pos != (-1, -1) and new_pos[0] == promo_row:
        pawn_promote(new_pos, piece)
    return True



# ---------------------------------------------------------------------------
# Castling helper
# ---------------------------------------------------------------------------

def _try_castling(rook_piece, rook_r, rook_c, king_piece, king_r, king_c, color):
    """
    Attempt castling. Returns True and modifies board if successful.
    """
    global castled_W, castled_B, castling_ok_W, castling_ok_B

    if color == "W" and (castled_W or not castling_ok_W):
        return False
    if color == "B" and (castled_B or not castling_ok_B):
        return False
    if king_in_check(color):
        return False
    if not path_clear(rook_r, rook_c, king_r, king_c):
        return False

    # Perform castling
    if rook_c > king_c:
        # Rook to the right of king
        new_rook_c = king_c + 1
        new_king_c = rook_c - 1
    else:
        # Rook to the left of king
        new_rook_c = king_c - 1
        new_king_c = rook_c + 2

    arr[rook_r][rook_c] = "   "
    arr[king_r][king_c] = "   "
    arr[rook_r][new_rook_c] = rook_piece
    arr[king_r][new_king_c] = king_piece

    if color == "W":
        castled_W = True
        castling_ok_W = False
    else:
        castled_B = True
        castling_ok_B = False

    return True


# ---------------------------------------------------------------------------
# Rook movement
# ---------------------------------------------------------------------------

def _do_straight_move(piece, pos, dest):
    """
    Move piece from pos to dest along a straight line.
    Handles castling if dest is same-color king.
    Returns True on success.
    """
    global illegal_W, illegal_B, castling_ok_W, castling_ok_B

    color = piece[0]
    r, c = pos
    dr, dc = dest

    if not in_bounds(dr, dc):
        print("  Destination out of bounds.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    # Check for castling attempt
    king_piece = "WLn" if color == "W" else "BLn"
    if arr[dr][dc] == king_piece:
        result = _try_castling(piece, r, c, king_piece, dr, dc, color)
        if result:
            moved.add(piece)
            return True
        else:
            print("  Castling not available.")
            if color == "W":
                illegal_W += 1
            else:
                illegal_B += 1
            return False

    # Must move in straight line
    if dr != r and dc != c:
        print("  Rook must move in a straight line.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    if dr == r and dc == c:
        print("  Must move to a different square.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    target = arr[dr][dc]
    if target != "   " and target[0] == color:
        print("  Cannot capture your own piece.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    if not path_clear(r, c, dr, dc):
        print("  Path is blocked.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    saved = _save_board()
    arr[dr][dc] = piece
    arr[r][c] = "   "

    if king_in_check(color):
        _restore_board(saved)
        print("  Move leaves your king in check. Illegal!")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    moved.add(piece)
    # Moving rook disables castling
    if piece[1] == "R":
        if color == "W":
            castling_ok_W = False
        else:
            castling_ok_B = False
    return True


def move_rook(piece):
    global illegal_W, illegal_B

    pos = search(piece)
    if pos == (-1, -1):
        return False
    color = piece[0]

    print(f"Moving rook {piece}")
    dest = get_destination(piece)
    if dest is None:
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    return _do_straight_move(piece, pos, dest)


# ---------------------------------------------------------------------------
# Bishop movement
# ---------------------------------------------------------------------------

def _do_diagonal_move(piece, pos, dest):
    global illegal_W, illegal_B

    color = piece[0]
    r, c = pos
    dr, dc = dest

    if not in_bounds(dr, dc):
        print("  Destination out of bounds.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    if abs(dr - r) != abs(dc - c) or (dr == r and dc == c):
        print("  Bishop must move diagonally.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    target = arr[dr][dc]
    if target != "   " and target[0] == color:
        print("  Cannot capture your own piece.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    if not path_clear(r, c, dr, dc):
        print("  Path is blocked.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    saved = _save_board()
    arr[dr][dc] = piece
    arr[r][c] = "   "

    if king_in_check(color):
        _restore_board(saved)
        print("  Move leaves your king in check. Illegal!")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    moved.add(piece)
    return True


def move_bishop(piece):
    global illegal_W, illegal_B

    pos = search(piece)
    if pos == (-1, -1):
        return False
    color = piece[0]

    print(f"Moving bishop {piece}")
    dest = get_destination(piece)
    if dest is None:
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    return _do_diagonal_move(piece, pos, dest)


# ---------------------------------------------------------------------------
# Queen movement
# ---------------------------------------------------------------------------

def move_queen(piece):
    global illegal_W, illegal_B

    pos = search(piece)
    if pos == (-1, -1):
        return False
    color = piece[0]
    r, c = pos

    print(f"Moving queen {piece}")
    dest = get_destination(piece)
    if dest is None:
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    dr, dc = dest
    if dr == r or dc == c:
        return _do_straight_move(piece, pos, dest)
    elif abs(dr - r) == abs(dc - c):
        return _do_diagonal_move(piece, pos, dest)
    else:
        print("  Queen must move straight or diagonally.")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False


# ---------------------------------------------------------------------------
# King movement
# ---------------------------------------------------------------------------

def move_king(piece):
    global illegal_W, illegal_B, castling_ok_W, castling_ok_B

    pos = search(piece)
    if pos == (-1, -1):
        return False
    color = piece[0]
    r, c = pos

    move = inp_int(
        "Enter your move: \n1. left\n2. right\n3. up\n4. down"
        "\n5. upleft\n6. upright\n7. downleft\n8. downright\nInput:\t")

    offsets = {
        1: (0,  -1),   # left
        2: (0,   1),   # right
        3: (-1,  0),   # up
        4: (1,   0),   # down
        5: (-1, -1),   # upleft
        6: (-1,  1),   # upright
        7: (1,  -1),   # downleft
        8: (1,   1),   # downright
    }

    if move not in offsets:
        print("Enter valid input:")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    dr_off, dc_off = offsets[move]
    nr, nc = r + dr_off, c + dc_off

    if not in_bounds(nr, nc):
        print("Try some other way out : ")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    target = arr[nr][nc]
    if target != "   " and target[0] == color:
        print("Try some other way out : ")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    saved = _save_board()
    arr[nr][nc] = piece
    arr[r][c] = "   "

    if king_in_check(color):
        _restore_board(saved)
        print("Check not resolved!!! Also you made an invalid move:")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    moved.add(piece)
    # Moving king disables castling
    if color == "W":
        castling_ok_W = False
    else:
        castling_ok_B = False

    return True


# ---------------------------------------------------------------------------
# Knight movement
# ---------------------------------------------------------------------------

def move_knight(piece):
    global illegal_W, illegal_B

    pos = search(piece)
    if pos == (-1, -1):
        return False
    color = piece[0]
    r, c = pos

    move = inp_int(
        "Enter your move:\n1. up-up-left\n2. up-up-right\n3. down-down-left\n4. down-down-right"
        "\n5. left-left-up\n6. left-left-down\n7. right-right-up\n8. right-right-down\nInput:\t")

    offsets = {
        1: (-2, -1),   # up-up-left
        2: (-2,  1),   # up-up-right
        3: ( 2, -1),   # down-down-left
        4: ( 2,  1),   # down-down-right
        5: (-1, -2),   # left-left-up
        6: ( 1, -2),   # left-left-down
        7: (-1,  2),   # right-right-up
        8: ( 1,  2),   # right-right-down
    }

    if move not in offsets:
        print("Enter valid input:")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    dr_off, dc_off = offsets[move]
    nr, nc = r + dr_off, c + dc_off

    if not in_bounds(nr, nc):
        print("Try some other way out : ")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    target = arr[nr][nc]
    if target != "   " and target[0] == color:
        print("Try some other way out : ")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    saved = _save_board()
    arr[nr][nc] = piece
    arr[r][c] = "   "

    if king_in_check(color):
        _restore_board(saved)
        print("Check not resolved!!! Also you made an invalid move:")
        if color == "W":
            illegal_W += 1
        else:
            illegal_B += 1
        return False

    moved.add(piece)
    return True


# ---------------------------------------------------------------------------
# Player turn
# ---------------------------------------------------------------------------

def player_turn(color):
    king_piece = "WLn" if color == "W" else "BLn"
    name       = player1_name if color == "W" else player2_name
    ill        = illegal_W if color == "W" else illegal_B

    print(f"{name}'s Turn to go:\n")
    print(f"Invalid moves left : {3 - ill}")

    print_check_warnings(color)
    threat_count    = threats_on_king(color)
    force_king_only = threat_count >= 2
    display()

    if force_king_only:
        print("Save your King before it gets killed!!!")
        while True:
            ok = move_king(king_piece)
            victory()
            if ok:
                return

    while True:
        victory()
        try:
            piece = input("Enter a cookie :").strip()
        except EOFError:
            return

        if len(piece) != 3 or piece[0] != color:
            print("Invalid input")
            add_illegal(color)
            victory()
            continue

        ptype = piece[1]
        if ptype == "P":
            result = move_pawn(piece, color)
        elif ptype == "R":
            result = move_rook(piece)
        elif ptype == "K":
            result = move_knight(piece)
        elif ptype == "B":
            result = move_bishop(piece)
        elif ptype == "Q":
            result = move_queen(piece)
        elif ptype == "L":
            result = move_king(piece)
        else:
            print("There may be a mistake in writing input, try again.....!!!!")
            add_illegal(color)
            victory()
            continue

        victory()
        if result:
            return


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global player1_name, player2_name, chance

    print("Kon'nichiwa(Hello)")
    print("Welcome to the game of chess....")
    sel = input("Enter :\n1.Basic Instructions for the game\n2.Start Game\nInput: ").strip()
    if sel == "1":
        details()

    player1_name = input("\nEnter Name of 1st Player : ").strip() or "Player1"
    player2_name = input("Enter Name of 2nd Player : ").strip() or "Player2"
    print(f"\n{player1_name} is alocated White army and {player2_name}"
          f" has been alocated Black Army \nHereby Game of chess starts:\n")

    while True:
        victory()
        if chance % 2 == 0:
            player_turn("W")
        else:
            player_turn("B")
        victory()
        print("----------------------------------------------------------------------")
        chance += 1


if __name__ == "__main__":
    main()
