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

        # if self.filtros.fechas != None:
        #     self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
        #     self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None

    async def Temporada(self):
        yAxis = []
        series = []
        arreglo = []
        auxiliar = []
        hayResultados = 'no'
        query = ''
        categories = []
        venta = [0.0]
        ticketPromedio = []
        if self.titulo == 'Pedidos Levantados Hoy (con impuesto)':
            categories.append(0)
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
                        if (pedidosEntregados[-1] + pedidosHoyATiempo[-1] + pedidosHoyAtrasados[-1]) > 0:
                            ticketPromedio.append(venta[-1] / float(pedidosEntregados[-1] + pedidosHoyATiempo[-1] + pedidosHoyAtrasados[-1]))
                        else:
                            ticketPromedio.append(0)
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
                if (pedidosEntregados[-1] + pedidosHoyATiempo[-1] + pedidosHoyAtrasados[-1]) > 0:
                    ticketPromedio.append(venta[-1] / float(pedidosEntregados[-1] + pedidosHoyATiempo[-1] + pedidosHoyAtrasados[-1]))
                else:
                    ticketPromedio.append(0)
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
            categories.append(0)
            hoy = int(datetime.today().strftime('%Y%m%d'))
            if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '':
                filtroCanal = f'and idCanal = {self.filtros.canal}'
            else:
                filtroCanal = 'and idCanal not in (0)'
            query = f"""select hora, sum(nTicket) pedidos, sum(ventaSinImpuestos) venta
            from DWH.artus.ventaDiariaHora vdh
            where fecha = {hoy}
            {filtroCanal}
            group by hora
            order by hora
            """
            # print (f"query desde ejesMultiplesApilados->Temporada->2a. gráfica: {str(query)}")
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
                    if int(pedidosNum) > 0:
                        ticketPromedio.append(ventaNum / float(pedidosNum))
                    else:
                        ticketPromedio.append(0)
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
        if self.titulo == 'Pedidos por Día':
            hoy = int(datetime.today().strftime('%Y%m%d'))
            # print(f"Fecha_fin: {self.filtros.fechas['fecha_fin']}")
            fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
            fecha_fin = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ')
            fecha_fin_menos_1 = fecha_fin - timedelta(days=1)
            fecha_fin_menos_1 = fecha_fin_menos_1.strftime('%Y-%m-%d')
            fecha_fin = fecha_fin.strftime('%Y-%m-%d')
            hayCanal = False if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '' else True
            query = f"""select a.*,case when b.vTF=0 then 0 else a.ventaSinImp / b.vTF end * 100 partvsTF,co.Objetivo
                from
                (
                {'select vdh.idCanal' if hayCanal else 'select cc.esOmnicanal'},
                dt.fecha, SUM(nTicket) pedidos, sum(ventaSinImpuestos) ventaSinImp,sum(ventaSinImpuestos)/SUM(nTicket) ticketPromedio
                from DWH.artus.ventaDiariaHora vdh
                left join DWH.dbo.dim_tiempo dt on dt.id_fecha =vdh.fecha
                left join (select distinct tipo,esOmnicanal from DWH.artus.catCanal) cc on vdh.idCanal =cc.Tipo
                where dt.fecha = '{fecha_fin}'
                and {'vdh.idCanal = 1' if hayCanal else 'cc.esOmnicanal = -1'}
                group by {"vdh.idCanal" if hayCanal else "cc.esOmnicanal"}, dt.fecha
                ) a
                left join (select dtt.fecha,sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaDiariaHora vd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha =vd.fecha
                where dtt.fecha = '{fecha_fin}' and idCanal = 0
                group by dtt.fecha) b on a.fecha =b.fecha
                left join DWH.artus.catObjetivo co on co.idTipo =a.{"idCanal" if hayCanal else "esOmnicanal"} and format(a.fecha,'yyyyMM')=co.nMes
                union
                select a.*, case when b.vTF=0 then 0 else a.ventaSinImp / b.vTF end * 100 partvsTF,co.Objetivo
                from
                (
                select {"cc.tipo" if hayCanal else "cc.esOmnicanal"},
                dt.fecha, sum(nTicket) Pedidos, sum(ventaSinImpuestos) VentaSinImp,sum(ventaSinImpuestos)/SUM(nTicket) ticketPromedio
                from DWH.artus.ventaDiaria vd
                inner join DWH.dbo.dim_tiempo dt on dt.id_fecha = vd.fecha
                left join DWH.artus.catCanal cc on cc.idCanal = vd.idCanal
                where dt.fecha BETWEEN '{fecha_ini}' and '{fecha_fin_menos_1}'
                and {"cc.tipo=1" if hayCanal else "cc.esOmnicanal = -1"}
                group by {"cc.tipo" if hayCanal else "cc.esOmnicanal"}, dt.fecha
                ) a
                left join (select dtt.fecha,sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaxdia vd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha =vd.fecha
                where dtt.fecha BETWEEN '{fecha_ini}' and '{fecha_fin_menos_1}' 
                and idCanal = 0
                group by dtt.fecha) b on a.fecha =b.fecha
                left join DWH.artus.catObjetivo co on co.idTipo = a.{"tipo" if hayCanal else "esOmnicanal"}
                and format(a.fecha,'yyyyMM')=co.nMes
            """
            # print (f"query desde ejesMultiplesApilados->Temporada->3a. gráfica: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                pedidos = []
                venta = []
                porc_participacion = []
                objetivo = []
                diferencia = []
                multiple = []
                contador = 0
                for elemento in arreglo:
                    pedidos.append(elemento['pedidos'])
                    venta.append(elemento['ventaSinImp'])
                    ticketPromedio.append(elemento['ticketPromedio'])
                    porc_participacion.append(elemento['partvsTF'])
                    objetivo.append(elemento['Objetivo'])
                    diferencia.append(float(elemento['partvsTF']) - float(elemento['Objetivo']))
                    # categories.append(datetime.strptime(elemento['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'))
                    categories.append(elemento['fecha'].strftime('%d/%m/%Y'))
                    multiple.append(contador)
                    contador += 1
                # Los ejes Y son fijos y los creamos aquí:
                yAxis = [
                    {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'secondary', 'opposite': False},
                    {'formato': 'porcentaje', 'titulo': 'Part Vs. Objetivo', 'color': 'danger', 'opposite': False},
                    {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True},
                    {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True}
                ]
                # Creamos la serie auxiliar
                auxiliar = [
                    {'name': 'Part vs. Tienda Física', 'data':porc_participacion, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Objetivo', 'data':objetivo, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Diferencia', 'data':diferencia, 'formato':'porcentaje', 'lugar': 'principal'}
                ]
                # Creamos las series con los arreglos que hicimos
                series = [
                    {'name': 'Pedidos', 'data':pedidos, 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'secondary'},
                    {'name': 'Part vs. Objetivo', 'data':multiple, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'multiple', 'color':'danger'},
                    {'name': 'Venta', 'data':venta, 'type': 'spline', 'yAxis': 2, 'formato_tooltip':'moneda', 'color':'primary'},
                    {'name': 'Ticket Promedio', 'data':ticketPromedio, 'type': 'spline', 'yAxis': 3, 'formato_tooltip':'moneda', 'color':'dark'},
                ]
                # print(f"Auxiliar desde ejesMultipolesApilados: {str(auxiliar)}")
        # print(f"Lo que vamos a regresar desde ejesMultiplesApilados: {str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'yAxis': yAxis})}")
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': query, 'yAxis': yAxis, 'auxiliar': auxiliar}

@router.post("/{seccion}")
async def ejes_multiples_apilados (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = EjesMultiplesApilados(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}