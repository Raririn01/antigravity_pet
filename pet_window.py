"""
Desktop Pet & Quick Chat Companion Window implementation using PyQt6.
Fully integrated with Antigravity 2.0:
1. Hover over pet shows mini choice pill ([✎] [॥]) to open chat or app.
2. Single click toggles Quick Chat bar with anchor position preserved.
3. Can hide/collapse Quick Chat bar even while working/thinking.
4. Double-click launches & focuses Antigravity 2.0.
5. Persistent conversation session synced directly to Antigravity 2.0.
6. Dragging pet plays running animation (running-right / running-left).
7. Rich '+' button menu with Plugins/Skills and real Antigravity 2.0 conversation history.
"""

import os
import sys
import glob
import math
import time
import json
import shutil
import ctypes
from ctypes import wintypes
import threading
import webbrowser
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QPoint, QTimer, QRectF, pyqtSignal, QObject, QSettings
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QAction, QContextMenuEvent,
    QMouseEvent, QTransform, QColor, QFont, QPen, QBrush, QCursor
)
from PyQt6.QtWidgets import (
    QWidget, QMenu, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QTextEdit, QApplication
)
from PIL import Image

from spritesheet import SpriteSheet, CELL_WIDTH, CELL_HEIGHT
from antigravity_bridge import AntigravityWatcher, start_http_server


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    rgba = pil_img.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


def sync_conversation_to_antigravity(conversation_id: str):
    """Syncs conversation DB and transcript files from CLI to Antigravity 2.0 and IDE."""
    if not conversation_id:
        return
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    src_base = os.path.join(user_profile, ".gemini", "antigravity-cli")
    targets = [
        os.path.join(user_profile, ".gemini", "antigravity"),
        os.path.join(user_profile, ".gemini", "antigravity-ide")
    ]
    for dst_base in targets:
        try:
            # 1. DB file
            src_db = os.path.join(src_base, "conversations", f"{conversation_id}.db")
            dst_db_dir = os.path.join(dst_base, "conversations")
            os.makedirs(dst_db_dir, exist_ok=True)
            if os.path.isfile(src_db):
                shutil.copy2(src_db, os.path.join(dst_db_dir, f"{conversation_id}.db"))

            # 2. Pbtxt
            src_pb = os.path.join(src_base, "annotations", f"{conversation_id}.pbtxt")
            dst_pb_dir = os.path.join(dst_base, "annotations")
            os.makedirs(dst_pb_dir, exist_ok=True)
            if os.path.isfile(src_pb):
                shutil.copy2(src_pb, os.path.join(dst_pb_dir, f"{conversation_id}.pbtxt"))

            # 3. Brain logs & transcript
            src_brain = os.path.join(src_base, "brain", conversation_id)
            dst_brain = os.path.join(dst_base, "brain", conversation_id)
            if os.path.isdir(src_brain):
                shutil.copytree(src_brain, dst_brain, dirs_exist_ok=True)
        except Exception:
            pass


def get_recent_antigravity_conversations(limit: int = 8):
    """Retrieves real recent conversation titles from Antigravity 2.0."""
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    roots = [
        os.path.join(user_profile, ".gemini", "antigravity", "brain"),
        os.path.join(user_profile, ".gemini", "antigravity-ide", "brain"),
        os.path.join(user_profile, ".gemini", "antigravity-cli", "brain")
    ]
    seen = set()
    convos = []
    for r in roots:
        if not os.path.isdir(r):
            continue
        for p in glob.glob(os.path.join(r, "*", ".system_generated", "logs", "transcript.jsonl")):
            cid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p))))
            if cid in seen:
                continue
            seen.add(cid)
            mtime = os.path.getmtime(p)
            title = ""
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if '"USER_INPUT"' in line:
                            step = json.loads(line)
                            c = str(step.get("content") or "")
                            if "<USER_REQUEST>" in c:
                                c = c.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
                            title = c.replace("\n", " ")[:36].strip()
                            break
            except Exception:
                pass
            if not title:
                title = f"บทสนทนา #{cid[:8]}"
            convos.append({"id": cid, "title": title, "mtime": mtime})
    convos.sort(key=lambda x: x["mtime"], reverse=True)
    return convos[:limit]


class StateSignalEmitter(QObject):
    state_received = pyqtSignal(str, str)
    hotkey_triggered = pyqtSignal()
    appshot_signal = pyqtSignal()
    select_pet_signal = pyqtSignal(str)
    settings_changed_signal = pyqtSignal(dict)
    chat_completed_signal = pyqtSignal(str, str, str)
    call_pet_signal = pyqtSignal()


