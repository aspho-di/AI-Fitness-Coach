import cv2
import time
import numpy as np
from angle_calculator import calculate_angle_3d, get_best_leg


class Calibrator:
    """
    Автоматически определяет пороговые значения углов
    путём калибровки в начале сессии.
    """

    def __init__(self, detector):
        self.detector = detector

    def run(self, cap):
        """
        Калибровка с GUI — показывает инструкции в окне OpenCV.
        Используется при запуске main.py напрямую.

        Возвращает:
            dict с ключами 'up_angle' и 'down_angle'
        """
        up_angle   = self._calibrate_phase(cap, phase="UP")
        down_angle = self._calibrate_phase(cap, phase="DOWN")

        up_threshold   = round(up_angle * 0.85, 1)
        down_threshold = round(down_angle * 1.25, 1)

        print(f"\nCalibration complete!")
        print(f"Standing angle: {up_angle} deg  → UP threshold: {up_threshold}")
        print(f"Squat angle:    {down_angle} deg → DOWN threshold: {down_threshold}")

        return {
            "up_angle":   up_threshold,
            "down_angle": down_threshold
        }

    def run_headless(self, cap, set_frame_callback):
        """
        Калибровка без GUI — кадры с инструкциями передаются в браузер
        через callback функцию set_frame_callback(jpeg_bytes).

        Используется из web/server.py когда видео стримится в браузер.

        Возвращает:
            dict с ключами 'up_angle' и 'down_angle'
        """
        up_angle   = self._calibrate_phase_headless(cap, phase="UP",   set_frame=set_frame_callback)
        down_angle = self._calibrate_phase_headless(cap, phase="DOWN", set_frame=set_frame_callback)

        up_threshold   = round(up_angle * 0.85, 1)
        down_threshold = round(down_angle * 1.25, 1)

        print(f"\nHeadless calibration complete!")
        print(f"Standing angle: {up_angle} deg  → UP threshold: {up_threshold}")
        print(f"Squat angle:    {down_angle} deg → DOWN threshold: {down_threshold}")

        return {
            "up_angle":   up_threshold,
            "down_angle": down_threshold
        }

    # ── Приватные методы ───────────────────────────────────────────────────

    def _calibrate_phase(self, cap, phase):
        """Один этап калибровки с GUI окном OpenCV."""
        if phase == "UP":
            instruction = "Stand straight! Measuring in 3 sec..."
            color       = (0, 255, 0)
        else:
            instruction = "Squat down! Measuring in 3 sec..."
            color       = (0, 165, 255)

        # Показываем инструкцию 3 секунды
        deadline = time.time() + 3
        while time.time() < deadline:
            ret, frame = cap.read()
            if not ret:
                break

            remaining = int(deadline - time.time()) + 1
            h, w, _   = frame.shape

            cv2.rectangle(frame, (0, 0), (w, h), (30, 30, 30), -1)
            cv2.putText(frame, instruction,    (w//2 - 280, h//2 - 20), cv2.FONT_HERSHEY_DUPLEX, 0.9, color, 2)
            cv2.putText(frame, str(remaining), (w//2 - 20,  h//2 + 60), cv2.FONT_HERSHEY_DUPLEX, 3.0, color, 3)
            cv2.imshow("AI Fitness Coach — Calibration", frame)
            cv2.waitKey(1)

        # Собираем углы 2 секунды
        angles   = []
        deadline = time.time() + 2

        while time.time() < deadline:
            ret, frame = cap.read()
            if not ret:
                break

            results   = self.detector.process_frame(frame)
            leg       = get_best_leg(results)
            landmarks = self.detector.get_landmarks(results, frame.shape, leg=leg)

            if landmarks:
                angle = calculate_angle_3d(landmarks["hip_3d"], landmarks["knee_3d"], landmarks["ankle_3d"])
                angles.append(angle)

            h, w, _ = frame.shape
            cv2.rectangle(frame, (0, 0), (w, h), (30, 30, 30), -1)
            cv2.putText(frame, "Measuring...", (w//2 - 120, h//2), cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 2)
            if angles:
                cv2.putText(frame, f"Angle: {int(angles[-1])} deg", (w//2 - 100, h//2 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            cv2.imshow("AI Fitness Coach — Calibration", frame)
            cv2.waitKey(1)

        cv2.destroyWindow("AI Fitness Coach — Calibration")

        if not angles:
            print(f"Warning: could not measure {phase} angle, using default.")
            return 160 if phase == "UP" else 70

        return round(float(np.median(angles)), 1)

    def _calibrate_phase_headless(self, cap, phase, set_frame):
        """Один этап калибровки без GUI — отправляет кадры в браузер через callback."""
        if phase == "UP":
            instruction = "STAND STRAIGHT"
            sub         = "Hold position for calibration..."
            color       = (0, 255, 0)
        else:
            instruction = "SQUAT DOWN"
            sub         = "Hold squat for calibration..."
            color       = (0, 165, 255)

        # Показываем инструкцию 3 секунды
        deadline = time.time() + 3
        while time.time() < deadline:
            ret, frame = cap.read()
            if not ret:
                break

            remaining = int(deadline - time.time()) + 1
            h, w, _   = frame.shape

            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

            cv2.putText(frame, instruction,    (w//2 - 200, h//2 - 30), cv2.FONT_HERSHEY_DUPLEX,   1.4, color,           2)
            cv2.putText(frame, sub,            (w//2 - 180, h//2 + 10), cv2.FONT_HERSHEY_SIMPLEX,  0.8, (200, 200, 200), 1)
            cv2.putText(frame, str(remaining), (w//2 - 25,  h//2 + 80), cv2.FONT_HERSHEY_DUPLEX,   3.0, color,           3)

            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            set_frame(jpeg.tobytes())

        # Собираем углы 2 секунды
        angles   = []
        deadline = time.time() + 2

        while time.time() < deadline:
            ret, frame = cap.read()
            if not ret:
                break

            results   = self.detector.process_frame(frame)
            leg       = get_best_leg(results)
            landmarks = self.detector.get_landmarks(results, frame.shape, leg=leg)

            if landmarks:
                angle = calculate_angle_3d(landmarks["hip_3d"], landmarks["knee_3d"], landmarks["ankle_3d"])
                angles.append(angle)

            h, w, _ = frame.shape
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            cv2.putText(frame, "Measuring...", (w//2 - 120, h//2), cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 2)
            if angles:
                cv2.putText(frame, f"Angle: {int(angles[-1])} deg", (w//2 - 100, h//2 + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            set_frame(jpeg.tobytes())

        if not angles:
            print(f"Warning: could not measure {phase} angle, using default.")
            return 160 if phase == "UP" else 70

        return round(float(np.median(angles)), 1)