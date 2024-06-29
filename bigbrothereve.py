import os
import time
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True
import cv2
import win32clipboard
import win32con
from ctypes import windll
import requests
from io import BytesIO
import pytesseract
import json
import base64
from pykeyboard import *
import uiautomation as auto
from uiautomation.uiautomation import Bitmap
import tkinter.scrolledtext as scrolledtext
import subprocess


def load_corporation_names(file_path):
    with open(file_path, 'r') as file:
        corporation_names = [line.strip() for line in file.readlines()]
    return corporation_names

def load_devices(file_path):
    with open(file_path, 'r') as file:
        devices = {}
        for line in file.readlines():
            parts = line.strip().split()
            if len(parts) == 2:
                devices[parts[0]] = [parts[1], False] 
    return devices

def read_discord_webhook():
    webhook = None
    with open('discord_webhook.txt', 'r') as file:
        webhook = file.readline().strip()
    return webhook

discord_webhook = read_discord_webhook()

conVal = 0.8  

path = 'dist'  
devices = load_devices('devices.txt')
gameSendPosition = {
    'Second Channel': '38 117',
    'Third Channel': '38 170',
    'Fourth Channel': '38 223',
    'Fifth Channel': '38 278',
    'Sixth Channel': '38 332',
    'Seventh Channel': '38 382'
}
sendTo = gameSendPosition['Third Channel']

mutex = threading.Lock()

def setClipboardFile(paths):
    try:
        im = Image.open(paths)
        im.save('1.bmp')
        aString = windll.user32.LoadImageW(0, r"1.bmp", win32con.IMAGE_BITMAP, 0, 0, win32con.LR_LOADFROMFILE)
    except UnidentifiedImageError:
        setClipboardFile(paths)
        return

    if aString != 0:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_BITMAP, aString)
        win32clipboard.CloseClipboard()
        return
    print('Image loading failed')

def send_discord_msg(content, image=None):
   
    payload = {"content": content}
 
    files = None
    if image:
        # convertir la imagen a bytes
        img_byte_array = BytesIO()
        image.save(img_byte_array, format="PNG")
        img_byte_array.seek(0)
        files = {"file": ("image.png", img_byte_array)}

    # enviar el mensaje a Discord
    print("Sending message to Discord...")
    response = requests.post(discord_webhook, data=payload, files=files)

    print("Response:", response)
    print("Response Text:", response.text)

    if response.status_code == 200:
        print("Message sent to Discord successfully")
        if "attachments" in response.json():
            attachment_url = response.json()["attachments"][0]["url"]
            print("Attachment URL:", attachment_url)
    else:
        print("Failed to send message to Discord")

def send_msg(content, msg_type=1):
    if msg_type == 1:
        auto.SetClipboardText(content)
    elif msg_type == 2:
        auto.SetClipboardBitmap(Bitmap.FromFile(content))
    elif msg_type == 3:
        auto.SetClipboardBitmap(Bitmap.FromFile(content))
    send_discord_msg(content)

def Start():
    with open(f'list.png', 'rb') as sc1:
        con = sc1.read()
        for k in devices:
            f = open(f'new_{k}_list.png', 'wb')
            f.write(con)
            f.close()
    
    with open(f'playerList.png', 'rb') as sc:
        con = sc.read()
        for k in devices:
            f = open(f'old_{k}_playerList.png', 'wb')
            f.write(con)
            f.close()
            f = open(f'new_{k}_playerList.png', 'wb')
            f.write(con)
            f.close()
    for k in devices:
        t = threading.Thread(target=Listening, args=(k, ))
        t.start()
    
    print('Started')
    context = f"Detection System Online, Currently monitoring: {devices.keys()}"
    mutex.acquire()
    send_msg(context, msg_type=1)
    mutex.release()

def screenc(filename, num):
    command = f'adb -s {devices[filename][0]} exec-out screencap -p > {filename}_{num}.png'
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def crop(x1, y1, x2, y2, scFileName, svFileName):
    try:
        img = Image.open(scFileName)
        re = img.crop((x1, y1, x2, y2))
        re.save(svFileName)
        img.close()
        re.close()
    except Exception:
        return

def LoadImage(img1, img2):
    i1 = cv2.imread(img1, 0)
    i2 = cv2.imread(img2, 0)
    return i1, i2

def IF_Img_I(src, mp):
    res = None
    try:
        res = cv2.matchTemplate(src,mp,cv2.TM_CCOEFF_NORMED)
    except Exception:
        return False, 0.999
    _, mac_v, _, _ = cv2.minMaxLoc(res)
    if mac_v < 0.99:
        return True, mac_v
    return False, mac_v

