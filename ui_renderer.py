import cv2


class UIRenderer:
    """
    Класс для отрисовки всех визуальных элементов на кадре.
    Отвечает только за внешний вид — никакой логики здесь нет.
    """

    COLOR_GREEN  = (0, 255, 0)
    COLOR_RED    = (0, 0, 255)
    COLOR_WHITE  = (255, 255, 255)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_ORANGE = (0, 165, 255)
    COLOR_DARK   = (50, 50, 50)
    COLOR_BLUE   = (255, 100, 0)

    def draw_joint_lines(self, frame, hip, knee, ankle, color):
        cv2.line(frame, tuple(hip),   tuple(knee),  self.COLOR_BLUE, 3)
        cv2.line(frame, tuple(knee),  tuple(ankle), self.COLOR_BLUE, 3)
        cv2.circle(frame, tuple(hip),   10, self.COLOR_WHITE, -1)
        cv2.circle(frame, tuple(knee),  10, color,            -1)
        cv2.circle(frame, tuple(ankle), 10, self.COLOR_WHITE, -1)

    def draw_angle(self, frame, knee, angle, color):
        cv2.putText(
            frame, f"{int(angle)} deg",
            (knee[0] + 15, knee[1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8, color, 2
        )

    def draw_header(self, frame, counter, stage):
        h, w, _ = frame.shape
        cv2.rectangle(frame, (0, 0), (w, 80), self.COLOR_DARK, -1)

        cv2.putText(
            frame, f"Squats: {counter}",
            (20, 55),
            cv2.FONT_HERSHEY_DUPLEX,
            1.5, self.COLOR_WHITE, 2
        )

        stage_text  = stage if stage else "---"
        stage_color = self.COLOR_GREEN if stage == "UP" else self.COLOR_RED

        cv2.putText(
            frame, stage_text,
            (w - 150, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2, stage_color, 2
        )

    def draw_feedback(self, frame, feedback, color):
        h, w, _ = frame.shape
        cv2.rectangle(frame, (0, h - 60), (w, h), self.COLOR_DARK, -1)
        cv2.putText(
            frame, feedback,
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9, color, 2
        )

    def draw_back_angle(self, frame, angle, is_good):
        h, w, _ = frame.shape
        color   = self.COLOR_GREEN if is_good else self.COLOR_RED
        cv2.putText(
            frame, f"Back: {int(angle)} deg",
            (20, h - 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, color, 2
        )

    def draw_form_warnings(self, frame, warnings):
        """
        Выводит предупреждения о технике в правом верхнем углу.
        """
        if not warnings:
            return

        h, w, _ = frame.shape
        y_start = 100

        for i, warning in enumerate(warnings):
            y         = y_start + i * 35
            text_size = cv2.getTextSize(warning, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)[0]

            cv2.rectangle(
                frame,
                (w - text_size[0] - 25, y - 22),
                (w - 5, y + 8),
                self.COLOR_DARK, -1
            )
            cv2.putText(
                frame, warning,
                (w - text_size[0] - 15, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65, self.COLOR_RED, 2
            )

    def draw_camera_warning(self, frame, deviation):
        """
        Рисует предупреждение о положении камеры в центре экрана.
        Показывается только первые несколько секунд или по запросу.

        Параметры:
            frame:     кадр
            deviation: угол отклонения камеры в градусах
        """
        h, w, _ = frame.shape

        # Полупрозрачный тёмный фон по центру
        overlay = frame.copy()
        cv2.rectangle(overlay, (w//2 - 280, h//2 - 50), (w//2 + 280, h//2 + 50), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        cv2.putText(
            frame,
            f"Camera is diagonal (~{int(deviation)} deg off)",
            (w//2 - 260, h//2 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75, self.COLOR_ORANGE, 2
        )
        cv2.putText(
            frame,
            "For best results: place camera strictly to the side",
            (w//2 - 260, h//2 + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, self.COLOR_WHITE, 1
        )