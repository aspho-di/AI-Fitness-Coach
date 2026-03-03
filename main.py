"""
AI Fitness Coach — PyQt6 application
Run: python main.py
Requires: pip install PyQt6
"""
import sys, os, time, cv2, numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QFileDialog, QSizePolicy, QGraphicsDropShadowEffect,
    QSpacerItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize
from PyQt6.QtGui import QImage, QPixmap, QFont, QPainter, QColor, QPen, QPalette, QLinearGradient, QBrush

sys.path.insert(0, os.path.dirname(__file__))

def resource_path(rel):
    """Resolves resource path for both .py and PyInstaller .exe."""
    import sys, os
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

# Color palette  
C = {
    "bg":       "#060a0e",
    "panel":    "#0d1a24",
    "panel2":   "#101f2c",
    "border":   "#1a2e3e",
    "border2":  "#223040",
    "neon":     "#00e5a0",
    "neon2":    "#00b4d8",
    "red":      "#ff3b5c",
    "amber":    "#ffb703",
    "muted":    "#4a6070",
    "white":    "#dce8f0",
    "dim":      "#1e2e3a",
}

# QSS Styles
GLOBAL_STYLE = f"""
* {{
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
}}
QMainWindow, QWidget#root {{
    background: {C['bg']};
}}
QWidget {{
    color: {C['white']};
}}
"""

BTN_PRIMARY = f"""
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #0a2018, stop:1 #050f0c);
    color: {C['neon']};
    border: 1px solid #1a4030;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 3px;
    padding: 0 28px;
    min-height: 48px;
    text-transform: uppercase;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #0f3025, stop:1 #081a12);
    border: 1px solid {C['neon']};
    color: {C['neon']};
}}
QPushButton:pressed {{
    background: #040d0a;
    border: 1px solid #009060;
}}
"""

BTN_SECONDARY = f"""
QPushButton {{
    background: {C['panel2']};
    color: {C['muted']};
    border: 1px solid {C['dim']};
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    padding: 0 16px;
    min-height: 40px;
}}
QPushButton:hover {{
    background: #162028;
    border: 1px solid #3a5060;
    color: #8ab0c0;
}}
QPushButton:pressed {{
    background: {C['panel']};
}}
"""

BTN_MENU = f"""
QPushButton {{
    background: {C['panel2']};
    color: {C['muted']};
    border: 1px solid {C['dim']};
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    min-width: 80px;
    min-height: 44px;
}}
QPushButton:hover {{
    background: #162028;
    border: 1px solid {C['neon']};
    color: {C['neon']};
}}
"""

# Utilities 
def make_shadow(widget, color=C['neon'], blur=20, alpha=80):
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setOffset(0, 0)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    widget.setGraphicsEffect(fx)
    return fx

def neon_label(text, color=None, size=24, mono=True, parent=None):
    lbl = QLabel(text, parent)
    if color is None: color = C['neon']
    font_family = "Consolas, 'Courier New', monospace" if mono else "'Segoe UI', Arial"
    lbl.setStyleSheet(f"""
        color: {color};
        font-family: Consolas, 'Courier New', monospace;
        font-size: {size}px;
        font-weight: 700;
        letter-spacing: 3px;
        background: transparent;
    """)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    make_shadow(lbl, color, 16, 100)
    return lbl

def muted_label(text, size=10, parent=None):
    lbl = QLabel(text, parent)
    lbl.setStyleSheet(f"""
        color: {C['muted']};
        font-size: {size}px;
        letter-spacing: 3px;
        text-transform: uppercase;
        background: transparent;
    """)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl

def hsep():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {C['border2']}; background: {C['border2']}; max-height: 1px;")
    return line

def vsep():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFixedWidth(1)
    line.setStyleSheet(f"background: {C['border']}; margin: 8px 0;")
    return line

