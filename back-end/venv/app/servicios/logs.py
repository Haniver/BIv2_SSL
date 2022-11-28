from app.servicios.urls import rutaLogs
from datetime import datetime

def loguearConsulta(grafico, usuario, seccion, titulo, filtros = None, ip='?'):
    with open(f"{rutaLogs()}{usuario}.log", "a+") as file:
        if filtros is not None:
            arr_filtros = [f"{key}: {value}" for key, value in vars(filtros).items() if value is not None]
        else:
            arr_filtros = []
        file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Desde IP {ip} | consultó {seccion} -> {grafico} -> {titulo} | con Filtros: {str(arr_filtros)}\n")
        # print(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Consulta {grafico}->{seccion}->{titulo} | Filtros: {str(arr_filtros)}\n")
        file.close()

def loguearError(grafico, usuario, seccion, titulo, error, filtros = None, ip='?'):
    with open(f"{rutaLogs()}Errores.log", "a+") as file:
        if filtros is not None:
            arr_filtros = [f"{key}: {value}" for key, value in vars(filtros).items() if value is not None]
        else:
            arr_filtros = []
        file.write(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} {usuario} con IP {ip} | consultó {seccion} -> {grafico} -> {titulo} | con Filtros: {str(arr_filtros)}\n | Y obtuvo el error: {error}")
        # print(f"\n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} Consulta {grafico}->{seccion}->{titulo} | Filtros: {str(arr_filtros)}\n")
        file.close()



