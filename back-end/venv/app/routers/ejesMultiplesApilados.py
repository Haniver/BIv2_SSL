from os import pipe
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.formatoFechas import mesTexto
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from copy import deepcopy
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/ejesMultiplesApilados",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class EjesMultiplesApilados():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None

    async def Temporada(self):
        yAxis = []
        series = []
        arreglo = []
        hayResultados = 'no'
        categories = [0]
        venta = [0.0]
        ticketPromedio = []
        if self.titulo == 'Pedidos Levantados Hoy (con impuesto)':
            pedidosEntregados = [0]
            pedidosHoyATiempo = [0]
            pedidosHoyAtrasados = [0]
            hoy = datetime.today().strftime('%Y-%m-%d')
            query = f"""select hora, estatus, sum(pedidos) pedidos, sum(ventaConImp) venta
            from DWH.report.pedido_hora ph
            where fechaCreacion = '{hoy}'
            group by hora, estatus
            order by hora, estatus
            """
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                # Los elementos están ordenados por hora y luego por estatus. Por cada hora hay varios estatus, así que las horas se repiten.
                for elemento in arreglo:
                    # Si es una hora nueva,
                    if int(elemento['hora']) > categories[-1]:
                        # Agregamos al arreglo ticketPromedio la venta de la hora pasada entre la suma de todos los pedidos para esa hora
                        ticketPromedio.append(venta[-1] / float(pedidosEntregados[-1] + pedidosHoyATiempo[-1] + pedidosHoyAtrasados[-1]))
                        # Agregamos la nueva hora a las categorías
                        categories.append(int(elemento['hora']))
                        # Inicializamos a 0 los pedidos y la venta para esa hora
                        pedidosEntregados.append(0)
                        pedidosHoyATiempo.append(0)
                        pedidosHoyAtrasados.append(0)
                        venta.append(0.0)
                    if elemento['estatus'] == 'Entregado':
                        pedidosEntregados[int(elemento['hora'])] += int(elemento['pedidos'])
                    elif elemento['estatus'] == 'Hoy a tiempo':
                        pedidosHoyATiempo[int(elemento['hora'])] += int(elemento['pedidos'])
                    elif elemento['estatus'] == 'Hoy Atrasado':
                        pedidosHoyAtrasados[int(elemento['hora'])] += int(elemento['pedidos'])
                    venta[int(elemento['hora'])] += float(elemento['venta'])
                # Volvemos a sacar el ticket promedio para la última hora
                ticketPromedio.append(venta[-1] / float(pedidosEntregados[-1] + pedidosHoyATiempo[-1] + pedidosHoyAtrasados[-1]))
                # Los ejes Y son fijos y los creamos aquí:
                yAxis = [
                    {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'success', 'opposite': False},
                    {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True},
                    {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True}
                ]
                # Creamos las series con los arreglos que hicimos
                series = [
                    {'name': 'Entegado', 'data':pedidosEntregados, 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'success'},
                    {'name': 'Hoy a Tiempo', 'data':pedidosHoyATiempo, 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'info'},
                    {'name': 'Hoy Atrasado', 'data':pedidosHoyAtrasados, 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'danger'},
                    {'name': 'Venta', 'data':venta, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'moneda', 'color':'primary'},
                    {'name': 'Ticket Promedio', 'data':ticketPromedio, 'type': 'spline', 'yAxis': 2, 'formato_tooltip':'moneda', 'color':'dark'},
                ]
                # Cambiamos el formato de hora de las categorías para que se vea más chido:
                categories = [f"0{str(horaInt)}:00" if horaInt < 10 else f"{str(horaInt)}:00" for horaInt in categories]
        if self.titulo == 'Pedidos Pagados Hoy (sin impuesto)':
            hoy = int(datetime.today().strftime('%Y%m%d'))
            query = f"""select hora, sum(nTicket) pedidos, sum(ventaSinImpuestos) venta
            from DWH.artus.ventaDiariaHora vdh
            where fecha = {hoy}
            and idCanal = 1
            group by hora
            order by hora
            """
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                pedidos = []
                venta = []
                for elemento in arreglo:
                    ventaNum = float(elemento['venta'])
                    pedidosNum = elemento['pedidos']
                    pedidos.append(int(pedidosNum))
                    venta.append(ventaNum)
                    ticketPromedio.append(ventaNum / float(pedidosNum))
                    categories.append(int(elemento['hora']))
                # Los ejes Y son fijos y los creamos aquí:
                yAxis = [
                    {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'success', 'opposite': False},
                    {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True},
                    {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True}
                ]
                # Creamos las series con los arreglos que hicimos
                series = [
                    {'name': 'Pedidos', 'data':pedidos, 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'secondary'},
                    {'name': 'Venta', 'data':venta, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'moneda', 'color':'primary'},
                    {'name': 'Ticket Promedio', 'data':ticketPromedio, 'type': 'spline', 'yAxis': 2, 'formato_tooltip':'moneda', 'color':'dark'},
                ]
                # Cambiamos el formato de hora de las categorías para que se vea más chido:
                categories = [f"0{str(horaInt)}:00" if horaInt < 10 else f"{str(horaInt)}:00" for horaInt in categories]
        # print(f"Lo que vamos a regresar desde ejesMultiplesApilados: {str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'yAxis': yAxis})}")
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': query, 'yAxis': yAxis}

@router.post("/{seccion}")
async def ejes_multiples_apilados (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = EjesMultiplesApilados(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}