# HUD panel with corner accents
class HudPanel(QFrame):
    """Panel with neon corner markers and glowing border."""
    def __init__(self, parent=None, accent=None, corner=20):
        super().__init__(parent)
        self._accent = QColor(accent or C['neon'])
        self._corner = corner
        self.setStyleSheet(f"""
            QFrame {{
                background: {C['panel']};
                border: 1px solid {C['border2']};
                border-radius: 10px;
            }}
        """)

    def paintEvent(self, e):
        super().paintEvent(e)
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r  = self.rect().adjusted(1, 1, -1, -1)
        cs = self._corner
        ac = self._accent

        # Layered glow on corner lines
        for width, alpha in [(6, 18), (4, 30), (2, 60), (2, 255)]:
            gc = QColor(ac)
            gc.setAlpha(alpha)
            pen = QPen(gc, width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            # All 4 corners
            segs = [
                (r.left(), r.top() + cs,   r.left(),      r.top(),       r.left() + cs,  r.top()),
                (r.right()-cs, r.top(),     r.right(),     r.top(),       r.right(),      r.top() + cs),
                (r.left(), r.bottom()-cs,   r.left(),      r.bottom(),    r.left() + cs,  r.bottom()),
                (r.right()-cs, r.bottom(),  r.right(),     r.bottom(),    r.right(),      r.bottom()-cs),
            ]
            for x1,y1,mx,my,x2,y2 in segs:
                p.drawLine(QPoint(x1,y1), QPoint(mx,my))
                p.drawLine(QPoint(mx,my), QPoint(x2,y2))
        p.end()

# Video frame widget
class VideoWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: #000; border: none;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 180)

    def show_frame(self, bgr):
        if bgr is None: return
        h, w = bgr.shape[:2]
        vw = max(self.width(),  1)
        vh = max(self.height(), 1)
        scale = min(vw/w, vh/h)
        nw, nh = int(w*scale), int(h*scale)
        frame = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_LINEAR)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img   = QImage(rgb.data, nw, nh, nw*3, QImage.Format.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(img))

