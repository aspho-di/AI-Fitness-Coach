import cv2
import time
import argparse
import sys
import numpy as np
from pose_detector import PoseDetector
from angle_calculator import (
    calculate_angle_3d,
    calculate_back_angle,
    calculate_knee_deviation_3d,
    estimate_camera_angle,
    get_best_leg
)
from ui_renderer import UIRenderer
from calibration import Calibrator


BACK_ANGLE_LIMIT      = 35
KNEE_DEVIATION_LIMIT  = 0.15
CAMERA_WARNING_FRAMES = 90
WINDOW_NAME           = "AI Fitness Coach"

# Размеры окна по умолчанию
DEFAULT_W = 1280
DEFAULT_H = 720


def open_file_dialog():
    """Открывает системный диалог выбора файла через tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()          # прячем главное окно tk
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        root.destroy()
        return path or ''
    except Exception:
        return ''


def get_source_interactive(renderer):
    """
    Показывает экран выбора источника в окне OpenCV.
    Возвращает (source_type, path).
    source_type: 'webcam' или 'video'
    """
    frame    = np.zeros((DEFAULT_H, DEFAULT_W, 3), dtype=np.uint8)
    selected = 0  # 0 = webcam, 1 = video

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, DEFAULT_W, DEFAULT_H)

    # Мышь для экрана меню
    menu_mouse   = [0, 0]
    menu_click   = [False]

    def on_menu_mouse(event, x, y, flags, param):
        menu_mouse[0] = x
        menu_mouse[1] = y
        if event == cv2.EVENT_LBUTTONUP:
            menu_click[0] = True

    cv2.setMouseCallback(WINDOW_NAME, on_menu_mouse)

    while True:
        display = frame.copy()
        btns = renderer.draw_source_selection(display, selected, menu_mouse)
        cv2.imshow(WINDOW_NAME, display)

        # Обработка клика мышью
        if menu_click[0]:
            menu_click[0] = False
            mx, my = menu_mouse
            for i, (bx1, by1, bx2, by2) in enumerate(btns):
                if bx1 <= mx <= bx2 and by1 <= my <= by2:
                    selected = i
                    # Двойной клик (уже выбран) или просто подтверждение кликом
                    if i == 0:
                        return 'webcam', ''
                    else:
                        cv2.destroyAllWindows()
                        path = open_file_dialog()
                        if not path:
                            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
                            cv2.resizeWindow(WINDOW_NAME, DEFAULT_W, DEFAULT_H)
                            cv2.setMouseCallback(WINDOW_NAME, on_menu_mouse)
                        else:
                            return 'video', path

        # waitKeyEx возвращает полный код клавиши (нужен для стрелок на Windows)
        key = cv2.waitKeyEx(33)

        # ── Закрытие крестиком ────────────────────────────────────────────
        try:
            visible = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE)
        except Exception:
            visible = 0
        if visible < 1:
            cv2.destroyAllWindows()
            sys.exit(0)

        if key == -1:
            continue

        # ── Стрелки (Windows: 0x260000 / 0x280000, Linux: 82 / 84) ──────
        if key in (0x260000, 65362, 82, ord('w'), ord('W')):   # вверх
            selected = 0
        elif key in (0x280000, 65364, 84, ord('s'), ord('S')): # вниз
            selected = 1

        elif key == ord('1'):
            selected = 0
        elif key == ord('2'):
            selected = 1

        elif key & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            sys.exit(0)

        elif key & 0xFF == ord('f'):
            toggle_fullscreen()

        elif key & 0xFF in (13, 32):  # Enter / Space
            if selected == 0:
                return 'webcam', ''
            else:
                # Открываем системный диалог выбора файла
                cv2.destroyAllWindows()
                path = open_file_dialog()
                if not path:
                    # Если отменили — возвращаемся в меню
                    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
                    cv2.resizeWindow(WINDOW_NAME, DEFAULT_W, DEFAULT_H)
                    continue
                return 'video', path


def toggle_fullscreen():
    """Переключает полноэкранный режим."""
    prop = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    if prop == cv2.WINDOW_FULLSCREEN:
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    else:
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def get_source_from_args():
    """Читает аргументы командной строки."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default=None, choices=['webcam', 'video'])
    parser.add_argument('--path',   type=str, default='')
    parser.add_argument('--width',  type=int, default=DEFAULT_W)
    parser.add_argument('--height', type=int, default=DEFAULT_H)
    return parser.parse_args()


