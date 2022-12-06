from app.servicios.urls import rutaLogs
from datetime import datetime
import os

def loguearConsulta(grafico, usuario, seccion, titulo, filtros = None, ip='?'):
    with open(f"{rutaLogs()}{usuario}.log", "a+") as file:
        if filtros is not None:
            arr_filtros = [f"{key}: {value}" for key, value in vars(filtros).items() if value is not None]
        else:
            arr_filtros = []
        file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Desde IP {ip} | consultó {seccion} -> {grafico} -> {titulo} | con Filtros: {str(arr_filtros)}\n")
        file.close()

def loguearError(grafico, usuario, seccion, titulo, error, filtros = None, ip='?'):
    with open(f"{rutaLogs()}Errores.log", "a+") as file:
        if filtros is not None:
            arr_filtros = [f"{key}: {value}" for key, value in vars(filtros).items() if value is not None]
        else:
            arr_filtros = []
        file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} {usuario} con IP {ip} | consultó {seccion} -> {grafico} -> {titulo} | con Filtros: {str(arr_filtros)}\n | Y obtuvo el error: {error}")
        file.close()

def loguearAcceso(ip, usuario):
    with open(f"{rutaLogs()}{usuario}.log", "a+") as file:
        file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Acceso exitoso Desde IP {ip}\n")
        file.close()

def intentoFallidoDeAcceso(ip, usuario, razon):
    if razon == 'usuario no encontrado':
        with open(f"{rutaLogs()}Errores.log", "a+") as file:
            file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Intento fallido de acceso desde la IP {ip}. Usuario no existe: {usuario} \n")
            file.close()
    else:
        with open(f"{rutaLogs()}{usuario}.log", "a+") as file:
            file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Desde IP {ip} | Intento fallido de acceso: {razon}.\n")
            file.close()    

def errorUltimoLogin(ip, usuario):
    with open(f"{rutaLogs()}{usuario}.log", "a+") as file:
        file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Desde IP {ip} | Error al intentar actualizar el último login del usuario.\n")
        file.close()    

def reducirArchivoLogs(usuario):
    size = os.path.getsize(f"{rutaLogs()}{usuario}.log")
    if size > 5000000:
        with open(f"{rutaLogs()}{usuario}.log", "r") as f:
            text = f.read()
            length = len(text)
            cut_off_point = round(length * 0.25)
            new_text = text[cut_off_point:]
        with open(f"{rutaLogs()}{usuario}.log", 'w') as f:
            f.write(new_text)
    return