# Worker thread
class Worker(QThread):
    preview_frame  = pyqtSignal(object)
    calib_frame    = pyqtSignal(object)
    calib_done     = pyqtSignal(float, float)
    analysis_frame = pyqtSignal(object)
    hud            = pyqtSignal(int, str, str, str, int, int, bool, list, int)
    # hud: counter, stage, feedback, color_hex, fps, back_angle, back_ok, warnings, depth_pct
    ended          = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._source   = None
        self._path     = ''
        self._mode     = None
        self._alive    = True
        self._up       = 140.0
        self._dn       = 90.0

    def setup(self, source, path=''):
        self._source = source
        self._path   = path

    def go_preview(self):   self._mode = 'preview'
    def go_calibrate(self): self._mode = 'calibrate'
    def go_analyze(self, up=None, dn=None):
        if up is not None: self._up = up
        if dn is not None: self._dn = dn
        self._mode = 'analyze'

    def stop(self):
        self._alive = False
        self.wait(2000)

    def run(self):
        from pose_detector import PoseDetector
        from angle_calculator import (calculate_angle_3d, calculate_back_angle,
            calculate_knee_deviation_3d, estimate_camera_angle, get_best_leg)
        from ui_renderer import UIRenderer

        renderer = UIRenderer()
        detector = PoseDetector(0.7, 0.7)
        cap = (cv2.VideoCapture(0) if self._source == 'webcam'
               else cv2.VideoCapture(self._path))

        if not cap.isOpened():
            self._alive = False; return

        # Pass source FPS to detector for accurate timestamps
        src_fps = cap.get(cv2.CAP_PROP_FPS)
        detector.set_fps(src_fps if src_fps > 0 else 30.0)

        # Grab first frame for video preview
        if self._source == 'video':
            ok, first = cap.read()
            if ok: self.preview_frame.emit(first)

        # Preview loop
        while self._alive and self._mode == 'preview':
            if self._source == 'webcam':
                ok, f = cap.read()
                if ok: self.preview_frame.emit(f)
            self.msleep(30)

        # Calibration
        if self._alive and self._mode == 'calibrate':
            up_a  = self._cal_phase(cap, detector, renderer, 'UP')
            dn_a  = self._cal_phase(cap, detector, renderer, 'DOWN')
            # Emit raw angles — thresholds are computed in go_analyze
            self.calib_done.emit(round(up_a, 1), round(dn_a, 1))
            self._mode = None
            while self._alive and self._mode is None:
                self.msleep(30)

        # ── Analysis: squat rep counter ─────────────────────────────────────
        #
        # Uses relative hysteresis — independent of absolute angle thresholds.
        #
        # After calibration we know standing_angle and squat_angle.
        # A rep is counted when:
        #   1. Angle drops below UP_THRESH (= standing * 0.85)  → enter DOWN
        #   2. Angle rises back above UP_THRESH                  → exit DOWN
        #   3. Minimum angle during DOWN was <= DN_THRESH (= avg of standing + squat)
        #
        # Works at any camera angle — thresholds adapt to the user's
        # actual standing angle, not fixed values like 140°/90°.

        counter           = 0
        stage             = None      # None | 'UP' | 'DOWN'
        min_angle_reached = 360.0
        angle_buf         = []
        BUF_SIZE          = 5

        # Thresholds from calibration; use defaults if not calibrated
        # self._up = standing angle  (calibrated ~160°, default 140°)
        # self._dn = squat angle     (calibrated ~70°,  default 90°)
        standing = self._up
        squatting = self._dn

        # UP_THRESH: angle above which = "standing"  (85% of standing angle)
        # DN_THRESH: minimum angle required to count a rep (midpoint of range)
        UP_THRESH = round(standing * 0.85, 1)
        DN_THRESH = round((standing + squatting) / 2.0, 1)

        # Ensure minimum gap between thresholds
        if UP_THRESH - DN_THRESH < 20:
            DN_THRESH = UP_THRESH - 20

        print(f"[Analyze] standing={standing} squatting={squatting} UP_THRESH={UP_THRESH} DN_THRESH={DN_THRESH}")

        fps_t = time.time(); fps_n = 0; fps = 0
        BACK_LIM, KNEE_LIM = 35, 0.15
        current_leg = 'left'

        while self._alive and self._mode == 'analyze':
            ok, frame = cap.read()
            if not ok:
                self.ended.emit(counter)
                break

            results     = detector.process_frame(frame)
            detector.draw_skeleton(frame, results)
            current_leg = get_best_leg(results, current_leg)
            lm          = detector.get_landmarks(results, frame.shape, leg=current_leg)

            feedback = "Stand in front of camera"
            fb_color = C['amber']
            angle    = 0.0
            warnings = []
            back_ang = 0
            back_ok  = True

            if lm:
                raw = calculate_angle_3d(lm['hip_3d'], lm['knee_3d'], lm['ankle_3d'])
                back_ang = calculate_back_angle(lm['shoulder'], lm['hip'])
                knee_dev = calculate_knee_deviation_3d(lm['knee_3d'], lm['ankle_3d'], lm['hip_3d'])
                back_ok  = back_ang <= BACK_LIM

                angle_buf.append(raw)
                if len(angle_buf) > BUF_SIZE:
                    angle_buf.pop(0)
                angle = sum(angle_buf) / len(angle_buf)

                # Track minimum angle while not in UP
                if stage != 'UP':
                    min_angle_reached = min(min_angle_reached, angle)

                if stage == 'DOWN':
                    if not back_ok:
                        warnings.append('Round back')
                    if knee_dev < -KNEE_LIM:
                        warnings.append('Knees caving in')

                # State machine
                if angle > UP_THRESH:
                    if stage == 'DOWN':
                        if min_angle_reached <= DN_THRESH:
                            counter += 1
                            feedback = f"Rep #{counter}!"
                            fb_color = C['neon']
                            print(f"[REP] #{counter}  min={min_angle_reached:.1f}  DN={DN_THRESH}")
                        else:
                            feedback = f"Go deeper next time ({int(min_angle_reached)}° > {int(DN_THRESH)}°)"
                            fb_color = C['red']
                        min_angle_reached = 360.0
                    else:
                        feedback = "Ready — squat down!"
                        fb_color = C['neon']
                    stage = 'UP'

                elif angle < DN_THRESH:
                    stage    = 'DOWN'
                    feedback = "Good — stand up!"
                    fb_color = C['neon']

                else:
                    if stage == 'DOWN':
                        feedback = f"Stand up!  {int(angle)}° → {int(UP_THRESH)}°"
                        fb_color = C['neon']
                    elif stage == 'UP':
                        feedback = f"Squat down!  {int(angle)}° → {int(DN_THRESH)}°"
                        fb_color = C['neon']
                    else:
                        feedback = "Ready — squat down!"
                        fb_color = C['neon']

                col_bgr = tuple(int(fb_color.lstrip('#')[i:i+2], 16) for i in (4, 2, 0))
                renderer.draw_joint_lines(frame, lm['hip'], lm['knee'], lm['ankle'], col_bgr)
                renderer.draw_angle(frame, lm['knee'], angle, col_bgr)
            else:
                angle_buf = []

            renderer.draw_form_warnings(frame, warnings)
            pct = int(max(0, min(100, (UP_THRESH - max(DN_THRESH, min(UP_THRESH, angle))) /
                                       max(1, UP_THRESH - DN_THRESH) * 100)))
            fps_n += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_n; fps_n = 0; fps_t = time.time()

            self.analysis_frame.emit(frame)
            self.hud.emit(counter, stage or '', feedback, fb_color, fps,
                          int(back_ang), bool(back_ok), warnings, pct)
            self.msleep(1)

        cap.release()

    def _cal_phase(self, cap, detector, renderer, phase):
        from angle_calculator import calculate_angle_3d, get_best_leg
        import numpy as np
        deadline = time.time() + 3
        while time.time() < deadline:
            ok, f = cap.read()
            if not ok: break
            renderer.draw_calibration_overlay(f, phase, int(deadline-time.time())+1)
            self.calib_frame.emit(f)
            self.msleep(30)
        angles = []; deadline = time.time() + 2
        while time.time() < deadline:
            ok, f = cap.read()
            if not ok: break
            res = detector.process_frame(f)
            leg = get_best_leg(res)
            lm  = detector.get_landmarks(res, f.shape, leg=leg)
            a   = None
            if lm:
                a = calculate_angle_3d(lm['hip_3d'], lm['knee_3d'], lm['ankle_3d'])
                angles.append(a)
            renderer.draw_calibration_overlay(f, phase, 0, a)
            self.calib_frame.emit(f)
            self.msleep(30)
        return float(np.median(angles)) if angles else (160.0 if phase=='UP' else 70.0)

