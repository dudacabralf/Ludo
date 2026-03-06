from pyscript import window, document
from pyodide.ffi import create_proxy
import random

# ============================================================
# CONSTANTES
# ============================================================
CELL_SIZE = 40
BOARD_SIZE = 15
COLORS = {
    'red': '#ff3e3e',
    'green': '#2ecc71',
    'yellow': '#f1c40f',
    'blue': '#2c9aff'
}
COLOR_NAMES = {
    'red': 'Vermelho',
    'blue': 'Azul',
    'yellow': 'Amarelo',
    'green': 'Verde'
}

SAFE_CELLS = [0, 8, 13, 21, 26, 34, 39, 47]
PLAYER_ORDER = ['red', 'blue', 'yellow', 'green']

# ============================================================
# ESTADO DO JOGO
# ============================================================
TURN_INDEX = 0
DICE_VALUE = 0
GAME_STATE = "WAITING_DICE"  # WAITING_DICE, WAITING_PIECE, ANIMATING, GAME_OVER

# ============================================================
# POSIÇÕES DAS PEÇAS
# ============================================================
pieces = {
    'red':    [{'id': 'r1', 'pos': -1, 'status': 'base'},
               {'id': 'r2', 'pos': -1, 'status': 'base'},
               {'id': 'r3', 'pos': -1, 'status': 'base'},
               {'id': 'r4', 'pos': -1, 'status': 'base'}],
    'blue':   [{'id': 'b1', 'pos': -1, 'status': 'base'},
               {'id': 'b2', 'pos': -1, 'status': 'base'},
               {'id': 'b3', 'pos': -1, 'status': 'base'},
               {'id': 'b4', 'pos': -1, 'status': 'base'}],
    'yellow': [{'id': 'y1', 'pos': -1, 'status': 'base'},
               {'id': 'y2', 'pos': -1, 'status': 'base'},
               {'id': 'y3', 'pos': -1, 'status': 'base'},
               {'id': 'y4', 'pos': -1, 'status': 'base'}],
    'green':  [{'id': 'g1', 'pos': -1, 'status': 'base'},
               {'id': 'g2', 'pos': -1, 'status': 'base'},
               {'id': 'g3', 'pos': -1, 'status': 'base'},
               {'id': 'g4', 'pos': -1, 'status': 'base'}],
}

# Posições (col, row) das 4 peças na base de cada cor
BASE_POSITIONS = {
    'red':    [(2, 2), (4, 2), (2, 4), (4, 4)],
    'blue':   [(10, 2), (12, 2), (10, 4), (12, 4)],
    'yellow': [(10, 10), (12, 10), (10, 12), (12, 12)],
    'green':  [(2, 10), (4, 10), (2, 12), (4, 12)],
}

# Caminho global: 52 casas (col, row)
GLOBAL_PATH = [
    (6,1), (6,2), (6,3), (6,4), (6,5),
    (5,6), (4,6), (3,6), (2,6), (1,6), (0,6),
    (0,7),
    (0,8), (1,8), (2,8), (3,8), (4,8), (5,8),
    (6,9), (6,10), (6,11), (6,12), (6,13), (6,14),
    (7,14),
    (8,14), (8,13), (8,12), (8,11), (8,10), (8,9),
    (9,8), (10,8), (11,8), (12,8), (13,8), (14,8),
    (14,7),
    (14,6), (13,6), (12,6), (11,6), (10,6), (9,6),
    (8,5), (8,4), (8,3), (8,2), (8,1), (8,0),
    (7,0),
]

# Índice de partida de cada cor no GLOBAL_PATH
START_IDX = {'red': 0, 'blue': 13, 'yellow': 26, 'green': 39}