class DesktopPet(QWidget):
    def __init__(self, spritesheet_path: str):
        super().__init__()

        self.setWindowTitle("Antigravity Desktop Pet")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

        self.scale_factor = 0.68
        self.is_always_on_top = True
        self.live_sync_antigravity = True
        self.show_status_bubble = True
        self.auto_roam = False
        self.mini_mode = False
        self.floating_mode = "collapsed"  # "collapsed", "composer", "status"
        self.activity_tray_visible = False
        self.voice_listening = False
        self.quick_chat_mode = False

        self.preferences = QSettings("Antigravity", "DesktopPet")
        self.active_pet_id = "hime"
        self.status_message = "พร้อมใช้งาน"
        self.status_message_expire_time = time.time() + 3.0

        self.current_action = "idle"
        self.frame_index = 0
        self.animations_enabled = True
        self.facing_direction = 1
        self.pixmap_cache: Dict[str, List[QPixmap]] = {}

        # Dragging & clicking detection
        self.is_dragging = False
        self.has_dragged = False
        self.press_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.last_drag_x = 0
        self.last_user_interaction = time.time()

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.default_spritesheet_path = spritesheet_path
        self.current_spritesheet_path = spritesheet_path

        # Chat session state for Antigravity 2.0
        self.is_thinking = False
        self.active_conversation_id = str(self.preferences.value("active_conversation_id", "") or "")
        self.last_response_text = ""

        # Load pet sprites
        self.load_spritesheet(spritesheet_path)

        # Build UI Elements
        self._init_ui()

        # Timers
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_animation_tick)
        self.anim_timer.start(125)

        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self._on_ai_tick)
        self.ai_timer.start(1000)

        # Single vs Double click disambiguation timer
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self._on_single_click)

        # Hover mini-pill hide timer
        self.hover_hide_timer = QTimer(self)
        self.hover_hide_timer.setSingleShot(True)
        self.hover_hide_timer.timeout.connect(self._on_hover_timeout)

        # Signals & Bridge
        self.state_emitter = StateSignalEmitter()
        self.state_emitter.state_received.connect(self._on_external_state)
        self.state_emitter.hotkey_triggered.connect(self._on_hotkey)
        self.state_emitter.select_pet_signal.connect(self._on_select_pet_slot)
        self.state_emitter.settings_changed_signal.connect(self.apply_settings)
        self.state_emitter.chat_completed_signal.connect(self._on_chat_completed)
        self.state_emitter.call_pet_signal.connect(self._on_call_pet_slot)
        self.state_emitter.appshot_signal.connect(self.capture_appshot)

        self.ag_watcher = AntigravityWatcher(on_state_change=self._on_bridge_state_change)
        self.ag_poll_timer = QTimer(self)
        self.ag_poll_timer.timeout.connect(self._poll_antigravity)
        self.ag_poll_timer.start(350)

        # Start HTTP Server on port 21420
        self.http_server = start_http_server(port=21420, pet_window=self)

        # Global Hotkey
        self._init_global_hotkey()

    def _init_ui(self):
        """Creates the unified Glassmorphic Capsule bar and floating Activity Tray matching ChatGPT Pet spec."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(6)

        # 1. Response Card Popup
        self.response_card = QFrame(self)
        self.response_card.setStyleSheet("""
            QFrame {
                background-color: rgba(24, 24, 27, 245);
                border: 1px solid #3f3f46;
                border-radius: 16px;
            }
        """)
        resp_layout = QVBoxLayout(self.response_card)
        resp_layout.setContentsMargins(14, 10, 14, 10)
        resp_layout.setSpacing(6)

        resp_header = QHBoxLayout()
        self.resp_title = QLabel("✦ Antigravity 2.0", self.response_card)
        self.resp_title.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold;")
        self.copy_btn = QPushButton("คัดลอก", self.response_card)
        self.copy_btn.setFixedSize(50, 22)
        self.copy_btn.setStyleSheet("""
            QPushButton { background: #3f3f46; color: #f4f4f5; border-radius: 11px; font-size: 11px; }
            QPushButton:hover { background: #52525b; }
        """)
        self.copy_btn.clicked.connect(self._copy_response)
        self.close_resp_btn = QPushButton("✕", self.response_card)
        self.close_resp_btn.setFixedSize(22, 22)
        self.close_resp_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #71717a; border: none; font-size: 12px; }
            QPushButton:hover { color: #f4f4f5; }
        """)
        self.close_resp_btn.clicked.connect(self.hide_response_card)
        resp_header.addWidget(self.resp_title)
        resp_header.addStretch()
        resp_header.addWidget(self.copy_btn)
        resp_header.addWidget(self.close_resp_btn)
        resp_layout.addLayout(resp_header)

        self.resp_text = QTextEdit(self.response_card)
        self.resp_text.setReadOnly(True)
        self.resp_text.setFixedHeight(120)
        self.resp_text.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #fafafa;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        resp_layout.addWidget(self.resp_text)
        self.response_card.hide()
        self.main_layout.addWidget(self.response_card)

        # 2. Activity Tray Floating Card (Phase 1.3)
        self.activity_tray = QFrame(self)
        self.activity_tray.setObjectName("activity_tray")
        self.activity_tray.setStyleSheet("""
            QFrame#activity_tray {
                background-color: rgba(22, 22, 26, 252);
                border: 1px solid #3f3f46;
                border-radius: 16px;
            }
        """)
        tray_layout = QVBoxLayout(self.activity_tray)
        tray_layout.setContentsMargins(12, 10, 12, 10)
        tray_layout.setSpacing(6)

        tray_head = QHBoxLayout()
        self.tray_title = QLabel("🔔 กิจกรรม AI ล่าสุด (Activity Tray)", self.activity_tray)
        self.tray_title.setStyleSheet("color: #f4f4f5; font-size: 11px; font-weight: bold;")
        self.tray_badge = QLabel("0 งาน", self.activity_tray)
        self.tray_badge.setStyleSheet("background: #27272a; color: #a1a1aa; border-radius: 8px; font-size: 10px; padding: 2px 6px;")
        self.close_tray_btn = QPushButton("✕", self.activity_tray)
        self.close_tray_btn.setFixedSize(20, 20)
        self.close_tray_btn.setStyleSheet("QPushButton { background: transparent; color: #71717a; border: none; font-size: 12px; } QPushButton:hover { color: #f4f4f5; }")
        self.close_tray_btn.clicked.connect(self.toggle_activity_tray)
        tray_head.addWidget(self.tray_title)
        tray_head.addWidget(self.tray_badge)
        tray_head.addStretch()
        tray_head.addWidget(self.close_tray_btn)
        tray_layout.addLayout(tray_head)

        self.tray_items_container = QWidget(self.activity_tray)
        self.tray_items_layout = QVBoxLayout(self.tray_items_container)
        self.tray_items_layout.setContentsMargins(0, 0, 0, 0)
        self.tray_items_layout.setSpacing(4)
        tray_layout.addWidget(self.tray_items_container)
        self.activity_tray.hide()
        self.main_layout.addWidget(self.activity_tray)

        # 3. Autocomplete Popup for @ and $ (Phase 2.2)
        self.autocomplete_popup = QFrame(self)
        self.autocomplete_popup.setObjectName("autocomplete_popup")
        self.autocomplete_popup.setStyleSheet("""
            QFrame#autocomplete_popup {
                background-color: rgba(24, 24, 27, 250);
                border: 1px solid #3f3f46;
                border-radius: 12px;
            }
        """)
        ac_layout = QVBoxLayout(self.autocomplete_popup)
        ac_layout.setContentsMargins(8, 6, 8, 6)
        ac_layout.setSpacing(4)
        self.ac_title = QLabel("📄 บริบท", self.autocomplete_popup)
        self.ac_title.setStyleSheet("color: #a1a1aa; font-size: 10px; font-weight: bold; padding: 2px 4px;")
        ac_layout.addWidget(self.ac_title)

        self.ac_list_container = QWidget(self.autocomplete_popup)
        self.ac_list_layout = QVBoxLayout(self.ac_list_container)
        self.ac_list_layout.setContentsMargins(0, 0, 0, 0)
        self.ac_list_layout.setSpacing(2)
        ac_layout.addWidget(self.ac_list_container)
        self.autocomplete_popup.hide()
        self.main_layout.addWidget(self.autocomplete_popup)

        # 4. Pet Sitting Space
        self.pet_space = QWidget(self)
        self.pet_space_height = int(CELL_HEIGHT * self.scale_factor)
        self.pet_space.setFixedHeight(self.pet_space_height)
        self.main_layout.addWidget(self.pet_space)

        # 5. Unified Glassmorphic Floating Capsule Pill (Phase 2.1)
        self.chat_pill = QFrame(self)
        self.chat_pill.setFixedHeight(50)
        self.chat_pill.setStyleSheet("""
            QFrame#chat_pill {
                background-color: rgba(31, 31, 35, 240);
                border: 1px solid #36363c;
                border-radius: 25px;
            }
        """)
        self.chat_pill.setObjectName("chat_pill")
        self.pill_layout = QHBoxLayout(self.chat_pill)
        self.pill_layout.setContentsMargins(8, 4, 8, 4)
        self.pill_layout.setSpacing(6)

        # A. Collapsed Capsule Bar: [✎ เริ่มแชท] [🎙] [🔔] [॥]
        self.collapsed_bar = QWidget(self.chat_pill)
        cb_layout = QHBoxLayout(self.collapsed_bar)
        cb_layout.setContentsMargins(4, 0, 4, 0)
        cb_layout.setSpacing(6)

        self.btn_open_composer = QPushButton("✎ เริ่มแชท", self.collapsed_bar)
        self.btn_open_composer.setToolTip("เปิดกล่องพิมพ์ข้อความ (Win+Alt+P)")
        self.btn_open_composer.setStyleSheet("""
            QPushButton {
                background: #27272a;
                color: #e4e4e7;
                font-size: 12px;
                font-weight: 500;
                border: 1px solid #3f3f46;
                border-radius: 15px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: #3f3f46;
                color: #ffffff;
            }
        """)
        self.btn_open_composer.clicked.connect(lambda: self.set_floating_mode("composer"))

        self.btn_voice = QPushButton("🎙", self.collapsed_bar)
        self.btn_voice.setToolTip("สนทนาด้วยเสียง (Voice Chat)")
        self.btn_voice.setFixedSize(32, 32)
        self.btn_voice.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                font-size: 15px;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: #27272a;
                color: #38bdf8;
            }
        """)
        self.btn_voice.clicked.connect(self.toggle_voice_mode)

        self.btn_bell = QPushButton("🔔", self.collapsed_bar)
        self.btn_bell.setToolTip("เปิด Activity Tray (รายการงานย่อย)")
        self.btn_bell.setFixedSize(34, 32)
        self.btn_bell.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                font-size: 14px;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: #27272a;
                color: #facc15;
            }
        """)
        self.btn_bell.clicked.connect(self.toggle_activity_tray)

        self.btn_open_app = QPushButton("॥", self.collapsed_bar)
        self.btn_open_app.setToolTip("เปิด Antigravity 2.0")
        self.btn_open_app.setFixedSize(30, 32)
        self.btn_open_app.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: #27272a;
                color: #ffffff;
            }
        """)
        self.btn_open_app.clicked.connect(self.open_antigravity)

        cb_layout.addWidget(self.btn_open_composer)
        cb_layout.addWidget(self.btn_voice)
        cb_layout.addWidget(self.btn_bell)
        cb_layout.addWidget(self.btn_open_app)
        self.pill_layout.addWidget(self.collapsed_bar)

        # B. Expanded Composer Bar: [+] [chat_input] [📷] [↑] [⌵]
        self.composer_bar = QWidget(self.chat_pill)
        comp_layout = QHBoxLayout(self.composer_bar)
        comp_layout.setContentsMargins(2, 0, 2, 0)
        comp_layout.setSpacing(6)

        self.plus_btn = QPushButton("+", self.composer_bar)
        self.plus_btn.setToolTip("เมนูบริบท สกิล และประวัติ")
        self.plus_btn.setFixedSize(30, 30)
        self.plus_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9ca3af;
                font-size: 20px;
                font-weight: 300;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: #2d2d32;
                color: #ffffff;
            }
        """)
        self.plus_btn.clicked.connect(self._show_plus_menu)

        self.chat_input = QLineEdit(self.composer_bar)
        self.chat_input.setPlaceholderText("เริ่มแชทใหม่ (พิมพ์ @ หรือ $ เพื่อแท็ก)")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f3f4f6;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                font-size: 13.5px;
                padding-left: 2px;
            }
            QLineEdit::placeholder {
                color: #71717a;
            }
        """)
        self.chat_input.returnPressed.connect(self._submit_quick_chat)
        self.chat_input.textEdited.connect(self._on_chat_text_changed)

        self.appshot_btn = QPushButton("📷", self.composer_bar)
        self.appshot_btn.setToolTip("จับภาพหน้าจอปัจจุบัน (Appshot - Win+Alt+S)")
        self.appshot_btn.setFixedSize(28, 28)
        self.appshot_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                font-size: 14px;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #2d2d32;
                color: #38bdf8;
            }
        """)
        self.appshot_btn.clicked.connect(self.capture_appshot)

        self.send_btn = QPushButton("↑", self.composer_bar)
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a855f7, stop:1 #7c3aed);
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c084fc, stop:1 #9333ea);
            }
        """)
        self.send_btn.clicked.connect(self._submit_quick_chat)

        self.btn_collapse = QPushButton("⌵", self.composer_bar)
        self.btn_collapse.setToolTip("พับเก็บแถบควบคุม")
        self.btn_collapse.setFixedSize(26, 26)
        self.btn_collapse.setStyleSheet("QPushButton { background: transparent; color: #a1a1aa; border: none; font-size: 14px; font-weight: bold; } QPushButton:hover { color: #fff; }")
        self.btn_collapse.clicked.connect(lambda: self.set_floating_mode("collapsed"))

        comp_layout.addWidget(self.plus_btn)
        comp_layout.addWidget(self.chat_input)
        comp_layout.addWidget(self.appshot_btn)
        comp_layout.addWidget(self.send_btn)
        comp_layout.addWidget(self.btn_collapse)
        self.composer_bar.hide()
        self.pill_layout.addWidget(self.composer_bar)

        # C. Status / Thinking Bar: [●] [กำลังคิด...] [✎] [🔔] [⌵]
        self.status_bar = QWidget(self.chat_pill)
        st_layout = QHBoxLayout(self.status_bar)
        st_layout.setContentsMargins(6, 0, 6, 0)
        st_layout.setSpacing(6)

        self.status_dot = QLabel("●", self.status_bar)
        self.status_dot.setStyleSheet("color: #38bdf8; font-size: 14px;")

        self.th_main_label = QLabel("กำลังคิด...", self.status_bar)
        self.th_main_label.setStyleSheet("color: #f4f4f5; font-size: 12.5px; font-weight: 600;")

        self.btn_edit = QPushButton("✎", self.status_bar)
        self.btn_edit.setToolTip("เปิดกล่องพิมพ์ข้อความ")
        self.btn_edit.setFixedSize(26, 26)
        self.btn_edit.setStyleSheet("QPushButton { background: transparent; color: #a1a1aa; border: none; font-size: 13px; } QPushButton:hover { color: #fff; }")
        self.btn_edit.clicked.connect(self._cancel_and_edit)

        self.btn_status_bell = QPushButton("🔔", self.status_bar)
        self.btn_status_bell.setToolTip("เปิด Activity Tray")
        self.btn_status_bell.setFixedSize(26, 26)
        self.btn_status_bell.setStyleSheet("QPushButton { background: transparent; color: #a1a1aa; border: none; font-size: 13px; } QPushButton:hover { color: #fff; }")
        self.btn_status_bell.clicked.connect(self.toggle_activity_tray)

        self.btn_status_collapse = QPushButton("⌵", self.status_bar)
        self.btn_status_collapse.setToolTip("พับเก็บ")
        self.btn_status_collapse.setFixedSize(26, 26)
        self.btn_status_collapse.setStyleSheet("QPushButton { background: transparent; color: #a1a1aa; border: none; font-size: 14px; font-weight: bold; } QPushButton:hover { color: #fff; }")
        self.btn_status_collapse.clicked.connect(lambda: self.set_floating_mode("collapsed"))

        st_layout.addWidget(self.status_dot)
        st_layout.addWidget(self.th_main_label)
        st_layout.addStretch()
        st_layout.addWidget(self.btn_edit)
        st_layout.addWidget(self.btn_status_bell)
        st_layout.addWidget(self.btn_status_collapse)
        self.status_bar.hide()
        self.pill_layout.addWidget(self.status_bar)

        self.main_layout.addWidget(self.chat_pill)

        # Initial mode
        self.set_floating_mode("collapsed")
        self.update_window_size(preserve_pet_pos=False)

    def get_pet_render_offset(self, in_composer_mode: bool) -> tuple[int, int]:
        target_w = int(CELL_WIDTH * self.scale_factor)
        card_offset = 160 if self.response_card.isVisible() else 0
        tray_offset = 200 if getattr(self, "activity_tray_visible", False) else 0
        ac_offset = 120 if (hasattr(self, "autocomplete_popup") and self.autocomplete_popup.isVisible()) else 0
        top_offset = card_offset + tray_offset + ac_offset

        if in_composer_mode:
            pet_x = 440 - target_w - 38
        else:
            pet_x = max(0, (self.width() - target_w) // 2)
        pet_y = top_offset + 10
        return pet_x, pet_y

    def update_window_size(self, preserve_pet_pos: bool = True):
        """Anchors pet in exact screen position when toggling bar states."""
        target_w = int(CELL_WIDTH * self.scale_factor)
        self.pet_space_height = int(CELL_HEIGHT * self.scale_factor) if not self.mini_mode else 0
        if not self.mini_mode:
            self.pet_space.setFixedHeight(self.pet_space_height)
            self.pet_space.show()
        else:
            self.pet_space.hide()

        card_offset = 160 if self.response_card.isVisible() else 0
        tray_offset = 200 if getattr(self, "activity_tray_visible", False) else 0
        ac_offset = 120 if (hasattr(self, "autocomplete_popup") and self.autocomplete_popup.isVisible()) else 0

        is_comp = (self.floating_mode == "composer")

        if preserve_pet_pos and not self.mini_mode:
            old_pet_x, old_pet_y = self.get_pet_render_offset(is_comp)
            current_screen_pet_x = self.x() + old_pet_x
            current_screen_pet_y = self.y() + old_pet_y

        if self.floating_mode == "composer":
            w = 440
        elif self.floating_mode == "status":
            w = 280
        else:
            w = 210

        h = self.pet_space_height + 56 + card_offset + tray_offset + ac_offset
        self.setFixedSize(w, h)

        if preserve_pet_pos and not self.mini_mode:
            new_pet_x, new_pet_y = self.get_pet_render_offset(is_comp)
            new_win_x = current_screen_pet_x - new_pet_x
            new_win_y = current_screen_pet_y - new_pet_y
            self.move(int(new_win_x), int(new_win_y))

        self.update()

    def set_floating_mode(self, mode: str):
        self.floating_mode = mode
        if mode == "composer":
            self.collapsed_bar.hide()
            self.status_bar.hide()
            self.composer_bar.show()
            self.quick_chat_mode = True
            self.chat_input.setFocus()
        elif mode == "status":
            self.collapsed_bar.hide()
            self.composer_bar.hide()
            self.status_bar.show()
            self.quick_chat_mode = False
        else:  # collapsed
            self.composer_bar.hide()
            self.status_bar.hide()
            self.collapsed_bar.show()
            self.quick_chat_mode = False
            if hasattr(self, "autocomplete_popup"):
                self.autocomplete_popup.hide()

        self.update_window_size(preserve_pet_pos=True)

    def toggle_quick_chat_mode(self):
        if self.floating_mode == "composer":
            self.set_floating_mode("collapsed")
        else:
            self.set_floating_mode("composer")

    def toggle_activity_tray(self):
        self.activity_tray_visible = not self.activity_tray_visible
        if self.activity_tray_visible:
            self.refresh_activity_tray()
            self.activity_tray.show()
            self.activity_tray.raise_()
        else:
            self.activity_tray.hide()
        self.update_window_size(preserve_pet_pos=True)

    def refresh_activity_tray(self):
        while self.tray_items_layout.count():
            item = self.tray_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        threads = getattr(self.ag_watcher, "recent_threads", [])[:4]
        self.tray_badge.setText(f"{len(threads)} เธรด")

        has_attention = any(t.get("status") in ("needs_input", "blocked", "ready") for t in threads)
        self._update_bell_badge(has_attention, threads[0].get("status") if threads else "idle")

        if not threads:
            empty_lbl = QLabel("ยังไม่มีกิจกรรมงานย่อยที่บันทึกไว้", self.activity_tray)
            empty_lbl.setStyleSheet("color: #71717a; font-size: 11px; padding: 6px;")
            self.tray_items_layout.addWidget(empty_lbl)
            return

        for t in threads:
            row_frame = QFrame(self.activity_tray)
            status = t.get("status", "idle")
            row_frame.setStyleSheet("""
                QFrame {
                    background-color: #27272a;
                    border: 1px solid #36363c;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: #323238;
                    border-color: #52525b;
                }
            """)
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(8, 5, 8, 5)
            row_layout.setSpacing(6)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(1)
            title_lbl = QLabel(t.get("title", "Thread"), row_frame)
            title_lbl.setStyleSheet("color: #f4f4f5; font-size: 11.5px; font-weight: 600;")
            sub_lbl = QLabel(f"{t.get('summary', '')} · {t.get('age_text', '')}", row_frame)
            sub_lbl.setStyleSheet("color: #a1a1aa; font-size: 9.5px;")
            info_layout.addWidget(title_lbl)
            info_layout.addWidget(sub_lbl)
            row_layout.addLayout(info_layout)
            row_layout.addStretch()

            badge_style = {
                "needs_input": ("💬 รอตอบกลับ", "#854d0e", "#fef08a"),
                "blocked": ("⚠️ ติดขัด", "#7f1d1d", "#fca5a5"),
                "ready": ("✨ เสร็จแล้ว", "#14532d", "#86efac"),
                "running": ("⚡ กำลังคิด", "#075985", "#7dd3fc"),
                "idle": ("ก่อนหน้า", "#334155", "#cbd5e1"),
            }.get(status, ("ปกติ", "#27272a", "#a1a1aa"))

            badge_lbl = QLabel(badge_style[0], row_frame)
            badge_lbl.setStyleSheet(f"background-color: {badge_style[1]}; color: {badge_style[2]}; font-size: 9.5px; font-weight: bold; border-radius: 5px; padding: 2px 6px;")
            row_layout.addWidget(badge_lbl)

            cid = t.get("id", "")
            title = t.get("title", "")
            row_frame.mousePressEvent = lambda e, c=cid, tit=title: self._on_tray_item_clicked(c, tit)
            row_frame.setCursor(Qt.CursorShape.PointingHandCursor)
            self.tray_items_layout.addWidget(row_frame)

    def _on_tray_item_clicked(self, cid: str, title: str):
        self._switch_conversation(cid, title)
        self.toggle_activity_tray()
        self.open_antigravity()

    def _update_bell_badge(self, has_attention: bool, top_status: str):
        bell_btns = []
        if hasattr(self, "btn_bell"):
            bell_btns.append(self.btn_bell)
        if hasattr(self, "btn_status_bell"):
            bell_btns.append(self.btn_status_bell)

        for btn in bell_btns:
            if has_attention:
                dot_color = "#facc15" if top_status == "needs_input" else ("#ef4444" if top_status == "blocked" else "#22c55e")
                btn.setText("🔔●")
                btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {dot_color}; font-size: 13px; border: none; font-weight: bold; }}")
            else:
                btn.setText("🔔")
                btn.setStyleSheet("QPushButton { background: transparent; color: #a1a1aa; font-size: 13px; border: none; } QPushButton:hover { color: #f4f4f5; }")

    def _update_status_bar(self, status: str, text: str):
        if not hasattr(self, "status_dot"):
            return
        dot_colors = {
            "running": "#38bdf8",
            "needs_input": "#facc15",
            "blocked": "#ef4444",
            "ready": "#22c55e",
            "idle": "#71717a",
        }
        self.status_dot.setStyleSheet(f"color: {dot_colors.get(status, '#38bdf8')}; font-size: 14px;")
        self.th_main_label.setText(text[:28])
        if self.floating_mode != "composer":
            self.set_floating_mode("status")

    def _on_chat_text_changed(self, text: str):
        cursor_pos = self.chat_input.cursorPosition()
        prefix = text[:cursor_pos]

        if prefix.endswith("@"):
            self._show_autocomplete("file")
        elif prefix.endswith("$"):
            self._show_autocomplete("skill")
        else:
            if hasattr(self, "autocomplete_popup") and self.autocomplete_popup.isVisible():
                self.autocomplete_popup.hide()
                self.update_window_size(preserve_pet_pos=True)

    def _show_autocomplete(self, mode: str):
        if not hasattr(self, "autocomplete_popup"):
            return
        while self.ac_list_layout.count():
            item = self.ac_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if mode == "file":
            candidates = [
                "ROADMAP.md", "README.md", "settings.html", "main.py",
                "pet_window.py", "antigravity_bridge.py", "spritesheet.py",
                "scripts/pet_tools.py", "assets/hime_pet.png", "assets/swan_pet.png"
            ]
            self.ac_title.setText("📄 อ้างอิงไฟล์ใน Workspace (@)")
        else:
            candidates = [
                "create-pet", "ui-ux-pro-max", "antigravity-guide",
                "alphagenome-single-variant-analysis", "credentials"
            ]
            self.ac_title.setText("⚡ เรียกใช้ Skill ($)")

        for c in candidates[:6]:
            btn = QPushButton(c, self.autocomplete_popup)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #e4e4e7;
                    font-size: 11.5px;
                    text-align: left;
                    padding: 3px 6px;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background: #3f3f46;
                    color: #38bdf8;
                }
            """)
            btn.clicked.connect(lambda checked=False, item_name=c, m=mode: self._insert_autocomplete_tag(item_name, m))
            self.ac_list_layout.addWidget(btn)

        self.autocomplete_popup.show()
        self.autocomplete_popup.raise_()
        self.update_window_size(preserve_pet_pos=True)

    def _insert_autocomplete_tag(self, item_name: str, mode: str):
        curr = self.chat_input.text()
        pos = self.chat_input.cursorPosition()
        if mode == "file":
            idx = curr.rfind("@", 0, pos)
            if idx != -1:
                new_text = curr[:idx] + f"@[{item_name}] " + curr[pos:]
                self.chat_input.setText(new_text)
                self.chat_input.setCursorPosition(idx + len(item_name) + 4)
        else:
            idx = curr.rfind("$", 0, pos)
            if idx != -1:
                new_text = curr[:idx] + f"${item_name} " + curr[pos:]
                self.chat_input.setText(new_text)
                self.chat_input.setCursorPosition(idx + len(item_name) + 2)

        self.autocomplete_popup.hide()
        self.chat_input.setFocus()
        self.update_window_size(preserve_pet_pos=True)

    def capture_appshot(self):
        """Captures active window/screen and attaches it to Quick Chat."""
        was_visible = self.isVisible()
        self.hide()
        QApplication.processEvents()
        time.sleep(0.08)

        screen = QApplication.primaryScreen()
        if screen:
            pix = screen.grabWindow(0)
            appshot_path = os.path.join(self.assets_dir, "appshot_latest.png")
            pix.save(appshot_path, "PNG")

        if was_visible:
            self.show()
            self.raise_()
            self.activateWindow()

        rel_path = "assets/appshot_latest.png"
        existing = self.chat_input.text()
        if f"@[{rel_path}]" not in existing:
            self.chat_input.setText(f"@[{rel_path}] " + existing)

        self.set_floating_mode("composer")
        self.chat_input.setFocus()
        self.set_action("review", "จับภาพหน้าจอเรียบร้อย! 📷")

    def toggle_mini_mode(self):
        self.mini_mode = not self.mini_mode
        self.preferences.setValue("mini_mode", self.mini_mode)
        if self.mini_mode:
            self.pet_space.hide()
            self.set_action("idle", "")
        else:
            self.pet_space.show()
        self.update_window_size(preserve_pet_pos=False)

    def toggle_voice_mode(self):
        self.voice_listening = not self.voice_listening
        if self.voice_listening:
            self.set_floating_mode("composer")
            self.chat_input.setPlaceholderText("🎙 กำลังฟังเสียงสดของคุณ... (คลิกอีกครั้งเพื่อส่ง)")
            self.set_action("waving", "กำลังฟังเสียงสดของคุณค่ะ 🎙")
        else:
            self.chat_input.setPlaceholderText("เริ่มแชทใหม่ (พิมพ์ @ หรือ $ เพื่อแท็ก)")
            if not self.chat_input.text().strip():
                self.chat_input.setText("ช่วยสรุปภาพรวม Roadmap และกิจกรรมล่าสุดให้หน่อย")
            self.set_action("review", "บันทึกเสียงแล้ว พร้อมส่ง ✨")

    def enterEvent(self, event):
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)

    def _on_hover_timeout(self):
        pass

    def _show_plus_menu(self):
        """Requirement: Rich '+' popup menu matching Image 2 & 3 with Plugins & Conversations."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e24;
                border: 1px solid #383a46;
                border-radius: 14px;
                padding: 6px;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QMenu::section {
                color: #9ca3af;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 14px 4px 14px;
                background: transparent;
            }
            QMenu::item {
                color: #f4f4f5;
                font-size: 13px;
                padding: 7px 18px 7px 12px;
                border-radius: 8px;
                margin: 1px 4px;
            }
            QMenu::item:selected {
                background-color: #2d2d38;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #343744;
                margin: 4px 8px;
            }
        """)

        # 1. Quick Actions
        act_new = menu.addAction("➕ เริ่มแชทใหม่ (เริ่มบทสนทนาใหม่ใน Antigravity 2.0)")
        act_new.triggered.connect(self._reset_chat)

        act_appshot = menu.addAction("📷 จับภาพหน้าจอปัจจุบัน (Appshot - Win+Alt+S)")
        act_appshot.triggered.connect(self.capture_appshot)

        act_tray = menu.addAction("🔔 ถาดกิจกรรม AI (Activity Tray)")
        act_tray.triggered.connect(self.toggle_activity_tray)

        act_mini = menu.addAction("🔲 โหมด Mini (ซ่อน/แสดงสัตว์เลี้ยง)" if not self.mini_mode else "🐱 แสดงตัวสัตว์เลี้ยง")
        act_mini.triggered.connect(self.toggle_mini_mode)

        act_voice = menu.addAction("🎙 สนทนาด้วยเสียง (Voice Input)")
        act_voice.triggered.connect(self.toggle_voice_mode)

        menu.addSeparator()

        # 2. Plugins & Skills Section (Matches Image 2)
        menu.addSection("ปลั๊กอิน & สกิล (Plugins & Skills)")
        plugins = [
            ("🎨 tldraw", "วาดและออกแบบไดอะแกรมร่วมกับเอเจนต์", "@tldraw "),
            ("🔍 ค้นหาเว็บ", "ค้นหาข้อมูลออนไลน์และเอกสาร (Web Search)", "@web-search "),
            ("⚡ รันโค้ด", "รันคำสั่งและประมวลผลโค้ด (Code Executor)", "@code-executor "),
            ("🌐 เว็บเบราว์เซอร์", "ควบคุมและเปิดเว็บเบราว์เซอร์อัตโนมัติ (Browser)", "@browser "),
            ("📁 ไฟล์และข้อมูล", "อ่าน ตรวจสอบ และแก้ไขไฟล์ในโปรเจกต์", "@file-tools "),
            ("📄 เอกสาร & PDF", "อ่าน สร้าง และวิเคราะห์เอกสาร PDF", "@pdf "),
        ]
        for name, desc, tag in plugins:
            act = menu.addAction(f"{name}   {desc}")
            act.triggered.connect(lambda checked=False, t=tag: self._insert_plugin_tag(t))

        menu.addSeparator()

        # 3. Conversations in Antigravity 2.0 Section (Matches Image 3)
        menu.addSection("การสนทนาใน Antigravity 2.0")
        recent_convos = get_recent_antigravity_conversations(limit=7)
        if recent_convos:
            for item in recent_convos:
                cid = item["id"]
                title = item["title"]
                is_active = (cid == self.active_conversation_id)
                prefix = "✓ " if is_active else "💬 "
                act_convo = menu.addAction(f"{prefix}{title}")
                act_convo.setToolTip(f"ID: {cid}")
                act_convo.triggered.connect(lambda checked=False, c=cid, t=title: self._switch_conversation(c, t))
        else:
            act_none = menu.addAction("ยังไม่พบบทสนทนา")
            act_none.setEnabled(False)

        menu.addSeparator()

        # 4. App & Settings
        menu.addSection("แอป & การตั้งค่า")
        act_open_ag = menu.addAction("🪐 เปิด Antigravity 2.0")
        act_open_ag.triggered.connect(self.open_antigravity)

        act_settings = menu.addAction("⚙️ ตั้งค่าสัตว์เลี้ยง (Settings UI)...")
        act_settings.triggered.connect(lambda: webbrowser.open("http://127.0.0.1:21420/settings"))

        act_toggle = menu.addAction("สลับโหมดสัตว์เลี้ยงลอยอิสระ" if self.quick_chat_mode else "เปิดแถบแชทลัด")
        act_toggle.triggered.connect(self.toggle_quick_chat_mode)

        # Popup above the plus button
        menu.exec(QCursor.pos())

    def _insert_plugin_tag(self, tag: str):
        self.chat_input.setText(tag + self.chat_input.text())
        self.chat_input.setFocus()

    def _switch_conversation(self, cid: str, title: str):
        """Switches active session to a past Antigravity 2.0 conversation."""
        self.active_conversation_id = cid
        self.preferences.setValue("active_conversation_id", cid)
        self.chat_input.setPlaceholderText(f"ต่อแชท: {title[:25]}...")
        self.set_action("review", f"สลับไปยัง: {title[:20]}")
        self.chat_input.setFocus()

    def _reset_chat(self):
        self.active_conversation_id = ""
        self.preferences.setValue("active_conversation_id", "")
        self.chat_input.clear()
        self.chat_input.setPlaceholderText("เริ่มแชทใหม่")
        self.hide_response_card()
        self.set_thinking(False)
        self.set_action("idle", "เริ่มบทสนทนาใหม่แล้ว")

    def _submit_quick_chat(self):
        """Runs prompt and records in Antigravity 2.0."""
        text = self.chat_input.text().strip()
        if not text:
            return
        self.set_thinking(True, text)
        job_id = threading.get_ident()
        cid = self.active_conversation_id

        def worker(prompt, conversation_id):
            try:
                import subprocess
                cli = os.path.join(os.environ.get("LOCALAPPDATA", ""), "agy", "bin", "agy.exe")
                if not os.path.isfile(cli):
                    cli = "agy"
                args = [cli, "-p", prompt, "--output-format", "json", "--sandbox", "--disable-slash-commands", "--print-timeout", "120s"]
                if conversation_id:
                    args.extend(["--conversation", conversation_id])

                res = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
                out = res.stdout or ""
                err = res.stderr or ""
                resp_text = ""
                new_cid = conversation_id
                if "{" in out and "}" in out:
                    try:
                        json_str = out[out.find("{"):out.rfind("}") + 1]
                        payload = json.loads(json_str)
                        resp_text = payload.get("response", "") or payload.get("error", "")
                        new_cid = payload.get("conversation_id", conversation_id)
                    except Exception:
                        pass

                if not resp_text:
                    resp_text = out.strip() or err.strip()

                if new_cid:
                    sync_conversation_to_antigravity(new_cid)

                if not resp_text:
                    resp_text = "เสร็จเรียบร้อยแล้วค่ะ! ✨"
                self.state_emitter.chat_completed_signal.emit(str(job_id), new_cid or "", resp_text)
            except Exception as e:
                self.state_emitter.chat_completed_signal.emit(str(job_id), cid or "", f"เกิดข้อผิดพลาด: {str(e)}")

        t = threading.Thread(target=worker, args=(text, cid), daemon=True)
        t.start()

    def _on_chat_completed(self, job_id: str, new_conversation_id: str, response: str):
        if new_conversation_id:
            self.active_conversation_id = new_conversation_id
            self.preferences.setValue("active_conversation_id", new_conversation_id)
        self.set_thinking(False)
        self.last_response_text = response
        self.resp_text.setPlainText(response)
        self.response_card.show()
        self.update_window_size(preserve_pet_pos=True)
        self.set_action("review", "เสร็จแล้วค่ะ! ✨")

    def hide_response_card(self):
        self.response_card.hide()
        self.update_window_size(preserve_pet_pos=True)

    def _copy_response(self):
        if self.last_response_text:
            QApplication.clipboard().setText(self.last_response_text)
            self.copy_btn.setText("คัดลอกแล้ว!")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("คัดลอก"))

    def _cancel_and_edit(self):
        self.set_thinking(False)
        self.chat_input.setFocus()
        self.chat_input.selectAll()

    def set_thinking(self, thinking: bool, prompt_text: str = ""):
        self.is_thinking = thinking
        if thinking:
            if hasattr(self, "th_main_label"):
                self.th_main_label.setText(prompt_text or "กำลังคิด...")
            self.set_floating_mode("status")
            self.set_action("thinking", prompt_text or "กำลังคิด...")
        else:
            if self.floating_mode == "status":
                self.set_floating_mode("collapsed")
            if self.current_action == "thinking":
                self.set_action("idle")

    # --- Global Hotkey ---

    def _init_global_hotkey(self):
        def listener():
            user32 = ctypes.windll.user32
            HOTKEY_ID_PET = 1001
            HOTKEY_ID_APPHOT = 1002
            MOD_ALT = 0x0001
            MOD_WIN = 0x0008
            VK_P = 0x50
            VK_S = 0x53
            user32.RegisterHotKey(None, HOTKEY_ID_PET, MOD_ALT | MOD_WIN, VK_P)
            user32.RegisterHotKey(None, HOTKEY_ID_APPHOT, MOD_ALT | MOD_WIN, VK_S)
            try:
                msg = wintypes.MSG()
                while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    if msg.message == 0x0312:
                        if msg.wParam == HOTKEY_ID_PET:
                            self.state_emitter.hotkey_triggered.emit()
                        elif msg.wParam == HOTKEY_ID_APPHOT:
                            self.state_emitter.appshot_signal.emit()
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
            finally:
                user32.UnregisterHotKey(None, HOTKEY_ID_PET)
                user32.UnregisterHotKey(None, HOTKEY_ID_APPHOT)

        t = threading.Thread(target=listener, daemon=True)
        t.start()

    def _on_hotkey(self):
        """Alt + Win + P: Toggle or focus companion."""
        if not self.isVisible():
            self.show()
            self.raise_()
            self.activateWindow()
            self.quick_chat_mode = True
            self.update_window_size(preserve_pet_pos=True)
            self.chat_input.setFocus()
            self.set_action("waving", "สวัสดีค่ะ! ✨")
        else:
            self.raise_()
            self.activateWindow()
            self.chat_input.setFocus()

    def open_antigravity(self):
        """Launches and focuses Antigravity 2.0."""
        user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        local_app_data = os.environ.get("LOCALAPPDATA") or os.path.join(user_profile, "AppData", "Local")
        ag_path = os.path.join(local_app_data, "Programs", "antigravity", "Antigravity.exe")
        if not os.path.isfile(ag_path):
            ag_path = os.path.join(local_app_data, "Programs", "Antigravity IDE", "Antigravity IDE.exe")

        if os.path.isfile(ag_path):
            os.startfile(ag_path)
            user32 = ctypes.windll.user32
            def focus_cb(hwnd, lp):
                buf = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, buf, 256)
                if "Antigravity" in buf.value:
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
                return True
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(focus_cb), 0)
        else:
            webbrowser.open("http://127.0.0.1:21420/settings#activity")

    def select_pet_by_id(self, pet_id: str):
        self.state_emitter.select_pet_signal.emit(pet_id)

    def _on_select_pet_slot(self, pet_id: str):
        self.active_pet_id = pet_id
        self.preferences.setValue("active_pet_id", pet_id)
        if pet_id == "none":
            self.hide()
            return

        if pet_id == "hime":
            sheet = os.path.join(self.assets_dir, "hime_pet.png")
        elif pet_id == "swan":
            sheet = os.path.join(self.assets_dir, "swan_pet.png")
        elif pet_id == "codex":
            sheet = os.path.join(self.assets_dir, "codex_pet.png")
        elif pet_id == "agy_bot":
            sheet = os.path.join(self.assets_dir, "default_pet.png")
        elif pet_id == "custom_agy_chibi_pipeline":
            sheet = os.path.join(self.assets_dir, "custom_agy_chibi_pipeline.png")
        else:
            for candidate in [f"{pet_id}.png", f"{pet_id}_pet.png"]:
                custom_path = os.path.join(self.assets_dir, candidate)
                if os.path.exists(custom_path):
                    sheet = custom_path
                    break
            else:
                sheet = self.default_spritesheet_path

        if os.path.exists(sheet):
            self.load_spritesheet(sheet)
            self.current_spritesheet_path = sheet
            self.update_window_size(preserve_pet_pos=True)
            self.show()
            self.set_action("review", f"{pet_id.capitalize()} พร้อมแล้ว!")

    def _on_call_pet_slot(self):
        self.set_visibility(True)
        self.preferences.setValue("visible", True)
        self.snap_to_bottom_right()
        self.show()
        self.raise_()
        self.activateWindow()
        self.set_action("waving", "ฉันอยู่นี่แล้วค่ะ! ✨", force_reset=True)

    def set_visibility(self, visible: bool):
        if visible:
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()

    def apply_settings(self, data: dict):
        if "visible" in data:
            self.set_visibility(bool(data["visible"]))
            self.preferences.setValue("visible", bool(data["visible"]))
        if "scale" in data:
            self.set_scale(max(0.5, min(1.25, float(data["scale"]))))
        for key, attr in (("live_sync", "live_sync_antigravity"), ("show_bubble", "show_status_bubble"), ("auto_roam", "auto_roam")):
            if key in data:
                setattr(self, attr, bool(data[key]))
                self.preferences.setValue(key, bool(data[key]))
        self.update()

    def restore_preferences(self):
        def saved_bool(key, default):
            value = self.preferences.value(key, default)
            return value if isinstance(value, bool) else str(value).lower() == "true"
        saved_visible = saved_bool("visible", True)
        self.apply_settings({
            "scale": float(self.preferences.value("scale", 0.68)),
            "live_sync": saved_bool("live_sync", True),
            "show_bubble": saved_bool("show_bubble", True),
            "auto_roam": saved_bool("auto_roam", False),
        })
        pet_id = str(self.preferences.value("active_pet_id", "hime"))
        self._on_select_pet_slot(pet_id)
        self.preferences.setValue("visible", saved_visible)
        x = self.preferences.value("position_x")
        y = self.preferences.value("position_y")
        if x is not None and y is not None:
            screen = QApplication.primaryScreen()
            if screen:
                area = screen.availableGeometry()
                px = max(area.left(), min(int(x), area.right() - self.width()))
                py = max(area.top(), min(int(y), area.bottom() - self.height()))
                self.move(px, py)
        else:
            self.snap_to_bottom_right()
        return saved_visible

    def load_spritesheet(self, path: str):
        self.sheet = SpriteSheet(path)
        self.pixmap_cache.clear()
        for action, frames in self.sheet.frames.items():
            self.pixmap_cache[action] = [pil_to_qpixmap(f) for f in frames]
        self.current_action = "idle"
        self.frame_index = 0
        self.update()

    def snap_to_bottom_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            w = self.width()
            h = self.height()
            x = geom.right() - w - 40
            y = geom.bottom() - h - 30
            self.move(x, y)

    def set_action(self, action_name: str, message: str = "", force_reset: bool = False):
        action = str(action_name or "").lower().strip()
        aliases = {
            "work": "thinking",
            "curious": "thinking",
            "running": "running-right",
            "celebrate": "review",
            "happy": "waving",
            "wake": "waving",
            "play": "jumping",
            "jump": "jumping",
            "jumping": "jumping",
            "run": "running-right",
            "walk": "running-right",
            "walking": "running-right",
            "wave": "waving",
            "waving": "waving",
            "rest": "idle",
            "sleep": "waiting",
            "waiting": "waiting",
            "idle": "idle",
        }
        action = aliases.get(action, action)
        if action not in self.pixmap_cache:
            action = "idle"

        if message:
            self.status_message = message
            self.status_message_expire_time = time.time() + 4.0

        if force_reset or self.current_action != action:
            self.current_action = action
            self.frame_index = 0
            self.update()

    # --- Live Sync Callbacks ---

    def _poll_antigravity(self):
        if time.time() < getattr(self, "manual_action_expire_time", 0):
            return
        if self.live_sync_antigravity and not self.is_dragging:
            self.ag_watcher.poll()
            threads = getattr(self.ag_watcher, "recent_threads", [])
            has_attention = any(t.get("status") in ("needs_input", "blocked", "ready") for t in threads)
            top_status = threads[0].get("status") if threads else "idle"
            self._update_bell_badge(has_attention, top_status)
            if getattr(self, "activity_tray_visible", False):
                self.refresh_activity_tray()

    def _on_bridge_state_change(self, state: str, reason: str):
        self.state_emitter.state_received.emit(state, reason)

    def _on_external_state(self, state: str, reason: str):
        if self.is_dragging:
            return

        self.manual_action_expire_time = time.time() + 4.5
        action = str(state or "").lower().strip()

        if action in ("work", "thinking", "running"):
            self.th_main_label.setText(reason or "กำลังคิด...")
            self.set_thinking(True, reason)
            self.set_action("thinking", reason or "กำลังคิด...", force_reset=False)
            self._update_status_bar("running", reason or "กำลังคิด...")
        elif action in ("needs_input", "waiting"):
            self.set_thinking(False)
            self.set_action("waiting", reason or "รอการตอบกลับของคุณ 🔔", force_reset=True)
            self._update_status_bar("needs_input", reason or "รอการตอบกลับของคุณ 🔔")
        elif action in ("blocked", "failed", "error"):
            self.set_thinking(False)
            self.set_action("failed", reason or "พบข้อผิดพลาด ⚠️", force_reset=True)
            self._update_status_bar("blocked", reason or "พบข้อผิดพลาด ⚠️")
        elif action in ("ready", "review", "celebrate"):
            self.set_thinking(False)
            self.set_action("review", reason or "เสร็จแล้ว! ✨", force_reset=True)
            self._update_status_bar("ready", reason or "เสร็จแล้ว! ✨")
        elif action in ("idle", "sleep"):
            self.set_thinking(False)
            self.set_action("idle" if action == "idle" else "waiting", reason or "พร้อมใช้งาน", force_reset=True)
            if self.floating_mode == "status":
                self.set_floating_mode("collapsed")
        else:
            self.set_thinking(False)
            self.set_action(action, reason or "ทดสอบท่าทาง ✨", force_reset=True)

    # --- Animation Tick ---

    def _on_animation_tick(self):
        frames = self.pixmap_cache.get(self.current_action, [])
        if not frames:
            return

        self.frame_index = (self.frame_index + 1) % len(frames)

        if self.current_action in ("review", "waving", "jumping") and self.frame_index == len(frames) - 1:
            if time.time() - self.last_user_interaction > 3 and not self.ag_watcher.turn_in_progress and not self.is_thinking and not self.is_dragging:
                self.set_action("idle")

        self.update()

    def _on_ai_tick(self):
        if self.is_dragging or self.ag_watcher.turn_in_progress or self.is_thinking:
            return
        idle_duration = time.time() - self.last_user_interaction
        if idle_duration > 60 and self.current_action == "idle":
            self.set_action("waiting")

    # --- Mouse & Interaction Events ---

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = event.globalPosition().toPoint()
            self.drag_start_pos = event.globalPosition().toPoint() - self.pos()
            self.last_drag_x = event.globalPosition().toPoint().x()
            self.has_dragged = False
            self.is_dragging = False
            self.last_user_interaction = time.time()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Clicking and dragging animates as RUNNING!"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            curr_pos = event.globalPosition().toPoint()
            delta = (curr_pos - self.press_pos).manhattanLength()
            if delta > 6:
                self.is_dragging = True
                self.has_dragged = True

                dx = curr_pos.x() - self.last_drag_x
                if dx > 1:
                    self.set_action("running-right")
                elif dx < -1:
                    self.set_action("running-left")

                self.last_drag_x = curr_pos.x()
                new_pos = curr_pos - self.drag_start_pos
                self.move(new_pos)
                self.last_user_interaction = time.time()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging:
                self.is_dragging = False
                self.last_user_interaction = time.time()
                self.preferences.setValue("position_x", self.x())
                self.preferences.setValue("position_y", self.y())
                if self.is_thinking:
                    self.set_action("thinking")
                else:
                    self.set_action("idle")
            elif not self.has_dragged:
                self.last_user_interaction = time.time()
                self.click_timer.start(240)
            event.accept()

    def _on_single_click(self):
        """1 click toggles chat bar with perfect anchor."""
        self.toggle_quick_chat_mode()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double click launches & focuses Antigravity 2.0!"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.click_timer.isActive():
                self.click_timer.stop()
            self.last_user_interaction = time.time()
            self.open_antigravity()
            event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent):
        self._show_plus_menu()

    def set_scale(self, factor: float):
        self.scale_factor = factor
        self.preferences.setValue("scale", factor)
        self.update_window_size(preserve_pet_pos=True)

    # --- Paint Event ---

    def paintEvent(self, event):
        if self.active_pet_id == "none" or self.mini_mode:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        frames = self.pixmap_cache.get(self.current_action, [])
        if not frames:
            return

        frame = frames[self.frame_index % len(frames)]

        target_w = int(CELL_WIDTH * self.scale_factor)
        target_h = int(CELL_HEIGHT * self.scale_factor)

        scaled = frame.scaled(
            target_w, target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        pet_x, pet_y = self.get_pet_render_offset(self.quick_chat_mode)
        painter.drawPixmap(pet_x, pet_y, scaled)
