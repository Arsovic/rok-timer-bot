import sys
import os
import json
import traceback
import win32gui
from PyQt5 import QtWidgets, QtCore, QtGui
import mss
import mss.tools
import asyncio
import requests
import cv2
import numpy as np
import pytesseract
from datetime import datetime, timedelta
from pyrogram import Client

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  #Твой путь к тессеракту #Укажи свой путь в ковычках

API_ID = 12345  
API_HASH = "123апбв342б"
BOT_USERNAME = "бот_123_рок"

TITLE = "Rise of Kingdoms" #Название окна привязки
BOT_TOKEN = "и23и4234рр4" #Токен, который датс @botFather
CHANNEL_ID = -12345678 #ID канала, куда бот кидает уведомления
USER_ID = 123456 (для Pyrogram)

user_app = Client("rok_userbot", api_id=API_ID, api_hash=API_HASH)

ACCOUNTS_FILE = "accounts.json"
REGION_FILE = "region.json"
TG_SEND_MSG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

async def send_timer_async(account: str, troop: int, end_iso: str):
    if not user_app.is_connected:
        await user_app.start()
    text = f"#TIMER# {account}|{troop}|{end_iso}"
    await user_app.send_message(BOT_USERNAME, text)


def send_timer(account: str, troop: int, end_iso: str):
    # даём Pyrogram самому управлять циклом
    user_app.run(send_timer_async(account, troop, end_iso))


# === РАБОТА С АККАУНТАМИ ===

def load_accounts(user_id: int):
    if not os.path.exists(ACCOUNTS_FILE):
        return None, []

    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None, []

    user_data = data.get(str(user_id))
    if not user_data:
        return None, []

    current = user_data.get("current")
    accounts = user_data.get("accounts", [])
    return current, accounts


def save_current_account(user_id: int, current_name: str):
    if not os.path.exists(ACCOUNTS_FILE):
        data = {}
    else:
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    user_str = str(user_id)
    if user_str not in data:
        data[user_str] = {"current": current_name, "accounts": [current_name]}
    else:
        data[user_str]["current"] = current_name
        if "accounts" not in data[user_str]:
            data[user_str]["accounts"] = [current_name]
        elif current_name not in data[user_str]["accounts"]:
            data[user_str]["accounts"].append(current_name)

    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === РАБОТА С ОБЛАСТЬЮ ===

def save_region(region: dict):
    try:
        with open(REGION_FILE, "w", encoding="utf-8") as f:
            json.dump(region, f, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()


def load_region() -> dict | None:
    if not os.path.exists(REGION_FILE):
        return None
    try:
        with open(REGION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# === ТЕЛЕГРАМ-ТЕКСТ ===

def send_text_to_channel(text: str):
    try:
        data = {
            "chat_id": str(CHANNEL_ID),
            "text": text,
            "parse_mode": "HTML",
        }
        resp = requests.post(TG_SEND_MSG_URL, data=data, timeout=30)
        print("Ответ TG (сообщение):", resp.status_code, resp.text)
    except Exception:
        print("Ошибка при отправке текста в TG:")
        traceback.print_exc()

def send_text_to_user(text: str):
    try:
        data = {
            "chat_id": str(USER_ID),
            "text": text,
            "parse_mode": "HTML",
        }
        resp = requests.post(TG_SEND_MSG_URL, data=data, timeout=30)
        print("Ответ TG (личка):", resp.status_code, resp.text)
    except Exception:
        print("Ошибка при отправке в личку TG:")
        traceback.print_exc()

# === СКРИН ОКНА ИГРЫ ===

def find_rok_hwnd():
    hwnd = win32gui.FindWindow(None, TITLE)
    if not hwnd:
        print("RoK окно не найдено")
        return None
    return hwnd

def get_rok_rect(hwnd):
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception as e:
        print("Ошибка GetWindowRect:", e)
        return None


def grab_rok_screenshot(hwnd):
    rect = get_rok_rect(hwnd)
    if not rect:
        print("Нет rect окна RoK")
        return None, None, None
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    monitor = {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }

    filename = "rok_screen.png"
    print("Делаю скрин:", filename)

    try:
        with mss.mss() as sct:
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
        print("Скрин сохранён:", filename)
    except Exception:
        print("Ошибка при скрине:")
        traceback.print_exc()
        return None, None, None

    img = np.array(sct_img)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img, (width, height), (left, top)


def crop_by_region(img, win_origin, region: dict):
    """
    region: { "x": ..., "y": ..., "w": ..., "h": ... } в координатах ЭКРАНА
    win_origin: (left, top) окна RoK
    """
    win_left, win_top = win_origin
    x = region["x"] - win_left
    y = region["y"] - win_top
    w = region["w"]
    h = region["h"]

    x = max(0, x)
    y = max(0, y)
    x2 = min(x + w, img.shape[1])
    y2 = min(y + h, img.shape[0])

    crop = img[y:y2, x:x2]
    cv2.imwrite("timers_crop.png", crop)
    print("Сохранён crop таймеров: timers_crop.png")
    return crop


# === OCR ТАЙМЕРОВ ===

def ocr_timers(img_crop):
    gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_LINEAR)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imwrite("timers_ocr_input.png", thresh)  # <- добавь эту строку

    config = "--oem 3 --psm 7"  # попробуем строку целиком
    text = pytesseract.image_to_string(thresh, config=config)
    print("OCR сырой текст:")
    print(repr(text))
    return text


def parse_timers(text: str):
    import re

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    timers = []

    pattern_hms = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})")
    pattern_ms = re.compile(r"(\d{1,2}):(\d{2})")

    for line in lines:
        # убираем слово "Сбор" и пробелы
        line = line.replace("Сбор", "").replace("сбор", "")
        line = line.replace(" ", "")

        m = pattern_hms.search(line)
        if m:
            h, m_, s = map(int, m.groups())
            timers.append(timedelta(hours=h, minutes=m_, seconds=s))
            continue

        m = pattern_ms.search(line)
        if m:
            m_, s = map(int, m.groups())
            timers.append(timedelta(minutes=m_, seconds=s))

    return timers