def SendGameMessage(tag):
    str1 = f'adb -s {devices[tag][0]} '
    commands = [
        f"{str1}shell input tap 211 478",
        f"{str1}shell input tap {sendTo}",
        f"{str1}shell input tap 266 520",
        f"{str1}shell input tap 843 511",
        f"{str1}shell input tap 68 292",
        f"{str1}shell input tap 250 433",
        f"{str1}shell input tap 344 190",
        f"{str1}shell input tap 342 512"
    ]
    for command in commands:
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.3)
    time.sleep(5)


def SendDiscordMessage(tag, num):
    mutex.acquire()
    
    context = f"{tag}"
    with open(f'{tag}_{num}.png', 'rb') as file:
        image = Image.open(file)
        send_discord_msg(context, image)
    mutex.release()

def process_image_with_tesseract(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        print("#####", text)
        return text
    except Exception as e:
        print(f"Error processing image with Tesseract: {e}")
        return None
    

def Listening(tag):
    def task2(tag):
        num = 0
        last_detected_text = None 
        while True:
            screenc(tag, 1)
            time.sleep(0.5)
            crop(728, 43, 956, 212, f'{tag}_1.png', f'new_{tag}_list.png')
            text = process_image_with_tesseract(f'new_{tag}_list.png')

            corporation_names = load_corporation_names('corporation_names.txt')

            detected_corporation = None
            for corporation_name in corporation_names:
                if corporation_name.lower() in text.lower():
                    detected_corporation = corporation_name
                    break

            if detected_corporation:
                print("Detected corporation:", detected_corporation)
                print("Ignoring the report to Discord.")
                num = 0
                continue

            if text != last_detected_text:  
                last_detected_text = text 
                print("Change detected. Sending to Discord.")
                SendDiscordMessage(tag, 1)
                num = 0
                screenc(tag, 1)
                time.sleep(10)
                screenc(tag,1)
            else:
                print("No change detected.")

            i3, i4 = LoadImage(f"new_{tag}_list.png", f"list.png")
            list_status, list_mac_v = IF_Img_I(i3, i4)

            if list_mac_v != 0.0 and list_mac_v < 0.10:
                if num < 1:
                    num += 1
                    print('Secondary detection')
                    time.sleep(2)
                    continue

                num = 0
                print(tag + ' Detected ships in the list', list_mac_v)
                SendDiscordMessage(tag, 1)
                i1, i2 = LoadImage(f"new_{tag}_playerList.png", f"old_{tag}_playerList.png")
                cv2.imwrite(f'old_{tag}_playerList.png', i1, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                time.sleep(40)
                continue

    t = threading.Thread(target=task2, args=(tag, ))
    t.start()

    while True:
        screenc(tag, 2)
        time.sleep(conVal)
        time.sleep(0.35)
        crop(774, 502, 956, 537, f'{tag}_2.png', f'new_{tag}_playerList.png')
        i1, i2 = LoadImage(f"new_{tag}_playerList.png", f"old_{tag}_playerList.png")
        list_status, list_mac_v = IF_Img_I(i1, i2)

        if list_mac_v <= 0.01:
            print(tag, 'Suspected malfunction')
            time.sleep(3)
            continue
            
        if list_status:
            print(tag + ' Warning')
            SendGameMessage(tag)
            cv2.imwrite(f'old_{tag}_playerList.png', i1, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            time.sleep(5)

def main():
    def start_monitoring():
        Start()

    def stop_monitoring():
        os._exit(1)

    root = tk.Tk()
    root.title("Monitoring App")

    start_button = ttk.Button(root, text="Start Monitoring", command=start_monitoring)
    start_button.pack(pady=5)

    stop_button = ttk.Button(root, text="Stop Monitoring", command=stop_monitoring)
    stop_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    def start_monitoring():
        Start()

    def stop_monitoring():
        os._exit(1)


    root = tk.Tk()
    root.title("Eve Big Brother")
    icono = tk.PhotoImage(file='icon.png')
    root.tk.call('wm', 'iconphoto', root._w, icono)


    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side="bottom", fill="x")

    start_button = tk.Button(bottom_frame, text="Start Monitoring", command=start_monitoring)
    start_button.pack(side="top", padx=5, pady=5)

    stop_button = tk.Button(bottom_frame, text="Stop Monitoring", command=stop_monitoring)
    stop_button.pack(side="top", padx=5, pady=5)


    additional_info = tk.Label(bottom_frame, text="Discord: riksx | GitHub: Riksx0")
    additional_info.pack(side="bottom", padx=5, pady=5)

    root.mainloop()