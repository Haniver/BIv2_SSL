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
        multiple = []
        contador = 0
        diferencia = []
        arrFromSibling = []
        hayCanal = False if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '' else True
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
                    {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'success', 'opposite': False, 'visible': True},
                    {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True, 'visible': True},
                    {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True, 'visible': True}
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
            if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '':
                filtroCanal = 'and idCanal not in (0)'
            else:
                filtroCanal = f'and idCanal = {self.filtros.canal}'
            query = f"""select hora, sum(nTicket) pedidos, sum(ventaSinImpuestos) venta
            from DWH.artus.ventaDiariaHora vdh
            where fecha = {hoy}
            {filtroCanal}
            group by hora
            order by hora
            """
            # print (f"query desde ejesMultiplesApilados->Temporada->Pedidos Pagados hoy: {str(query)}")
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
                    {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'success', 'opposite': False, 'visible': True},
                    {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True, 'visible': True},
                    {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True, 'visible': True}
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
            print(f"Hoy es {datetime.today()}")
            # print(f"Fecha_fin: {self.filtros.fechas['fecha_fin']}")
            fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
            fecha_fin = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ')
            fecha_fin_menos_1 = fecha_fin - timedelta(days=1)
            fecha_fin_menos_1 = fecha_fin_menos_1.strftime('%Y-%m-%d')
            fecha_fin = fecha_fin.strftime('%Y-%m-%d')
            query = f"""select a.*,case when b.vTF=0 then 0 else a.ventaSinImp / b.vTF end * 100 PartvsTF,co.Objetivo
                from
                (
                {'select vdh.idCanal' if hayCanal else 'select cc.esOmnicanal'},
                dt.fecha, SUM(nTicket) pedidos, sum(ventaSinImpuestos) ventaSinImp,sum(ventaSinImpuestos)/SUM(nTicket) ticketPromedio
                from DWH.artus.ventaDiariaHora vdh
                left join DWH.dbo.dim_tiempo dt on dt.id_fecha =vdh.fecha
                left join (select distinct tipo,esOmnicanal from DWH.artus.catCanal) cc on vdh.idCanal =cc.Tipo
                where dt.fecha = '{fecha_fin}'
                and {'vdh.idCanal = '+self.filtros.canal if hayCanal else 'cc.esOmnicanal = -1'}
                group by {"vdh.idCanal" if hayCanal else "cc.esOmnicanal"}, dt.fecha
                ) a
                left join (select dtt.fecha,sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaDiariaHora vd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha =vd.fecha
                where dtt.fecha = '{fecha_fin}' and idCanal = 0
                group by dtt.fecha) b on a.fecha =b.fecha
                left join DWH.artus.catObjetivo co on co.idTipo =a.{"idCanal" if hayCanal else "esOmnicanal"} and format(a.fecha,'yyyyMM')=co.nMes
                union
                select a.*, case when b.vTF=0 then 0 else a.ventaSinImp / b.vTF end * 100 PartvsTF,co.Objetivo
                from
                (
                select {"cc.tipo" if hayCanal else "cc.esOmnicanal"},
                dt.fecha, sum(nTicket) Pedidos, sum(ventaSinImpuestos) VentaSinImp,sum(ventaSinImpuestos)/SUM(nTicket) ticketPromedio
                from DWH.artus.ventaDiaria vd
                inner join DWH.dbo.dim_tiempo dt on dt.id_fecha = vd.fecha
                left join DWH.artus.catCanal cc on cc.idCanal = vd.idCanal
                where dt.fecha BETWEEN '{fecha_ini}' and '{fecha_fin_menos_1}'
                and {"cc.tipo="+self.filtros.canal if hayCanal else "cc.esOmnicanal = -1"}
                and vd.ventaSinImpuestos <> 0
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
                order by fecha
            """
            # print (f"query desde ejesMultiplesApilados->Temporada->Pedidos por día: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                pedidos = []
                venta = []
                porc_participacion = []
                objetivo = []
                for elemento in arreglo:
                    pedidos.append(elemento['pedidos'])
                    venta.append(elemento['ventaSinImp'])
                    ticketPromedio.append(elemento['ticketPromedio'])
                    porc_participacion.append(float(elemento['PartvsTF'])/100)
                    if elemento['Objetivo'] is not None:
                        objetivo.append(float(elemento['Objetivo'])/100)
                    else:
                        objetivo.append(0)
                    if elemento['Objetivo'] is not None and elemento['PartvsTF'] is not None:
                        diferencia.append((float(elemento['PartvsTF']) - float(elemento['Objetivo']))/100)
                    else:
                        diferencia.append(0)
                    # categories.append(datetime.strptime(elemento['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'))
                    categories.append(elemento['fecha'].strftime('%d/%m/%Y'))
                    multiple.append(contador)
                    contador += 1
                # Los ejes Y son fijos y los creamos aquí:
                yAxis = [
                    {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'secondary', 'opposite': False, 'visible': True},
                    {'formato': 'porcentaje', 'titulo': 'Part Vs. Objetivo', 'color': 'danger', 'opposite': False, 'visible': True},
                    {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True, 'visible': True},
                    {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True, 'visible': True}
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
                    {'name': 'Part vs. TF', 'data':multiple, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'multiple', 'color':'danger'},
                    {'name': 'Venta', 'data':venta, 'type': 'spline', 'yAxis': 2, 'formato_tooltip':'moneda', 'color':'primary'},
                    {'name': 'Ticket Promedio', 'data':ticketPromedio, 'type': 'spline', 'yAxis': 3, 'formato_tooltip':'moneda', 'color':'dark'},
                ]
                # print(f"Auxiliar desde ejesMultipolesApilados: {str(auxiliar)}")

        fecha_ini_str = self.filtros.fechas['fecha_ini'][:10]
        fecha_ini_int = int(fecha_ini_str[0:4]) * 10000 + int(fecha_ini_str[5:7]) * 100 + int(fecha_ini_str[8:10])
        fecha_fin_str = self.filtros.fechas['fecha_fin'][:10]
        fecha_fin_int = int(fecha_fin_str[0:4]) * 10000 + int(fecha_fin_str[5:7]) * 100 + int(fecha_fin_str[8:10])

        if self.titulo == 'Venta por Región':
            query = f"""select ct.regionNombre,
                sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) ventaActual,
                case when sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end)=0 then 0 else round(((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) /
                sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end))-1)*100,2) end PartvsAA,
                round((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) / (select sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaxdia vxd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha = vxd.fecha
                where vxd.fecha BETWEEN '{fecha_ini_int}' and '{fecha_fin_int}' and idCanal = 0))*100,2) PartvsTF,max(co.Objetivo) Objetivo
                from DWH.artus.ventaDiaria a
                left join DWH.artus.catTienda ct on a.idTienda = ct.tienda
                left join DWH.dbo.dim_tiempo dt on a.fecha =dt.fechaComparacion
                left join DWH.dbo.dim_tiempo dt2 on a.fecha =dt2.id_fecha
                left join DWH.artus.catCanal cc on a.idCanal =cc.idCanal
                left join DWH.artus.catObjetivo co on co.idTipo = cc.{'esOmnicanal' if not hayCanal else 'idCanal'} and format(dt2.fecha,'yyyyMM')=co.nMes
                where (dt2.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}'
                or dt.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}')
                and cc.tipo {'= '+self.filtros.canal if hayCanal else 'not in (0)'}
                group by ct.regionNombre
                order by ct.regionNombre
                """
            # print (f"query desde ejesMultiples->Temporada -> Venta por región: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                ventaActual = []
                PartvsAA = []
                PartvsTF = []
                Objetivo = []
                yAxis = [
                    {'visible': False},
                    {'visible': False}
                ]
                for elemento in arreglo:
                    categories.append(elemento['regionNombre'])
                    if elemento['ventaActual'] is not None:
                        ventaActual.append(elemento['ventaActual'])
                    else:
                        ventaActual.append(float(0))
                    if elemento['PartvsAA'] is not None:
                        PartvsAA.append(float(elemento['PartvsAA'])/100)
                    else:
                        PartvsAA.append(float(0))
                    if elemento['PartvsTF'] is not None:
                        PartvsTF.append(float(elemento['PartvsTF'])/100)
                    else:
                        PartvsTF.append(float(0))
                    if elemento['Objetivo'] is not None:
                        Objetivo.append(float(elemento['Objetivo'])/100)
                    else:
                        Objetivo.append(float(0))
                    if elemento['PartvsTF'] is not None and elemento['Objetivo'] is not None:
                        diferencia.append((float(elemento['PartvsTF']) - float(elemento['Objetivo']))/100)
                    else:
                        diferencia.append(0)
                    multiple.append(contador)
                    contador += 1
                # Creamos las series con los arreglos que hicimos
                auxiliar = [
                    {'name': 'Part vs. Tienda Física', 'data':PartvsTF, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Objetivo', 'data':Objetivo, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Diferencia', 'data':diferencia, 'formato':'porcentaje', 'lugar': 'principal'}
                ]
                series = [
                    {
                        'name': 'Venta Actual',
                        'data': ventaActual, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary',
                        'yAxis': 0
                    },
                    {'name': 'Part vs. TF', 'data':multiple, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'multiple', 'color':'danger'},
                    {
                        'name': 'Var vs. Año Anterior',
                        'data': PartvsAA, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark',
                        'yAxis': 1
                    }
                ]

        if self.titulo == 'Venta por Departamento':
            query = f"""Select cd.deptoDescrip, cd.idDepto,
                sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) ventaActual,
                case when sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end)=0 then 0 else round(((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) /
                sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end))-1)*100,2) end PartvsAA,
                round((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) / (select sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaxdia vxd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha = vxd.fecha
                where vxd.fecha BETWEEN '{fecha_ini_int}' and '{fecha_fin_int}' and idCanal = 0))*100,2) PartvsTF,max(co.Objetivo) Objetivo
                from DWH.artus.ventaDiaria a
                left join DWH.artus.cat_departamento cd on cd.idSubDepto = a.subDepto
                left join DWH.dbo.dim_tiempo dt on a.fecha =dt.fechaComparacion
                left join DWH.dbo.dim_tiempo dt2 on a.fecha =dt2.id_fecha
                left join DWH.artus.catCanal cc on a.idCanal =cc.idCanal
                left join DWH.artus.catObjetivo co on co.idTipo = cc.{'esOmnicanal' if not hayCanal else 'idCanal'} and format(dt2.fecha,'yyyyMM')=co.nMes
                where (dt2.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}'
                or dt.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}')
                and cc.tipo {'= '+self.filtros.canal if hayCanal else 'not in (0)'}
                and cd.deptoDescrip not in ('0')
                group by cd.deptoDescrip, cd.idDepto 
                order by cd.deptoDescrip 
                """
            # print (f"query desde ejesMultiples->Temporada-> Vta por depto: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                ventaActual = []
                PartvsAA = []
                PartvsTF = []
                Objetivo = []
                yAxis = [
                    {'visible': False},
                    {'visible': False}
                ]
                for elemento in arreglo:
                    categories.append(elemento['deptoDescrip'])
                    arrFromSibling.append(elemento['idDepto'])
                    if elemento['ventaActual'] is not None:
                        ventaActual.append(elemento['ventaActual'])
                    else:
                        ventaActual.append(float(0))
                    if elemento['PartvsAA'] is not None:
                        PartvsAA.append(float(elemento['PartvsAA'])/100)
                    else:
                        PartvsAA.append(float(0))
                    if elemento['PartvsTF'] is not None:
                        PartvsTF.append(float(elemento['PartvsTF'])/100)
                    else:
                        PartvsTF.append(float(0))
                    if elemento['Objetivo'] is not None:
                        Objetivo.append(float(elemento['Objetivo'])/100)
                    else:
                        Objetivo.append(float(0))
                    if elemento['PartvsTF'] is not None and elemento['Objetivo'] is not None:
                        diferencia.append((float(elemento['PartvsTF']) - float(elemento['Objetivo']))/100)
                    else:
                        diferencia.append(0)
                    multiple.append(contador)
                    contador += 1
                # Creamos las series con los arreglos que hicimos
                auxiliar = [
                    {'name': 'Part vs. Tienda Física', 'data':PartvsTF, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Objetivo', 'data':Objetivo, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Diferencia', 'data':diferencia, 'formato':'porcentaje', 'lugar': 'principal'}
                ]
                series = [
                    {
                        'name': 'Venta Actual',
                        'data': ventaActual, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary',
                        'yAxis': 0
                    },
                    {'name': 'Part vs. TF', 'data':multiple, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'multiple', 'color':'danger'},
                    {
                        'name': 'Var vs. Año Anterior',
                        'data': PartvsAA, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark',
                        'yAxis': 1
                    }
                ]

        if self.titulo == 'Venta por Formato':
            query = f"""Select ct.formatoNombre,
                sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) ventaActual,
                case when sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end)=0 then 0 else round(((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) /
                sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end))-1)*100,2) end PartvsAA,
                round((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) / (select sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaxdia vxd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha = vxd.fecha
                where vxd.fecha BETWEEN '{fecha_ini_int}' and '{fecha_fin_int}' and idCanal = 0))*100,2) PartvsTF,max(co.Objetivo) Objetivo
                from DWH.artus.ventaDiaria a
                left join DWH.artus.catTienda ct on a.idTienda = ct.tienda
                left join DWH.dbo.dim_tiempo dt on a.fecha =dt.fechaComparacion
                left join DWH.dbo.dim_tiempo dt2 on a.fecha =dt2.id_fecha
                left join DWH.artus.catCanal cc on a.idCanal =cc.idCanal
                left join DWH.artus.catObjetivo co on co.idTipo = cc.{'esOmnicanal' if not hayCanal else 'idCanal'} and format(dt2.fecha,'yyyyMM')=co.nMes
                where (dt2.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}'
                or dt.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}')
                and cc.tipo {'= '+self.filtros.canal if hayCanal else 'not in (0)'}
                group by ct.formatoNombre 
                order by ct.formatoNombre 
                """
            # print (f"query desde ejesMultiples->Temporada-> Venta por formato: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                ventaActual = []
                PartvsAA = []
                PartvsTF = []
                Objetivo = []
                yAxis = [
                    {'visible': False},
                    {'visible': False}
                ]
                for elemento in arreglo:
                    categories.append(elemento['formatoNombre'])
                    if elemento['ventaActual'] is not None:
                        ventaActual.append(elemento['ventaActual'])
                    else:
                        ventaActual.append(float(0))
                    if elemento['PartvsAA'] is not None:
                        PartvsAA.append(float(elemento['PartvsAA'])/100)
                    else:
                        PartvsAA.append(float(0))
                    if elemento['PartvsTF'] is not None:
                        PartvsTF.append(float(elemento['PartvsTF'])/100)
                    else:
                        PartvsTF.append(float(0))
                    if elemento['Objetivo'] is not None:
                        Objetivo.append(float(elemento['Objetivo'])/100)
                    else:
                        Objetivo.append(float(0))
                    if elemento['PartvsTF'] is not None and elemento['Objetivo'] is not None:
                        diferencia.append((float(elemento['PartvsTF']) - float(elemento['Objetivo']))/100)
                    else:
                        diferencia.append(0)
                    multiple.append(contador)
                    contador += 1
                # Creamos las series con los arreglos que hicimos
                auxiliar = [
                    {'name': 'Part vs. Tienda Física', 'data':PartvsTF, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Objetivo', 'data':Objetivo, 'formato':'porcentaje', 'lugar': 'secundario'},
                    {'name': 'Diferencia', 'data':diferencia, 'formato':'porcentaje', 'lugar': 'principal'}
                ]
                series = [
                    {
                        'name': 'Venta Actual',
                        'data': ventaActual, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary',
                        'yAxis': 0
                    },
                    {'name': 'Part vs. TF', 'data':multiple, 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'multiple', 'color':'danger'},
                    {
                        'name': 'Var vs. Año Anterior',
                        'data': PartvsAA, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark',
                        'yAxis': 1
                    }
                ]

        # print(f"Lo que vamos a regresar desde ejesMultiplesApilados -> {self.titulo}: {str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'yAxis': yAxis, 'auxiliar': auxiliar})}")
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'query': query, 'yAxis': yAxis, 'auxiliar': auxiliar, 'arrFromSibling': arrFromSibling}

@router.post("/{seccion}")
async def ejes_multiples_apilados (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = EjesMultiplesApilados(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}