def build_message_from_timers(account_name: str | None, timers, base_index: int = 1):
    if not account_name:
        return ("<b>(ник не задан)</b>\n"
                "Сначала задай имя аккаунта командой /setname в боте.\n"
                "Таймеры не привязаны к аккаунту.")

    if not timers:
        return f"<b>{account_name}</b>\nТаймеры не распознаны."

    now = datetime.now()
    lines = []
    meta_lines = []

    for i, td in enumerate(timers):
        idx = base_index + i
        end_time = now + td
        # человеческий текст
        lines.append(
            f"Отряд {idx}: через {str(td)} (до {end_time.strftime('%H:%M:%S')})"
        )
        # служебная строка для бота
        end_iso = end_time.isoformat(timespec="seconds")
        meta_lines.append(f"#TIMER# {account_name}|{idx}|{end_iso}")

    # обычный текст + мета-блок
    msg = "<b>" + account_name + "</b>\n" + "\n".join(lines)
    msg += "\n\n" + "\n".join(meta_lines)
    return msg

# === ОКНО ВЫБОРА ОБЛАСТИ ===

class RegionSelector(QtWidgets.QWidget):
    """
    Полупрозрачный фуллскрин-оверлей для выбора прямоугольника мышкой.
    """

    region_selected = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.start_pos = None
        self.end_pos = None
        self.current_rect = QtCore.QRect()


    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.start_pos = event.globalPos()
            self.end_pos = self.start_pos
            self.current_rect = QtCore.QRect(self.start_pos, self.end_pos)
            self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.start_pos is not None:
            self.end_pos = event.globalPos()
            self.current_rect = QtCore.QRect(self.start_pos, self.end_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton and self.start_pos is not None:
            self.end_pos = event.globalPos()
            self.current_rect = QtCore.QRect(self.start_pos, self.end_pos).normalized()
            rect = self.current_rect
            region = {
                "x": rect.left(),
                "y": rect.top(),
                "w": rect.width(),
                "h": rect.height(),
            }
            print("Выбранная область:", region)
            self.region_selected.emit(region)
            self.close()
        elif event.button() == QtCore.Qt.RightButton:
            # правой кнопкой — отмена
            self.close()

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # затемняем весь экран
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))

        # рисуем выбранный прямоугольник
        if not self.current_rect.isNull():
            pen = QtGui.QPen(QtGui.QColor(0, 255, 0), 2)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(self.current_rect)


# === ПАНЕЛЬ ===

class RokPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- аккаунты ---
        self.current_account, accounts = load_accounts(USER_ID)

        self.account_combo = QtWidgets.QComboBox(self)
        self.account_combo.addItems(accounts)
        if self.current_account and self.current_account in accounts:
            self.account_combo.setCurrentText(self.current_account)
        self.account_combo.currentTextChanged.connect(self.on_account_changed)

        # --- номер отряда ---
        self.troop_spin = QtWidgets.QSpinBox(self)
        self.troop_spin.setMinimum(1)
        self.troop_spin.setMaximum(50)  # с запасом
        self.troop_spin.setValue(1)

        self.btn_region = QtWidgets.QPushButton("Выбрать область", self)
        self.btn_region.clicked.connect(self.on_select_region)

        self.btn_shot = QtWidgets.QPushButton("Скрин + таймеры", self)
        self.btn_shot.clicked.connect(self.on_shot_clicked)

        layout.addWidget(self.account_combo)
        layout.addWidget(self.troop_spin)
        layout.addWidget(self.btn_region)
        layout.addWidget(self.btn_shot)

        self.resize(350, 40)

        self.rok_hwnd = find_rok_hwnd()
        self.panel_hwnd = int(self.winId())

        self.follow_timer = QtCore.QTimer(self)
        self.follow_timer.timeout.connect(self.follow_rok_window)
        self.follow_timer.start(100)

        self.active_timer = QtCore.QTimer(self)
        self.active_timer.timeout.connect(self.check_active_window)
        self.active_timer.start(200)

        self.region = load_region()
        self.region_selector = None  # держим ссылку, чтобы не убило GC
        if self.region:
            print("Загружена область из файла:", self.region)

    def follow_rok_window(self):
        if not self.rok_hwnd or not win32gui.IsWindow(self.rok_hwnd):
            self.rok_hwnd = find_rok_hwnd()
            if not self.rok_hwnd:
                return

        rect = get_rok_rect(self.rok_hwnd)
        if not rect:
            return

        left, top, right, bottom = rect

        offset_x = 10
        offset_y = 10

        panel_w = self.width()
        panel_h = self.height()

        x = right - panel_w - offset_x
        y = bottom - panel_h - offset_y

        self.move(x, y)

    def check_active_window(self):
        try:
            fg = win32gui.GetForegroundWindow()
        except Exception:
            return

        if (self.rok_hwnd and fg == self.rok_hwnd) or fg == self.panel_hwnd:
            if not self.isVisible():
                self.show()
        else:
            if self.isVisible():
                self.hide()

    def on_select_region(self):
        print("Режим выбора области")
        if self.region_selector is not None:
            self.region_selector.close()
            self.region_selector = None

        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self.on_region_selected)
        self.region_selector.showFullScreen()
        self.region_selector.raise_()
        self.region_selector.activateWindow()

    def on_region_selected(self, region: dict):
        print("Сохранена область:", region)
        self.region = region
        save_region(region)
        # после выбора сбрасываем ссылку
        self.region_selector = None

    def on_shot_clicked(self):
        print("OCR...")
        account_name = self.current_account or None
        print(f"Аккаунт: {account_name}")
        
        if not self.rok_hwnd or not win32gui.IsWindow(self.rok_hwnd):
            self.rok_hwnd = find_rok_hwnd()
        
        if not self.rok_hwnd:
            print("RoK окно не найдено")
            text = "⚠️ RoK окно не найдено. Откройте игру."
            send_text_to_channel(text)
            return
        
        if not self.region:
            text = "❌ Регион не выбран. Нажмите 'Выбрать регион'."
            send_text_to_channel(text)
            print(text)
            return
        
        img, winsize, win_origin = grab_rok_screenshot(self.rok_hwnd)
        if img is None:
            text = "⚠️ Не удалось захватить скрин RoK."
            send_text_to_channel(text)
            return
        
        crop = crop_by_region(img, win_origin, self.region)
        text_raw = ocr_timers(crop)
        timers = parse_timers(text_raw)
        
        base_index = self.troop_spin.value()
        msg = build_message_from_timers(account_name, timers, base_index)
        print("Сформирован текст:")
        print(msg)
        
        # делим: человекочитаемое в канал, мета – в личку
        human_part = msg.split("\n\n#TIMER#", 1)[0]
        meta_part = msg[len(human_part):].strip()
        
        # в канал – только верх (без служебных строк)
        send_text_to_channel(human_part)
        
        # отправляем каждый таймер через userbot в личку боту
        now = datetime.now()
        for i, td in enumerate(timers):
            idx = base_index + i
            end_time = now + td
            end_iso = end_time.isoformat(timespec='seconds')
            send_timer(account_name, idx, end_iso)

    def on_account_changed(self, name: str):
        self.current_account = name
        save_current_account(USER_ID, name)
        print(f"Аккаунт изменён на: {name}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    panel = RokPanel()
    panel.show()
    sys.exit(app.exec_())