def show_no_camera_screen(renderer):
    """
    Показывает экран ошибки камеры.
    Возвращает True = вернуться в меню, False = выйти.
    """
    frame = np.zeros((DEFAULT_H, DEFAULT_W, 3), dtype=np.uint8)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, DEFAULT_W, DEFAULT_H)

    while True:
        display = frame.copy()

        h, w = DEFAULT_H, DEFAULT_W
        # Тёмный фон с рамкой
        cv2.rectangle(display, (0, 0), (w, h), (10, 13, 20), -1)
        cv2.rectangle(display, (2, 2), (w-2, h-2), (50, 0, 0), 2)

        # Иконка — перечёркнутый круг
        cx, cy, r = w//2, h//2 - 40, 60
        cv2.circle(display, (cx, cy), r, (60, 0, 0), -1)
        cv2.circle(display, (cx, cy), r, (0, 50, 200), 3)
        cv2.line(display, (cx - r + 15, cy - r + 15), (cx + r - 15, cy + r - 15), (0, 50, 200), 4)

        # Текст
        t1 = "CAMERA NOT FOUND"
        t2 = "Could not open webcam or video file."
        t3 = "Press ENTER to go back   |   Q to quit"

        for txt, y, scale, col in [
            (t1, h//2 + 50, 1.1, (0, 80, 255)),
            (t2, h//2 + 95, 0.65, (100, 110, 130)),
            (t3, h//2 + 145, 0.6, (0, 245, 160)),
        ]:
            tw = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, scale, 2)[0][0]
            cv2.putText(display, txt, (w//2 - tw//2, y),
                        cv2.FONT_HERSHEY_DUPLEX, scale, col, 2, cv2.LINE_AA)

        cv2.imshow(WINDOW_NAME, display)
        key = cv2.waitKey(33) & 0xFF

        try:
            visible = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE)
        except Exception:
            visible = 0
        if visible < 1:
            return False

        if key in (13, 32):   # Enter / Space → назад в меню
            return True
        elif key == ord('q') or key == 27:
            return False


def letterbox(frame, target_w, target_h):
    """
    Масштабирует кадр с сохранением пропорций.
    Добавляет чёрные полосы сверху/снизу или по бокам (letterbox).
    """
    fh, fw = frame.shape[:2]
    scale  = min(target_w / fw, target_h / fh)
    nw     = int(fw * scale)
    nh     = int(fh * scale)

    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)

    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_off  = (target_w - nw) // 2
    y_off  = (target_h - nh) // 2
    canvas[y_off:y_off+nh, x_off:x_off+nw] = resized
    return canvas


def main():
    args     = get_source_from_args()
    detector = PoseDetector(detection_confidence=0.7, tracking_confidence=0.7)
    renderer = UIRenderer()

    # ── Главный цикл — позволяет вернуться в меню ─────────────────────────
    while True:
        # ── Выбор источника ───────────────────────────────────────────────
        if args.source is None:
            source, path = get_source_interactive(renderer)
        elif args.source == 'video':
            source, path = 'video', args.path
        else:
            source, path = 'webcam', ''

        # После первого прохода всегда показываем меню
        args.source = None

        # ── Открываем захват ──────────────────────────────────────────────
        is_video = (source == 'video' and path)
        if is_video:
            print(f"Opening video: {path}")
            cap = cv2.VideoCapture(path)
        else:
            print("Opening webcam...")
            cap = cv2.VideoCapture(0)

        # ── Окно ──────────────────────────────────────────────────────────
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, DEFAULT_W, DEFAULT_H)

        if not cap.isOpened():
            go_back = show_no_camera_screen(renderer)
            if not go_back:
                break
            continue

        # ── Калибровка только для камеры, для видео используем дефолт ────
        if is_video:
            SQUAT_UP_ANGLE   = 140.0
            SQUAT_DOWN_ANGLE = 90.0

            # ── Экран предпросмотра видео с кнопкой START ANALYSIS ────────
            vid_mouse = [0, 0]
            vid_click = [False]

            def on_vid_mouse(event, x, y, flags, param):
                vid_mouse[0] = x
                vid_mouse[1] = y
                if event == cv2.EVENT_LBUTTONUP:
                    vid_click[0] = True

            cv2.setMouseCallback(WINDOW_NAME, on_vid_mouse)

            # Читаем первый кадр для предпросмотра
            ret_p, preview_frame = cap.read()
            if not ret_p:
                cap.release()
                continue

            start_analysis = False
            while not start_analysis:
                if preview_frame is not None:
                    preview = letterbox(preview_frame, DEFAULT_W, DEFAULT_H)
                else:
                    preview = np.zeros((DEFAULT_H, DEFAULT_W, 3), dtype=np.uint8)

                h_p, w_p = preview.shape[:2]

                # Тёмный оверлей снизу
                overlay = preview.copy()
                cv2.rectangle(overlay, (0, h_p - 120), (w_p, h_p), (10, 13, 20), -1)
                cv2.addWeighted(overlay, 0.80, preview, 0.20, 0, preview)

                # Заголовок
                title = "VIDEO LOADED"
                tw = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.0, 2)[0][0]
                cv2.putText(preview, title, (w_p//2 - tw//2, h_p - 82),
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 245, 160), 2, cv2.LINE_AA)

                import os
                fname = os.path.basename(path)
                sw = cv2.getTextSize(fname, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)[0][0]
                cv2.putText(preview, fname, (w_p//2 - sw//2, h_p - 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (160, 170, 190), 1, cv2.LINE_AA)

                # Кнопки
                mx, my = vid_mouse
                bx1 = w_p//2 - 140; bx2 = w_p//2 + 140
                by1 = h_p - 42;     by2 = h_p - 6
                btn_hover = renderer.draw_button(preview, "START ANALYSIS", bx1, by1, bx2, by2, vid_mouse, 'primary')
                bk_hover  = renderer.draw_button(preview, "< MENU", 10, h_p - 42, 120, h_p - 6, vid_mouse, 'secondary')

                cv2.imshow(WINDOW_NAME, preview)
                key = cv2.waitKey(1) & 0xFF

                if vid_click[0]:
                    vid_click[0] = False
                    if btn_hover:
                        start_analysis = True
                    elif bk_hover:
                        cap.release()
                        cap = None
                        break

                if key in (13, 32):
                    start_analysis = True
                elif key == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                elif key == 27:
                    cap.release()
                    cap = None
                    break

                try:
                    visible = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE)
                except Exception:
                    visible = 0
                if visible < 1:
                    if cap:
                        cap.release()
                    cv2.destroyAllWindows()
                    return

            if cap is None:
                continue   # вернуться в меню

            # Сбрасываем позицию видео на начало
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        else:
            # ── Экран ожидания: показываем камеру + кнопку START ──────────
            calib_mouse   = [0, 0]
            calib_click   = [False]

            def on_calib_mouse(event, x, y, flags, param):
                calib_mouse[0] = x
                calib_mouse[1] = y
                if event == cv2.EVENT_LBUTTONUP:
                    calib_click[0] = True

            cv2.setMouseCallback(WINDOW_NAME, on_calib_mouse)

            start_calib = False
            while not start_calib:
                ret, preview = cap.read()
                if not ret:
                    break

                h_p, w_p = preview.shape[:2]

                # Тёмный полупрозрачный оверлей снизу
                overlay = preview.copy()
                cv2.rectangle(overlay, (0, h_p - 110), (w_p, h_p), (10, 13, 20), -1)
                cv2.addWeighted(overlay, 0.75, preview, 0.25, 0, preview)

                # Заголовок
                title = "CAMERA READY"
                tw = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.0, 2)[0][0]
                cv2.putText(preview, title, (w_p//2 - tw//2, h_p - 75),
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 245, 160), 2, cv2.LINE_AA)

                sub = "Stand in front of camera, then click START CALIBRATION"
                sw = cv2.getTextSize(sub, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)[0][0]
                cv2.putText(preview, sub, (w_p//2 - sw//2, h_p - 48),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (160, 170, 190), 1, cv2.LINE_AA)

                # Кнопки
                mx, my = calib_mouse
                bx1 = w_p//2 - 160; bx2 = w_p//2 + 160
                by1 = h_p - 42;     by2 = h_p - 6
                btn_hover = renderer.draw_button(preview, "START CALIBRATION", bx1, by1, bx2, by2, calib_mouse, 'primary')
                bk_hover  = renderer.draw_button(preview, "< MENU", 10, h_p - 42, 120, h_p - 6, calib_mouse, 'secondary')

                cv2.imshow(WINDOW_NAME, preview)
                key = cv2.waitKey(1) & 0xFF

                # Клик по кнопкам
                if calib_click[0]:
                    calib_click[0] = False
                    if btn_hover:
                        start_calib = True
                    elif bk_hover:
                        cap.release()
                        cap = None
                        break

                # Enter / Space тоже запускает
                if key in (13, 32):
                    start_calib = True
                elif key == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                elif key == 27:
                    cap.release()
                    cap = None
                    break   # ESC — назад в меню

                try:
                    visible = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE)
                except Exception:
                    visible = 0
                if visible < 1:
                    cap.release()
                    cv2.destroyAllWindows()
                    return

            if not start_calib:
                if cap is not None:
                    cap.release()
                continue   # вернуться в меню

            # ── Запускаем калибровку ──────────────────────────────────────
            calibrator = Calibrator(detector)
            thresholds = calibrator.run(cap)
            SQUAT_UP_ANGLE   = thresholds["up_angle"]
            SQUAT_DOWN_ANGLE = thresholds["down_angle"]

        print(f"Thresholds - UP: >{SQUAT_UP_ANGLE} | DOWN: <{SQUAT_DOWN_ANGLE}")

        counter              = 0
        stage                = None
        min_angle_reached    = 180
        camera_warning_timer = 0
        last_cam_deviation   = 0
        win_w, win_h         = DEFAULT_W, DEFAULT_H
        go_back_to_menu      = False

        # FPS
        fps_time    = time.time()
        fps_counter = 0
        fps_display = 0

        # ── Мышь ──────────────────────────────────────────────────────────
        mouse_pos   = [0, 0]
        mouse_click = [False]

        def on_mouse(event, x, y, flags, param):
            mouse_pos[0] = x
            mouse_pos[1] = y
            if event == cv2.EVENT_LBUTTONUP:
                mouse_click[0] = True

        cv2.setMouseCallback(WINDOW_NAME, on_mouse)

        # ── Основной цикл обработки ───────────────────────────────────────
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Stream ended.")
                # ── Экран результатов для видео ───────────────────────────
                if is_video:
                    res_mouse = [0, 0]
                    res_click = [False]
                    def on_res_mouse(event, x, y, flags, param):
                        res_mouse[0] = x
                        res_mouse[1] = y
                        if event == cv2.EVENT_LBUTTONUP:
                            res_click[0] = True
                    cv2.setMouseCallback(WINDOW_NAME, on_res_mouse)

                    # Последний кадр остаётся на экране, добавляем оверлей
                    result_bg = frame.copy() if frame is not None else np.zeros((DEFAULT_H, DEFAULT_W, 3), dtype=np.uint8)

                    while True:
                        display = result_bg.copy()
                        h_r, w_r = display.shape[:2]

                        # Полупрозрачный тёмный оверлей
                        ov = display.copy()
                        cv2.rectangle(ov, (0, 0), (w_r, h_r), (10, 13, 20), -1)
                        cv2.addWeighted(ov, 0.70, display, 0.30, 0, display)

                        # Заголовок
                        t1 = "ANALYSIS COMPLETE"
                        tw = cv2.getTextSize(t1, cv2.FONT_HERSHEY_DUPLEX, 1.4, 3)[0][0]
                        cv2.putText(display, t1, (w_r//2 - tw//2, h_r//2 - 80),
                                    cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 245, 160), 3, cv2.LINE_AA)

                        # Счётчик приседаний
                        t2 = f"{counter} SQUATS"
                        tw2 = cv2.getTextSize(t2, cv2.FONT_HERSHEY_DUPLEX, 2.5, 4)[0][0]
                        cv2.putText(display, t2, (w_r//2 - tw2//2, h_r//2 + 10),
                                    cv2.FONT_HERSHEY_DUPLEX, 2.5, (255, 255, 255), 4, cv2.LINE_AA)

                        # Кнопка BACK TO MENU
                        bx1 = w_r//2 - 130; bx2 = w_r//2 + 130
                        by1 = h_r//2 + 50;  by2 = h_r//2 + 92
                        mx, my = res_mouse
                        btn_hover = renderer.draw_button(display, "BACK TO MENU", bx1, by1, bx2, by2, res_mouse, 'primary')

                        cv2.imshow(WINDOW_NAME, display)
                        key = cv2.waitKey(1) & 0xFF

                        if res_click[0]:
                            res_click[0] = False
                            if btn_hover:
                                go_back_to_menu = True
                                break

                        if key == ord('q'):
                            cap.release()
                            cv2.destroyAllWindows()
                            return
                        elif key in (13, 32, 27):
                            go_back_to_menu = True
                            break

                        try:
                            visible = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE)
                        except Exception:
                            visible = 0
                        if visible < 1:
                            cap.release()
                            cv2.destroyAllWindows()
                            return
                else:
                    go_back_to_menu = True
                break

            # Для видео — сохраняем пропорции, добавляем letterbox
            if is_video:
                frame = letterbox(frame, win_w, win_h)

            results  = detector.process_frame(frame)
            detector.draw_skeleton(frame, results)

            leg       = get_best_leg(results)
            landmarks = detector.get_landmarks(results, frame.shape, leg=leg)

            feedback = "Stand in front of camera"
            color    = renderer.COLOR_YELLOW
            angle    = 0
            warnings = []

            if landmarks:
                shoulder = landmarks["shoulder"]
                hip      = landmarks["hip"]
                knee     = landmarks["knee"]
                ankle    = landmarks["ankle"]

                cam_position, cam_deviation = estimate_camera_angle({
                    "left_hip_z":  landmarks["left_hip_z"],
                    "right_hip_z": landmarks["right_hip_z"]
                })

                if cam_position == "diagonal" and not is_video:
                    last_cam_deviation   = cam_deviation
                    camera_warning_timer = CAMERA_WARNING_FRAMES

                angle      = calculate_angle_3d(landmarks["hip_3d"], landmarks["knee_3d"], landmarks["ankle_3d"])
                back_angle = calculate_back_angle(shoulder, hip)
                knee_dev   = calculate_knee_deviation_3d(landmarks["knee_3d"], landmarks["ankle_3d"], landmarks["hip_3d"])

                back_is_good = back_angle <= BACK_ANGLE_LIMIT

                if not back_is_good and stage == "DOWN":
                    warnings.append("! Round back")
                if knee_dev < -KNEE_DEVIATION_LIMIT and stage == "DOWN":
                    warnings.append("! Knees caving in")

                if stage == "DOWN":
                    min_angle_reached = min(min_angle_reached, angle)

                if angle > SQUAT_UP_ANGLE:
                    if stage == "DOWN":
                        if min_angle_reached <= SQUAT_DOWN_ANGLE:
                            counter += 1
                            feedback = f"Great! Rep #{counter} counted!"
                            color    = renderer.COLOR_GREEN
                        else:
                            feedback = f"Not deep enough! Min: {int(min_angle_reached)} deg"
                            color    = renderer.COLOR_RED
                        min_angle_reached = 180
                    else:
                        feedback = "Ready - go down!"
                        color    = renderer.COLOR_GREEN
                    stage = "UP"

                elif angle < SQUAT_DOWN_ANGLE:
                    stage    = "DOWN"
                    feedback = "Great depth - stand up!"
                    color    = renderer.COLOR_GREEN
                else:
                    if stage == "DOWN":
                        feedback = f"Lower! Need < {int(SQUAT_DOWN_ANGLE)} deg  Now: {int(angle)} deg"
                        color    = renderer.COLOR_RED
                    else:
                        feedback = "Ready - go down!"
                        color    = renderer.COLOR_GREEN

                renderer.draw_joint_lines(frame, hip, knee, ankle, color)
                renderer.draw_angle(frame, knee, angle, color)
                renderer.draw_back_angle(frame, back_angle, back_is_good)
                renderer.draw_angle_bar(frame, angle, SQUAT_UP_ANGLE, SQUAT_DOWN_ANGLE)

            btn_menu = renderer.draw_header(frame, counter, stage, mouse_pos)
            renderer.draw_feedback(frame, feedback, color)
            renderer.draw_form_warnings(frame, warnings)
            renderer.draw_fps(frame, fps_display)

            if camera_warning_timer > 0:
                renderer.draw_camera_warning(frame, last_cam_deviation)
                camera_warning_timer -= 1

            cv2.imshow(WINDOW_NAME, frame)

            # Клик по кнопке Menu
            if mouse_click[0]:
                mouse_click[0] = False
                mx, my = mouse_pos
                if btn_menu and btn_menu[0] <= mx <= btn_menu[2] and btn_menu[1] <= my <= btn_menu[3]:
                    go_back_to_menu = True
                    break

            fps_counter += 1
            if time.time() - fps_time >= 1.0:
                fps_display = fps_counter
                fps_counter = 0
                fps_time    = time.time()

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return
            elif key == 27:   # ESC — вернуться в меню
                go_back_to_menu = True
                break
            elif key == ord('f'):
                toggle_fullscreen()
            elif key == ord('+') or key == ord('='):
                win_w = min(win_w + 80, 1920)
                win_h = min(win_h + 45, 1080)
                cv2.resizeWindow(WINDOW_NAME, win_w, win_h)
            elif key == ord('-'):
                win_w = max(win_w - 80, 640)
                win_h = max(win_h - 45, 360)
                cv2.resizeWindow(WINDOW_NAME, win_w, win_h)

            try:
                visible = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE)
            except Exception:
                visible = 0
            if visible < 1:
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()

        if not go_back_to_menu:
            break   # Q или крестик — полный выход
        # иначе — продолжаем внешний цикл (возврат в меню)

    cv2.destroyAllWindows()
    print("Workout complete!")


if __name__ == "__main__":
    main()