# Caminhos finais (col, row) — 6 casas cada (índice 0..5, sendo 5 = centro/vitória)
HOME_PATHS = {
    'red':    [(7,1), (7,2), (7,3), (7,4), (7,5), (7,6)],
    'blue':   [(1,7), (2,7), (3,7), (4,7), (5,7), (6,7)],
    'yellow': [(7,13), (7,12), (7,11), (7,10), (7,9), (7,8)],
    'green':  [(13,7), (12,7), (11,7), (10,7), (9,7), (8,7)],
}

# Guarda referências de proxies para não serem coletadas pelo GC
proxies = []

# ============================================================
# FUNÇÕES DE COORDENADAS
# ============================================================
def get_pixel_coords(color, piece_index):
    """Retorna (px_x, px_y) do centro de uma peça para renderização."""
    p = pieces[color][piece_index]
    status = p['status']

    if status == 'base':
        col, row = BASE_POSITIONS[color][piece_index]
    elif status == 'path':
        path_pos = int(p['pos'])
        col, row = GLOBAL_PATH[path_pos % 52]
    elif status == 'home':
        home_pos = int(p['pos'])
        col, row = HOME_PATHS[color][home_pos]
    elif status == 'win':
        col, row = (7, 7)
    else:
        col, row = (0, 0)

    px_x = col * CELL_SIZE + CELL_SIZE / 2
    px_y = row * CELL_SIZE + CELL_SIZE / 2
    return (px_x, px_y)


# ============================================================
# CRIAR TABULEIRO
# ============================================================
def create_board():
    svg = document.getElementById("board-svg")
    if not svg:
        print("ERRO: SVG não encontrado!")
        return

    # Preservar <defs> e limpar o resto
    to_remove = []
    for i in range(svg.childNodes.length):
        node = svg.childNodes.item(i)
        if node and node.nodeName and node.nodeName.lower() != "defs":
            to_remove.append(node)
    for node in to_remove:
        svg.removeChild(node)

    # Desenhar células do tabuleiro
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
            rect.setAttribute("x", str(col * CELL_SIZE))
            rect.setAttribute("y", str(row * CELL_SIZE))
            rect.setAttribute("width", str(CELL_SIZE))
            rect.setAttribute("height", str(CELL_SIZE))
            rect.setAttribute("class", "cell")

            # Bases coloridas
            if col < 6 and row < 6:
                rect.setAttribute("class", "cell base-red")
            elif col > 8 and row < 6:
                rect.setAttribute("class", "cell base-blue")
            elif col > 8 and row > 8:
                rect.setAttribute("class", "cell base-yellow")
            elif col < 6 and row > 8:
                rect.setAttribute("class", "cell base-green")
            elif 6 <= col <= 8 and 6 <= row <= 8:
                rect.setAttribute("fill", "#1a1a2e")

            svg.appendChild(rect)

    # Casas seguras
    for idx in SAFE_CELLS:
        col, row = GLOBAL_PATH[idx]
        star = document.createElementNS("http://www.w3.org/2000/svg", "text")
        star.setAttribute("x", str(col * CELL_SIZE + CELL_SIZE / 2))
        star.setAttribute("y", str(row * CELL_SIZE + CELL_SIZE / 2 + 5))
        star.setAttribute("text-anchor", "middle")
        star.setAttribute("font-size", "16")
        star.setAttribute("fill", "rgba(255,255,255,0.15)")
        star.textContent = "★"
        svg.appendChild(star)

    # Caminhos de casa (home paths coloridos)
    for color, path in HOME_PATHS.items():
        for i, pos in enumerate(path):
            if i < 5:
                rect = document.createElementNS("http://www.w3.org/2000/svg", "rect")
                rect.setAttribute("x", str(pos[0] * CELL_SIZE))
                rect.setAttribute("y", str(pos[1] * CELL_SIZE))
                rect.setAttribute("width", str(CELL_SIZE))
                rect.setAttribute("height", str(CELL_SIZE))
                rect.setAttribute("fill", COLORS[color])
                rect.setAttribute("opacity", "0.15")
                svg.appendChild(rect)

    # Centro do tabuleiro
    center = document.createElementNS("http://www.w3.org/2000/svg", "rect")
    center.setAttribute("x", str(6 * CELL_SIZE))
    center.setAttribute("y", str(6 * CELL_SIZE))
    center.setAttribute("width", str(3 * CELL_SIZE))
    center.setAttribute("height", str(3 * CELL_SIZE))
    center.setAttribute("fill", "#1a1a2e")
    center.setAttribute("stroke", "rgba(255,255,255,0.1)")
    center.setAttribute("stroke-width", "1")
    svg.appendChild(center)

    # Criar os 16 bonecos
    for color in PLAYER_ORDER:
        for i in range(4):
            p = pieces[color][i]
            circle = document.createElementNS("http://www.w3.org/2000/svg", "circle")
            circle.setAttribute("id", p['id'])
            circle.setAttribute("r", str(CELL_SIZE * 0.35))
            circle.setAttribute("class", f"piece piece-{color}")
            circle.setAttribute("fill", COLORS[color])
            circle.setAttribute("stroke", "white")
            circle.setAttribute("stroke-width", "2.5")
            circle.setAttribute("style", "cursor: pointer; pointer-events: all;")

            # Criar handler com closure correta
            def make_click_handler(c, idx):
                def handler(event):
                    on_piece_click(c, idx)
                return handler

            handler_fn = make_click_handler(color, i)
            pxy = create_proxy(handler_fn)
            proxies.append(pxy)
            circle.addEventListener("click", pxy)
            svg.appendChild(circle)

    # Posicionar peças
    refresh_all_pieces()
    print("Tabuleiro criado com sucesso!")


