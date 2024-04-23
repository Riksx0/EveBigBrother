import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab, Image, ImageChops
import numpy
import threading
import time
import mss
import cv2
import requests
import pytesseract
from io import BytesIO
import sys
import os
import subprocess

#######################################################

def check_for_updates(repo_owner, repo_name, current_version):
    # Definir el nombre de usuario del propietario del repositorio y el nombre del repositorio
    owner = repo_owner
    repo = repo_name
    # Ruta al archivo que contiene la versión actual de la aplicación
    version_file = "version.txt"

    # Endpoint de la API de GitHub para obtener la última versión de la aplicación
    url = f"https://api.github.com/repos/Riksx0/EveBigBrother/releases/latest"

    try:
        # Realizar una solicitud GET a la API de GitHub
        response = requests.get(url)
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Obtener la información de la versión más reciente
            latest_version = response.json()["tag_name"]
            # Comparar la versión actual con la versión más reciente
            if latest_version != current_version:
                print("¡Hay una nueva versión disponible!")
                # Descargar y actualizar la aplicación
                download_and_update_app(owner, repo)
            else:
                print("La aplicación está actualizada.")
        else:
            print("Error al obtener la información de la versión:", response.status_code)
    except Exception as e:
        print("Error al verificar actualizaciones:", e)

def download_and_update_app(owner, repo):
    try:
        # Descargar el archivo de la última versión desde GitHub
        subprocess.run(["git", "clone", f"https://github.com/Riksx0/EveBigBrother.git", "temp_repo"])
        # Mover los archivos relevantes de la nueva versión a la ubicación de la aplicación actual
        subprocess.run(["cp", "-r", "temp_repo/*", "app_directory"])
        print("¡La aplicación se ha actualizado correctamente!")
    except Exception as e:
        print("Error al descargar y actualizar la aplicación:", e)
    finally:
        # Eliminar el repositorio temporal
        subprocess.run(["rm", "-rf", "temp_repo"])

##################################################################3

class ConsoleWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Console")
        self.geometry("400x300")

        self.text_console = tk.Text(self, wrap="word")
        self.text_console.pack(expand=True, fill="both")

        sys.stdout = self

    def write(self, text):
        self.text_console.insert("end", text)

    def flush(self):
        pass


class Console(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Console")
        self.geometry("500x300")

        self.textbox = tk.Text(self, wrap="word")
        self.textbox.pack(expand=True, fill="both")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.textbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.textbox.configure(yscrollcommand=self.scrollbar.set)

    def log(self, message):
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

class ConfigDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Screen resolution and Webhook URL")
        self.geometry("300x200")

        self.lbl_width = ttk.Label(self, text="Width:")
        self.lbl_width.pack(pady=5)
        self.entry_width = ttk.Entry(self)
        self.entry_width.pack()

        self.lbl_height = ttk.Label(self, text="Height:")
        self.lbl_height.pack(pady=5)
        self.entry_height = ttk.Entry(self)
        self.entry_height.pack()

        self.lbl_webhook = ttk.Label(self, text="Webhook URL:")
        self.lbl_webhook.pack(pady=5)
        self.entry_webhook = ttk.Entry(self)
        self.entry_webhook.pack()

        self.btn_ok = ttk.Button(self, text="Accept", command=self.save_config)
        self.btn_ok.pack(pady=10)

    def save_config(self):
        try:
            width = int(self.entry_width.get())
            height = int(self.entry_height.get())
            webhook_url = self.entry_webhook.get()
            self.master.set_resolution(width, height, webhook_url)
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid resolution.")


class RegionSelector(tk.Toplevel):
    def __init__(self, master):
        self.master = master
        self.app = master
        self.screen_width = master.screen_width
        self.screen_height = master.screen_height

        self.window = tk.Toplevel(master)
        self.window.overrideredirect(True)
        self.window.attributes('-alpha', 0.5)  

        self.console = master.console

        self.canvas = tk.Canvas(self.window, width=self.screen_width, height=self.screen_height, highlightthickness=0)
        self.canvas.pack()

        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)

    def start_selection(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def update_selection(self, event):
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)
        self.draw_selection_rectangle()

    def end_selection(self, event):
        x1 = min(max(self.start_x, 0), self.screen_width)
        y1 = min(max(self.start_y, 0), self.screen_height)
        x2 = min(max(self.end_x, 0), self.screen_width)
        y2 = min(max(self.end_y, 0), self.screen_height)
        selected_region = (x1, y1, x2, y2)

        self.show_region_name_dialog(selected_region)

        self.window.destroy()

    def draw_selection_rectangle(self):
        self.canvas.delete("selection_rect")
        self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline='red', tags="selection_rect")

    def show_region_name_dialog(self, region):
        region_name_dialog = RegionNameDialog(self.master, region)
        region_name_dialog.transient(self.master)
        region_name_dialog.grab_set()
        self.master.wait_window(region_name_dialog.window)


