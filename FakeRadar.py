#!/usr/bin/env python3
"""
RADAR SIMULATOR v2 - Sistema di sorveglianza fittizio
Radar a sinistra | Pannello informazioni a destra ampio e dettagliato
"""

import tkinter as tk
import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional

# ─── PALETTE ───────────────────────────────────────────────────────────────────
BG          = "#000d00"
G_BRIGHT    = "#00ff41"
G_MID       = "#00cc33"
G_DIM       = "#003b10"
G_VDIM      = "#001a08"
G_GRID      = "#001f00"
AMBER       = "#ffaa00"
AMBER_DIM   = "#7a5000"
RED         = "#ff2200"
RED_DIM     = "#4a0a00"
CYAN        = "#00eeff"
WHITE_G     = "#aaffcc"
PANEL_BG    = "#000b00"
BORDER      = "#004400"

SWEEP_SPEED = 1.8       # gradi/frame
FPS         = 40
MAX_T       = 20

TARGET_TYPES = [
    {"label": "AEREO",    "speed": (0.4, 1.2), "size": 3, "count": 5,  "color": G_BRIGHT, "icon": "✈"},
    {"label": "NAVE",     "speed": (0.1, 0.4), "size": 4, "count": 4,  "color": G_MID,    "icon": "⛵"},
    {"label": "ELICOT",   "speed": (0.2, 0.7), "size": 3, "count": 3,  "color": G_BRIGHT, "icon": "🚁"},
    {"label": "MISSILE",  "speed": (1.5, 3.0), "size": 2, "count": 2,  "color": AMBER,    "icon": "⚡"},
    {"label": "IGNOTO",   "speed": (0.3, 0.9), "size": 3, "count": 2,  "color": RED,      "icon": "?"},
    {"label": "DRONE",    "speed": (0.6, 1.4), "size": 2, "count": 2,  "color": CYAN,     "icon": "◆"},
]

IFF_CODES  = ["AMI-", "NATO", "ITA-", "CVN-", "UNK-", "---"]
CALLSIGNS  = ["FALCO", "AQUILA", "VIPER", "COBRA", "GHOST", "STORM",
              "BRAVO", "DELTA", "ECHO",  "FOXT",  "INDIA", "KILO"]

# ─── BERSAGLIO ─────────────────────────────────────────────────────────────────
@dataclass
class Target:
    x: float; y: float
    vx: float; vy: float
    label: str; size: int; color: str; icon: str
    id_str: str; callsign: str; iff: str
    altitude: int; speed_knots: int; heading: int
    angle_visible: float = -999.0
    trail: list = field(default_factory=list)
    blink: int = 0
    threat_level: int = 0   # 0=none 1=watch 2=alert

