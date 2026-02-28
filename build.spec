# -*- mode: python ; coding: utf-8 -*-
import mediapipe
import os

mediapipe_path = os.path.dirname(mediapipe.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pose_landmarker_full.task', '.'),
        # Копируем весь пакет mediapipe целиком
        (mediapipe_path, 'mediapipe'),
    ],
    hiddenimports=[
        'mediapipe',
        'mediapipe.tasks',
        'mediapipe.tasks.python',
        'mediapipe.tasks.python.vision',
        'mediapipe.tasks.c',
        'mediapipe.python',
        'mediapipe.python._framework_bindings',
        'mediapipe.python.solutions',
        'google.protobuf',
        'absl',
        'absl.logging',
        'cv2',
        'numpy',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_agg',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'pandas', 'IPython', 'jupyter'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AI_Fitness_Coach',
    debug=False,
    strip=False,
    upx=False,       # UPX отключён — он ломает C-расширения MediaPipe
    console=True,    # Пока True чтобы видеть ошибки при тестировании
    runtime_tmpdir=None,
)