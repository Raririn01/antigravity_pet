"""Local Antigravity activity, Pet settings, and CLI Quick Chat bridge."""

import os
import glob
import json
import time
import base64
import threading
import uuid
import subprocess
import shutil
from urllib.parse import parse_qs, urlsplit
from PIL import Image
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable, Dict, Any

from spritesheet import validate_spritesheet

# Base directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
CATALOG_PATH = os.path.join(ASSETS_DIR, "custom_pets.json")
CHAT_JOBS = {}
CHAT_LOCK = threading.Lock()


def run_quick_chat(job_id, prompt, conversation_id):
    cli = shutil.which("agy")
    if not cli or not os.path.isfile(cli):
        local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
        cli = os.path.join(local_app_data, "agy", "bin", "agy.exe")
    args = [cli, "-p", prompt, "--output-format", "json", "--mode", "plan", "--sandbox", "--disable-slash-commands", "--print-timeout", "120s"]
    if conversation_id:
        args.extend(["--conversation", conversation_id])
    try:
        if not os.path.isfile(cli):
            raise RuntimeError("ไม่พบ Antigravity CLI (agy.exe)")
        result = subprocess.run(args, cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=130,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout or "Antigravity CLI failed").strip()[-500:])
        payload = json.loads(result.stdout)
        if payload.get("status") != "SUCCESS":
            raise RuntimeError(str(payload.get("error") or payload.get("status") or "Antigravity did not finish"))
        update = {"status": "done", "response": payload.get("response", ""),
                  "conversation_id": payload.get("conversation_id", conversation_id)}
    except Exception as exc:
        update = {"status": "error", "error": str(exc)[:500]}
    with CHAT_LOCK:
        CHAT_JOBS[job_id].update(update)


def load_custom_metadata():
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def save_custom_metadata(metadata):
    temp_path = CATALOG_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    os.replace(temp_path, CATALOG_PATH)


def available_pets():
    pets = [
        {"id": "none", "name": "Mini", "description": "โหมดกะทัดรัด แสดงเฉพาะปุ่ม Quick Chat และกิจกรรม AI", "preview": None, "spritesheet": None, "is_custom": False},
        {"id": "hime", "name": "Hime (ฮิเมะ)", "description": "จิ้งจอกสาวจิ๋วผมขาว ตาแดง ชุดแดงขาว คู่หูช่างสงสัยจาก ChatGPT Work", "preview": "/assets/hime_preview.png", "spritesheet": "/assets/hime_pet.png", "is_custom": False},
        {"id": "swan", "name": "Swan (สวอน)", "description": "สาวน้อยผมม่วงลาเวนเดอร์ในชุดราตรีสีน้ำเงินขาว สไปรต์พิกเซลระดับ S-Tier (สร้างด้วย Skill create-pet)", "preview": "/assets/swan_preview.png", "spritesheet": "/assets/swan_pet.png", "is_custom": False},
        {"id": "custom_agy_chibi_pipeline", "name": "Agy Chibi", "description": "มาสคอตสาวหุ่นยนต์ไซเบอร์ หูแมวเรืองแสง Visor >_ สร้างด้วย AI สำหรับ Antigravity", "preview": "/assets/agy_mascot_preview.png", "spritesheet": "/assets/custom_agy_chibi_pipeline.png", "is_custom": False},
        {"id": "codex", "name": "Codex", "description": "หุ่นยนต์บลูคิวบ์พร้อมหน้าจอเทอร์มินัล >_ คู่หูดั้งเดิม", "preview": "/assets/codex_preview.png", "spritesheet": "/assets/codex_pet.png", "is_custom": False},
        {"id": "agy_bot", "name": "Agy Bot", "description": "Antigravity AI Cyber Bot ผู้ช่วยเขียนโค้ดคู่หู บินดุ๊กดิ๊กพร้อมพิมพ์งาน", "preview": "/assets/agy_preview.png", "spritesheet": "/assets/default_pet.png", "is_custom": False},
    ]
    metadata = load_custom_metadata()
    for path in sorted(glob.glob(os.path.join(ASSETS_DIR, "custom_*.png"))):
        pet_id = os.path.splitext(os.path.basename(path))[0]
        if pet_id in ("custom_agy_chibi_pipeline", "custom_pets"):
            continue
        info = metadata.get(pet_id, {})
        pets.append({"id": pet_id, "name": info.get("name", pet_id.replace("custom_", "").capitalize()), "description": info.get("description", "สัตว์เลี้ยงที่นำเข้า"), "preview": f"/assets/{pet_id}.png", "spritesheet": f"/assets/{pet_id}.png", "is_custom": True})
    return pets


