# build.spec — исправленная версия для MediaPipe Tasks API
import os
import mediapipe

mediapipe_path = os.path.dirname(mediapipe.__file__)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[
        # Главная C-библиотека MediaPipe Tasks (критично!)
        (os.path.join(mediapipe_path, 'tasks', 'c', '*.dll'), 'mediapipe/tasks/c'),   # Windows
        (os.path.join(mediapipe_path, 'tasks', 'c', '*.so'),  'mediapipe/tasks/c'),   # Linux/Mac
    ],
    datas=[
        ('pose_landmarker_full.task', '.'),      # модель MediaPipe
        (os.path.join(mediapipe_path, 'modules'), 'mediapipe/modules'),
    ],
    hiddenimports=[
        # MediaPipe core
        'mediapipe',
        'mediapipe.python',
        'mediapipe.python._framework_bindings',

        # MediaPipe Tasks — добавлены недостающие
        'mediapipe.tasks',
        'mediapipe.tasks.c',
        'mediapipe.tasks.core',
        'mediapipe.tasks.python',
        'mediapipe.tasks.python.core',
        'mediapipe.tasks.python.core._task_base',
        'mediapipe.tasks.python.vision',
        'mediapipe.tasks.python.vision.core',
        'mediapipe.tasks.python.vision.pose_landmarker',
        'mediapipe.tasks.python.components',
        'mediapipe.tasks.python.components.containers',
        'mediapipe.tasks.python.components.containers.landmark',

        # Зависимости
        'cv2',
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy.core._methods',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='AI_Fitness_Coach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # поставь False чтобы скрыть окно консоли
    icon=None,      # укажи путь к .ico если нужна иконка
)