#  SCREENS

# Source selection screen
class MenuScreen(QWidget):
    sig_webcam = pyqtSignal()
    sig_video  = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName('root')
        self.setStyleSheet(f"background: {C['bg']};")

        # Background animation timer
        self._tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(50)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = HudPanel(accent=C['neon'], corner=22)
        panel.setFixedSize(460, 340)

        inner = QVBoxLayout(panel)
        inner.setContentsMargins(44, 40, 44, 40)
        inner.setSpacing(0)

        # Title
        title = neon_label("AI FITNESS COACH", C['neon'], 22)
        inner.addWidget(title)
        inner.addSpacing(8)

        sub = muted_label("SELECT INPUT SOURCE", 10)
        inner.addWidget(sub)
        inner.addSpacing(20)
        inner.addWidget(hsep())
        inner.addSpacing(24)

        btn_w = QPushButton("WEBCAM")
        btn_w.setStyleSheet(BTN_PRIMARY)
        btn_w.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_w.clicked.connect(self.sig_webcam.emit)
        inner.addWidget(btn_w)
        inner.addSpacing(12)

        btn_v = QPushButton("VIDEO FILE")
        btn_v.setStyleSheet(BTN_PRIMARY)
        btn_v.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_v.clicked.connect(self._pick)
        inner.addWidget(btn_v)

        root.addWidget(panel)

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select video", "",
            "Video (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All (*.*)")
        if path: self.sig_video.emit(path)

    def _on_tick(self):
        self._tick = (self._tick + 1) % 400
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Dot grid with subtle drift animation
        spacing = 36
        offset = (self._tick * 0.15) % spacing
        c_dot = QColor(C['neon'])
        c_dot.setAlpha(22)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c_dot))
        gx = -spacing
        while gx < w + spacing:
            gy = -spacing
            while gy < h + spacing:
                dx = int(gx + offset)
                dy = int(gy + offset)
                p.drawEllipse(QPoint(dx, dy), 1, 1)
                gy += spacing
            gx += spacing

        # Screen corner accents
        cs = 50
        for width, alpha in [(7, 8), (4, 20), (2, 70)]:
            ac = QColor(C['neon'])
            ac.setAlpha(alpha)
            pen = QPen(ac, width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            segs = [
                (0, cs, 0, 0, cs, 0),
                (w-cs, 0, w, 0, w, cs),
                (0, h-cs, 0, h, cs, h),
                (w-cs, h, w, h, w, h-cs),
            ]
            for x1,y1,mx,my,x2,y2 in segs:
                p.drawLine(QPoint(x1,y1), QPoint(mx,my))
                p.drawLine(QPoint(mx,my), QPoint(x2,y2))

        # Thin horizontal scan lines
        for y_frac in [0.25, 0.5, 0.75]:
            lc = QColor(C['neon'])
            lc.setAlpha(12)
            p.setPen(QPen(lc, 1))
            p.drawLine(0, int(h * y_frac), w, int(h * y_frac))

        p.end()

# Preview screen
class PreviewScreen(QWidget):
    sig_confirm = pyqtSignal()
    sig_back    = pyqtSignal()

    def __init__(self, title="CAMERA READY", btn_text="START CALIBRATION"):
        super().__init__()
        self.setStyleSheet(f"background: #000;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.video = VideoWidget()
        layout.addWidget(self.video)

        # Bottom action bar
        bar = QFrame()
        bar.setFixedHeight(90)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {C['panel']};
                border-top: 2px solid {C['neon']};
                border-radius: 0;
            }}
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(20, 0, 20, 0)
        bl.setSpacing(16)

        btn_back = QPushButton("← MENU")
        btn_back.setStyleSheet(BTN_SECONDARY)
        btn_back.setFixedWidth(110)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.sig_back.emit)

        info = QVBoxLayout()
        info.setSpacing(4)
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet(f"""
            color: {C['neon']}; font-family: Consolas, monospace;
            font-size: 15px; font-weight: 700; letter-spacing: 3px;
            background: transparent;
        """)
        self.lbl_sub = QLabel("Stand in front of camera and click the button")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet(f"color: {C['muted']}; font-size: 12px; background: transparent;")
        info.addWidget(self.lbl_title)
        info.addWidget(self.lbl_sub)

        btn_start = QPushButton(btn_text)
        btn_start.setStyleSheet(BTN_PRIMARY)
        btn_start.setMinimumWidth(220)
        btn_start.setFixedHeight(48)
        btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start.clicked.connect(self.sig_confirm.emit)

        bl.addWidget(btn_back)
        bl.addLayout(info, 1)
        bl.addWidget(btn_start)
        layout.addWidget(bar)

    def push(self, frame): self.video.show_frame(frame)
    def set_sub(self, t):  self.lbl_sub.setText(t)
    def set_title(self, t): self.lbl_title.setText(t)

