from pyscript import display, window, document
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

# Jogadores e Turnos
PLAYER_ORDER = ['red', 'blue', 'yellow', 'green']
TURN_INDEX = 0
DICE_VALUE = 0
GAME_STATE = "WAITING_DICE" # WAITING_DICE, WAITING_PIECE, ANIMATING

# Posições das Peças
# No Ludo, as peças podem estar na BASE, no PATH ou no HOME
# status: 'base', 'path', 'home', 'win'
# pos: index no respectivo array
# dist: total de casas percorridas (0-56)
pieces = {
    'red': [{'id': 'r1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'r2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'r3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'r4', 'pos': 3, 'status': 'base', 'dist': 0}],
    'blue': [{'id': 'b1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'b2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'b3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'b4', 'pos': 3, 'status': 'base', 'dist': 0}],
    'yellow': [{'id': 'y1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'y2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'y3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'y4', 'pos': 3, 'status': 'base', 'dist': 0}],
    'green': [{'id': 'g1', 'pos': 0, 'status': 'base', 'dist': 0}, {'id': 'g2', 'pos': 1, 'status': 'base', 'dist': 0}, {'id': 'g3', 'pos': 2, 'status': 'base', 'dist': 0}, {'id': 'g4', 'pos': 3, 'status': 'base', 'dist': 0}],
}

# Coordenadas da Base (4 lugares por cor)
BASE_POS = {
    'red': [(1,1), (1,4), (4,1), (4,4)],
    'blue': [(1,10), (1,13), (4,10), (4,13)],
    'yellow': [(10,10), (10,13), (13,10), (13,13)],
    'green': [(10,1), (10,4), (13,1), (13,4)],
}

# Caminho global (52 casas)
# sentido horário começando de cima
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

# Índices de Entrada no Path
START_IDX = {
    'red': 1,
    'blue': 14,
    'yellow': 27,
    'green': 40
}

# Caminhos de Casa (Home Steps)
HOME_PATHS = {
    'red': [(7,1), (7,2), (7,3), (7,4), (7,5), (7,6)],
    'blue': [(1,7), (2,7), (3,7), (4,7), (5,7), (6,7)],
    'yellow': [(7,13), (7,12), (7,11), (7,10), (7,9), (7,8)],
    'green': [(13,7), (12,7), (11,7), (10,7), (9,7), (8,7)]
}

def create_board():
    svg = document.getElementById("board-svg")
    svg.innerHTML = "" # Clear
    
    # Desenhar Grid Base (Fundo)
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
            rect.setAttribute("x", x * CELL_SIZE)
            rect.setAttribute("y", y * CELL_SIZE)
            rect.setAttribute("width", CELL_SIZE)
            rect.setAttribute("height", CELL_SIZE)
            rect.setAttribute("class", "cell")
            
            # Pintar áreas especiais
            if x < 6 and y < 6: rect.setAttribute("class", "cell base-red")
            elif x > 8 and y < 6: rect.setAttribute("class", "cell base-green")
            elif x > 8 and y > 8: rect.setAttribute("class", "cell base-yellow")
            elif x < 6 and y > 8: rect.setAttribute("class", "cell base-blue")
            
            # Centro
            elif 6 <= x <= 8 and 6 <= y <= 8:
                rect.setAttribute("fill", "#222")
            
            svg.appendChild(rect)

    # Casas de Cor no Path
    for color, path in HOME_PATHS.items():
        for i, pos in enumerate(path):
            if i < 5: # As 5 primeiras são o caminho final
                rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
                rect.setAttribute("x", pos[0] * CELL_SIZE)
                rect.setAttribute("y", pos[1] * CELL_SIZE)
                rect.setAttribute("width", CELL_SIZE)
                rect.setAttribute("height", CELL_SIZE)
                rect.setAttribute("fill", COLORS[color])
                rect.setAttribute("opacity", "0.6")
                svg.appendChild(rect)

    # Pontos de Início
    for color, idx in START_IDX.items():
        pos = GLOBAL_PATH[idx]
        rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
        rect.setAttribute("x", pos[0] * CELL_SIZE)
        rect.setAttribute("y", pos[1] * CELL_SIZE)
        rect.setAttribute("width", CELL_SIZE)
        rect.setAttribute("height", CELL_SIZE)
        rect.setAttribute("fill", COLORS[color])
        svg.appendChild(rect)

    # Desenhar Peças
    for color in PLAYER_ORDER:
        for i, p in enumerate(pieces[color]):
            circle = document.createElementNS("http://www.w3.org/2000/svg", "circle")
            circle.setAttribute("id", p['id'])
            circle.setAttribute("r", CELL_SIZE * 0.35)
            circle.setAttribute("class", f"piece piece-{color}")
            circle.setAttribute("fill", f"url(#grad-{color})")
            circle.setAttribute("stroke", "white")
            circle.setAttribute("stroke-width", "0.5")
            circle.setAttribute("filter", "url(#shadow)")
            
            # Registrar evento de clique via Python
            circle.onclick = lambda e, c=color, idx=i: piece_clicked(c, idx)
            
            svg.appendChild(circle)

    update_pieces_ui()

def get_pos_coords(color: str, piece_idx: int):
    p = pieces[color][piece_idx]
    st = p['status']
    idx = int(p['pos'])
    
    if st == 'base':
        return BASE_POS[color][idx]
    elif st == 'path':
        return GLOBAL_PATH[idx]
    elif st == 'home':
        return HOME_PATHS[color][idx]
    elif st == 'win':
        return (7, 7)
    return (0, 0)

def update_pieces_ui():
    for color in PLAYER_ORDER:
        for i, p in enumerate(pieces[color]):
            coords = get_pos_coords(color, i)
            elem = document.getElementById(p['id'])
            # Offset center of cell
            cx = coords[0] * CELL_SIZE + CELL_SIZE / 2
            cy = coords[1] * CELL_SIZE + CELL_SIZE / 2
            
            # Se houver múltiplas peças na mesma casa, espalhar levemente (TODO)
            elem.setAttribute("cx", cx)
            elem.setAttribute("cy", cy)
            
            # Highlights
            if GAME_STATE == "WAITING_PIECE" and color == PLAYER_ORDER[TURN_INDEX]:
                if can_move(p, DICE_VALUE):
                    elem.classList.add("active")
                else:
                    elem.classList.remove("active")
            else:
                elem.classList.remove("active")

def can_move(piece, die):
    if piece['status'] == 'base':
        return die == 6
    if piece['status'] == 'win':
        return False
    # Check if home path overflow
    if piece['status'] == 'home':
        return piece['pos'] + die <= 5
    return True

def roll_dice(event):
    global DICE_VALUE, GAME_STATE
    if GAME_STATE != "WAITING_DICE":
        return
    
    btn = document.getElementById("roll-btn")
    btn.disabled = True
    
    # Animação simples
    die_face = document.getElementById("die-face")
    
    # Sorteio
    DICE_VALUE = random.randint(1, 6)
    die_face.innerText = str(DICE_VALUE)
    die_face.style.transform = "rotate(360deg)"
    
    document.getElementById("game-msg").innerText = f"Você tirou {DICE_VALUE}!"
    
    # Verificar se jogador tem jogadas possíveis
    possible = False
    current_color = PLAYER_ORDER[TURN_INDEX]
    for i, p in enumerate(pieces[current_color]):
        if can_move(p, DICE_VALUE):
            possible = True
            break
            
    if not possible:
        document.getElementById("game-msg").innerText += " Sem jogadas. Próximo!"
        window.setTimeout(next_turn, 1500)
    else:
        GAME_STATE = "WAITING_PIECE"
        update_pieces_ui()

def next_turn():
    global TURN_INDEX, GAME_STATE
    # Se tirou 6, joga de novo, senão muda o turno
    if DICE_VALUE != 6:
        TURN_INDEX = (TURN_INDEX + 1) % 4
    
    GAME_STATE = "WAITING_DICE"
    current_color = PLAYER_ORDER[TURN_INDEX]
    
    title = document.getElementById("turn-title")
    title.innerText = f"Turno do {current_color.capitalize()}"
    document.getElementById("status-display").style.borderLeftColor = COLORS[current_color]
    document.getElementById("game-msg").innerText = "Lançar o dado!"
    document.getElementById("die-face").innerText = "?"
    document.getElementById("die-face").style.transform = "rotate(0deg)"
    document.getElementById("roll-btn").disabled = False
    update_pieces_ui()

def piece_clicked(color, idx):
    global GAME_STATE
    if GAME_STATE != "WAITING_PIECE":
        return
    if color != PLAYER_ORDER[TURN_INDEX]:
        return
    
    piece = pieces[color][idx]
    if not can_move(piece, DICE_VALUE):
        return
    
    move_piece(color, idx, DICE_VALUE)

def move_piece(color, idx, steps):
    global GAME_STATE
    p = pieces[color][idx]
    
    if p['status'] == 'base':
        # Sai da base
        p['status'] = 'path'
        p['pos'] = START_IDX[color]
        p['dist'] = 0 # Initialize distance when leaving base
    elif p['status'] == 'path':
        dist = int(p['dist'])
        dist += steps
        if dist > 50: # Entra no home após 51 casas no path global
            overflow = dist - 51
            if overflow <= 5:
                p['status'] = 'home'
                p['pos'] = overflow
                p['dist'] = dist
            else:
                # Não altera nada (fica onde está se passar do win)
                pass 
        else:
            p['pos'] = (int(p['pos']) + steps) % 52
            p['dist'] = dist
            # Verificar captura
            check_capture(color, int(p['pos']))
            
    elif p['status'] == 'home':
        p['pos'] += steps
        if p['pos'] == 5:
            p['status'] = 'win'
            document.getElementById("game-msg").innerText = "Peça finalizada!"

    GAME_STATE = "ANIMATING"
    update_pieces_ui()
    
    # Checar vitória (4 peças no win)
    wins = sum(1 for pi in pieces[color] if pi['status'] == 'win')
    if wins == 4:
        document.getElementById("game-msg").innerText = f"JOGADOR {color.upper()} VENCEU!"
        return

    window.setTimeout(next_turn, 800)

def check_capture(color, path_idx):
    # Procura peças de outras cores no mesmo path_idx
    for other_color in PLAYER_ORDER:
        if other_color == color: continue
        for i, p in enumerate(pieces[other_color]):
            if p['status'] == 'path' and p['pos'] == path_idx:
                # Volta para a base
                p['status'] = 'base'
                p['pos'] = i # slot original
                p['dist'] = 0
                document.getElementById("game-msg").innerText = f"{color} capturou {other_color}!"

# Inicialização
create_board()
document.getElementById("loading-screen").style.display = "none"
print("Motor Antigravity Pronto!")