# ============================================================
# ATUALIZAR POSIÇÕES VISUAIS
# ============================================================
def refresh_all_pieces():
    """Atualiza a posição visual de todas as 16 peças."""
    # Calcular posições e lidar com sobreposição
    position_groups = {}

    for color in PLAYER_ORDER:
        for i in range(4):
            px_x, px_y = get_pixel_coords(color, i)
            key = f"{int(px_x)},{int(px_y)}"
            if key not in position_groups:
                position_groups[key] = []
            position_groups[key].append((color, i, px_x, px_y))

    for key, group in position_groups.items():
        for gi, (color, i, px_x, px_y) in enumerate(group):
            p = pieces[color][i]
            elem = document.getElementById(p['id'])
            if not elem:
                continue

            # Offset para peças sobrepostas
            ox, oy = 0, 0
            if len(group) > 1:
                offsets = [(-6, -6), (6, -6), (-6, 6), (6, 6)]
                ox, oy = offsets[gi % 4]

            elem.setAttribute("cx", str(px_x + ox))
            elem.setAttribute("cy", str(px_y + oy))

    # Destacar peças que podem ser movidas
    current_color = PLAYER_ORDER[TURN_INDEX]
    for color in PLAYER_ORDER:
        for i in range(4):
            p = pieces[color][i]
            elem = document.getElementById(p['id'])
            if not elem:
                continue

            if GAME_STATE == "WAITING_PIECE" and color == current_color:
                if can_move_piece(p, DICE_VALUE):
                    elem.classList.add("active")
                    elem.setAttribute("style", "cursor: pointer; pointer-events: all;")
                else:
                    elem.classList.remove("active")
            else:
                elem.classList.remove("active")


# ============================================================
# LÓGICA DE MOVIMENTO
# ============================================================
def can_move_piece(piece, dice):
    """Verifica se uma peça pode se mover com o valor do dado."""
    status = piece['status']
    if status == 'win':
        return False
    if status == 'base':
        return dice == 6
    if status == 'home':
        new_pos = int(piece['pos']) + dice
        return new_pos <= 5
    if status == 'path':
        # Calcular distância percorrida
        return True
    return False