class RegionNameDialog(tk.Toplevel):
    def __init__(self, master, region):
        super().__init__(master)
        self.title("Region Name")
        self.geometry("300x300")

        self.region = region

        self.lbl_region_name = ttk.Label(self, text="Enter Region Name:")
        self.lbl_region_name.pack(pady=5)
        self.entry_region_name = ttk.Entry(self)
        self.entry_region_name.pack()

        self.lbl_delay = ttk.Label(self, text="Enter Delay (in seconds):")
        self.lbl_delay.pack(pady=5)
        self.entry_delay = ttk.Entry(self)
        self.entry_delay.pack()

        self.btn_ok = ttk.Button(self, text="OK", command=self.save_region_name)
        self.btn_ok.pack(pady=5)
        self.window = self

    def save_region_name(self):
        region_name = self.entry_region_name.get()
        delay = self.entry_delay.get()
        try:
            delay = float(delay)
            if region_name:
                self.master.add_region(self.region, region_name, delay)
                self.destroy()
            else:
                messagebox.showerror("Error", "Region name cannot be empty.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid delay (in seconds).")


class MonitoreoRegion:
    def __init__(self, master, region, webhook_url, app, region_names, delay):
        self.master = master
        self.region = region
        self.app = app
        self.region_names = region_names 
        self.monitoreo_en_curso = False
        self.imagen_inicial = None
        self.nombre_archivo_imagen_inicial = f"imagen_inicial_{id(self)}.png"
        self.webhook_url = webhook_url
        self.delay = delay
        self.aliados = App.get_aliados()  

        self.frame = ttk.Frame(self.master)

        self.btn_iniciar = ttk.Button(self.frame, text="Start monitoring", command=self.iniciar_monitoreo)
        self.btn_iniciar.pack(pady=5)

        self.btn_detener = ttk.Button(self.frame, text="Stop monitoring", command=self.detener_monitoreo, state=tk.DISABLED)
        self.btn_detener.pack(pady=5)

        self.btn_borrar = ttk.Button(self.frame, text="Delete Region", command=self.borrar_region)
        self.btn_borrar.pack(pady=5)

        x1, y1, x2, y2 = self.region

        canvas_width = x2 - x1
        canvas_height = y2 - y1

        self.canvas = tk.Canvas(self.frame, width=canvas_width, height=canvas_height, highlightthickness=0)
        self.canvas.pack()

    def iniciar_monitoreo(self):
        x1, y1, x2, y2 = self.region
        if x1 is None:
            messagebox.showerror("Error", "No se pudo encontrar la ventana en la pantalla")
            return
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        width = x2 - x1
        height = y2 - y1
        with mss.mss() as sct:
            monitor = {"top": y1, "left": x1, "width": width, "height": height}
            try:
                screenshot = sct.grab(monitor)
                self.imagen_inicial = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                self.imagen_inicial.save(self.nombre_archivo_imagen_inicial)
            except Exception as e:
                print("Error al tomar la captura inicial:", e)
                return

        self.monitoreo_en_curso = True
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_detener.config(state=tk.NORMAL)
        threading.Thread(target=self.monitorear_ventana, args=(x1, y1, width, height)).start()

    def monitorear_ventana(self, x, y, width, height):
        while self.monitoreo_en_curso:
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                try:
                    screenshot = sct.grab(monitor)
                    screenshot = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                except Exception as e:
                    print("Error al capturar la pantalla:", e)
                    continue

                if self.imagen_inicial is None:
                    print("La imagen inicial es invalida")
                    continue

                if self.es_aliado_en_imagen(screenshot):
                    print("Se detectó un aliado en la imagen. No se actualizará la imagen inicial.")
                    texto_detectado = pytesseract.image_to_string(screenshot)
                    print("Texto detectado en la imagen actual:", texto_detectado)
                    self.imagen_inicial = self.imagen_inicial
                elif self.comparar_imagenes(self.imagen_inicial, screenshot):
                    print("Las imagenes son diferentes. Enviando captura de pantalla a Discord...")
                    texto_detectado = pytesseract.image_to_string(screenshot)
                    print("Texto detectado en la imagen actual:", texto_detectado)
                    self.enviar_a_discord(screenshot)
                    self.imagen_inicial=screenshot
                else:
                    print("Las imagenes son iguales. No se enviará captura de pantalla a Discord.")
                    texto_detectado = pytesseract.image_to_string(screenshot)
                    print("Texto detectado en la imagen actual:", texto_detectado)
                time.sleep(self.delay)

    def es_aliado_en_imagen(self, imagen):
        texto_en_imagen = pytesseract.image_to_string(imagen)
        for aliado in self.aliados:
            if aliado in texto_en_imagen:
                return True
        return False

    def enviar_a_discord(self, imagen):
        try:
            width = self.region[2] - self.region[0]
            height = self.region[3] - self.region[1]
            imagen_redimensionada = imagen.resize((width, height))
            with BytesIO() as image_buffer:
                imagen_redimensionada.save(image_buffer, format="PNG")
                image_buffer.seek(0)
                files = {'file': ('captura.png', image_buffer, 'image/png')}
                region_name = None
                for region, name in self.app.region_names.items():
                    if region == self.region:
                        region_name = name
                        break
                if region_name is None:
                    print("No se encontró el nombre de la región correspondiente.")
                    return
                message = f"{region_name} has movement"
                data = {'content': message}
                response = requests.post(self.webhook_url, files=files, data=data)

            if response.status_code == 200:
                print("Captura de pantalla enviada.")
            else:
                print("Error al enviar la captura de pantalla.", response.text)
        except Exception as e:
            print("Error al enviar la captura de pantalla.", e)

    def detener_monitoreo(self):
        self.monitoreo_en_curso = False
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_detener.config(state=tk.DISABLED)

    def borrar_region(self):
        self.frame.destroy()

    def comparar_imagenes(self, imagen1, imagen2):
        diferencia = ImageChops.difference(imagen1, imagen2)
        diferencia_array = numpy.array(diferencia)
        suma_diferencia = numpy.sum(diferencia_array)
        umbral = 200000
        return suma_diferencia > umbral


