from fastapi import APIRouter

from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.enviarEmail import enviarEmail
from app.servicios.urls import frontendUrlHttp
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from app.servicios.urls import rutaLogs
import os

router = APIRouter()

def buscarExpirados():
    print("Se entró a buscarExpirados()")
    hoy = date.today()
    ahorita = datetime.now()
    haceUnMes = ahorita - relativedelta(months=1)
    haceUnMes = haceUnMes.strftime('%Y-%m-%d %H:%M:%S')
    # Bloquear al usuario si no se ha logueado en un mes.
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor()
    query = f"""SELECT nombre, usuario FROM DJANGO.php.usuarios
    WHERE fecha_ultimo_login is not null
    AND fecha_ultimo_login < '{haceUnMes}'"""
    cursor.execute(query)
    arreglo = crear_diccionario(cursor)
    if len(arreglo) > 0:
        query = f"""UPDATE DJANGO.php.usuarios
        SET estatus='expirado', fecha_ultimo_login=null
        WHERE fecha_ultimo_login is not null
        AND fecha_ultimo_login < '{haceUnMes}'"""
        cursor.execute(query)
        cnxn.commit()
        for row in arreglo:
            print (row['nombre'])
            cuerpo = f"<html><head></head><body><p>{row['nombre']},<p><p>Tu usuario en el BI ha expirado debido a inactividad. Si quieres recuperarlo, crea una nueva contraseña en:</p><p><a href='{frontendUrlHttp()}/recuperar'>{frontendUrlHttp()}/recuperar</a></p><span style='color:#1A2976;'>Saludos,<br />BI Omnicanal<br />Grupo Comercial Chedraui <img src='https://i.ibb.co/qyc21cy/logo-Email.png'></span></p></body></html>"
            receivers = [row['usuario']]
            titulo = "Tu usuario de BI Omnicanal ha expirado"
            enviarEmail(titulo, receivers, cuerpo)
        with open(f"{rutaLogs()}Expirados.log", "a+") as file:
            file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {row['nombre']} ({row['usuario']}) ha expirado.\n")
            file.close()    

def reducirArchivosLogs():
    print("Se entró a reducirArchivosLogs()")
    size = os.path.getsize(f"{rutaLogs()}Errores.log")
    if size > 50000000:
        with open(f"{rutaLogs()}Errores.log", "r") as f:
            text = f.read()
            length = len(text)
            cut_off_point = round(length * 0.25)
            new_text = text[cut_off_point:]
        with open(f"{rutaLogs()}Errores.log", 'w') as f:
            f.write(new_text)
    size = os.path.getsize(f"{rutaLogs()}updateFaltantes.log")
    if size > 50000000:
        with open(f"{rutaLogs()}updateFaltantes.log", "r") as f:
            text = f.read()
            length = len(text)
            cut_off_point = round(length * 0.25)
            new_text = text[cut_off_point:]
        with open(f"{rutaLogs()}updateFaltantes.log", 'w') as f:
            f.write(new_text)
    return