def get_distance_traveled(color, piece):
    """Calcula quantas casas a peça percorreu no caminho global."""
    if piece['status'] != 'path':
        return 0
    start = START_IDX[color]
    current = int(piece['pos'])
    if current >= start:
        return current - start
    else:
        return (52 - start) + current


def on_piece_click(color, idx):
    """Handler de clique em uma peça."""
    global GAME_STATE
    if GAME_STATE != "WAITING_PIECE":
        return
    if color != PLAYER_ORDER[TURN_INDEX]:
        return

    p = pieces[color][idx]
    if not can_move_piece(p, DICE_VALUE):
        return

    do_move(color, idx, DICE_VALUE)


def do_move(color, idx, steps):
    """Executa o movimento de uma peça."""
    global GAME_STATE
    p = pieces[color][idx]

    if p['status'] == 'base':
        # Sair da base — colocar na casa de partida
        p['status'] = 'path'
        p['pos'] = START_IDX[color]
        set_msg(f"🚀 {COLOR_NAMES[color]} saiu da base!")

    elif p['status'] == 'path':
        start = START_IDX[color]
        current_pos = int(p['pos'])
        traveled = get_distance_traveled(color, p)
        new_traveled = traveled + steps

        if new_traveled >= 51:
            # Entrar no caminho final (home)
            home_pos = new_traveled - 51
            if home_pos <= 5:
                p['status'] = 'home'
                p['pos'] = home_pos
                if home_pos == 5:
                    p['status'] = 'win'
                    set_msg(f"🎉 Peça do {COLOR_NAMES[color]} chegou em casa!")
                else:
                    set_msg(f"➡️ {COLOR_NAMES[color]} entrou na reta final!")
            else:
                set_msg(f"❌ Não pode mover — passaria da casa!")
                return
        else:
            # Mover no caminho global
            new_pos = (current_pos + steps) % 52
            p['pos'] = new_pos

            # Verificar captura
            if new_pos not in SAFE_CELLS:
                check_capture(color, new_pos)

            set_msg(f"🎲 {COLOR_NAMES[color]} moveu {steps} casas!")

    elif p['status'] == 'home':
        new_pos = int(p['pos']) + steps
        if new_pos == 5:
            p['status'] = 'win'
            p['pos'] = 5
            set_msg(f"🎉 Peça do {COLOR_NAMES[color]} chegou em casa!")
        elif new_pos < 5:
            p['pos'] = new_pos
            set_msg(f"➡️ {COLOR_NAMES[color]} avançou na reta final!")
        else:
            return

    # Atualizar visual
    GAME_STATE = "ANIMATING"
    refresh_all_pieces()

    # Verificar vitória
    wins = 0
    for pi in pieces[color]:
        if pi['status'] == 'win':
            wins += 1
    if wins == 4:
        GAME_STATE = "GAME_OVER"
        set_msg(f"🏆 {COLOR_NAMES[color].upper()} VENCEU O JOGO! 🏆")
        try:
            window.confetti()
        except:
            pass
        return

    # Próximo turno (com delay)
    pxy = create_proxy(lambda: next_turn())
    proxies.append(pxy)
    window.setTimeout(pxy, 800)


def check_capture(color, path_pos):
    """Verifica se capturou alguma peça adversária."""
    for other_color in PLAYER_ORDER:
        if other_color == color:
            continue
        for i, p in enumerate(pieces[other_color]):
            if p['status'] == 'path' and int(p['pos']) == path_pos:
                p['status'] = 'base'
                p['pos'] = -1
                set_msg(f"💥 {COLOR_NAMES[color]} capturou peça do {COLOR_NAMES[other_color]}!")


