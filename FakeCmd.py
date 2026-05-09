#!/usr/bin/env python3
"""
vfx_terminal.py — Cinema Visual Effects Terminal Simulator
"""

import sys
import time
import random
import string
import os
import argparse
import tty
import termios

# ─────────────────────────────────────────────
#  VALORI DEFAULT
# ─────────────────────────────────────────────

DEFAULT_PROMPT  = "root@mainframe:~# "
DEFAULT_COMMAND = "ssh -i ~/.ssh/id_rsa admin@192.168.1.1"
DEFAULT_ACTION  = "access_granted"

VALID_ACTIONS = ["access_granted", "access_denied", "matrix", "decrypt", "upload", "custom"]

TYPING_SPEED       = 0.04
PAUSE_BEFORE_ENTER = 0.8

CHAOS_CHARS = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?/"

CUSTOM_OUTPUT = """
[CUSTOM] Inserisci qui il tuo messaggio personalizzato.
"""

# ─────────────────────────────────────────────
#  COLORI ANSI
# ─────────────────────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[32m"
    BGREEN  = "\033[92m"
    RED     = "\033[31m"
    BRED    = "\033[91m"
    YELLOW  = "\033[33m"
    CYAN    = "\033[36m"
    BCYAN   = "\033[96m"
    WHITE   = "\033[97m"

# ─────────────────────────────────────────────
#  UTILITY
# ─────────────────────────────────────────────

def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()

def sleep(t, jitter=0.0):
    time.sleep(max(0.0, t + random.uniform(-jitter, jitter)))

def terminal_cols():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def wait_for_enter():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"):
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ─────────────────────────────────────────────
#  PROMPT E COMANDO
# ─────────────────────────────────────────────

def print_prompt(prompt):
    write(C.BOLD + C.BGREEN + prompt + C.RESET)

def type_command(cmd, chaos=False):
    for ch in cmd:
        if chaos:
            n = random.randint(1, 3)
            for _ in range(n):
                write(C.DIM + C.CYAN + random.choice(CHAOS_CHARS) + C.RESET)
                sleep(0.045, jitter=0.02)
            write("\b \b" * n)
        write(C.WHITE + ch + C.RESET)
        sleep(TYPING_SPEED, jitter=TYPING_SPEED * 0.4)

def press_enter():
    write("\n")

# ─────────────────────────────────────────────
#  AZIONI FINALI
# ─────────────────────────────────────────────

def action_access_granted():
    sleep(0.3)
    for line in [
        C.BGREEN + "[✔] Autenticazione completata" + C.RESET,
        C.BGREEN + "[✔] Connessione stabilita — sessione cifrata AES-256" + C.RESET,
        C.BGREEN + "[✔] Accesso consentito. Benvenuto, Amministratore." + C.RESET,
    ]:
        sleep(0.25)
        write(line + "\n")
    sleep(0.4)
    write(C.BOLD + C.BGREEN + "\n"
        "  ██████╗ ██╗  ██╗\n"
        "  ██╔═══╝ ██║ ██╔╝\n"
        "  ██║     █████╔╝ \n"
        "  ██║     ██╔═██╗ \n"
        "  ██████╗ ██║  ██╗\n"
        "  ╚═════╝ ╚═╝  ╚═╝  ACCESS GRANTED\n\n" + C.RESET)

def action_access_denied():
    sleep(0.3)
    for line in [
        C.BRED + "[✘] Autenticazione fallita" + C.RESET,
        C.BRED + "[✘] Credenziali non valide o account bloccato" + C.RESET,
        C.YELLOW + "[!] Tentativo registrato — avviso inviato al SOC" + C.RESET,
    ]:
        sleep(0.3)
        write(line + "\n")
    sleep(0.4)
    write(C.BOLD + C.BRED + "\n"
        "  ██████╗ ███████╗███╗   ██╗██╗███████╗██████╗ \n"
        "  ██╔══██╗██╔════╝████╗  ██║██║██╔════╝██╔══██╗\n"
        "  ██║  ██║█████╗  ██╔██╗ ██║██║█████╗  ██║  ██║\n"
        "  ██║  ██║██╔══╝  ██║╚██╗██║██║██╔══╝  ██║  ██║\n"
        "  ██████╔╝███████╗██║ ╚████║██║███████╗██████╔╝\n"
        "  ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝╚══════╝╚═════╝ \n\n" + C.RESET)

def action_matrix():
    sleep(0.2)
    write(C.BGREEN + "Inizializzazione canale sicuro...\n" + C.RESET)
    sleep(0.4)
    cols   = terminal_cols()
    glyphs = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"
    for _ in range(14):
        row = "".join(
            random.choice(glyphs) if random.random() > 0.3 else " "
            for _ in range(cols)
        )
        brightness = random.choice([C.GREEN, C.BGREEN, C.DIM + C.GREEN])
        write(brightness + row + C.RESET + "\n")
        sleep(0.07)
    write("\n" + C.BOLD + C.BCYAN + "[SISTEMA ONLINE]" + C.RESET + "\n\n")