class AntigravityWatcher:
    """Watches the Antigravity conversation transcripts to infer agent state."""

    def __init__(self, brain_root: Optional[str] = None, on_state_change: Optional[Callable[[str, str], None]] = None):
        user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        self.brain_roots = [
            os.path.join(user_profile, ".gemini", "antigravity", "brain"),
            os.path.join(user_profile, ".gemini", "antigravity-ide", "brain")
        ]
        if brain_root and brain_root not in self.brain_roots:
            self.brain_roots.insert(0, brain_root)
        self.brain_root = self.brain_roots[0]
        self.on_state_change = on_state_change
        
        self.current_state = "idle"
        self.active_transcript_path: Optional[str] = None
        self.last_file_pos = 0
        self.last_step_index = -1
        self.last_activity_time = time.time()
        self.turn_in_progress = False

    def find_latest_transcript(self) -> Optional[str]:
        all_matches = []
        for root in self.brain_roots:
            pattern = os.path.join(root, "*", ".system_generated", "logs", "transcript.jsonl")
            all_matches.extend(glob.glob(pattern))
        if not all_matches:
            return None
        all_matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return all_matches[0]

    def _set_state(self, state: str, reason: str = ""):
        if self.current_state != state:
            self.current_state = state
            if self.on_state_change:
                self.on_state_change(state, reason)

    def poll(self):
        latest_file = self.find_latest_transcript()
        if not latest_file:
            return

        if latest_file != self.active_transcript_path:
            self.active_transcript_path = latest_file
            try:
                self.last_file_pos = os.path.getsize(latest_file)
            except OSError:
                self.last_file_pos = 0

        try:
            current_size = os.path.getsize(latest_file)
            mtime = os.path.getmtime(latest_file)
            time_since_mod = time.time() - mtime

            if current_size > self.last_file_pos:
                with open(latest_file, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(self.last_file_pos)
                    new_lines = f.readlines()
                    self.last_file_pos = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        step = json.loads(line)
                        step_idx = step.get("step_index", 0)
                        self.last_step_index = step_idx
                        source = step.get("source", "")
                        step_type = step.get("type", "")
                        status = step.get("status", "")
                        tool_calls = step.get("tool_calls", [])

                        self.last_activity_time = time.time()

                        if step_type == "USER_INPUT":
                            self.turn_in_progress = True
                            self._set_state("thinking", "กำลังคิด...")
                        elif step_type == "PLANNER_RESPONSE":
                            if tool_calls:
                                self.turn_in_progress = True
                                tool_name = tool_calls[0].get("name", "คำสั่ง")
                                self._set_state("thinking", f"กำลังคิด ({tool_name})...")
                            else:
                                self.turn_in_progress = False
                                self._set_state("review", "เสร็จแล้ว! ✨")
                        elif status == "ERROR":
                            self._set_state("thinking", "กำลังตรวจสอบ...")
                    except json.JSONDecodeError:
                        continue

            if self.turn_in_progress:
                if time_since_mod > 10.0:
                    self.turn_in_progress = False
                    self._set_state("review", "เสร็จแล้ว! ✨")
            else:
                idle_sec = time.time() - self.last_activity_time
                if idle_sec > 60.0 and self.current_state not in ("sleep", "wake"):
                    self._set_state("sleep", "Zzz")
                elif 5.0 < idle_sec <= 60.0 and self.current_state in ("review", "celebrate", "happy", "curious", "work", "thinking"):
                    self._set_state("idle", "พร้อมใช้งาน")

        except Exception:
            pass


class PetHttpHandler(BaseHTTPRequestHandler):
    pet_window_ref = None

    def _send_json(self, data: Any, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/chat":
            job_id = parse_qs(urlsplit(self.path).query).get("job", [""])[0]
            with CHAT_LOCK:
                job = CHAT_JOBS.get(job_id)
                self._send_json(dict(job) if job else {"error": "Chat job not found"}, 200 if job else 404)
            return

        if path == "/health":
            self._send_json({"status": "ok", "pet": "Antigravity Pet"})
            return

        if path == "/settings" or path == "/":
            settings_html_path = os.path.join(SCRIPT_DIR, "settings.html")
            if os.path.exists(settings_html_path):
                with open(settings_html_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Settings page not found")
            return

        if path.startswith("/assets/"):
            filename = os.path.basename(path)
            file_path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(file_path):
                mime = "image/png" if file_path.endswith(".png") else "image/webp"
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Asset not found")
            return

        if path == "/api/pets":
            pw = PetHttpHandler.pet_window_ref
            if not pw:
                self._send_json({"error": "Pet window not attached"}, 500)
                return

            pets = available_pets()

            resp = {
                "active_pet_id": pw.active_pet_id,
                "visible": pw.isVisible(),
                "scale": pw.scale_factor,
                "live_sync": pw.live_sync_antigravity,
                "show_bubble": pw.show_status_bubble,
                "auto_roam": getattr(pw, "auto_roam", False),
                "current_action": pw.current_action,
                "status": "running" if pw.ag_watcher.turn_in_progress else ("blocked" if pw.ag_watcher.current_state == "curious" else "ready"),
                "pets": pets
            }
            self._send_json(resp)
            return

        if path == "/api/activity":
            pw = PetHttpHandler.pet_window_ref
            root = pw.ag_watcher.brain_root if pw else ""
            pattern = os.path.join(root, "*", ".system_generated", "logs", "transcript.jsonl")
            paths = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:8]
            activity = []
            for file_path in paths:
                conversation_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(file_path))))
                activity.append({"id": conversation_id, "updated_at": os.path.getmtime(file_path), "status": "running" if pw and file_path == pw.ag_watcher.active_transcript_path and pw.ag_watcher.turn_in_progress else "recent"})
            self._send_json({"activity": activity})
            return

        if path == "/api/download-pet":
            pet_id = parse_qs(urlsplit(self.path).query).get("id", [""])[0]
            pet = next((item for item in available_pets() if item["id"] == pet_id and item["spritesheet"]), None)
            if not pet:
                self._send_json({"error": "Pet not found"}, 404)
                return
            file_path = os.path.join(ASSETS_DIR, os.path.basename(pet["spritesheet"]))
            with open(file_path, "rb") as handle:
                content = handle.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Disposition", f'attachment; filename="{pet_id}.png"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_error(404)

    def do_POST(self):
        # Origin check removed for local loopback IPC
        if not self.headers.get("Content-Type", "").lower().startswith("application/json"):
            self._send_json({"error": "JSON request required"}, 415)
            return
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 28 * 1024 * 1024:
            self._send_json({"error": "Request too large"}, 413)
            return
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        pw = PetHttpHandler.pet_window_ref

        if self.path == "/api/chat":
            prompt = str(data.get("prompt", "")).strip()
            conversation_id = str(data.get("conversation_id", "")).strip()
            if not prompt or len(prompt) > 12000:
                self._send_json({"error": "Enter a message up to 12,000 characters"}, 400)
                return
            if conversation_id and (len(conversation_id) != 36 or any(c not in "0123456789abcdef-" for c in conversation_id.lower())):
                self._send_json({"error": "Invalid conversation ID"}, 400)
                return
            job_id = uuid.uuid4().hex
            with CHAT_LOCK:
                for key in list(CHAT_JOBS):
                    if CHAT_JOBS[key].get("status") != "running" and time.time() - CHAT_JOBS[key]["created_at"] > 3600:
                        del CHAT_JOBS[key]
                CHAT_JOBS[job_id] = {"status": "running", "created_at": time.time()}
            threading.Thread(target=run_quick_chat, args=(job_id, prompt, conversation_id), daemon=True).start()
            self._send_json({"job": job_id, "status": "running"}, 202)
            return

        if self.path == "/api/select-pet":
            pet_id = data.get("pet_id")
            if pet_id not in {item["id"] for item in available_pets()}:
                self._send_json({"error": "Pet not found"}, 404)
            elif pw:
                pw.select_pet_by_id(pet_id)
                self._send_json({"status": "success", "active_pet_id": pet_id})
            else:
                self._send_json({"error": "Pet window not attached"}, 500)
            return

        if self.path == "/api/open-antigravity":
            user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
            local_app_data = os.environ.get("LOCALAPPDATA") or os.path.join(user_profile, "AppData", "Local")
            app_path = os.path.join(local_app_data, "Programs", "antigravity", "Antigravity.exe")
            if not os.path.isfile(app_path):
                app_path = os.path.join(local_app_data, "Programs", "Antigravity IDE", "Antigravity IDE.exe")
            if not os.path.isfile(app_path):
                self._send_json({"error": "Antigravity app not found"}, 404)
                return
            os.startfile(app_path)
            self._send_json({"status": "success"})
            return

        if self.path in ("/api/call-pet", "/api/focus-pet"):
            if pw:
                pw.state_emitter.hotkey_triggered.emit()
                self._send_json({"status": "success", "message": "Pet summoned to front"})
            else:
                self._send_json({"error": "Pet window not attached"}, 500)
            return

        if self.path == "/api/update-pet":
            pet_id = str(data.get("pet_id", ""))
            pet = next((item for item in available_pets() if item["id"] == pet_id), None)
            if not pet or not pet["is_custom"]:
                self._send_json({"error": "Only uploaded pets can be edited"}, 400)
                return
            name = str(data.get("name", "")).strip()[:80]
            description = str(data.get("description", "")).strip()[:240]
            if not name:
                self._send_json({"error": "Pet name is required"}, 400)
                return
            metadata = load_custom_metadata()
            metadata[pet_id] = {"name": name, "description": description}
            save_custom_metadata(metadata)
            self._send_json({"status": "success", "pet_id": pet_id})
            return

        if self.path == "/api/delete-pet":
            pet_id = str(data.get("pet_id", ""))
            pet = next((item for item in available_pets() if item["id"] == pet_id), None)
            if not pet or not pet["is_custom"]:
                self._send_json({"error": "Only uploaded pets can be deleted"}, 400)
                return
            if pw and pw.active_pet_id == pet_id:
                pw.select_pet_by_id("hime")
            os.remove(os.path.join(ASSETS_DIR, pet_id + ".png"))
            metadata = load_custom_metadata()
            metadata.pop(pet_id, None)
            save_custom_metadata(metadata)
            self._send_json({"status": "success", "deleted": pet_id})
            return

        if self.path == "/api/settings":
            if not pw:
                self._send_json({"error": "Pet window not attached"}, 500)
                return

            pw.state_emitter.settings_changed_signal.emit(data)

            self._send_json({
                "status": "success",
                "visible": pw.isVisible(),
                "scale": pw.scale_factor,
                "live_sync": pw.live_sync_antigravity,
                "show_bubble": pw.show_status_bubble,
                "auto_roam": getattr(pw, "auto_roam", False)
            })
            return

        if self.path == "/state":
            state = data.get("state", "idle")
            msg = data.get("message", "")
            if pw:
                pw.state_emitter.state_received.emit(state, msg)
            self._send_json({"status": "success"})
            return

        if self.path == "/api/upload-pet":
            filename = os.path.basename(str(data.get("filename", "custom_pet.png"))).replace("\\", "_")
            if not filename.lower().endswith((".png", ".webp")):
                self._send_json({"error": "Upload a PNG or WebP sprite sheet"}, 400)
                return
            b64_content = data.get("content", "")
            if not b64_content:
                self._send_json({"error": "Missing content"}, 400)
                return

            if "," in b64_content:
                b64_content = b64_content.split(",", 1)[1]

            pet_id = "custom_" + uuid.uuid4().hex[:12]
            target_path = os.path.join(ASSETS_DIR, pet_id + ".png")
            try:
                raw_bytes = base64.b64decode(b64_content)
                if len(raw_bytes) > 20 * 1024 * 1024:
                    self._send_json({"error": "Sprite sheet exceeds 20 MiB"}, 400)
                    return
                from io import BytesIO
                with Image.open(BytesIO(raw_bytes)) as image:
                    if image.format not in ("PNG", "WEBP"):
                        self._send_json({"error": "File is not PNG or WebP"}, 400)
                        return
                    image.convert("RGBA").save(target_path, "PNG")

                val = validate_spritesheet(target_path)
                if not val.is_valid:
                    os.remove(target_path)
                    self._send_json({"error": "Invalid spritesheet", "details": val.errors}, 400)
                    return

                if pw:
                    pw.select_pet_by_id(pet_id)

                metadata = load_custom_metadata()
                metadata[pet_id] = {"name": os.path.splitext(filename)[0][:80], "description": "Pet ที่อัปโหลด"}
                save_custom_metadata(metadata)

                self._send_json({"status": "success", "pet_id": pet_id})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        pass


def start_http_server(port: int = 21420, pet_window=None) -> Optional[HTTPServer]:
    PetHttpHandler.pet_window_ref = pet_window
    for attempt in range(15):
        try:
            server = HTTPServer(("127.0.0.1", port), PetHttpHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            print(f"Pet HTTP server listening on http://127.0.0.1:{port}")
            return server
        except Exception as e:
            if attempt < 14:
                time.sleep(0.5)
            else:
                print(f"Could not bind HTTP server to port {port}: {e}")
                return None

