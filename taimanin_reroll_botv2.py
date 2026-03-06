"""
TaimaninSquad Auto-Reroll Bot — ADB Edition (Database Matching Final)
==========================================================================
Controla cada instancia de MuMu 12 directamente via ADB.
Detecta las rarezas buscando las caras (char1.png - char11.png).
"""

import subprocess
import threading
import time
import sys
import io
import os
import glob
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

# =============================================================================
#  !! CONFIGURACION — EDITA ESTA SECCION !!
# =============================================================================

INSTANCES = [
    {"name": "Rerroll 1", "serial": "emulator-5560"},
    {"name": "Rerroll 2", "serial": "emulator-5562"},
    {"name": "Rerroll 3", "serial": "emulator-5564"},
    {"name": "Rerroll 4", "serial": "emulator-5566"},
]

# Minimo de personajes SSR (5 estrellas) para parar esa instancia
# ¡Recuerda! Lo tenías en 1 para las pruebas, lo he devuelto a 3 que era tu objetivo.
MIN_SSR = 3

# Segundos de espera tras tocar Re-recruit
WAIT_AFTER_RECRUIT = 3.5
STARTUP_DELAY = 3

# Ruta al ejecutable ADB
ADB_PATH = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"

# =============================================================================
#  Coordenadas de los botones (resolucion interna 960x540)
# =============================================================================
RERECRUIT_X = 790
RERECRUIT_Y = 495

# =============================================================================
#  Configuración de Plantillas (Base de datos de Personajes)
# =============================================================================

MATCH_THRESHOLD = 0.85 
SSR_FOLDER = "ssr_personajes"

# Lista para guardar las plantillas y sus nombres
ssr_templates = []

# Cargar automáticamente todas las imágenes que se llamen "char...png"
if os.path.exists(SSR_FOLDER):
    # Busca char1.png, char2.png, etc.
    archivos = glob.glob(f"{SSR_FOLDER}/char*.png")
    for filepath in archivos:
        tpl = cv2.imread(filepath, cv2.IMREAD_COLOR)
        if tpl is not None:
            nombre_archivo = os.path.basename(filepath)
            ssr_templates.append((nombre_archivo, tpl))

# =============================================================================

# ─── Logging thread-safe ──────────────────────────────────────────────────────
_print_lock = threading.Lock()

def log(name: str, msg: str):
    with _print_lock:
        print(f"  [{name:12s}] {msg}", flush=True)

# =============================================================================
#  ADB: conexion y comandos basicos
# =============================================================================

def adb(serial: str, *args, timeout: int = 10) -> Tuple[bool, bytes]:
    cmd = [ADB_PATH, "-s", serial] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, b""
    except FileNotFoundError:
        print(f"\n[ERROR] ADB no encontrado en '{ADB_PATH}'.")
        sys.exit(1)

def connect_instance(serial: str, name: str) -> bool:
    ok, out = adb(serial, "get-state")
    output = out.decode(errors="ignore").strip()
    if ok and "device" in output:
        log(name, f"✓ ADB OK ({serial})")
        return True
    log(name, f"✗ No disponible ({serial}): {output}")
    return False

def screenshot_adb(serial: str) -> Optional[np.ndarray]:
    ok, data = adb(serial, "exec-out", "screencap", "-p", timeout=15)
    if not ok or len(data) < 1000:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception:
        return None

def tap(serial: str, x: int, y: int) -> bool:
    ok, _ = adb(serial, "shell", "input", "tap", str(x), str(y))
    return ok

# =============================================================================
#  Deteccion de personajes SSR
# =============================================================================

def count_ssr(img_bgr: np.ndarray) -> Tuple[int, int]:
    """
    Busca todas las caras de la base de datos en la captura.
    Devuelve la cantidad de SSR encontrados.
    """
    matches_encontrados = []
    
    # Pasamos la foto de CADA personaje por la pantalla
    for nombre_archivo, tpl in ssr_templates:
        res = cv2.matchTemplate(img_bgr, tpl, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= MATCH_THRESHOLD)
        
        for pt in zip(*loc[::-1]):  
            # Evitamos contar al mismo personaje en el mismo sitio dos veces (distancia de 50px)
            if all(abs(pt[0] - m[0]) > 50 for m in matches_encontrados):
                matches_encontrados.append(pt)
                
    ssr_count = len(matches_encontrados)
    
    # En este método no buscamos 4 estrellas, así que devolvemos 0 para SR
    return ssr_count, 0 

# =============================================================================
#  Worker por instancia
# =============================================================================