class ChangeNameDialog(tk.Toplevel):
    def __init__(self, master, region):
        super().__init__(master)
        self.title("Change Region Name")
        self.geometry("200x100")

        self.region = region

        self.lbl_new_name = ttk.Label(self, text="New Name:")
        self.lbl_new_name.pack(pady=5)
        self.entry_new_name = ttk.Entry(self)
        self.entry_new_name.pack()

        self.btn_ok = ttk.Button(self, text="OK", command=self.change_name)
        self.btn_ok.pack(pady=5)

    def change_name(self):
        new_name = self.entry_new_name.get()
        if new_name:
            self.master.change_region_name(self.region, new_name)
            self.destroy()
        else:
            messagebox.showerror("Error", "New name cannot be empty.")







class App(tk.Tk):
    _aliados = ["CRB","PAND", "REAS", "DUNE", "GRA", "LEGN", "S3VG", "XAN", "RED1", "GONE", 
                "KNEE", "UFCG", "HTP", "PYRT", "S2N", "NILF", "SUM", "SHIE", "CBWA", "B1G", 
                "SOAF", "SAKU", "FKG", "ORDN", "BKRN", "FLBR", "IQE", "UEE", "VHGS", "AMSH", 
                "BSF", "BGE", "SC2", "TLC", "REKE", "VIDA", "ODST", "ROOK", "REKI", "ODSF", 
                "ODIF", "AGS", "DN", "ASMR", "HMZ", "L1NF", "LGQ", "KLU", "P1BC", "PIBC", 
                "SYKY", "FVM", "AURY", "PER", "MM", "ROLL", "RED2", "VECT", "KP", "XCOM", 
                "L4D", "SJI", "BNI", "NIFI", "HOME", "2SUM", "NCR0", "A15P", "F00L", "OLDS", 
                "VIRI", "SHHC", "HOGS", "H0GS", "CC", "CBFS", "PJM", "CC", "SHLD", "HOGS",
                 "TOGC", "GIST", "SMU", "DT13", "O0SF", "DOSF", "RAN", "8IG",
                 "A1sP", "A15P", "VEE", "REDI", "H0ME", "HOME", "KNEE"]

    @classmethod
    def get_aliados(cls):
        return cls._aliados

    def __init__(self):
        super().__init__()
        self.title("EVE Big Brother")
        self.geometry("600x400")
        self.iconphoto(True, tk.PhotoImage(file="icon.png"))



        self.region_names = {}

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack()

        self.btn_configure = ttk.Button(self.button_frame, text="Config", command=self.open_config)
        self.btn_configure.pack(side=tk.LEFT, padx=5)

        self.btn_add_region = ttk.Button(self.button_frame, text="Add Region", command=self.select_region)
        self.btn_add_region.pack(side=tk.LEFT, padx=5)

        self.btn_open_console = ttk.Button(self.button_frame, text="Open Console", command=self.open_console)
        self.btn_open_console.pack(side=tk.LEFT, padx=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.webhook_url = ''  

        self.lbl_watermark = ttk.Label(self, text="GitHub: Riksx0 | Discord: riksx")
        self.lbl_watermark.pack(side=tk.BOTTOM, pady=5)

        self.console = Console(self)

        

    def open_config(self):
        dialog = ConfigDialog(self)
        dialog.transient(self)
        dialog.grab_set()
    
    def open_console(self):
        self.console_window = ConsoleWindow(self)
        self.console_window.mainloop()


    def set_resolution(self, width, height, webhook_url):
        self.screen_width = width
        self.screen_height = height
        self.webhook_url = webhook_url

    def add_region_tab(self, region, name, delay):
        frame = MonitoreoRegion(self.notebook, region, self.webhook_url, self, self.region_names, delay)
        self.notebook.add(frame.frame, text=name)

    def add_region(self, region, name, delay):
        if name:
            self.region_names[region] = name
            print("Region names dictionary after adding new region:", self.region_names)
            self.add_region_tab(region, name, delay)
        else:
            messagebox.showerror("Error", "Region name cannot be empty.")

    def select_region(self):
        selector = RegionSelector(self)
        self.wait_window(selector.window)

    def change_region_name(self, region, new_name):
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, option="text") == new_name:
                messagebox.showerror("Error", "Region name already exists.")
                return
        self.notebook.tab(self.notebook.select(), text=new_name)
        print("Region names dictionary after changing region name:", self.region_names)

if __name__ == "__main__":
    app = App()
    app.mainloop()
#########################
    repo_owner = "Riksx0"
    repo_name = "EveBigBrother"
    current_version = "2.5"
    # Verificar si hay actualizaciones disponibles
    check_for_updates(repo_owner, repo_name, current_version)



# Version 2.5