# ─── APP ───────────────────────────────────────────────────────────────────────
class RadarApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AN/TPS-75 TACTICAL RADAR — MODALITÀ OPERATIVA")
        self.root.configure(bg=BG)
        self.root.geometry("1440x860")
        self.root.minsize(1000, 650)

        self.sweep_angle  = 0.0
        self.targets: List[Target] = []
        self.frame_count  = 0
        self.start_time   = time.time()
        self.fullscreen   = False
        self.scan_count   = 0
        self.noise_dots   = self._gen_noise()
        self.selected: Optional[Target] = None
        self.alert_blink  = 0
        self.wind_dir     = random.randint(0, 359)
        self.wind_speed   = random.randint(5, 45)
        self.temperature  = random.randint(-5, 32)
        self.pressure     = random.randint(990, 1030)

        self._build_ui()
        self._spawn_all()
        self._loop()

        self.root.bind("<F11>",   self._toggle_fs)
        self.root.bind("<Escape>",self._on_esc)
        self.root.bind("<F5>",    lambda e: self._add_target())
        self.canvas.bind("<Button-1>", self._on_click)

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        mf = tk.Frame(self.root, bg=BG)
        mf.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ── HEADER ──────────────────────────────────────────────────────────
        hdr = tk.Frame(mf, bg=BG, height=44)
        hdr.pack(fill=tk.X, pady=(0, 4))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="◈ SISTEMA RADAR DIFESA AEREA  |  AN/TPS-75  |  MODO: OPERATIVO ◈",
                 fg=G_BRIGHT, bg=BG,
                 font=("Courier New", 15, "bold")).pack(side=tk.LEFT, padx=12)

        self.lbl_status = tk.Label(hdr, text="● OPERATIVO", fg=G_BRIGHT, bg=BG,
                                   font=("Courier New", 13, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=16)

        self.lbl_time = tk.Label(hdr, text="", fg=AMBER, bg=BG,
                                 font=("Courier New", 12))
        self.lbl_time.pack(side=tk.RIGHT, padx=20)

        # ── CORPO ───────────────────────────────────────────────────────────
        body = tk.Frame(mf, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)

        # Canvas radar — prende solo la parte sinistra
        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=2,
                                highlightbackground=BORDER, width=660)
        self.canvas.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Separatore verticale
        sep = tk.Frame(body, bg=BORDER, width=2)
        sep.pack(side=tk.LEFT, fill=tk.Y)

        # Pannello destro — prende tutto il resto
        right = tk.Frame(body, bg=PANEL_BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self._build_right(right)

        # ── FOOTER ──────────────────────────────────────────────────────────
        foot = tk.Frame(mf, bg=BG, height=26)
        foot.pack(fill=tk.X, pady=(4, 0))
        foot.pack_propagate(False)
        tk.Label(foot,
                 text="  [F11] Schermo Intero    [F5] Aggiungi Bersaglio    "
                      "[Click] Seleziona contatto    [ESC] Esci",
                 fg=G_DIM, bg=BG, font=("Courier New", 9)).pack(side=tk.LEFT)
        self.lbl_scan = tk.Label(foot, text="SCANSIONI: 0", fg=G_MID, bg=BG,
                                 font=("Courier New", 9))
        self.lbl_scan.pack(side=tk.RIGHT, padx=10)

    # ══════════════════════════════════════════════════════════════════════════
    #  PANNELLO DESTRO
    # ══════════════════════════════════════════════════════════════════════════
    def _build_right(self, p):
        # Helper per sezioni
        def section(title, color=AMBER):
            tk.Frame(p, bg=BORDER, height=1).pack(fill=tk.X, pady=(10, 0), padx=6)
            hf = tk.Frame(p, bg=PANEL_BG)
            hf.pack(fill=tk.X, padx=10, pady=(3, 2))
            tk.Label(hf, text=f"▶  {title}", fg=color, bg=PANEL_BG,
                     font=("Courier New", 12, "bold")).pack(anchor=tk.W)
            tk.Frame(p, bg=BORDER, height=1).pack(fill=tk.X, padx=6, pady=(0, 4))

        def info_row(parent, lbl, val, lw=18, lc=G_DIM, vc=G_BRIGHT, fs=11):
            f = tk.Frame(parent, bg=PANEL_BG)
            f.pack(fill=tk.X, pady=3, padx=14)
            tk.Label(f, text=lbl, fg=lc, bg=PANEL_BG,
                     font=("Courier New", fs), width=lw, anchor=tk.W).pack(side=tk.LEFT)
            lv = tk.Label(f, text=val, fg=vc, bg=PANEL_BG,
                          font=("Courier New", fs, "bold"), anchor=tk.W)
            lv.pack(side=tk.LEFT)
            return lv

        # ── INFO SISTEMA ────────────────────────────────────────────────────
        section("PARAMETRI SISTEMA")
        sys_f = tk.Frame(p, bg=PANEL_BG)
        sys_f.pack(fill=tk.X)
        # colonna sinistra / destra affiancate
        cl = tk.Frame(sys_f, bg=PANEL_BG); cl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cr = tk.Frame(sys_f, bg=PANEL_BG); cr.pack(side=tk.LEFT, fill=tk.X, expand=True)
        info_row(cl, "Modello:",      "AN/TPS-75")
        info_row(cl, "Frequenza:",    "9.410 GHz")
        info_row(cl, "PRF:",          "1200 Hz")
        info_row(cl, "Potenza TX:",   "850 kW")
        info_row(cr, "Portata:",       "450 NM")
        info_row(cr, "Copertura:",     "360° / 40°el")
        info_row(cr, "Risoluzione:",   "150 m")
        info_row(cr, "Sensibilità:",   "-108 dBm")

        # ── STATO SENSORI ───────────────────────────────────────────────────
        section("STATO SENSORI")
        sns_f = tk.Frame(p, bg=PANEL_BG); sns_f.pack(fill=tk.X)
        cl2 = tk.Frame(sns_f, bg=PANEL_BG); cl2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cr2 = tk.Frame(sns_f, bg=PANEL_BG); cr2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_rpm   = info_row(cl2, "Velocità rotaz.:", f"{SWEEP_SPEED*FPS/6:.1f} RPM")
        self.lbl_az    = info_row(cl2, "Azimut corrente:", "000.00°")
        self.lbl_range = info_row(cl2, "Portata attiva:", "450 NM")
        self.lbl_jam   = info_row(cl2, "Jamming:", "NESSUNO", vc=G_MID)
        self.lbl_iff_m = info_row(cr2, "Modo IFF:", "MODE-3/A")
        self.lbl_clut  = info_row(cr2, "CFAR Clutter:", "ATTIVO")
        self.lbl_mti   = info_row(cr2, "MTI Filter:", "ON")
        self.lbl_ec    = info_row(cr2, "ECCM:", "ATTIVO")

        # ── METEO ───────────────────────────────────────────────────────────
        section("CONDIZIONI METEO")
        met_f = tk.Frame(p, bg=PANEL_BG); met_f.pack(fill=tk.X)
        ml = tk.Frame(met_f, bg=PANEL_BG); ml.pack(side=tk.LEFT, fill=tk.X, expand=True)
        mr = tk.Frame(met_f, bg=PANEL_BG); mr.pack(side=tk.LEFT, fill=tk.X, expand=True)
        info_row(ml, "Vento:",       f"{self.wind_dir:03d}° / {self.wind_speed} kts")
        info_row(ml, "Temperatura:", f"{self.temperature}°C")
        info_row(mr, "Pressione:",   f"{self.pressure} hPa")
        info_row(mr, "Visibilità:",  "10+ km")

        # ── TRAFFICO ────────────────────────────────────────────────────────
        section("TRAFFICO RILEVATO")
        tr_f = tk.Frame(p, bg=PANEL_BG); tr_f.pack(fill=tk.X)
        tl = tk.Frame(tr_f, bg=PANEL_BG); tl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tr2= tk.Frame(tr_f, bg=PANEL_BG); tr2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_tot   = info_row(tl, "Totale contatti:", "0", fs=12)
        self.lbl_air   = info_row(tl, "Aerei/Elicot.:",  "0")
        self.lbl_nav   = info_row(tl, "Navi:",            "0")
        self.lbl_dr    = info_row(tl, "Droni:",           "0")
        self.lbl_mis   = info_row(tr2,"Missili:",         "0", vc=AMBER)
        self.lbl_unk   = info_row(tr2,"Ignoti:",          "0", vc=RED)
        self.lbl_thr   = info_row(tr2,"In sorveglianza:", "0", vc=AMBER)
        self.lbl_alr   = info_row(tr2,"⚠  ALLERTA:",     "0", vc=RED, fs=12)

        # ── LISTA CONTATTI ──────────────────────────────────────────────────
        section("CONTATTI RILEVATI  (click per selezionare)")
        hdr_f = tk.Frame(p, bg=G_VDIM)
        hdr_f.pack(fill=tk.X, padx=6, pady=(0, 1))
        for col, w in [("ID",7),("TIPO",9),("IFF",6),("DIST",7),("AZ",6),
                       ("ALT",7),("VEL",7),("HDG",6),("LIVELLO",9)]:
            tk.Label(hdr_f, text=col, fg=AMBER, bg=G_VDIM,
                     font=("Courier New", 9, "bold"), width=w, anchor=tk.W
                     ).pack(side=tk.LEFT, padx=2)

        list_frame = tk.Frame(p, bg=PANEL_BG)
        list_frame.pack(fill=tk.X, padx=6)
        self.contact_box = tk.Text(
            list_frame, bg="#000800", fg=G_BRIGHT,
            font=("Courier New", 10), height=10,
            bd=0, insertbackground=G_BRIGHT,
            selectbackground=G_DIM, relief=tk.FLAT)
        sb = tk.Scrollbar(list_frame, command=self.contact_box.yview,
                          bg=G_DIM, troughcolor=BG, width=10)
        self.contact_box.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.contact_box.pack(fill=tk.BOTH)
        self.contact_box.config(state=tk.DISABLED)
        self.contact_box.tag_config("alert", foreground=RED)
        self.contact_box.tag_config("warn",  foreground=AMBER)
        self.contact_box.tag_config("cyan",  foreground=CYAN)
        self.contact_box.tag_config("sel",   foreground=WHITE_G, background=G_DIM)

        # ── DETTAGLIO BERSAGLIO ─────────────────────────────────────────────
        section("DETTAGLIO CONTATTO SELEZIONATO", color=CYAN)
        det = tk.Frame(p, bg=PANEL_BG); det.pack(fill=tk.X)
        dl = tk.Frame(det, bg=PANEL_BG); dl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        dr = tk.Frame(det, bg=PANEL_BG); dr.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.d_id   = info_row(dl, "ID / Callsign:", "—", vc=CYAN,    fs=12)
        self.d_tipo = info_row(dl, "Tipo:",          "—", vc=G_BRIGHT, fs=11)
        self.d_iff  = info_row(dl, "Codice IFF:",    "—")
        self.d_alt  = info_row(dl, "Quota:",         "—")
        self.d_vel  = info_row(dr, "Velocità:",      "—", vc=G_BRIGHT, fs=11)
        self.d_hdg  = info_row(dr, "Rotta:",         "—")
        self.d_dist = info_row(dr, "Distanza:",      "—")
        self.d_thr  = info_row(dr, "Minaccia:",      "—")

        # ── LOG EVENTI ──────────────────────────────────────────────────────
        section("LOG EVENTI")
        log_frame = tk.Frame(p, bg=PANEL_BG); log_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))
        self.log_box = tk.Text(
            log_frame, bg="#000800", fg=G_MID,
            font=("Courier New", 9), bd=0,
            insertbackground=G_BRIGHT, relief=tk.FLAT)
        lsb = tk.Scrollbar(log_frame, command=self.log_box.yview,
                           bg=G_DIM, troughcolor=BG, width=10)
        self.log_box.config(yscrollcommand=lsb.set)
        lsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log_box.tag_config("warn",  foreground=AMBER)
        self.log_box.tag_config("alert", foreground=RED)
        self.log_box.tag_config("info",  foreground=G_MID)
        self.log_box.config(state=tk.DISABLED)

    # ══════════════════════════════════════════════════════════════════════════
    #  RUMORE / SPAWN
    # ══════════════════════════════════════════════════════════════════════════
    def _gen_noise(self):
        return [(random.uniform(-0.93, 0.93), random.uniform(-0.93, 0.93),
                 random.uniform(0.2, 0.9)) for _ in range(90)]

    def _spawn_all(self):
        for tt in TARGET_TYPES:
            for _ in range(tt["count"]):
                self._spawn_target(tt)

    def _spawn_target(self, tt=None):
        if tt is None:
            tt = random.choice(TARGET_TYPES)
        ang  = random.uniform(0, math.tau)
        dist = random.uniform(0.12, 0.88)
        x, y = dist * math.cos(ang), dist * math.sin(ang)
        spd  = random.uniform(*tt["speed"]) * 0.003
        hdg  = random.uniform(0, math.tau)
        vx, vy = spd * math.cos(hdg), spd * math.sin(hdg)
        tid  = f"{tt['label'][0]}{random.randint(10,99)}-{random.randint(100,999)}"
        cs   = random.choice(CALLSIGNS) + str(random.randint(1, 9))
        iff  = random.choice(IFF_CODES)
        alt  = random.randint(500, 39000) if tt["label"] != "NAVE" else 0
        vel  = random.randint(10, 950)
        heading = int(math.degrees(hdg)) % 360
        threat = 2 if tt["label"] == "IGNOTO" else (1 if tt["label"] == "MISSILE" else 0)
        t = Target(x=x, y=y, vx=vx, vy=vy,
                   label=tt["label"], size=tt["size"],
                   color=tt["color"], icon=tt["icon"],
                   id_str=tid, callsign=cs, iff=iff,
                   altitude=alt, speed_knots=vel, heading=heading,
                   threat_level=threat)
        self.targets.append(t)
        tag = "alert" if threat == 2 else ("warn" if threat == 1 else "info")
        self._log(f"NUOVO CONTATTO: {tid} [{tt['label']}] IFF:{iff}", tag)

    def _add_target(self):
        if len(self.targets) < MAX_T:
            self._spawn_target()

    # ══════════════════════════════════════════════════════════════════════════
    #  LOOP
    # ══════════════════════════════════════════════════════════════════════════
    def _loop(self):
        self.frame_count += 1
        self._update()
        self._draw()
        self.root.after(1000 // FPS, self._loop)

    def _update(self):
        prev = self.sweep_angle
        self.sweep_angle = (self.sweep_angle + SWEEP_SPEED) % 360
        if self.sweep_angle < prev:
            self.scan_count += 1

        for t in self.targets:
            t.x += t.vx; t.y += t.vy
            dist = math.hypot(t.x, t.y)
            if dist > 0.95:
                nx, ny = t.x / dist, t.y / dist
                dot = t.vx * nx + t.vy * ny
                t.vx -= 2 * dot * nx
                t.vy -= 2 * dot * ny
                t.x, t.y = nx * 0.93, ny * 0.93
                t.heading = int(math.degrees(math.atan2(t.vy, t.vx))) % 360

            ta = math.degrees(math.atan2(-t.y, t.x)) % 360
            if (self.sweep_angle - ta) % 360 < SWEEP_SPEED * 2.5:
                t.angle_visible = self.sweep_angle
                t.trail.append((t.x, t.y))
                if len(t.trail) > 10: t.trail.pop(0)
                t.blink = 10
            if t.blink > 0: t.blink -= 1

        # Time
        el = int(time.time() - self.start_time)
        self.lbl_time.config(
            text=f"T+{el//3600:02d}:{(el%3600)//60:02d}:{el%60:02d}   "
                 f"UTC {time.strftime('%H:%M:%S')}   "
                 f"{time.strftime('%d/%m/%Y')}")
        self.lbl_scan.config(text=f"SCANSIONI: {self.scan_count}")
        self.lbl_az.config(text=f"{self.sweep_angle:06.2f}°")

        # Conteggi
        n_air = sum(1 for t in self.targets if t.label in ("AEREO","ELICOT"))
        n_nav = sum(1 for t in self.targets if t.label == "NAVE")
        n_mis = sum(1 for t in self.targets if t.label == "MISSILE")
        n_dr  = sum(1 for t in self.targets if t.label == "DRONE")
        n_unk = sum(1 for t in self.targets if t.label == "IGNOTO")
        n_w   = sum(1 for t in self.targets if t.threat_level == 1)
        n_a   = sum(1 for t in self.targets if t.threat_level == 2)
        self.lbl_tot.config(text=str(len(self.targets)))
        self.lbl_air.config(text=str(n_air))
        self.lbl_nav.config(text=str(n_nav))
        self.lbl_dr.config(text=str(n_dr))
        self.lbl_mis.config(text=str(n_mis), fg=AMBER if n_mis else G_DIM)
        self.lbl_unk.config(text=str(n_unk), fg=RED   if n_unk else G_DIM)
        self.lbl_thr.config(text=str(n_w),   fg=AMBER if n_w   else G_DIM)
        self.lbl_alr.config(text=str(n_a),   fg=RED   if n_a   else G_DIM)

        if n_a > 0:
            self.alert_blink = (self.alert_blink + 1) % 20
            col = RED if self.alert_blink < 10 else AMBER
            self.lbl_status.config(text="⚠  ALLERTA", fg=col)
        elif n_w > 0:
            self.lbl_status.config(text="● SORVEGLIANZA", fg=AMBER)
        else:
            self.lbl_status.config(text="● OPERATIVO", fg=G_BRIGHT)

        self._update_contact_list()
        self._update_detail()

    # ══════════════════════════════════════════════════════════════════════════
    #  LISTA CONTATTI
    # ══════════════════════════════════════════════════════════════════════════
    def _update_contact_list(self):
        self.contact_box.config(state=tk.NORMAL)
        self.contact_box.delete("1.0", tk.END)
        for t in sorted(self.targets, key=lambda x: (-x.threat_level, x.id_str)):
            dist_nm = int(math.hypot(t.x, t.y) * 450)
            az      = int(math.degrees(math.atan2(-t.y, t.x)) % 360)
            alt_s   = f"FL{t.altitude//100:03d}" if t.altitude > 0 else "SFC"
            thr_s   = ["  OK  ", " WATCH", "ALLERTA"][t.threat_level]
            line = (f" {t.id_str:<10} {t.label:<8} {t.iff:<6} "
                    f"{dist_nm:>4}NM {az:>3}°  {alt_s:<7} "
                    f"{t.speed_knots:>4}kt {t.heading:>3}°  {thr_s}\n")
            tag = "alert" if t.threat_level == 2 else \
                  "warn"  if t.threat_level == 1 else \
                  "cyan"  if t.label == "DRONE"  else ""
            if self.selected and t.id_str == self.selected.id_str:
                tag = "sel"
            self.contact_box.insert(tk.END, line, tag)
        self.contact_box.config(state=tk.DISABLED)

    def _update_detail(self):
        t = self.selected
        if not t:
            for lbl in [self.d_id, self.d_tipo, self.d_iff, self.d_alt,
                        self.d_vel, self.d_hdg, self.d_dist, self.d_thr]:
                lbl.config(text="—", fg=G_DIM)
            return
        dist_nm = int(math.hypot(t.x, t.y) * 450)
        alt_s   = f"FL{t.altitude//100:03d} ({t.altitude} ft)" if t.altitude else "SFC (0 ft)"
        thr_s   = ["NESSUNA", "SORVEGLIANZA", "⚠ ALLERTA"][t.threat_level]
        thr_c   = [G_MID, AMBER, RED][t.threat_level]
        self.d_id.config(  text=f"{t.id_str}  /  {t.callsign}", fg=CYAN)
        self.d_tipo.config(text=f"{t.icon}  {t.label}", fg=t.color)
        self.d_iff.config( text=t.iff, fg=G_BRIGHT)
        self.d_alt.config( text=alt_s, fg=G_BRIGHT)
        self.d_vel.config( text=f"{t.speed_knots} kt", fg=G_BRIGHT)
        self.d_hdg.config( text=f"{t.heading:03d}°", fg=G_BRIGHT)
        self.d_dist.config(text=f"{dist_nm} NM", fg=G_BRIGHT)
        self.d_thr.config( text=thr_s, fg=thr_c)

    # ══════════════════════════════════════════════════════════════════════════
    #  DISEGNO RADAR
    # ══════════════════════════════════════════════════════════════════════════
    def _draw(self):
        c = self.canvas
        c.delete("all")
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 10 or H < 10: return

        # Radar ancorato a sinistra: centro a 1/2 altezza, x = R + margine
        R = int(min(W - 20, H - 60) * 0.46)
        cx = R + 15
        cy = H // 2

        self._draw_bg(c, cx, cy, R)
        self._draw_grid(c, cx, cy, R)
        self._draw_sweep(c, cx, cy, R)
        self._draw_noise(c, cx, cy, R)
        self._draw_targets(c, cx, cy, R)
        self._draw_hud(c, cx, cy, R, W, H)

    def _draw_bg(self, c, cx, cy, R):
        # Gradiente sfondo (simulato con cerchi)
        for i in range(8, 0, -1):
            r_ = R * i // 7
            shade = 3 + i * 3
            col = f"#00{min(shade,25):02x}00"
            c.create_oval(cx-r_, cy-r_, cx+r_, cy+r_, fill=col, outline="")
        c.create_oval(cx-R, cy-R, cx+R, cy+R, outline=G_MID, width=2, fill="#000800")
        # Anello esterno decorativo
        c.create_oval(cx-R-4, cy-R-4, cx+R+4, cy+R+4,
                      outline=BORDER, width=1, fill="")

    def _draw_grid(self, c, cx, cy, R):
        # Anelli distanza
        for i in range(1, 5):
            r_ = R * i // 4
            nm = 450 * i // 4
            c.create_oval(cx-r_, cy-r_, cx+r_, cy+r_, outline=G_GRID, width=1)
            c.create_text(cx + r_ + 3, cy - 10, text=f"{nm}NM",
                          fill=G_DIM, font=("Courier New", 8), anchor=tk.W)
        # Raggi ogni 30°
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            x1 = cx + int(R * 0.04 * cos_r); y1 = cy - int(R * 0.04 * sin_r)
            x2 = cx + int(R * cos_r);         y2 = cy - int(R * sin_r)
            thick = 2 if deg % 90 == 0 else 1
            col   = G_DIM if deg % 90 == 0 else G_GRID
            c.create_line(x1, y1, x2, y2, fill=col, width=thick)
            lx = cx + int((R + 16) * cos_r)
            ly = cy - int((R + 16) * sin_r)
            if deg % 90 == 0:
                lbl = {0:"E",90:"N",180:"W",270:"S"}[deg]
                c.create_text(lx, ly, text=lbl, fill=G_MID, font=("Courier New", 11, "bold"))
            elif deg % 30 == 0:
                c.create_text(lx, ly, text=str(deg), fill=G_DIM, font=("Courier New", 7))
        # Croce centrale
        for dx, dy in [(-8,0),(8,0),(0,-8),(0,8)]:
            c.create_line(cx+dx//2, cy+dy//2, cx+dx, cy+dy, fill=G_BRIGHT, width=1)
        c.create_oval(cx-2, cy-2, cx+2, cy+2, fill=G_BRIGHT, outline=G_BRIGHT)

    def _draw_sweep(self, c, cx, cy, R):
        sweep_rad = math.radians(self.sweep_angle)
        # Fanale: 70 linee con dissolvenza
        for i in range(70):
            past = self.sweep_angle - i
            a = math.radians(past)
            alpha = (70 - i) / 70.0
            g = int(alpha * 0x55)
            col = f"#00{g:02x}00"
            x2 = cx + int(R * math.cos(a))
            y2 = cy - int(R * math.sin(a))
            w_ = max(1, int(alpha * 3))
            c.create_line(cx, cy, x2, y2, fill=col, width=w_)
        # Linea principale
        x2 = cx + int(R * math.cos(sweep_rad))
        y2 = cy - int(R * math.sin(sweep_rad))
        c.create_line(cx, cy, x2, y2, fill=G_BRIGHT, width=2)
        # Punta brillante
        c.create_oval(x2-3, y2-3, x2+3, y2+3, fill=G_BRIGHT, outline="")

    def _draw_noise(self, c, cx, cy, R):
        for (nx, ny, br) in self.noise_dots:
            if math.hypot(nx, ny) > 0.95: continue
            if self.frame_count % 5 == 0 and random.random() < 0.15: continue
            px = cx + int(nx * R)
            py = cy + int(ny * R)
            g = int(br * 0x16)
            c.create_oval(px, py, px+1, py+1, fill=f"#00{g:02x}00", outline="")

    def _draw_targets(self, c, cx, cy, R):
        for t in self.targets:
            px = cx + int(t.x * R)
            py = cy + int(t.y * R)

            # Scia
            if len(t.trail) > 1:
                for i in range(len(t.trail)-1):
                    alpha = (i+1)/len(t.trail)
                    sx = cx + int(t.trail[i][0] * R)
                    sy = cy + int(t.trail[i][1] * R)
                    sx2= cx + int(t.trail[i+1][0] * R)
                    sy2= cy + int(t.trail[i+1][1] * R)
                    g = int(alpha * 0x66)
                    if   t.color == G_BRIGHT: scol = f"#00{g:02x}00"
                    elif t.color == AMBER:    scol = f"#{g:02x}{g//2:02x}00"
                    elif t.color == RED:      scol = f"#{g:02x}0000"
                    else:                     scol = f"00{g:02x}{g:02x}"
                    c.create_line(sx, sy, sx2, sy2, fill=scol, width=1)

            if t.angle_visible < -990 and t.blink == 0:
                continue

            visible = t.blink > 0
            s = t.size + (1 if visible else 0)
            col = t.color if visible else G_DIM

            is_sel = self.selected and t.id_str == self.selected.id_str

            if visible:
                # Glow per minacce
                if t.threat_level == 2:
                    gl = s * 4 + (4 if self.frame_count % 10 < 5 else 0)
                    c.create_oval(px-gl, py-gl, px+gl, py+gl,
                                  fill="", outline=RED_DIM, width=2)
                elif t.threat_level == 1:
                    c.create_oval(px-s*3, py-s*3, px+s*3, py+s*3,
                                  fill="", outline=AMBER_DIM, width=1)

                # Halo selected
                if is_sel:
                    c.create_oval(px-s*3-2, py-s*3-2, px+s*3+2, py+s*3+2,
                                  fill="", outline=WHITE_G, width=1, dash=(4,3))

                # Punto
                c.create_oval(px-s, py-s, px+s, py+s, fill=col, outline=col)
                # Croce direzionale
                hdg_r = math.radians(t.heading)
                ex = px + int(s*3 * math.cos(hdg_r))
                ey = py - int(s*3 * math.sin(hdg_r))
                c.create_line(px, py, ex, ey, fill=col, width=1, arrow=tk.LAST, arrowshape=(5,6,2))

                # Etichetta
                c.create_text(px+s+5, py-s-4,
                              text=t.id_str, fill=col, font=("Courier New", 7))
                c.create_text(px+s+5, py+3,
                              text=f"{t.callsign}", fill=G_DIM, font=("Courier New", 6))
                if t.altitude > 0:
                    c.create_text(px+s+5, py+11,
                                  text=f"FL{t.altitude//100:03d}", fill=G_DIM, font=("Courier New", 6))
            else:
                c.create_oval(px-s, py-s, px+s, py+s, fill=G_DIM, outline="")

    def _draw_hud(self, c, cx, cy, R, W, H):
        # Info angolo sweep
        ay = cy - R - 32
        c.create_text(cx, ay, text=f"AZ {self.sweep_angle:06.2f}°",
                      fill=G_MID, font=("Courier New", 10, "bold"))
        # Posizione
        c.create_text(cx, ay + 16, text="40°41'22\"N  14°47'09\"E",
                      fill=G_DIM, font=("Courier New", 8))
        # Basso: meteo
        c.create_text(cx, cy + R + 14,
                      text=f"VENTO {self.wind_dir:03d}°/{self.wind_speed}kt  "
                           f"TEMP {self.temperature}°C  PRES {self.pressure}hPa",
                      fill=G_DIM, font=("Courier New", 8))
        # Cornice interna radar
        margin = 4
        c.create_rectangle(cx-R-margin, cy-R-margin, cx+R+margin, cy+R+margin,
                           outline=G_GRID, width=1, dash=(6, 6))
        # Scanlines CRT
        for y_l in range(0, H, 4):
            c.create_line(0, y_l, cx+R+20, y_l, fill="#000800",
                          width=1, stipple="gray12")

    # ══════════════════════════════════════════════════════════════════════════
    #  INTERAZIONE
    # ══════════════════════════════════════════════════════════════════════════
    def _on_click(self, event):
        W = self.canvas.winfo_width()
        H = self.canvas.winfo_height()
        R = int(min(W-20, H-60) * 0.46)
        cx = R + 15; cy = H // 2

        # Trova bersaglio più vicino al click
        best, best_d = None, 20
        for t in self.targets:
            px = cx + int(t.x * R)
            py = cy + int(t.y * R)
            d = math.hypot(event.x - px, event.y - py)
            if d < best_d:
                best_d, best = d, t
        self.selected = best
        if best:
            self._log(f"SELEZIONATO: {best.id_str} [{best.label}] {best.callsign}", "info")

    # ══════════════════════════════════════════════════════════════════════════
    #  LOG
    # ══════════════════════════════════════════════════════════════════════════
    def _log(self, msg, tag="info"):
        ts = time.strftime("%H:%M:%S")
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, f"[{ts}] {msg}\n", tag)
        self.log_box.see(tk.END)
        lines = int(self.log_box.index(tk.END).split(".")[0])
        if lines > 60:
            self.log_box.delete("1.0", "8.0")
        self.log_box.config(state=tk.DISABLED)

    # ══════════════════════════════════════════════════════════════════════════
    #  FULLSCREEN / ESC
    # ══════════════════════════════════════════════════════════════════════════
    def _toggle_fs(self, e=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def _on_esc(self, e=None):
        if self.fullscreen: self._toggle_fs()
        else: self.root.quit()


# ─── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    RadarApp(root)
    root.update_idletasks()
    root.mainloop()