def instance_worker(name: str, serial: str, stop_event: threading.Event):
    attempt = 0

    while not stop_event.is_set():
        attempt += 1

        img = screenshot_adb(serial)
        if img is None:
            log(name, f"#{attempt:03d} Screenshot fallido, reintentando...")
            time.sleep(1.0)
            continue

        ssr, sr = count_ssr(img)
        
        # Interfaz visual chula para la consola
        if ssr >= MIN_SSR:
            bar = ("★" * min(ssr, 5)).ljust(5) + f" ¡BINGO! SSR={ssr}"
        elif ssr > 0:
            bar = ("★" * min(ssr, 5)).ljust(5) + f" SSR={ssr}"
        else:
            bar = "       " + f" SSR={ssr}"
            
        log(name, f"#{attempt:03d} {bar}")

        if ssr >= MIN_SSR:
            with _print_lock:
                print()
                print(f"  ╔══════════════════════════════════════════════╗")
                print(f"  ║  ★★★  {name}: ¡{ssr} SSR ENCONTRADOS!  ★★★  ║")
                print(f"  ║  → Confirma manualmente el reclutamiento     ║")
                print(f"  ╚══════════════════════════════════════════════╝")
                print()
            # print("\a\a\a")  # Beep de alerta
            stop_event.set()
            break

        # Si no hay 3 SSR, tocar Re-recruit
        ok = tap(serial, RERECRUIT_X, RERECRUIT_Y)
        if not ok:
            log(name, "Tap fallido, reintentando...")
            time.sleep(0.5)
            continue

        time.sleep(WAIT_AFTER_RECRUIT)

# =============================================================================
#  MAIN
# =============================================================================

def check_adb_available() -> bool:
    try:
        result = subprocess.run(
            [ADB_PATH, "version"],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.decode(errors="ignore").splitlines()[0]
            print(f"  ✓ ADB encontrado: {version}")
            return True
    except FileNotFoundError:
        pass
    print(f"\n  [ERROR] ADB no encontrado en '{ADB_PATH}'.")
    return False

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   TaimaninSquad Auto-Reroll Bot — Database Edition      ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Instancias : {len(INSTANCES):<44}║")
    print(f"║  Objetivo   : {MIN_SSR}+ SSR por instancia{' '*27}║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    if not ssr_templates:
        print(f"  [ERROR] No se encontraron imágenes en la carpeta '{SSR_FOLDER}'.")
        print(f"  Crea la carpeta '{SSR_FOLDER}' y mete ahí los recortes (char1.png a char11.png).")
        sys.exit(1)
    else:
        print(f"  ✓ Base de datos cargada: {len(ssr_templates)} personajes SSR listos.")
        # Mostrar los nombres de los archivos cargados (opcional, para confirmar que están todos)
        # print("  Cargados:", [nombre for nombre, _ in ssr_templates])

    print("\n► Verificando ADB...")
    if not check_adb_available():
        sys.exit(1)

    print("\n► Conectando instancias...")
    connected = []
    for inst in INSTANCES:
        if connect_instance(inst["serial"], inst["name"]):
            connected.append(inst)
        else:
            print(f"  ! {inst['name']} ({inst['serial']}) no disponible — saltando")

    if not connected:
        print("\n[ERROR] Ninguna instancia conectada.")
        sys.exit(1)

    print(f"\n  → {len(connected)}/{len(INSTANCES)} instancias conectadas\n")

    print(f"  Arrancando en {STARTUP_DELAY} segundos... (Ctrl+C para parar)\n")
    for i in range(STARTUP_DELAY, 0, -1):
        print(f"  {i}...", end="\r", flush=True)
        time.sleep(1)
    print("  ¡Arrancando!\n")

    workers = []
    for inst in connected:
        stop_event = threading.Event()
        t = threading.Thread(
            target=instance_worker,
            args=(inst["name"], inst["serial"], stop_event),
            daemon=True,
            name=inst["name"]
        )
        workers.append((inst["name"], t, stop_event))
        t.start()
        time.sleep(0.2) 

    try:
        while True:
            alive  = sum(1 for _, t, _ in workers if t.is_alive())
            stopped = len(workers) - alive
            print(
                f"  Estado → ✅ {stopped} paradas | 🔄 {alive} buscando...   ",
                end="\r", flush=True
            )
            if alive == 0:
                break
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n  ⛔ Detenido por el usuario.")
        for _, _, ev in workers:
            ev.set()
        sys.exit(0)

    print("\n\n  ══════════════════════════════════════════════")
    print("  ✅  Todas las instancias han terminado.        ")
    print(f"  Confirma manualmente las que tengan {MIN_SSR}+ SSR.   ")
    print("  ══════════════════════════════════════════════")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⛔ Detenido.")
        sys.exit(0)