# Analysis screen
class AnalysisScreen(QWidget):
    sig_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: #000;")
        self._warn_timer = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(68)
        header.setStyleSheet(f"""
            QFrame {{
                background: {C['panel']};
                border-bottom: none;
                border-radius: 0;
            }}
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        hl.setSpacing(14)

        self.btn_menu = QPushButton("MENU")
        self.btn_menu.setStyleSheet(BTN_MENU)
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.clicked.connect(self.sig_menu.emit)

        hl.addWidget(self.btn_menu)
        hl.addWidget(vsep())

        # Logo
        logo = QVBoxLayout()
        logo.setSpacing(0)
        t1 = QLabel("AI FITNESS")
        t1.setStyleSheet(f"color:{C['muted']}; font-size:9px; letter-spacing:3px; background:transparent;")
        t2 = QLabel("COACH")
        t2.setStyleSheet(f"color:{C['neon']}; font-family:Consolas,monospace; font-size:16px; font-weight:700; letter-spacing:3px; background:transparent;")
        logo.addWidget(t1); logo.addWidget(t2)
        hl.addLayout(logo)
        hl.addStretch(1)

        # Rep counter
        ctr = QVBoxLayout(); ctr.setSpacing(1)
        lbl_s = QLabel("SQUATS")
        lbl_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_s.setStyleSheet(f"color:{C['muted']}; font-size:9px; letter-spacing:4px; background:transparent;")
        self.lbl_counter = QLabel("0")
        self.lbl_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_counter.setStyleSheet(f"color:{C['white']}; font-family:Consolas,monospace; font-size:32px; font-weight:700; background:transparent;")
        ctr.addWidget(lbl_s); ctr.addWidget(self.lbl_counter)
        hl.addLayout(ctr)
        hl.addStretch(1)

        hl.addWidget(vsep())

        # Stage indicator
        stg = QVBoxLayout(); stg.setSpacing(2)
        lbl_st = QLabel("STAGE")
        lbl_st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_st.setStyleSheet(f"color:{C['muted']}; font-size:9px; letter-spacing:4px; background:transparent;")
        self.lbl_stage = QLabel("---")
        self.lbl_stage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stage.setStyleSheet(f"color:{C['muted']}; font-family:Consolas,monospace; font-size:18px; font-weight:700; background:transparent;")
        stg.addWidget(lbl_st); stg.addWidget(self.lbl_stage)
        hl.addLayout(stg)

        hl.addWidget(vsep())
        self.lbl_fps = QLabel("-- FPS")
        self.lbl_fps.setStyleSheet(f"color:{C['muted']}; font-size:10px; font-family:Consolas; background:transparent;")
        hl.addWidget(self.lbl_fps)

        layout.addWidget(header)

        # Video
        self.video = VideoWidget()
        layout.addWidget(self.video)

        # Depth bar overlaid on video (absolute positioning)
        self.depth_bar = QFrame(self.video)
        self.depth_bar.setGeometry(0, 0, 20, 160)
        self.depth_fill = QFrame(self.depth_bar)
        self.depth_fill.setStyleSheet(f"background:{C['neon']}; border-radius:3px;")
        self.depth_bar.setStyleSheet(f"background:{C['panel']}; border:1px solid {C['border']}; border-radius:4px;")

        # Bottom feedback bar
        self.fb_bar = QFrame()
        self.fb_bar.setFixedHeight(52)
        self._set_fb_style(C['neon'])
        fb_l = QHBoxLayout(self.fb_bar)
        fb_l.setContentsMargins(18, 0, 18, 0)
        fb_l.setSpacing(12)

        self.fb_dot = QLabel("●")
        self.fb_dot.setStyleSheet(f"color:{C['neon']}; font-size:10px; background:transparent;")
        self.fb_text = QLabel("Stand in front of camera")
        self.fb_text.setStyleSheet(f"color:{C['neon']}; font-size:14px; font-weight:600; background:transparent;")
        fb_l.addWidget(self.fb_dot)
        fb_l.addWidget(self.fb_text)
        fb_l.addStretch()

        self.lbl_back = QLabel()
        self.lbl_back.setStyleSheet(f"color:{C['muted']}; font-size:11px; font-family:Consolas; background:transparent;")
        fb_l.addWidget(self.lbl_back)

        layout.addWidget(self.fb_bar)

    def _set_fb_style(self, color):
        self.fb_bar.setStyleSheet(f"""
            QFrame {{
                background: {C['panel']};
                border-top: 2px solid {color};
                border-radius: 0;
            }}
        """)

    def push(self, frame):
        self.video.show_frame(frame)

    def reset(self):
        self.lbl_counter.setText("0")
        self.lbl_stage.setText("---")
        self.lbl_stage.setStyleSheet(f"color:{C['muted']}; font-family:Consolas,monospace; font-size:18px; font-weight:700; background:transparent;")
        self.fb_text.setText("Stand in front of camera")
        self.lbl_fps.setText("-- FPS")
        # Hide finish overlay left from previous session
        if hasattr(self, "_fin_overlay"):
            self._fin_overlay.hide()

    def update_hud(self, counter, stage, feedback, color, fps, back_ang, back_ok, warnings):
        self.lbl_counter.setText(str(counter))
        self.lbl_fps.setText(f"{fps} FPS")

        sc = C['neon'] if stage=='UP' else (C['neon2'] if stage=='DOWN' else C['muted'])
        self.lbl_stage.setText(stage or '---')
        self.lbl_stage.setStyleSheet(f"color:{sc}; font-family:Consolas,monospace; font-size:18px; font-weight:700; background:transparent;")

        self.fb_text.setText(feedback)
        self.fb_text.setStyleSheet(f"color:{color}; font-size:14px; font-weight:600; background:transparent;")
        self.fb_dot.setStyleSheet(f"color:{color}; font-size:10px; background:transparent;")
        self._set_fb_style(color)

        back_color = C['neon'] if back_ok else C['red']
        self.lbl_back.setText(f"BACK  {back_ang}°  {'✓' if back_ok else '!'}")
        self.lbl_back.setStyleSheet(f"color:{back_color}; font-size:11px; font-family:Consolas; background:transparent;")

    def set_depth(self, pct):
        bh  = self.depth_bar.height()
        fh  = int(bh * pct / 100)
        col = C["neon"] if pct>=95 else (C["amber"] if pct>50 else C["red"])
        self.depth_fill.setGeometry(1, bh-fh, 12, fh)
        self.depth_fill.setStyleSheet(f"background:{col}; border-radius:2px;")

    def show_finished(self, count):
        """Shows overlay on top of the last frame — window stays open."""
        if not hasattr(self, "_fin_overlay"):
            ov = QFrame(self)
            ov.setStyleSheet("background: rgba(6,10,14,210);")
            ov.hide()

            inner = QVBoxLayout(ov)
            inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inner.setSpacing(14)

            t1 = neon_label("ANALYSIS COMPLETE", C["neon"], 14)
            inner.addWidget(t1)

            line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet(f"color:{C['border2']}; background:{C['border2']}; max-height:1px;")
            inner.addWidget(line)
            inner.addSpacing(8)

            lbl_sub = muted_label("SQUATS PERFORMED", 10)
            inner.addWidget(lbl_sub)

            self._fin_count = QLabel("0")
            self._fin_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._fin_count.setStyleSheet(
                f"color:{C['white']}; font-family:Consolas,monospace; "
                f"font-size:96px; font-weight:700; background:transparent;"
            )
            inner.addWidget(self._fin_count)
            inner.addSpacing(8)

            btn = QPushButton("BACK TO MENU")
            btn.setStyleSheet(BTN_PRIMARY)
            btn.setFixedWidth(260)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.sig_menu.emit)
            inner.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

            self._fin_overlay = ov

        self._fin_count.setText(str(count))
        self._fin_overlay.setGeometry(self.rect())
        self._fin_overlay.show()
        self._fin_overlay.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        vh = self.video.height()
        bh = min(180, vh - 20)
        self.depth_bar.setGeometry(self.video.width() - 22, (vh - bh)//2, 14, bh)
        if hasattr(self, "_fin_overlay") and self._fin_overlay.isVisible():
            self._fin_overlay.setGeometry(self.rect())

# Results screen
class ResultsScreen(QWidget):
    sig_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{C['bg']};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel = HudPanel(accent=C['neon'], corner=22)
        panel.setFixedSize(400, 300)
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(44, 40, 44, 40)
        inner.setSpacing(8)

        inner.addWidget(neon_label("ANALYSIS COMPLETE", C['neon'], 14))
        inner.addWidget(hsep())
        inner.addSpacing(12)
        inner.addWidget(muted_label("SQUATS PERFORMED", 10))

        self.count_lbl = QLabel("0")
        self.count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_lbl.setStyleSheet(f"color:{C['white']}; font-family:Consolas,monospace; font-size:72px; font-weight:700; background:transparent;")
        inner.addWidget(self.count_lbl)

        inner.addSpacing(8)
        btn = QPushButton("BACK TO MENU")
        btn.setStyleSheet(BTN_PRIMARY)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.sig_menu.emit)
        inner.addWidget(btn)
        layout.addWidget(panel)

    def set_count(self, n): self.count_lbl.setText(str(n))

# Calibration overlay
class CalibOverlay(QWidget):
    """Fullscreen overlay shown on top of the analysis screen during calibration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet(f"background: rgba(6,10,14,220);")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self.lbl_step = muted_label("STEP 1 OF 2", 10)
        layout.addWidget(self.lbl_step)

        self.lbl_inst = neon_label("STAND STRAIGHT", C['neon'], 36)
        layout.addWidget(self.lbl_inst)
        layout.addSpacing(8)

        # Framed video preview
        self._frame_panel = HudPanel(accent=C['neon'], corner=16)
        self._frame_panel.setFixedSize(640, 360)
        fv = QVBoxLayout(self._frame_panel)
        fv.setContentsMargins(2, 2, 2, 2)
        self.video = VideoWidget()
        fv.addWidget(self.video)
        layout.addWidget(self._frame_panel)

    def show_frame(self, bgr): self.video.show_frame(bgr)
    def set_phase(self, phase):
        self.lbl_inst.setText("STAND STRAIGHT" if phase == "UP" else "SQUAT DOWN")
        self.lbl_step.setText("STEP 1 OF 2" if phase == "UP" else "STEP 2 OF 2")
        color = C['neon'] if phase == "UP" else C['neon2']
        self.lbl_inst.setStyleSheet(f"""
            color:{color}; font-family:Consolas,monospace;
            font-size:36px; font-weight:700; letter-spacing:4px; background:transparent;
        """)
    def resizeEvent(self, e):
        super().resizeEvent(e)
        available_h = max(180, self.height() - 160)
        available_w = max(320, self.width() - 40)
        panel_h = min(360, available_h)
        panel_w = min(640, available_w)
        if panel_w / panel_h > 16 / 9:
            panel_w = int(panel_h * 16 / 9)
        else:
            panel_h = int(panel_w * 9 / 16)
        self._frame_panel.setFixedSize(panel_w, panel_h)

#  MAIN WINDOW

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Fitness Coach")
        _ico = resource_path("icon.ico")
        if os.path.exists(_ico):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(_ico))
        self.resize(1280, 720)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(GLOBAL_STYLE)

        self._worker = None
        self._source = None

        self._stack   = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._menu    = MenuScreen()
        self._preview = PreviewScreen()
        self._analysis= AnalysisScreen()
        self._results = ResultsScreen()

        self._stack.addWidget(self._menu)     # 0
        self._stack.addWidget(self._preview)  # 1
        self._stack.addWidget(self._analysis) # 2
        self._stack.addWidget(self._results)  # 3

        self._calib_overlay = CalibOverlay(self._analysis)

        # Connect signals
        self._menu.sig_webcam.connect(lambda: self._start('webcam', ''))
        self._menu.sig_video.connect(lambda p: self._start('video', p))
        self._preview.sig_confirm.connect(self._on_confirm)
        self._preview.sig_back.connect(self._go_menu)
        self._analysis.sig_menu.connect(self._go_menu)
        self._results.sig_menu.connect(self._go_menu)

        self._stack.setCurrentIndex(0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self._update_calib_overlay)

    def _update_calib_overlay(self):
        self._calib_overlay.setGeometry(self._analysis.rect())
        if self._calib_overlay.isVisible():
            self._calib_overlay.raise_()

    # Navigation
    def _start(self, source, path):
        self._source = source
        fname = os.path.basename(path) if path else ""

        # Recreate preview screen with the correct text
        old = self._stack.widget(1)
        if source == 'webcam':
            self._preview = PreviewScreen("CAMERA READY", "START CALIBRATION")
        else:
            self._preview = PreviewScreen("VIDEO LOADED", "START ANALYSIS")
            self._preview.set_sub(fname)

        self._preview.sig_confirm.connect(self._on_confirm)
        self._preview.sig_back.connect(self._go_menu)
        self._stack.insertWidget(1, self._preview)
        self._stack.removeWidget(old)

        # Start worker thread
        self._stop_worker()
        self._worker = Worker()
        self._worker.setup(source, path)
        self._worker.preview_frame.connect(self._preview.push)
        self._worker.calib_frame.connect(self._on_calib_frame)
        self._worker.calib_done.connect(self._on_calib_done)
        self._worker.analysis_frame.connect(self._analysis.push)
        self._worker.hud.connect(self._on_hud)
        self._worker.ended.connect(self._on_ended)
        self._worker.go_preview()
        self._worker.start()

        self._stack.setCurrentWidget(self._preview)

    def _on_confirm(self):
        self._analysis.reset()
        self._stack.setCurrentWidget(self._analysis)
        if self._source == 'webcam':
            QTimer.singleShot(0, self._show_calib_overlay)
            self._worker.go_calibrate()
        else:
            self._worker.go_analyze()
    
    def _show_calib_overlay(self):
        self._calib_overlay.setGeometry(self._analysis.rect())
        self._calib_overlay.show()
        self._calib_overlay.raise_()

    def _go_menu(self):
        self._calib_overlay.hide()
        self._stop_worker()
        self._stack.setCurrentWidget(self._menu)

    # Slots
    def _on_calib_frame(self, f):
        self._calib_overlay.show_frame(f)

    def _on_calib_done(self, up, dn):
        self._calib_overlay.hide()
        self._worker.go_analyze(up, dn)

    def _on_hud(self, counter, stage, feedback, color, fps, back_ang, back_ok, warnings, pct):
        self._analysis.update_hud(counter, stage, feedback, color, fps, back_ang, back_ok, warnings)
        self._analysis.set_depth(pct)

    def _on_ended(self, counter):
        self._stop_worker()
        self._analysis.show_finished(counter)
    def _stop_worker(self):
        if self._worker:
            self._worker.stop()
            self._worker = None

    def closeEvent(self, e):
        self._stop_worker(); super().closeEvent(e)

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key.Key_Escape:
            self._go_menu()
        elif k in (Qt.Key.Key_F11, Qt.Key.Key_F):
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()


# Entry point
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,      QColor(C['bg']))
    palette.setColor(QPalette.ColorRole.WindowText,  QColor(C['white']))
    palette.setColor(QPalette.ColorRole.Base,        QColor(C['panel']))
    palette.setColor(QPalette.ColorRole.Button,      QColor(C['panel2']))
    palette.setColor(QPalette.ColorRole.ButtonText,  QColor(C['white']))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()