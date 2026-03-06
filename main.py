from pyscript import window, document
from pyodide.ffi import create_proxy
import random
import time

# Constantes do Board
CELL_SIZE = 40
BOARD_SIZE = 15
COLORS = {
    'red': '#ff3e3e',
    'green': '#2ecc71',
    'yellow': '#f1c40f',
    'blue': '#2c9aff'
}

SAFE_CELLS = [1, 9, 14, 22, 27, 35, 40, 48]

# Jogadores e Turnos
PLAYER_ORDER = ['red', 'blue', 'yellow', 'green']
TURN_INDEX = 0
DICE_VALUE = 0
GAME_STATE = "WAITING_DICE"

# Posições das Peças
pieces = {
    'red': [{'id': 'r1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'r2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'r3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'r4', 'pos': 3, 'status': 'base', 'dist': 0}],
    'blue': [{'id': 'b1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'b2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'b3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'b4', 'pos': 3, 'status': 'base', 'dist': 0}],
    'yellow': [{'id': 'y1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'y2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'y3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'y4', 'pos': 3, 'status': 'base', 'dist': 0}],
    'green': [{'id': 'g1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'g2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'g3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'g4', 'pos': 3, 'status': 'base', 'dist': 0}],
}

BASE_POS = {
    'red': [(1,1), (1,4), (4,1), (4,4)],
    'blue': [(1,10), (1,13), (4,10), (4,13)],
    'yellow': [(10,10), (10,13), (13,10), (13,13)],
    'green': [(10,1), (10,4), (13,1), (13,4)],
}

GLOBAL_PATH = [
    (6,0), (6,1), (6,2), (6,3), (6,4), (6,5),
    (5,6), (4,6), (3,6), (2,6), (1,6), (0,6),
    (0,7), (0,8), (1,8), (2,8), (3,8), (4,8), (5,8),
    (6,9), (6,10), (6,11), (6,12), (6,13), (6,14),
    (7,14), (8,14), (8,13), (8,12), (8,11), (8,10), (8,9),
    (9,8), (10,8), (11,8), (12,8), (13,8), (14,8),
    (14,7), (14,6), (13,6), (12,6), (11,6), (10,6), (9,6),
    (8,5), (8,4), (8,3), (8,2), (8,1), (8,0), (7,0)
]

START_IDX = {'red': 1, 'blue': 14, 'yellow': 27, 'green': 40}

HOME_PATHS = {
    'red': [(7,1), (7,2), (7,3), (7,4), (7,5), (7,6)],
    'blue': [(1,7), (2,7), (3,7), (4,7), (5,7), (6,7)],
    'yellow': [(7,13), (7,12), (7,11), (7,10), (7,9), (7,8)],
    'green': [(13,7), (12,7), (11,7), (10,7), (9,7), (8,7)]
}

proxies = []

def create_board():
    svg = document.getElementById("board-svg")
    if not svg: return
    
    # Preservar o defs removendo apenas outros elementos
    nodes = list(svg.childNodes)
    for node in nodes:
        if node.nodeName.lower() != "defs":
            svg.removeChild(node)
    
    # Gerar Células do Tabuleiro
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
            rect.setAttribute("x", str(x * CELL_SIZE))
            rect.setAttribute("y", str(y * CELL_SIZE))
            rect.setAttribute("width", str(CELL_SIZE))
            rect.setAttribute("height", str(CELL_SIZE))
            rect.setAttribute("class", "cell")
            if x < 6 and y < 6: rect.setAttribute("class", "cell base-red")
            elif x > 8 and y < 6: rect.setAttribute("class", "cell base-green")
            elif x > 8 and y > 8: rect.setAttribute("class", "cell base-yellow")
            elif x < 6 and y > 8: rect.setAttribute("class", "cell base-blue")
            elif 6 <= x <= 8 and 6 <= y <= 8: rect.setAttribute("fill", "#111")
            svg.appendChild(rect)

    # Marcadores de casas seguras
    for idx in SAFE_CELLS:
        pos = GLOBAL_PATH[idx]
        star = document.createElementNS("http://www.w3.org/2000/svg", "circle")
        star.setAttribute("cx", str(pos[0] * CELL_SIZE + CELL_SIZE/2))
        star.setAttribute("cy", str(pos[1] * CELL_SIZE + CELL_SIZE/2))
        star.setAttribute("r", str(CELL_SIZE/4))
        star.setAttribute("class", "safe-cell-mark")
        svg.appendChild(star)

    for color, path in HOME_PATHS.items():
        for i, pos in enumerate(path):
            if i < 5:
                rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
                rect.setAttribute("x", str(pos[0] * CELL_SIZE))
                rect.setAttribute("y", str(pos[1] * CELL_SIZE))
                rect.setAttribute("width", str(CELL_SIZE))
                rect.setAttribute("height", str(CELL_SIZE))
                rect.setAttribute("fill", COLORS[color])
                rect.setAttribute("opacity", "0.2")
                svg.appendChild(rect)

    # Criar Bonecos (Pieces)
    for color in PLAYER_ORDER:
        for i, p in enumerate(pieces[color]):
            circle = document.createElementNS("http://www.w3.org/2000/svg", "circle")
            circle.setAttribute("id", p['id'])
            circle.setAttribute("r", str(CELL_SIZE * 0.35))
            circle.setAttribute("class", f"piece piece-{color}")
            # Fallback fill caso o gradiente falhe
            circle.setAttribute("fill", COLORS[color])
            # Aplicar gradiente se disponível
            circle.setAttribute("fill", f"url(#grad-{color})")
            circle.setAttribute("stroke", "white")
            circle.setAttribute("stroke-width", "2")
            circle.setAttribute("filter", "url(#shadow)")
            
            # Usar fechamento para capturar color e i
            def make_handler(c=color, idx=i):
                return create_proxy(lambda e: piece_clicked(c, idx))
            
            pxy = make_handler()
            proxies.append(pxy)
            circle.addEventListener("click", pxy)
            svg.appendChild(circle)

    update_pieces_ui()

def get_pos_coords(color: str, piece_idx: int):
    p = pieces[color][piece_idx]
    st = p['status']
    idx = int(p['pos'])
    if st == 'base': return BASE_POS[color][idx]
    elif st == 'path': return GLOBAL_PATH[idx]
    elif st == 'home': return HOME_PATHS[color][idx]
    elif st == 'win': return (7, 7)
    return (0, 0)

def update_pieces_ui():
    # Cache positions to handle overlaps
    occupied = {}
    
    for color in PLAYER_ORDER:
        for i, p in enumerate(pieces[color]):
            coords = get_pos_coords(color, i)
            key = f"{coords[0]},{coords[1]}"
            if key not in occupied: occupied[key] = []
            occupied[key].append(p['id'])

    for color in PLAYER_ORDER:
        for i, p in enumerate(pieces[color]):
            coords = get_pos_coords(color, i)
            elem = document.getElementById(p['id'])
            if not elem: continue
            
            key = f"{coords[0]},{coords[1]}"
            group = occupied[key]
            offset_x = 0
            offset_y = 0
            
            if len(group) > 1:
                idx_in_group = group.index(p['id'])
                # Small spiral offset for multiple pieces
                angle = idx_in_group * (2 * 3.14159 / len(group))
                dist = 8
                offset_x = dist * 0.5 if idx_in_group % 2 == 0 else -dist * 0.5
                offset_y = dist * 0.5 if (idx_in_group // 2) % 2 == 0 else -dist * 0.5

            cx = coords[0] * CELL_SIZE + CELL_SIZE / 2 + offset_x
            cy = coords[1] * CELL_SIZE + CELL_SIZE / 2 + offset_y
            
            elem.setAttribute("cx", str(cx))
            elem.setAttribute("cy", str(cy))
            
            if GAME_STATE == "WAITING_PIECE" and color == PLAYER_ORDER[TURN_INDEX]:
                if can_move(p, DICE_VALUE): elem.classList.add("active")
                else: elem.classList.remove("active")
            else:
                elem.classList.remove("active")

def can_move(piece, die):
    if piece['status'] == 'base': return die == 6
    if piece['status'] == 'win': return False
    if piece['status'] == 'home': return int(piece['pos']) + die <= 5
    return True

def roll_dice(event):
    global DICE_VALUE, GAME_STATE
    if GAME_STATE != "WAITING_DICE": return
    btn = document.getElementById("roll-btn")
    btn.disabled = True
    die_face = document.getElementById("die-face")
    DICE_VALUE = random.randint(1, 6)
    die_face.innerText = str(DICE_VALUE)
    
    # Anim effect
    die_face.style.transform = "rotate(720deg) scale(1.2)"
    window.setTimeout(create_proxy(lambda: setattr(die_face.style, "transform", "rotate(720deg) scale(1)")), 500)
    
    document.getElementById("game-msg").innerText = f"Você tirou {DICE_VALUE}!"
    
    possible = False
    current_color = PLAYER_ORDER[TURN_INDEX]
    for i, p in enumerate(pieces[current_color]):
        if can_move(p, DICE_VALUE):
            possible = True
            break
            
    if not possible:
        document.getElementById("game-msg").innerText += " Sem jogadas... Próximo!"
        pxy = create_proxy(next_turn)
        proxies.append(pxy)
        window.setTimeout(pxy, 1500)
    else:
        GAME_STATE = "WAITING_PIECE"
        document.getElementById("game-msg").innerText += " Clique em uma peça para mover!"
        update_pieces_ui()

def next_turn():
    global TURN_INDEX, GAME_STATE
    if DICE_VALUE != 6:
        TURN_INDEX = (TURN_INDEX + 1) % 4
    GAME_STATE = "WAITING_DICE"
    current_color = PLAYER_ORDER[TURN_INDEX]
    title = document.getElementById("turn-title")
    title.innerText = f"Turno do {current_color.capitalize()}"
    document.getElementById("status-display").style.borderLeftColor = COLORS[current_color]
    document.getElementById("game-msg").innerText = "Sua vez!"
    document.getElementById("die-face").innerText = "?"
    document.getElementById("die-face").style.transform = "rotate(0deg)"
    document.getElementById("roll-btn").disabled = False
    update_pieces_ui()

def piece_clicked(color, idx):
    global GAME_STATE
    if GAME_STATE != "WAITING_PIECE": return
    if color != PLAYER_ORDER[TURN_INDEX]: return
    piece = pieces[color][idx]
    if not can_move(piece, DICE_VALUE): return
    move_piece(color, idx, DICE_VALUE)

def move_piece(color, idx, steps):
    global GAME_STATE
    p = pieces[color][idx]
    if p['status'] == 'base':
        p['status'] = 'path'
        p['pos'] = START_IDX[color]
        p['dist'] = 0
    elif p['status'] == 'path':
        dist = int(p['dist']) + steps
        if dist > 50:
            overflow = dist - 51
            if overflow <= 5:
                p['status'] = 'home'
                p['pos'] = overflow
                p['dist'] = dist
        else:
            p['pos'] = (int(p['pos']) + steps) % 52
            p['dist'] = dist
            # Only capture if NOT a safe cell
            if int(p['pos']) not in SAFE_CELLS:
                check_capture(color, int(p['pos']))
    elif p['status'] == 'home':
        p['pos'] = int(p['pos']) + steps
        if p['pos'] == 5:
            p['status'] = 'win'
            document.getElementById("game-msg").innerText = "Peça em casa! 🎉"
    
    GAME_STATE = "ANIMATING"
    update_pieces_ui()
    
    wins = sum(1 for pi in pieces[color] if pi['status'] == 'win')
    if wins == 4:
        document.getElementById("game-msg").innerText = f"🏆 {color.upper()} VENCEU O JOGO!"
        window.confetti() # Assuming global confetti if available, else just text
        return
        
    pxy = create_proxy(next_turn)
    proxies.append(pxy)
    window.setTimeout(pxy, 600)

def check_capture(color, path_idx):
    for other_color in PLAYER_ORDER:
        if other_color == color: continue
        for i, p in enumerate(pieces[other_color]):
            if p['status'] == 'path' and int(p['pos']) == path_idx:
                p['status'] = 'base'
                p['pos'] = i
                p['dist'] = 0
                document.getElementById("game-msg").innerText = f"💥 {color.upper()} capturou {other_color}!"

# Inicialização
try:
    print("Iniciando Tabuleiro...")
    create_board()
    # Garantir que o turno inicial esteja correto na UI
    next_turn()
    # Resetar para o primeiro jogador explicitamente
    TURN_INDEX = 0
    document.getElementById("loading-screen").style.opacity = "0"
    window.setTimeout(create_proxy(lambda: setattr(document.getElementById("loading-screen").style, "display", "none")), 500)
    print("Antigravity Engine High-Performance Ready.")
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    print(f"Erro Crítico: {e}\n{error_details}")
    if document.getElementById("game-msg"):
        document.getElementById("game-msg").innerText = f"Erro de Motor: {e}"