def action_decrypt():
    sleep(0.2)
    fake_hex = lambda n: " ".join(f"{random.randint(0, 255):02X}" for _ in range(n))
    write(C.YELLOW + "[*] Avvio decifratura payload...\n" + C.RESET)
    for block in ["PAYLOAD_ENC.bin", "MANIFEST.aes", "KEYS.vault"]:
        write(C.DIM + "  " + block + ": " + C.RESET)
        for _ in range(8):
            write(C.CYAN + fake_hex(4) + C.RESET + "  ")
            sleep(0.08)
        write("\r  " + C.BGREEN + block + ": OK ✔" + C.RESET + "          \n")
        sleep(0.2)
    sleep(0.3)
    write("\n" + C.BOLD + C.BGREEN + "[✔] Decifratura completata. Checksum verificato." + C.RESET + "\n\n")

def action_upload():
    sleep(0.2)
    filename  = "transfer_package_v3.tar.gz"
    size_mb   = 14.7
    cols      = terminal_cols()
    label_w   = 2 + len(filename) + 2
    stats_w   = len(" 99.9/99.9 MB  9.9 MB/s  ")
    bar_width = max(10, cols - label_w - stats_w - 2)

    write(C.CYAN + "[*] Upload in corso → target: 192.168.1.1/tmp/.hidden\n" + C.RESET)

    steps = bar_width * 4
    for i in range(steps + 1):
        pct     = i / steps
        filled  = int(pct * bar_width)
        bar     = "█" * filled + "░" * (bar_width - filled)
        mb_done = pct * size_mb
        speed   = random.uniform(1.8, 3.4)
        write("\r  " + C.YELLOW + filename + C.RESET +
              "  [" + C.BGREEN + bar + C.RESET + "]" +
              C.WHITE + f" {mb_done:4.1f}/{size_mb:.1f} MB  {speed:.1f} MB/s" + C.RESET + "  ")
        sleep(0.03)

    write("\n" + C.BGREEN + "[✔] Upload completato." + C.RESET + "\n\n")

def action_custom():
    sleep(0.3)
    write(C.BCYAN + CUSTOM_OUTPUT + C.RESET + "\n")

# ─────────────────────────────────────────────
#  DISPATCHER
# ─────────────────────────────────────────────

ACTIONS = {
    "access_granted": action_access_granted,
    "access_denied":  action_access_denied,
    "matrix":         action_matrix,
    "decrypt":        action_decrypt,
    "upload":         action_upload,
    "custom":         action_custom,
}

# ─────────────────────────────────────────────
#  ARGOMENTI CLI
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="VFX Terminal Simulator — effetto hacker da cinema",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Azioni disponibili: " + ", ".join(VALID_ACTIONS),
    )
    parser.add_argument("-p", "--prompt",
        default=DEFAULT_PROMPT, metavar="PROMPT",
        help='Stringa del prompt  (default: "' + DEFAULT_PROMPT + '")')
    parser.add_argument("-c", "--command",
        default=DEFAULT_COMMAND, metavar="CMD",
        help='Comando da digitare (default: "' + DEFAULT_COMMAND + '")')
    parser.add_argument("-a", "--action",
        default=DEFAULT_ACTION, choices=VALID_ACTIONS, metavar="ACTION",
        help="Azione finale       (default: %(default)s)\n"
             "Scelte: " + ", ".join(VALID_ACTIONS))
    parser.add_argument("-w", "--wait",
        action="store_true",
        help="Aspetta Invio dopo il comando, prima dell'azione finale")
    parser.add_argument("-W", "--wait-before",
        action="store_true",
        help="Aspetta Invio prima di iniziare a scrivere il comando")
    parser.add_argument("-k", "--keyboard",
        action="store_true",
        help="Simula ricerca sulla tastiera: tasti casuali intercalati e cancellati")
    parser.add_argument("-r", "--reprompt",
        action="store_true",
        help="Stampa di nuovo il prompt alla fine, prima dell'attesa finale")
    return parser.parse_args()

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    args = parse_args()

    clear_screen()
    print_prompt(args.prompt)

    if args.wait_before:
        wait_for_enter()

    type_command(args.command, chaos=args.keyboard)
    sleep(PAUSE_BEFORE_ENTER)

    if args.wait:
        wait_for_enter()
    press_enter()

    ACTIONS.get(args.action, action_custom)()

    if args.reprompt:
        print_prompt(args.prompt)
    wait_for_enter()

if __name__ == "__main__":
    main()