# ============================================================
# CONTROLE DE TURNO
# ============================================================
def roll_dice(event=None):
    """Lançar o dado."""
    global DICE_VALUE, GAME_STATE

    if GAME_STATE != "WAITING_DICE":
        return

    btn = document.getElementById("roll-btn")
    if btn:
        btn.disabled = True

    DICE_VALUE = random.randint(1, 6)

    die_face = document.getElementById("die-face")
    if die_face:
        die_face.textContent = str(DICE_VALUE)
        die_face.style.transform = "scale(1.3)"
        def reset_scale():
            die_face.style.transform = "scale(1)"
        pxy = create_proxy(reset_scale)
        proxies.append(pxy)
        window.setTimeout(pxy, 300)

    current_color = PLAYER_ORDER[TURN_INDEX]
    set_msg(f"🎲 {COLOR_NAMES[current_color]} tirou {DICE_VALUE}!")

    # Verificar se há jogadas possíveis
    movable = []
    for i, p in enumerate(pieces[current_color]):
        if can_move_piece(p, DICE_VALUE):
            movable.append(i)

    if len(movable) == 0:
        set_msg(f"🎲 Tirou {DICE_VALUE} — sem jogadas! Passando...")
        pxy = create_proxy(lambda: next_turn())
        proxies.append(pxy)
        window.setTimeout(pxy, 1500)
    elif len(movable) == 1:
        # Auto-mover se só há uma opção
        GAME_STATE = "WAITING_PIECE"
        refresh_all_pieces()
        def auto_move():
            do_move(current_color, movable[0], DICE_VALUE)
        pxy = create_proxy(auto_move)
        proxies.append(pxy)
        window.setTimeout(pxy, 500)
    else:
        GAME_STATE = "WAITING_PIECE"
        set_msg(f"🎲 Tirou {DICE_VALUE}! Clique na peça que quer mover!")
        refresh_all_pieces()


def next_turn():
    """Passar para o próximo turno."""
    global TURN_INDEX, GAME_STATE

    if GAME_STATE == "GAME_OVER":
        return

    # Se tirou 6, joga de novo
    if DICE_VALUE == 6:
        GAME_STATE = "WAITING_DICE"
        set_msg(f"🎯 Tirou 6! {COLOR_NAMES[PLAYER_ORDER[TURN_INDEX]]} joga de novo!")
    else:
        TURN_INDEX = (TURN_INDEX + 1) % 4
        GAME_STATE = "WAITING_DICE"

    current_color = PLAYER_ORDER[TURN_INDEX]

    title = document.getElementById("turn-title")
    if title:
        title.textContent = f"Turno do {COLOR_NAMES[current_color]}"

    status = document.getElementById("status-display")
    if status:
        status.style.borderLeftColor = COLORS[current_color]

    die_face = document.getElementById("die-face")
    if die_face:
        die_face.textContent = "?"
        die_face.style.transform = "rotate(0deg)"

    btn = document.getElementById("roll-btn")
    if btn:
        btn.disabled = False

    refresh_all_pieces()


# ============================================================
# UTILIDADES
# ============================================================
def set_msg(text):
    """Atualiza mensagem do jogo."""
    elem = document.getElementById("game-msg")
    if elem:
        elem.textContent = text


# ============================================================
# INICIALIZAÇÃO
# ============================================================
try:
    print("Iniciando Ludo Antigravity...")
    create_board()

    # Estado inicial
    TURN_INDEX = 0
    GAME_STATE = "WAITING_DICE"

    title = document.getElementById("turn-title")
    if title:
        title.textContent = f"Turno do {COLOR_NAMES['red']}"
    set_msg("Lance o dado para começar! 🎲")

    btn = document.getElementById("roll-btn")
    if btn:
        btn.disabled = False

    # Esconder loading
    loading = document.getElementById("loading-screen")
    if loading:
        loading.style.opacity = "0"
        def hide_loading():
            loading.style.display = "none"
        pxy = create_proxy(hide_loading)
        proxies.append(pxy)
        window.setTimeout(pxy, 500)

    print("Ludo Antigravity pronto!")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERRO: {e}")
    set_msg(f"Erro: {e}")
