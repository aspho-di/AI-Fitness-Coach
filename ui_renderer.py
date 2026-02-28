import cv2
import numpy as np


class UIRenderer:
    """
    Класс для отрисовки современного HUD интерфейса на кадре.
    Минималистичный спортивный дизайн с чёткими линиями.
    """

    # ── Цветовая палитра ───────────────────────────────────────────────────
    COLOR_GREEN   = (0, 255, 140)
    COLOR_RED     = (50, 60, 255)
    COLOR_WHITE   = (255, 255, 255)
    COLOR_YELLOW  = (0, 220, 255)
    COLOR_ORANGE  = (0, 165, 255)
    COLOR_DARK    = (12, 15, 22)
    COLOR_BLUE    = (255, 180, 0)
    COLOR_ACCENT  = (0, 245, 160)
    COLOR_MUTED   = (100, 110, 130)
    COLOR_BG      = (10, 13, 20)

    FONT_MONO  = cv2.FONT_HERSHEY_DUPLEX
    FONT_PLAIN = cv2.FONT_HERSHEY_SIMPLEX

    def _draw_rounded_rect(self, frame, x1, y1, x2, y2, color, alpha=0.75, radius=6):
        """Полупрозрачный прямоугольник с закруглёнными углами."""
        overlay = frame.copy()
        # Рисуем заполненный прямоугольник
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        # Скруглённые углы через круги
        for cx, cy in [(x1+radius, y1+radius), (x2-radius, y1+radius),
                       (x1+radius, y2-radius), (x2-radius, y2-radius)]:
            cv2.circle(overlay, (cx, cy), radius, color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

    def _draw_outlined_text(self, frame, text, pos, font, scale, color, thickness=2):
        """Текст с тонкой тёмной обводкой для читаемости на любом фоне."""
        x, y = pos
        cv2.putText(frame, text, (x+1, y+1), font, scale, (0, 0, 0), thickness+2, cv2.LINE_AA)
        cv2.putText(frame, text, pos, font, scale, color, thickness, cv2.LINE_AA)

    def _draw_accent_line(self, frame, x1, y, x2, color=None):
        """Тонкая акцентная линия-разделитель."""
        if color is None:
            color = self.COLOR_ACCENT
        cv2.line(frame, (x1, y), (x2, y), color, 1, cv2.LINE_AA)

    # ── Основные элементы ─────────────────────────────────────────────────

    def draw_button(self, frame, label, x1, y1, x2, y2, mouse_pos=None, style='primary'):
        """
        Универсальная кнопка. style: 'primary' (зелёная) или 'secondary' (серая).
        Возвращает True если курсор над кнопкой.
        """
        mx, my = (mouse_pos[0], mouse_pos[1]) if mouse_pos else (-1, -1)
        hover  = x1 <= mx <= x2 and y1 <= my <= y2

        if style == 'primary':
            bg_n  = (0, 45, 28)
            bg_h  = (0, 75, 48)
            brd_n = (0, 160, 90)
            brd_h = (0, 245, 140)
            txt_n = (0, 200, 110)
            txt_h = (0, 245, 140)
        else:  # secondary
            bg_n  = (22, 24, 32)
            bg_h  = (35, 38, 52)
            brd_n = (70, 75, 95)
            brd_h = (130, 140, 170)
            txt_n = (130, 140, 160)
            txt_h = (200, 210, 230)

        bg  = bg_h  if hover else bg_n
        brd = brd_h if hover else brd_n
        txt = txt_h if hover else txt_n

        # Фон
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), bg, -1)
        cv2.addWeighted(overlay, 0.92, frame, 0.08, 0, frame)
        # Рамка
        cv2.rectangle(frame, (x1, y1), (x2, y2), brd, 2 if hover else 1)

        # Текст по центру кнопки
        scale = 0.72
        tw, th = cv2.getTextSize(label, self.FONT_MONO, scale, 2)[0]
        tx = x1 + (x2 - x1) // 2 - tw // 2
        ty = y1 + (y2 - y1) // 2 + th // 2
        cv2.putText(frame, label, (tx, ty), self.FONT_MONO, scale, txt, 2, cv2.LINE_AA)

        return hover

    def draw_joint_lines(self, frame, hip, knee, ankle, color):
        """Рисует сегменты ноги с градиентным эффектом через несколько линий."""
        # Основные линии
        cv2.line(frame, tuple(hip),   tuple(knee),  color, 3, cv2.LINE_AA)
        cv2.line(frame, tuple(knee),  tuple(ankle), color, 3, cv2.LINE_AA)
        # Внешние суставы — белые кольца
        for pt in [tuple(hip), tuple(ankle)]:
            cv2.circle(frame, pt, 9, (30, 35, 45), -1)
            cv2.circle(frame, pt, 9, (80, 90, 110), 2, cv2.LINE_AA)
            cv2.circle(frame, pt, 4, self.COLOR_WHITE, -1, cv2.LINE_AA)
        # Колено — акцентный цвет
        cv2.circle(frame, tuple(knee), 11, (20, 25, 35), -1)
        cv2.circle(frame, tuple(knee), 11, color, 2, cv2.LINE_AA)
        cv2.circle(frame, tuple(knee), 5, color, -1, cv2.LINE_AA)

    def draw_angle(self, frame, knee, angle, color):
        """Угол у колена с красивым фоном."""
        text = f"{int(angle)} deg"
        x, y = knee[0] + 18, knee[1] - 5
        tw, th = cv2.getTextSize(text, self.FONT_MONO, 0.75, 2)[0]
        self._draw_rounded_rect(frame, x-6, y-th-4, x+tw+6, y+6, self.COLOR_BG, alpha=0.7)
        self._draw_outlined_text(frame, text, (x, y), self.FONT_MONO, 0.75, color, 2)

    def draw_header(self, frame, counter, stage, mouse_pos=None):
        """Верхняя панель с основной информацией. Возвращает rect кнопки Menu."""
        h, w, _ = frame.shape

        # Фон шапки
        self._draw_rounded_rect(frame, 0, 0, w, 72, self.COLOR_BG, alpha=0.85)
        self._draw_accent_line(frame, 0, 72, w)

        # ── Кнопка MENU слева ─────────────────────────────────────────────
        btn_x1, btn_y1, btn_x2, btn_y2 = 10, 10, 110, 62
        self.draw_button(frame, "MENU", btn_x1, btn_y1, btn_x2, btn_y2, mouse_pos, 'secondary')

        # Счётчик по центру
        count_text = str(counter)
        ctw = cv2.getTextSize(count_text, self.FONT_MONO, 2.2, 3)[0][0]
        cx  = w // 2 - ctw // 2

        label_text = "SQUATS"
        ltw = cv2.getTextSize(label_text, self.FONT_PLAIN, 0.45, 1)[0][0]
        cv2.putText(frame, label_text, (w//2 - ltw//2, 20), self.FONT_PLAIN, 0.45, self.COLOR_MUTED, 1, cv2.LINE_AA)
        self._draw_outlined_text(frame, count_text, (cx, 62), self.FONT_MONO, 2.2, self.COLOR_WHITE, 3)

        # Stage справа
        stage_text  = stage if stage else "---"
        stage_color = self.COLOR_GREEN if stage == "UP" else (self.COLOR_BLUE if stage == "DOWN" else self.COLOR_MUTED)

        stw = cv2.getTextSize(stage_text, self.FONT_MONO, 1.0, 2)[0][0]
        sx  = w - stw - 20

        cv2.putText(frame, "STAGE", (w - 80, 20), self.FONT_PLAIN, 0.45, self.COLOR_MUTED, 1, cv2.LINE_AA)

        # Фон стейджа
        self._draw_rounded_rect(frame, sx-8, 28, w-8, 66, stage_color, alpha=0.15)
        cv2.rectangle(frame, (sx-8, 28), (w-8, 66), stage_color, 1)
        self._draw_outlined_text(frame, stage_text, (sx, 60), self.FONT_MONO, 1.0, stage_color, 2)

        return (btn_x1, btn_y1, btn_x2, btn_y2)

    def draw_feedback(self, frame, feedback, color):
        """Нижняя полоса с фидбэком."""
        h, w, _ = frame.shape

        self._draw_rounded_rect(frame, 0, h-56, w, h, self.COLOR_BG, alpha=0.85)
        self._draw_accent_line(frame, 0, h-56, w, color)

        # Иконка-точка
        cv2.circle(frame, (18, h-25), 5, color, -1, cv2.LINE_AA)
        cv2.circle(frame, (18, h-25), 7, color, 1, cv2.LINE_AA)

        self._draw_outlined_text(frame, feedback, (32, h-18), self.FONT_PLAIN, 0.78, color, 2)

    def draw_back_angle(self, frame, angle, is_good):
        """Карточка угла спины в левом нижнем углу над фидбэком."""
        h, w, _ = frame.shape
        color   = self.COLOR_GREEN if is_good else self.COLOR_RED
        icon    = "\u2713" if is_good else "!"

        y_base = h - 65
        self._draw_rounded_rect(frame, 12, y_base-28, 170, y_base+8, self.COLOR_BG, alpha=0.75)

        cv2.putText(frame, "BACK", (20, y_base-10), self.FONT_PLAIN, 0.42, self.COLOR_MUTED, 1, cv2.LINE_AA)
        self._draw_outlined_text(frame, f"{icon} {int(angle)} deg", (20, y_base+4), self.FONT_MONO, 0.65, color, 2)

    def draw_form_warnings(self, frame, warnings):
        """Предупреждения о технике — карточки в правом верхнем углу."""
        if not warnings:
            return

        h, w, _ = frame.shape
        y_start = 82

        for i, warning in enumerate(warnings):
            y   = y_start + i * 38
            tw  = cv2.getTextSize(warning, self.FONT_PLAIN, 0.65, 2)[0][0]
            x1  = w - tw - 40
            x2  = w - 8

            self._draw_rounded_rect(frame, x1-4, y-24, x2, y+8, (40, 0, 0), alpha=0.85)
            cv2.rectangle(frame, (x1-4, y-24), (x2, y+8), self.COLOR_RED, 1)

            self._draw_outlined_text(frame, warning, (x1, y), self.FONT_PLAIN, 0.65, self.COLOR_RED, 2)

    def draw_camera_warning(self, frame, deviation):
        """Предупреждение о положении камеры."""
        h, w, _ = frame.shape
        cy = h // 2

        self._draw_rounded_rect(frame, w//2-280, cy-45, w//2+280, cy+45, self.COLOR_BG, alpha=0.9)
        cv2.rectangle(frame, (w//2-280, cy-45), (w//2+280, cy+45), self.COLOR_ORANGE, 1)

        line1 = f"Camera diagonal (~{int(deviation)} deg off)"
        line2 = "Place camera strictly to the side"

        l1w = cv2.getTextSize(line1, self.FONT_MONO, 0.72, 2)[0][0]
        l2w = cv2.getTextSize(line2, self.FONT_PLAIN, 0.58, 1)[0][0]

        self._draw_outlined_text(frame, line1, (w//2 - l1w//2, cy-10), self.FONT_MONO, 0.72, self.COLOR_ORANGE, 2)
        cv2.putText(frame, line2, (w//2 - l2w//2, cy+25), self.FONT_PLAIN, 0.58, self.COLOR_MUTED, 1, cv2.LINE_AA)

    def draw_angle_bar(self, frame, angle, up_thresh, down_thresh):
        """
        Вертикальный прогресс-бар глубины приседания (справа от кадра).
        Зелёный = хорошо, красный = не достаточно глубоко.
        """
        h, w, _ = frame.shape

        bar_x  = w - 28
        bar_y1 = 90
        bar_y2 = h - 70
        bar_h  = bar_y2 - bar_y1
        bw     = 12

        # Фон бара
        self._draw_rounded_rect(frame, bar_x, bar_y1, bar_x+bw, bar_y2, self.COLOR_BG, alpha=0.8)
        cv2.rectangle(frame, (bar_x, bar_y1), (bar_x+bw, bar_y2), (50, 55, 70), 1)

        # Заполнение: 0% = up_thresh (прямо), 100% = down_thresh (приседание)
        clamped = max(down_thresh, min(up_thresh, angle))
        pct     = (up_thresh - clamped) / max(1, up_thresh - down_thresh)
        fill_h  = int(bar_h * pct)
        fill_y  = bar_y2 - fill_h

        fill_color = self.COLOR_GREEN if pct >= 0.95 else (self.COLOR_YELLOW if pct > 0.5 else self.COLOR_RED)
        if fill_h > 0:
            cv2.rectangle(frame, (bar_x+1, fill_y), (bar_x+bw-1, bar_y2-1), fill_color, -1)

        # Метка
        cv2.putText(frame, "DEPTH", (bar_x-2, bar_y1-8), self.FONT_PLAIN, 0.38, self.COLOR_MUTED, 1, cv2.LINE_AA)

    def draw_fps(self, frame, fps):
        """FPS в правом верхнем углу."""
        h, w, _ = frame.shape
        text = f"{int(fps)} FPS"
        tw   = cv2.getTextSize(text, self.FONT_PLAIN, 0.45, 1)[0][0]
        cv2.putText(frame, text, (w - tw - 44, 88), self.FONT_PLAIN, 0.45, self.COLOR_MUTED, 1, cv2.LINE_AA)

    # ── Стартовый экран (выбор источника) ─────────────────────────────────

    def draw_source_selection(self, frame, selected=0, mouse_pos=None):
        """
        Экран выбора источника: 0 = webcam, 1 = video file.
        selected — индекс выбранного пункта.
        Возвращает список rect кнопок [(x1,y1,x2,y2), ...].
        """
        h, w, _ = frame.shape
        mx, my  = (mouse_pos[0], mouse_pos[1]) if mouse_pos else (-1, -1)

        # Полупрозрачный оверлей
        overlay = np.zeros_like(frame, dtype=np.uint8)
        overlay[:] = self.COLOR_BG
        cv2.addWeighted(overlay, 0.92, frame, 0.08, 0, frame)

        # Заголовок
        title  = "AI FITNESS COACH"
        tw     = cv2.getTextSize(title, self.FONT_MONO, 1.5, 3)[0][0]
        self._draw_outlined_text(frame, title, (w//2 - tw//2, h//2 - 120), self.FONT_MONO, 1.5, self.COLOR_ACCENT, 3)

        sub   = "SELECT INPUT SOURCE"
        sw    = cv2.getTextSize(sub, self.FONT_PLAIN, 0.55, 1)[0][0]
        cv2.putText(frame, sub, (w//2 - sw//2, h//2 - 80), self.FONT_PLAIN, 0.55, self.COLOR_MUTED, 1, cv2.LINE_AA)

        self._draw_accent_line(frame, w//2 - 200, h//2 - 64, w//2 + 200)

        options = [
            ("WEBCAM",       "Use live camera feed",  "[W]"),
            ("VIDEO FILE",   "Load recorded video",   "[V]"),
        ]

        btn_rects = []
        for i, (label, desc, shortcut) in enumerate(options):
            bx1 = w//2 - 200
            by1 = h//2 - 30 + i * 78
            bx2 = w//2 + 200
            by2 = by1 + 60
            btn_rects.append((bx1, by1, bx2, by2))

            self.draw_button(frame, label, bx1, by1, bx2, by2, mouse_pos, 'primary')

            # Подпись под кнопкой
            dw = cv2.getTextSize(desc, self.FONT_PLAIN, 0.46, 1)[0][0]
            cv2.putText(frame, desc, (w//2 - dw//2, by2 + 16),
                        self.FONT_PLAIN, 0.46, self.COLOR_MUTED, 1, cv2.LINE_AA)

        return btn_rects

    # ── Экран калибровки ──────────────────────────────────────────────────

    def draw_calibration_overlay(self, frame, phase, countdown, angle=None):
        """Красивый оверлей во время калибровки."""
        h, w, _ = frame.shape

        if phase == "UP":
            instruction = "STAND STRAIGHT"
            color       = self.COLOR_GREEN
        else:
            instruction = "SQUAT DOWN"
            color       = self.COLOR_BLUE

        # Тёмный оверлей
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), self.COLOR_BG, -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        # Рамка
        thick = 3
        for offset in range(0, 16, 8):
            alpha_v = 0.8 - offset * 0.04
            ov2 = frame.copy()
            cv2.rectangle(ov2, (offset, offset), (w-offset, h-offset), color, thick)
            cv2.addWeighted(ov2, alpha_v * 0.3, frame, 1 - alpha_v * 0.3, 0, frame)

        cv2.rectangle(frame, (0, 0), (w, h), color, 2)

        # Шаг
        step_text = "STEP 1 OF 2" if phase == "UP" else "STEP 2 OF 2"
        stw = cv2.getTextSize(step_text, self.FONT_PLAIN, 0.55, 1)[0][0]
        cv2.putText(frame, step_text, (w//2 - stw//2, h//2 - 140), self.FONT_PLAIN, 0.55, self.COLOR_MUTED, 1, cv2.LINE_AA)

        # Основная инструкция
        iw = cv2.getTextSize(instruction, self.FONT_MONO, 1.8, 3)[0][0]
        self._draw_outlined_text(frame, instruction, (w//2 - iw//2, h//2 - 90), self.FONT_MONO, 1.8, color, 3)

        # Счётчик
        if countdown > 0:
            cw = cv2.getTextSize(str(countdown), self.FONT_MONO, 5.0, 5)[0][0]
            self._draw_outlined_text(frame, str(countdown), (w//2 - cw//2, h//2 + 60), self.FONT_MONO, 5.0, color, 5)
        else:
            mw = cv2.getTextSize("Measuring...", self.FONT_MONO, 1.1, 2)[0][0]
            self._draw_outlined_text(frame, "Measuring...", (w//2 - mw//2, h//2 + 20), self.FONT_MONO, 1.1, color, 2)
            if angle is not None:
                aw = cv2.getTextSize(f"Angle: {int(angle)} deg", self.FONT_PLAIN, 0.8, 2)[0][0]
                self._draw_outlined_text(frame, f"Angle: {int(angle)} deg", (w//2 - aw//2, h//2 + 65), self.FONT_PLAIN, 0.8, self.COLOR_WHITE, 2)