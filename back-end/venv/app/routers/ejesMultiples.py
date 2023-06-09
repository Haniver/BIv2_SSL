from os import pipe, getcwd
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta, time
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.formatoFechas import fechaAbrevEspanol, ddmmyyyy, mesTexto
from copy import deepcopy
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack

router = APIRouter(
    prefix="/ejesMultiples",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class EjesMultiples():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
            # print(f"self.filtros.fechas['fecha_fin']: {str(self.filtros.fechas['fecha_fin'])}")
            # print(f"self.fecha_fin_a12: {str(self.fecha_fin_a12)}")

    async def FoundRate(self):
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        serie1 = []
        serie2 = []
        serie3 = []
        if self.titulo == 'Fulfillment Rate, Found Rate y Pedidos por Día':

            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        nivel = 'tienda'
                        lugar = int(self.filtros.tienda)
                    else:
                        nivel = 'zona'
                        lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    lugar = int(self.filtros.region)
            else:
                filtro_lugar = False
                lugar = ''

            collection = conexion_mongo('report').report_foundRate
            pipeline = [{'$unwind': '$sucursal'}]
            if filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$group':{'_id': {'fecha_interna': '$fechaUltimoCambio', 'fecha_mostrar': '$descrip_fecha'}, 'pedidos': {'$sum': '$n_pedido'}, 'items_ini': {'$sum': '$items_ini'}, 'items_fin': {'$sum': '$items_fin'}, 'items_found': {'$sum': '$items_found'}}})
            pipeline.append({'$project':{'_id':0, 'fecha_interna':'$_id.fecha_interna', 'fecha_mostrar':'$_id.fecha_mostrar', 'pedidos': '$pedidos', 'fulfillment_rate': {'$divide': ['$items_fin', '$items_ini']}, 'found_rate': {'$divide': ['$items_found', '$items_ini']}}})
            pipeline.append({'$sort':{'fecha_interna': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categories.append(row['fecha_mostrar'])
                    serie1.append(row['pedidos'])
                    serie2.append(round(row['fulfillment_rate'],4))
                    serie3.append(round(row['found_rate'], 4))
                series.extend([
                    {'name': 'Pedidos', 'data':serie1, 'type': 'column', 'formato_tooltip':'entero', 'color':'dark'},
                    {'name': 'Fulfillment Rate', 'data':serie2, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'primary'},
                    {'name': 'Found Rate', 'data':serie3, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'secondary'}
                ])
            else:
                hayResultados = "no"
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def VentaSinImpuesto(self):
        anioElegido = self.filtros.anio
        mesElegido = self.filtros.mes + 1
        # print(f"Mes elegido: {mesElegido}")
        ayer = date.today() - timedelta(days=1)
        if mesElegido == ayer.month and anioElegido == ayer.year:
            diaElegido = diaElegido = ayer.day
        else:
            last_day = date(anioElegido, mesElegido, 1).replace(
            month=mesElegido % 12 + 1, day=1) - timedelta(days=1)
            diaElegido = last_day.day
        mesEnTexto = mesTexto(mesElegido)

        anioElegido_inicio = datetime(anioElegido, 1, 1).strftime('%Y%m%d')
        # Get the last day of the given month
        last_day = date(int(anioElegido), int(mesElegido), 1).replace(month=mesElegido % 12 + 1, day=1) - timedelta(days=1)

        # Get the last second of the last minute of the last hour of the last day
        mesElegido_fin = datetime.combine(
            last_day, time.max).replace(
            hour=23, minute=59, second=59)

        self.ayer = datetime(anioElegido, mesElegido, diaElegido).strftime('%Y%m%d')
        anioElegido_fin = datetime(anioElegido, 12, 31).strftime('%Y%m%d')
        self.anioAnterior_inicio = datetime(anioElegido - 1, 1, 1).strftime('%Y%m%d')
        self.anioAnterior_fin = datetime(anioElegido - 1, mesElegido, diaElegido).strftime('%Y%m%d')
        mesElegido_inicio = datetime(anioElegido, mesElegido, 1).strftime('%Y%m%d')
        mesElegido_fin = datetime(anioElegido, mesElegido, diaElegido).strftime('%Y%m%d')
        self.mesAnterior_inicio = datetime(anioElegido - 1, mesElegido, 1).strftime('%Y%m%d')
        self.mesAnterior_fin = datetime(anioElegido - 1, mesElegido, diaElegido).strftime('%Y%m%d')
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'

        if self.filtros.canal != '' and self.filtros.canal != "False" and self.filtros.canal != None:
            canal = self.filtros.canal
        else:
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute("select distinct tipo from DWH.artus.catCanal where descripTipo not in ('Tienda Fisica')")
            arreglo = crear_diccionario(cursor)
            canal = ",".join([str(elemento['tipo']) for elemento in arreglo])
            # print(f"Arreglo desde EjesMultiples: {arreglo}")
            # canal = ''
        # print(f"canal desde ejesMultiples -> VentaSinImpuesto: {canal}")
        if self.titulo == 'Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo':
            mod_titulo_serie = ''
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []
            

            pipeline = f"""select dt.abrev_mes categoria,
            sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
            sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
            sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
            from DWH.artus.ventaDiaria vd
            left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
            left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
            left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
            left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
            where dt.anio in ({anioElegido},{anioElegido-1})
            and cc.tipo in ({canal}) """
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        pipeline += f""" and ct.tienda = {self.filtros.tienda} """
                    else:
                        pipeline += f""" and ct.zona = {self.filtros.zona} """
                else:
                    pipeline += f""" and ct.region = {self.filtros.region} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += " group by dt.abrev_mes,dt.num_mes order by dt.num_mes "
            # print(f"Query desde Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo: {pipeline}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    aAnterior = round((arreglo[i]['AAnterior']), 2) if arreglo[i]['AAnterior'] is not None else 0
                    aActual = round((arreglo[i]['AActual']), 2) if arreglo[i]['AActual'] is not None else 0
                    categories.append(arreglo[i]['categoria'])
                    serie1.append(aAnterior)
                    serie2.append(aActual)
                    # if arreglo[i]['AAnterior'] != 0:
                    # # if i != 0:
                    #     serie4.append(round(((arreglo[i]['AActual'] / arreglo[i]['AAnterior'])-1), 4))
                    # else:
                    #     serie4.append(0)
                    # if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                    serie3.append(round((arreglo[i]['objetivo']), 2))
                    # if arreglo[i]['objetivo'] != 0:
                    #     serie5.append(round(((arreglo[i]['AActual'] / arreglo[i]['objetivo'])-1), 4))
                    # else:
                    #     serie5.append(0)
                series.extend([
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'data':serie1, 'type': 'column', 'formato_tooltip':'moneda', 'color':'dark'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'data':serie2, 'type': 'column', 'formato_tooltip':'moneda', 'color':'secondary'}
                ])
                series.append({'name': 'Objetivo '+mod_titulo_serie+str(anioElegido), 'data':serie3, 'type': 'column', 'formato_tooltip':'moneda', 'color':'light'})
                # series.append({'name': '% Var Actual', 'data':serie4, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'})
                # series.append({'name': '% Var Objetivo', 'data':serie5, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'})
            else:
                hayResultados = "no"
                categories = []
                series = []

        if self.titulo == 'Venta mensual por día: $anioActual vs. $anioAnterior (fecha comparable) y Objetivo':
            mod_titulo_serie = f"{mesTexto(mesElegido)} "
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []

            filtrosAdicionales = ''
            filtrosAdicionales2 = ''
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        filtrosAdicionales += f""" and ct.tienda = {self.filtros.tienda} """
                        filtrosAdicionales2 += f""" and ct2.tienda = {self.filtros.tienda} """
                    else:
                        filtrosAdicionales += f""" and ct.zona = {self.filtros.zona} """
                        filtrosAdicionales2 += f""" and ct2.zona = {self.filtros.zona} """
                else:
                    filtrosAdicionales += f""" and ct.region = {self.filtros.region} """
                    filtrosAdicionales2 += f""" and ct2.region = {self.filtros.region} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    filtrosAdicionales += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                    filtrosAdicionales2 += f""" and cd2.idSubDepto = {self.filtros.subDepto} """
                else:
                    filtrosAdicionales += f""" and cd.idDepto = {self.filtros.depto} """
                    filtrosAdicionales2 += f""" and cd2.idDepto = {self.filtros.depto} """

            pipeline = f"""
                SELECT  dt.fecha
                    ,b.a AAnterior
                    ,convert(date,CONVERT (varchar,dt.fechaComparacion)) fechaComparacion
                    ,SUM(case WHEN anio = {anioElegido} THEN isnull (ventaSinImpuestos,0) else 0 end) AActual
                    ,SUM(case WHEN anio = {anioElegido} THEN objetivo else 0 end) objetivo
                FROM
                (
                    SELECT  dt2.id_fecha f
                        ,SUM(case WHEN anio = {anioElegido} THEN isnull (ventaSinImpuestos,0) else 0 end) a
                    FROM DWH.artus.ventaDiaria vd2
                    LEFT JOIN DWH.dbo.dim_tiempo dt2
                    ON dt2.fechaComparacion = vd2.fecha
                    LEFT JOIN DWH.artus.catTienda ct2
                    ON vd2.idTienda = ct2.tienda
                    LEFT JOIN DWH.artus.catCanal cc2
                    ON vd2.idCanal = cc2.idCanal
                    LEFT JOIN DWH.artus.cat_departamento cd2
                    ON vd2.subDepto = cd2.idSubDepto
                    WHERE dt2.anio IN ({anioElegido})
                    {filtrosAdicionales2}
                    AND dt2.abrev_mes = '{mesTexto(mesElegido)}'
                    AND cc2.tipo IN ({canal})
                    GROUP BY  dt2.id_fecha
                ) b
                LEFT JOIN DWH.artus.ventaDiaria vd
                ON b.f = vd.fecha
                LEFT JOIN DWH.dbo.dim_tiempo dt
                ON vd.fecha = dt.id_fecha
                LEFT JOIN DWH.artus.catTienda ct
                ON vd.idTienda = ct.tienda
                LEFT JOIN DWH.artus.catCanal cc
                ON vd.idCanal = cc.idCanal
                LEFT JOIN DWH.artus.cat_departamento cd
                ON vd.subDepto = cd.idSubDepto
                WHERE dt.anio IN ({anioElegido}, {anioElegido - 1})
                {filtrosAdicionales}
                AND dt.abrev_mes = '{mesTexto(mesElegido)}'
                AND cc.tipo IN ({canal})
                GROUP BY  dt.fecha
                        ,b.a
                        ,convert(date,CONVERT (varchar,dt.fechaComparacion))
                ORDER BY dt.fecha
            """
            # print(f"Query desde EjesMultiples -> VentaSinImpuesto -> {self.titulo}: {pipeline}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categories.append(fechaAbrevEspanol(arreglo[i]['fecha']))
                    serie1.append(round((arreglo[i]['AAnterior']), 2))
                    serie2.append(round((arreglo[i]['AActual']), 2))
                    if arreglo[i]['AAnterior'] != 0:
                    # if i != 0:
                        serie4.append(round(((arreglo[i]['AActual'] / arreglo[i]['AAnterior'])-1), 4))
                    else:
                        serie4.append(0)
                    if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                        serie3.append(round((arreglo[i]['objetivo']), 2))
                    if arreglo[i]['objetivo'] != 0:
                        serie5.append(round(((arreglo[i]['AActual'] / arreglo[i]['objetivo'])-1), 4))
                    else:
                        serie5.append(0)
                series.extend([
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'data':serie1, 'type': 'column', 'formato_tooltip':'moneda', 'color':'dark'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'data':serie2, 'type': 'column', 'formato_tooltip':'moneda', 'color':'secondary'}
                ])
                series.append({'name': 'Objetivo '+mod_titulo_serie+str(anioElegido), 'data':serie3, 'type': 'column', 'formato_tooltip':'moneda', 'color':'light'})
                # series.append({'name': '% Var Actual', 'data':serie4, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'})
                # series.append({'name': '% Var Objetivo', 'data':serie5, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'})
            else:
                hayResultados = "no"
                categories = []
                series = []

        if self.titulo == 'Venta anual por lugar: $anioActual vs. $anioAnterior y Objetivo':
            # print('self.filtros.canal = '+self.filtros.canal)
            mod_titulo_serie = ''
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []

            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    filtro_lugar = f" and ct.zona = {self.filtros.zona} "
                    campo_siguiente_lugar = 'tiendaNombre'
                else:
                    filtro_lugar = f" and ct.region = {self.filtros.region} "
                    campo_siguiente_lugar = 'zonaNombre'
            else:
                filtro_lugar = ''
                campo_siguiente_lugar = 'regionNombre'

            pipeline = f"""select ct.{campo_siguiente_lugar} categoria,
            sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
            sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
            sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
            from DWH.artus.ventaDiaria vd
            left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
            left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
            left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
            left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
            where dt.anio in ({anioElegido},{anioElegido-1})
            and cc.tipo in ({canal}) {filtro_lugar} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += f" group by ct.{campo_siguiente_lugar} "
            # print(f"Query desde EjesMultiples -> VentaSinImpuesto -> {self.titulo}: {pipeline}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categories.append(arreglo[i]['categoria'])
                    serie1.append(round((arreglo[i]['AAnterior']), 2))
                    serie2.append(round((arreglo[i]['AActual']), 2))
                    if arreglo[i]['AAnterior'] != 0:
                    # if i != 0:
                        serie4.append(round(((arreglo[i]['AActual'] / arreglo[i]['AAnterior'])-1), 4))
                    else:
                        serie4.append(0)
                    if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                        serie3.append(round((arreglo[i]['objetivo']), 2))
                    if arreglo[i]['objetivo'] != 0:
                        serie5.append(round(((arreglo[i]['AActual'] / arreglo[i]['objetivo'])-1), 4))
                    else:
                        serie5.append(0)
                series.extend([
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'data':serie1, 'type': 'column', 'formato_tooltip':'moneda', 'color':'dark'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'data':serie2, 'type': 'column', 'formato_tooltip':'moneda', 'color':'secondary'}
                ])
                series.append({'name': 'Objetivo '+mod_titulo_serie+str(anioElegido), 'data':serie3, 'type': 'column', 'formato_tooltip':'moneda', 'color':'light'})
                # series.append({'name': '% Var Actual', 'data':serie4, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'})
                # series.append({'name': '% Var Objetivo', 'data':serie5, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'})
            else:
                hayResultados = "no"
                categories = []
                series = []

        if self.titulo == 'Venta mensual por lugar: $anioActual vs. $anioAnterior y Objetivo':
            # print('self.filtros.canal = '+self.filtros.canal)
            mod_titulo_serie = f"{mesTexto(mesElegido)} "
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []

            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    filtro_lugar = f" and ct.zona = {self.filtros.zona} "
                    campo_siguiente_lugar = 'tiendaNombre'
                else:
                    filtro_lugar = f" and ct.region = {self.filtros.region} "
                    campo_siguiente_lugar = 'zonaNombre'
            else:
                filtro_lugar = ''
                campo_siguiente_lugar = 'regionNombre'

            pipeline = f"""select ct.{campo_siguiente_lugar} categoria,
                sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
                sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
                sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
                from DWH.artus.ventaDiaria vd
                left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
                left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
                left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
                left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
                where dt.anio in ({anioElegido},{anioElegido-1})
                and dt.abrev_mes='{mesTexto(mesElegido)}'
                and cc.tipo in ({canal}) {filtro_lugar} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += f" group by ct.{campo_siguiente_lugar} "
            # print(f"Query desde EjesMultiples -> Venta Sin impuesto -> Venta  Mensual Por Lugar: {pipeline}")

            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categories.append(arreglo[i]['categoria'])
                    serie1.append(round((arreglo[i]['AAnterior']), 2))
                    serie2.append(round((arreglo[i]['AActual']), 2))
                    if arreglo[i]['AAnterior'] != 0:
                    # if i != 0:
                        serie4.append(round(((arreglo[i]['AActual'] / arreglo[i]['AAnterior'])-1), 4))
                    else:
                        serie4.append(0)
                    if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                        serie3.append(round((arreglo[i]['objetivo']), 2))
                    if arreglo[i]['objetivo'] != 0:
                        serie5.append(round(((arreglo[i]['AActual'] / arreglo[i]['objetivo'])-1), 4))
                    else:
                        serie5.append(0)
                series.extend([
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'data':serie1, 'type': 'column', 'formato_tooltip':'moneda', 'color':'dark'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'data':serie2, 'type': 'column', 'formato_tooltip':'moneda', 'color':'secondary'}
                ])
                series.append({'name': 'Objetivo '+mod_titulo_serie+str(anioElegido), 'data':serie3, 'type': 'column', 'formato_tooltip':'moneda', 'color':'light'})
                # series.append({'name': '% Var Actual', 'data':serie4, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'})
                # series.append({'name': '% Var Objetivo', 'data':serie5, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'})
            else:
                hayResultados = "no"
                categories = []
                series = []

        if self.titulo == 'Venta anual de todas las zonas: $anioActual vs. $anioAnterior y Objetivo':
            # print('self.filtros.canal = '+self.filtros.canal)
            mod_titulo_serie = ''
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []

            filtro_lugar = ''
            campo_siguiente_lugar = 'zonaNombre'

            pipeline = f"""select ct.{campo_siguiente_lugar} categoria,
            sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
            sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
            sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
            from DWH.artus.ventaDiaria vd
            left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
            left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
            left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
            left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
            where dt.anio in ({anioElegido},{anioElegido-1})
            and cc.tipo in ({canal}) {filtro_lugar} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += f" group by ct.{campo_siguiente_lugar} "
            # print(f"Query desde EjesMultiples -> VentaSinImpuesto -> {self.titulo}: {pipeline}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categories.append(arreglo[i]['categoria'])
                    serie1.append(round((arreglo[i]['AAnterior']), 2))
                    serie2.append(round((arreglo[i]['AActual']), 2))
                    if arreglo[i]['AAnterior'] != 0:
                    # if i != 0:
                        serie4.append(round(((arreglo[i]['AActual'] / arreglo[i]['AAnterior'])-1), 4))
                    else:
                        serie4.append(0)
                    if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                        serie3.append(round((arreglo[i]['objetivo']), 2))
                    if arreglo[i]['objetivo'] != 0:
                        serie5.append(round(((arreglo[i]['AActual'] / arreglo[i]['objetivo'])-1), 4))
                    else:
                        serie5.append(0)
                series.extend([
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'data':serie1, 'type': 'column', 'formato_tooltip':'moneda', 'color':'dark'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'data':serie2, 'type': 'column', 'formato_tooltip':'moneda', 'color':'secondary'}
                ])
                series.append({'name': 'Objetivo '+mod_titulo_serie+str(anioElegido), 'data':serie3, 'type': 'column', 'formato_tooltip':'moneda', 'color':'light'})
                # series.append({'name': '% Var Actual', 'data':serie4, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'})
                # series.append({'name': '% Var Objetivo', 'data':serie5, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'})
            else:
                hayResultados = "no"
                categories = []
                series = []

        if self.titulo == 'Venta mensual de todas las zonas: $anioActual vs. $anioAnterior y Objetivo':
            # print('self.filtros.canal = '+self.filtros.canal)
            mod_titulo_serie = f"{mesTexto(mesElegido)} "
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []

            filtro_lugar = ''
            campo_siguiente_lugar = 'zonaNombre'

            pipeline = f"""select ct.{campo_siguiente_lugar} categoria,
                sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
                sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
                sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
                from DWH.artus.ventaDiaria vd
                left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
                left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
                left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
                left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
                where dt.anio in ({anioElegido},{anioElegido-1})
                and dt.abrev_mes='{mesTexto(mesElegido)}'
                and cc.tipo in ({canal}) {filtro_lugar} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += f" group by ct.{campo_siguiente_lugar} "
            # print(f"Query desde EjesMultiples -> Venta Sin impuesto -> Venta  Mensual Por Lugar: {pipeline}")

            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categories.append(arreglo[i]['categoria'])
                    serie1.append(round((arreglo[i]['AAnterior']), 2))
                    serie2.append(round((arreglo[i]['AActual']), 2))
                    if arreglo[i]['AAnterior'] != 0:
                    # if i != 0:
                        serie4.append(round(((arreglo[i]['AActual'] / arreglo[i]['AAnterior'])-1), 4))
                    else:
                        serie4.append(0)
                    if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                        serie3.append(round((arreglo[i]['objetivo']), 2))
                    if arreglo[i]['objetivo'] != 0:
                        serie5.append(round(((arreglo[i]['AActual'] / arreglo[i]['objetivo'])-1), 4))
                    else:
                        serie5.append(0)
                series.extend([
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'data':serie1, 'type': 'column', 'formato_tooltip':'moneda', 'color':'dark'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'data':serie2, 'type': 'column', 'formato_tooltip':'moneda', 'color':'secondary'}
                ])
                series.append({'name': 'Objetivo '+mod_titulo_serie+str(anioElegido), 'data':serie3, 'type': 'column', 'formato_tooltip':'moneda', 'color':'light'})
                # series.append({'name': '% Var Actual', 'data':serie4, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'})
                # series.append({'name': '% Var Objetivo', 'data':serie5, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'})
            else:
                hayResultados = "no"
                categories = []
                series = []

        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def PedidoPerfecto(self):
        # print("Entró a Ejes Múltiples")
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        # esta condición está aquí porque a veces los filtros no terminan de cargar y ya está cargando la gráfica. Hay que verificar que los filtros hagan sentido.
        if (self.titulo != 'Pedidos Perfectos Periodo Seleccionado Vs Anterior') and (not self.filtros.periodo or (self.filtros.agrupador == 'mes' and 'semana' in self.filtros.periodo) or (self.filtros.agrupador == 'semana' and not 'semana' in self.filtros.periodo) or (self.filtros.agrupador == 'dia' and not 'dia' in self.filtros.periodo)):
            return {'hayResultados':'no','Fcategories':[], 'series':[], 'pipeline': [], 'lenArreglo':0}
        clauseCatProveedor = False
        if len(self.filtros.provLogist) == 1:
            # print(f"provLogist[0] desde ejesMultiples -> PedidoPerfecto: {self.filtros.provLogist[0]}")
            clauseCatProveedor = {'$match': {'sucursal.Delivery': self.filtros.provLogist[0]}}
        elif len(self.filtros.provLogist) > 1:
            clauseCatProveedor = {'$match': {
                '$expr': {
                    '$or': []
                }
            }}
            for prov in self.filtros.provLogist:
                clauseCatProveedor['$match']['$expr']['$or'].append(
                    {'$eq': [
                        '$sucursal.Delivery',
                        prov
                    ]}
                )

        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idtienda'
                    lugar = int(self.filtros.tienda)
                    siguiente_lugar = 'tiendaNombre'
                else:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
                    siguiente_lugar = 'tiendaNombre'
            else:
                nivel = 'region'
                lugar = int(self.filtros.region)
                siguiente_lugar = 'zonaNombre'
        else:
            filtro_lugar = False
            lugar = ''
            siguiente_lugar = 'regionNombre'

        pipeline = [{'$unwind': '$sucursal'}]
        if filtro_lugar:
            pipeline.extend([
                {'$match': {'sucursal.'+ nivel: lugar}}
            ])
        if self.filtros.periodo:
            if self.filtros.agrupador == 'mes':
                periodo = '$nMes'
                anio_elegido = self.filtros.periodo['anio']
                mes_elegido = self.filtros.periodo['mes']
                fecha_fin = datetime(anio_elegido, mes_elegido, monthrange(anio_elegido, mes_elegido)[1])
                if fecha_fin.month == 1:
                    fecha_ini = datetime(fecha_fin.year - 1, 12, 1)
                else:
                    fecha_ini = datetime(fecha_fin.year, fecha_fin.month - 1, 1)
            elif self.filtros.agrupador == 'semana':
                periodo = '$idSemDS'
                semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
                anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
                monday = datetime.strptime(f'{anio_elegido}-{semana_elegida}-1', "%Y-%W-%w")
                # print(f"monday = {str(monday)}")
                fecha_fin = monday + timedelta(days=6)
                fecha_ini = monday - timedelta(days=7)
            elif self.filtros.agrupador == 'dia':
                periodo = '$fecha'
                anio_elegido = self.filtros.periodo['anio']
                mes_elegido = self.filtros.periodo['mes']
                dia_elegido = self.filtros.periodo['dia']
                fecha_fin = datetime(anio_elegido, mes_elegido, dia_elegido)
                fecha_ini = fecha_fin - timedelta(days=1)
            # print(f"fecha_fin en la primera línea desde {self.titulo}: {str(fecha_fin)}")
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59, microsecond=999999)
            # print(f"fecha_fin en la segunda línea desde {self.titulo}: {str(fecha_fin)}")
        collection = conexion_mongo('report').report_pedidoPerfecto

        if self.titulo == 'Pedidos Perfectos Todo el Rango':
            # print("Entró a Pedidos Perfectos Todo el Rango en Ejes Múltiples")
            # print(f"Desde ejesMultiples -> 'Pedidos Perfectos': Fecha inicio: {self.fecha_ini_a12}. Fecha fin: {self.fecha_fin_a12}")
            serie1 = []
            serie2 = []
            series = []
            pipeline.append(
                {'$match': {
                    'fecha': {
                        '$gte': self.fecha_ini_a12, 
                        '$lt': self.fecha_fin_a12
                    }
                }}
            )
            # print(f"Fecha_ini: {fecha_ini}, Fecha_fin: {fecha_fin}")
            if clauseCatProveedor:
                pipeline.append(clauseCatProveedor)
            pipeline.extend([
                {'$group': {
                    '_id': {},
                    'totales': {'$sum': '$Total_Pedidos'},
                    'perfectos': {'$sum': '$perfecto'}
                }}, 
                {'$sort': {'_id.anio': 1}}
            ])
            grupo = pipeline[-2]['$group']['_id']
            sort = pipeline[-1]['$sort']
            # print("Agrupador en Pedidos Perfectos en Ejes Múltiples = "+self.filtros.agrupador)
            if self.filtros.agrupador == 'mes' or self.filtros.agrupador == 'dia' :
                grupo['anio'] = {'$year': '$fecha'}
                grupo['mes'] = {'$month': '$fecha'}
                sort['_id.anio'] = 1
                sort['_id.mes'] = 1
                if self.filtros.agrupador == 'dia':
                    grupo['dia'] = {'$dayOfMonth': '$fecha'}
                    sort['_id.dia'] = 1
            elif self.filtros.agrupador == 'semana':
                grupo['semana'] = '$idSemDS'
                sort['_id.semana'] = 1
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(f"Pipeline desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
            # print(f"Arreglo desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(arreglo)}")
            if len(arreglo) >0:
                hayResultados = "si"
                # print(f"Agrupador desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(self.filtros.agrupador)}")
                for i in range(len(arreglo)):
                    if self.filtros.agrupador == 'mes' or self.filtros.agrupador == 'dia':
                        anio = arreglo[i]['_id']['anio']
                        mes = arreglo[i]['_id']['mes']
                        category = mesTexto(mes) + ' ' + str(anio)
                        if self.filtros.agrupador == 'dia':
                            category = str(arreglo[i]['_id']['dia']) + ' ' + category
                    elif self.filtros.agrupador == 'semana':
                        if arreglo[i]['_id']['semana'] != None:
                            cursor_semana = conexion_mongo('report').catTiempo.find({
                                'idSemDS': arreglo[i]['_id']['semana']
                            })
                            arreglo_semana = await cursor_semana.to_list(length=1)
                            category = arreglo_semana[0]['nSemDS']
                        else:
                            category = 'Semana no encontrada'
                            # print(f"Category desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(category)}")
                    categories.append(category)
                    if arreglo[i]['totales'] > 0:
                        serie1.append(round((arreglo[i]['perfectos']/arreglo[i]['totales']), 4))
                    else:
                        serie1.append(0)
                    serie2.append(round((serie1[i]-serie1[i-1]), 4)) if i > 0 else serie2.append(0)
                    
                series.extend([
                    {'name': '% Perfectos', 'data':serie1, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'secondary'},
                    {'name': '% Dif', 'data':serie2, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'dark'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Pedidos Perfectos Periodo Seleccionado Vs Anterior':
            # print("Entró a Pedidos Perfectos en Ejes Múltiples")
            # print(f"Desde ejesMultiples -> 'Pedidos Perfectos': Fecha inicio: {self.fecha_ini_a12}. Fecha fin: {self.fecha_fin_a12}")
            serie1 = []
            serie2 = []
            pipeline.append(
                {'$match': {
                    'fecha': {
                        '$gte': fecha_ini, 
                        '$lt': fecha_fin
                    }
                }}
            )
            if clauseCatProveedor:
                pipeline.append(clauseCatProveedor)
            pipeline.extend([
                {'$group': {
                    '_id': {},
                    'totales': {'$sum': '$Total_Pedidos'},
                    'perfectos': {'$sum': '$perfecto'}
                }}, 
                {'$sort': {'_id.anio': 1}}
            ])
            # print(str(pipeline))
            grupo = pipeline[-2]['$group']['_id']
            sort = pipeline[-1]['$sort']
            # print("Agrupador en Pedidos Perfectos en Ejes Múltiples = "+self.filtros.agrupador)
            if self.filtros.agrupador == 'mes' or self.filtros.agrupador == 'dia' :
                grupo['anio'] = {'$year': '$fecha'}
                grupo['mes'] = {'$month': '$fecha'}
                sort['_id.anio'] = 1
                sort['_id.mes'] = 1
                if self.filtros.agrupador == 'dia':
                    grupo['dia'] = {'$dayOfMonth': '$fecha'}
                    sort['_id.dia'] = 1
            elif self.filtros.agrupador == 'semana':
                grupo['semana'] = '$idSemDS'
                sort['_id.semana'] = 1
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(f"Pipeline desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
            if len(arreglo) >0:
                hayResultados = "si"
                # print("Arreglo de Pedidos Perfectos en Ejes Múltiples: "+str(arreglo))
                for i in range(len(arreglo)):
                    if self.filtros.agrupador == 'mes' or self.filtros.agrupador == 'dia':
                        anio = arreglo[i]['_id']['anio']
                        mes = arreglo[i]['_id']['mes']
                        category = mesTexto(mes) + ' ' + str(anio)
                        if self.filtros.agrupador == 'dia':
                            category = str(arreglo[i]['_id']['dia']) + ' ' + category
                    elif self.filtros.agrupador == 'semana':
                        if arreglo[i]['_id']['semana'] != None:
                            cursor_semana = conexion_mongo('report').catTiempo.find({
                                'idSemDS': arreglo[i]['_id']['semana']
                            })
                            arreglo_semana = await cursor_semana.to_list(length=1)
                            category = arreglo_semana[0]['nSemDS']
                        else:
                            category = 'Semana no encontrada'
                    categories.append(category)
                    if arreglo[i]['totales'] > 0:
                        serie1.append(round((arreglo[i]['perfectos']/arreglo[i]['totales']), 4))
                    else:
                        serie1.append(0)
                    serie2.append(round((serie1[i]-serie1[i-1]), 4)) if i > 0 else serie2.append(0)
                    
                series.extend([
                    {'name': '% Perfectos', 'data':serie1, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'secondary'},
                    {'name': '% Dif', 'data':serie2, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'dark'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Evaluación por KPI Pedido Perfecto':
            # if self.filtros.periodo:
            #     if self.filtros.agrupador == 'mes':
            #         periodo = '$nMes'
            #         anio_elegido = self.filtros.periodo['anio']
            #         mes_elegido = self.filtros.periodo['mes']
            #         fecha_fin = datetime(anio_elegido, mes_elegido, monthrange(anio_elegido, mes_elegido)[1])
            #         if fecha_fin.month == 1:
            #             fecha_ini = datetime(fecha_fin.year - 1, 12, 1)
            #         else:
            #             fecha_ini = datetime(fecha_fin.year, fecha_fin.month - 1, 1)
            #     elif self.filtros.agrupador == 'semana':
            #         periodo = '$idSemDS'
            #         semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
            #         anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
            #         monday = datetime.strptime(f'{anio_elegido}-{semana_elegida}-1', "%Y-%W-%w")
            #         fecha_fin = monday + timedelta(days=5)
            #         fecha_ini = monday - timedelta(days=8)
            #     elif self.filtros.agrupador == 'dia':
            #         periodo = '$fecha'
            #         anio_elegido = self.filtros.periodo['anio']
            #         mes_elegido = self.filtros.periodo['mes']
            #         dia_elegido = self.filtros.periodo['dia']
            #         fecha_fin = datetime(anio_elegido, mes_elegido, dia_elegido)
            #         fecha_ini = fecha_fin - timedelta(days=1)
            #     fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59, microsecond=999999)

                pipeline = [{'$unwind': '$sucursal'},
                    {'$match': {
                        'sucursal.region':{'$ne':None}
                    }}
                ]
                if filtro_lugar:
                    pipeline.extend([
                        {'$match': {'sucursal.'+ nivel: lugar}}
                    ])
                if clauseCatProveedor:
                    pipeline.append(clauseCatProveedor)

                pipeline.extend([
                    {'$match': {
                        'fecha': {
                            '$gte': fecha_ini,
                            '$lte': fecha_fin
                        }
                    }}
                ])
                pipeline.extend([
                    {'$group': {
                        '_id': {
                            # poner el agrupador
                            'periodo': periodo,
                        },
                        'con_quejas': {
                            '$sum': '$con_queja'
                        },
                        'retrasados': {
                            '$sum': '$retrasados'
                        },
                        'cancelados': {
                            '$sum': '$Cancelados'
                        },
                        'incompletos': {
                            '$sum': '$incompletos'
                        },
                        'totales': {
                            '$sum': '$Total_Pedidos'
                        }
                    }},
                    {
                        '$sort': {'_id.periodo': 1}
                    }
                ])
                # print(f"Pipeline desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                if len(arreglo) >0:
                    if len(arreglo) > 2:
                        print(f"Arreglo tiene más de dos registros: {str(arreglo)}")
                        print(f"fecha_ini = {str(fecha_ini)}, fecha_fin = {str(fecha_fin)}, periodo = {periodo}")
                        
                    # if len(arreglo) <= 1:
                    #     print(f"Arreglo tiene SOLO UN REGISTRO: {str(arreglo)}")
                    hayResultados = "si"
                    series = [[], []]
                    titulos = [[], []]
                    contador = 0
                    for registro in arreglo:
                        if self.filtros.agrupador == 'mes':
                            titulos[contador] = mesTexto(registro['_id']['periodo'])
                        elif self.filtros.agrupador == 'semana':
                            periodo = int(registro['_id']['periodo'])
                            anio = periodo // 100
                            numSem = periodo - anio * 100
                            titulos[contador] = 'Sem ' + str(numSem)
                        elif self.filtros.agrupador == 'dia':
                            fecha = registro['_id']['periodo']
                            titulos[contador] = str(fecha.day) + ' '+ mesTexto(fecha.month)
                        if registro['totales'] > 0:
                            series[contador].extend([
                                round((float(registro['con_quejas'])/float(registro['totales'])), 4), 
                                round((float(registro['retrasados'])/float(registro['totales'])), 4),
                                round((float(registro['cancelados'])/float(registro['totales'])), 4),
                                round((float(registro['incompletos'])/float(registro['totales'])), 4)
                            ])
                        else:
                            series[contador].extend([0, 0, 0, 0])
                        contador += 1
                    series = [
                        {'name': titulos[0], 'data':series[0], 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
                        {'name': titulos[1], 'data':series[1], 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'}
                    ]
                    categories = ['Con quejas', 'Retrasados', 'Cancelados', 'Incompletos']
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")

        # if self.titulo == 'Evaluación por KPI Pedido Perfecto':
        #     if self.filtros.periodo != {}:
        #         serie1 = []
        #         serie2 = []
        #         serie3 = []

        #         # pipeline.append(
        #         #     {'$match': {
        #         #         'fecha': {
        #         #             '$gte': self.fecha_ini_a12, 
        #         #             '$lt': self.fecha_fin_a12
        #         #         }
        #         #     }}
        #         # )
        #         pipeline.extend([
        #             {'$match': {
        #                 '$expr': {
        #                     '$or': [
        #                         {'$and': []},
        #                         {'$and': []}
        #                     ]
        #                 }
        #             }},
        #             {'$project': {
        #                 'con_queja': '$con_queja',
        #                 'retrasados': '$retrasados',
        #                 'Cancelados': '$Cancelados',
        #                 'incompletos': '$incompletos',
        #                 'upSells': '$upSells',
        #                 'Total_Pedidos': '$Total_Pedidos',
        #                 'periodo': {
        #                     '$cond': [
        #                         {'$and': []},
        #                         0,
        #                         1
        #                     ]
        #                 }
        #             }},
        #             {'$group': {
        #                 '_id': '$periodo',
        #                 'con_quejas': {
        #                     '$sum': '$con_queja'
        #                 },
        #                 'retrasados': {
        #                     '$sum': '$retrasados'
        #                 },
        #                 'cancelados': {
        #                     '$sum': '$Cancelados'
        #                 },
        #                 'incompletos': {
        #                     '$sum': '$incompletos'
        #                 },
        #                 'upSells': {
        #                     '$sum': '$upSells'
        #                 },
        #                 'totales': {
        #                     '$sum': '$Total_Pedidos'
        #                 }
        #             }},
        #             {'$sort': {'_id': 1}}
        #         ])
        #         # Lo copiamos en el otro facet:
        #         # pipe_facet_elegida = deepcopy(pipe_facet_anterior)
        #         # Creamos variables para manipular los diccionarios:
        #         # match_facet_anterior = pipe_facet_anterior[-2]['$match']['$expr']['$and']
        #         match1 = pipeline[-4]['$match']['$expr']['$or'][0]['$and']
        #         match2 = pipeline[-4]['$match']['$expr']['$or'][1]['$and']
        #         cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']
                
        #         # Modificamos los facets para el caso de que el agrupador sea por mes:
        #         if self.filtros.agrupador == 'mes':
        #             anio_elegido = self.filtros.periodo['anio']
        #             mes_elegido = self.filtros.periodo['mes']
        #             if mes_elegido > 1:
        #                 mes_anterior = mes_elegido - 1
        #                 anio_anterior = anio_elegido
        #             else:
        #                 mes_anterior = 12
        #                 anio_anterior = anio_elegido - 1
        #             condicion_anterior = [
        #                 {'$eq': [
        #                     anio_anterior,
        #                     {'$year': '$fecha'}
        #                 ]},
        #                 {'$eq': [
        #                     mes_anterior,
        #                     {'$month': '$fecha'}
        #                 ]}
        #             ]
        #             match1.extend(condicion_anterior)
        #             cond_periodo.extend(condicion_anterior)
        #             match2.extend([
        #                 {'$eq': [
        #                     anio_elegido,
        #                     {'$year': '$fecha'}
        #                 ]},
        #                 {'$eq': [
        #                     mes_elegido,
        #                     {'$month': '$fecha'}
        #                 ]}
        #             ])
        #             tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
        #             tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
        #         # Modificamos los facets para el caso de que el agrupador sea por semana:
        #         elif self.filtros.agrupador == 'semana':
        #             semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
        #             anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
        #             if semana_elegida != 1:
        #                 semana_anterior = semana_elegida - 1
        #                 anio_anterior = anio_elegido
        #             else:
        #                 anio_anterior = anio_elegido - 1
        #                 last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
        #                 semana_anterior = last_week.isocalendar()[1]
        #             semana_elegida_txt = '0' + str(semana_elegida) if semana_elegida < 10 else str(semana_elegida)
        #             semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
        #             semana_elegida_txt = int(str(anio_elegido) + semana_elegida_txt)
        #             semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
        #             condicion_anterior = [
        #                 {'$eq': [
        #                     semana_anterior_txt,
        #                     '$idSemDS'
        #                 ]}
        #             ]
        #             match1.extend(condicion_anterior)
        #             cond_periodo.extend(condicion_anterior)
        #             match2.extend([
        #                 {'$eq': [
        #                     semana_elegida_txt,
        #                     '$idSemDS'
        #                 ]}
        #             ])
        #         # Modificamos los facets para el caso de que el agrupador sea por día:
        #         elif self.filtros.agrupador == 'dia':
        #             anio_elegido = self.filtros.periodo['anio']
        #             mes_elegido = self.filtros.periodo['mes']
        #             dia_elegido = self.filtros.periodo['dia']
        #             if dia_elegido != 1:
        #                 dia_anterior = dia_elegido - 1
        #                 mes_anterior = mes_elegido
        #                 anio_anterior = anio_elegido
        #             else:
        #                 if mes_elegido != 1:
        #                     mes_anterior = mes_elegido - 1
        #                     anio_anterior = anio_elegido
        #                 else:
        #                     mes_anterior = 12
        #                     anio_anterior = anio_elegido - 1
        #                 dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
        #             condicion_anterior = [
        #                 {'$eq': [
        #                     anio_anterior,
        #                     {'$year': '$fecha'}
        #                 ]},
        #                 {'$eq': [
        #                     mes_anterior,
        #                     {'$month': '$fecha'}
        #                 ]},
        #                 {'$eq': [
        #                     dia_anterior,
        #                     {'$dayOfMonth': '$fecha'}
        #                 ]}
        #             ]
        #             match1.extend(condicion_anterior)
        #             cond_periodo.extend(condicion_anterior)
        #             match2.extend([
        #                 {'$eq': [
        #                     anio_elegido,
        #                     {'$year': '$fecha'}
        #                 ]},
        #                 {'$eq': [
        #                     mes_elegido,
        #                     {'$month': '$fecha'}
        #                 ]},
        #                 {'$eq': [
        #                     dia_elegido,
        #                     {'$dayOfMonth': '$fecha'}
        #                 ]}
        #             ])
        #             tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
        #             tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
        #         # Agregamos los facets al pipeline:
        #         print('Pipeline EjesMultiples -> Evaluación por KPI Pedido Perfecto: '+str(pipeline))
        #         # Ejecutamos el query:
        #         cursor = collection.aggregate(pipeline)
        #         arreglo = await cursor.to_list(length=1000)
        #         # print('Arreglo Evaluación por KPI Pedido Perfecto: '+str(arreglo))
        #         if len(arreglo) >= 2:
        #             hayResultados = "si"
        #             # Creamos los arreglos que alimentarán al gráfico:
        #             categories = ['Con Quejas', 'Retrasados', 'Cancelados', 'Incompletos', 'UpSells']
        #             arrEleg = arreglo[1]
        #             arrAnt = arreglo[0]
        #             if arrEleg == [] or arrAnt == []:
        #                 return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
        #             # print('Evaluación por KPI Pedido Perfecto:')
        #             # print(str('arrAnt = '+str(arrAnt)))
        #             # print(str('arrEleg = '+str(arrEleg)))
        #             arrAntUpSells = arrAnt['upSells'] if arrAnt['upSells'] != None else 0
        #             arrElegUpSells = arrEleg['upSells'] if arrEleg['upSells'] != None else 0
        #             if arrAnt['totales'] > 0:
        #                 serie1 = [
        #                     round((float(arrAnt['con_quejas'])/float(arrAnt['totales'])), 4), 
        #                     round((float(arrAnt['retrasados'])/float(arrAnt['totales'])), 4), 
        #                     round((float(arrAnt['cancelados'])/float(arrAnt['totales'])), 4), 
        #                     round((float(arrAnt['incompletos'])/float(arrAnt['totales'])), 4),
        #                     round((float(arrAntUpSells)/float(arrAnt['totales'])), 4)
        #                 ]
        #             else:
        #                 serie1 = [0,0,0,0,0]
        #             if arrEleg['totales'] > 0:
        #                 serie2 = [
        #                     round(float(arrEleg['con_quejas'])/float(arrEleg['totales']), 4), 
        #                     round(float(arrEleg['retrasados'])/float(arrEleg['totales']), 4), 
        #                     round(float(arrEleg['cancelados'])/float(arrEleg['totales']), 4), 
        #                     round(float(arrEleg['incompletos'])/float(arrEleg['totales']), 4),
        #                     round(float(arrElegUpSells)/float(arrEleg['totales']), 4)
        #                 ] if len(arrEleg) > 0 else []
        #             else:
        #                 serie2 = [0,0,0,0,0]
        #             if len(serie1) == len(serie2):
        #                 for i in range(len(serie1)):
        #                     serie3.append(round((serie2[i] - serie1[i]), 4))
        #             # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
        #             if self.filtros.agrupador == 'semana':
        #                 cursor_semana = conexion_mongo('report').catTiempo.find({
        #                     'idSemDS': semana_elegida_txt
        #                 })
        #                 arreglo_semana = await cursor_semana.to_list(length=1)
        #                 tituloElegida = arreglo_semana[0]['nSemDS']
        #                 cursor_semana = conexion_mongo('report').catTiempo.find({
        #                     'idSemDS': semana_anterior_txt
        #                 })
        #                 arreglo_semana = await cursor_semana.to_list(length=1)
        #                 tituloAnterior = arreglo_semana[0]['nSemDS']
        #             series = [
        #                 {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
        #                 {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'},
        #                 {'name': '% Dif', 'data':serie3, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'},
        #             ]
        #         else:
        #             hayResultados = "no"
        #             # print("No hay resultados 2")
        #     else:
        #         hayResultados = "no"
        #         # print("No hay resultados 1")

        if self.titulo == 'Evaluación por KPI':
            if self.filtros.periodo != {}:
                serie1 = []
                serie2 = []
                serie3 = []

                # pipeline.append(
                #     {'$match': {
                #         'fecha': {
                #             '$gte': self.fecha_ini_a12, 
                #             '$lt': self.fecha_fin_a12
                #         }
                #     }}
                # )
                # Vamos a crear 2 facets: uno para el periodo elegido y otro para el anterior. Creamos una plantilla para el facet:
                if clauseCatProveedor:
                    pipeline.append(clauseCatProveedor)
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                    {'$project': {
                        'itemsFound': '$itemsFound',
                        'itemsFin': '$itemsFin',
                        'itemsIni': '$itemsIni',
                        'periodo': {
                            '$cond': [
                                {'$and': []},
                                0,
                                1
                            ]
                        }
                    }},
                    {'$group': {
                        '_id': '$periodo',
                        'found': {
                            '$sum': '$itemsFound'
                        },
                        'fin': {
                            '$sum': '$itemsFin'
                        },
                        'ini': {
                            '$sum': '$itemsIni'
                        }
                    }},
                    {'$sort': {'_id': 1}}
                ])
                # Creamos variables para manipular los diccionarios:
                match1 = pipeline[-4]['$match']['$expr']['$or'][0]['$and']
                match2 = pipeline[-4]['$match']['$expr']['$or'][1]['$and']
                cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']
                
                # Modificamos los facets para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    if mes_elegido > 1:
                        mes_anterior = mes_elegido - 1
                        anio_anterior = anio_elegido
                    else:
                        mes_anterior = 12
                        anio_anterior = anio_elegido - 1
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]}
                    ])
                    tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Modificamos los facets para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
                    anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
                    if semana_elegida != 1:
                        semana_anterior = semana_elegida - 1
                        anio_anterior = anio_elegido
                    else:
                        anio_anterior = anio_elegido - 1
                        last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
                        semana_anterior = last_week.isocalendar()[1]
                    semana_elegida_txt = '0' + str(semana_elegida) if semana_elegida < 10 else str(semana_elegida)
                    semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
                    semana_elegida_txt = int(str(anio_elegido) + semana_elegida_txt)
                    semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
                    condicion_anterior = [
                        {'$eq': [
                            semana_elegida_txt,
                            '$idSemDS'
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            semana_anterior_txt,
                            '$idSemDS'
                        ]}
                    ])
                # Modificamos los facets para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    dia_elegido = self.filtros.periodo['dia']
                    if dia_elegido != 1:
                        dia_anterior = dia_elegido - 1
                        mes_anterior = mes_elegido
                        anio_anterior = anio_elegido
                    else:
                        if mes_elegido != 1:
                            mes_anterior = mes_elegido - 1
                            anio_anterior = anio_elegido
                        else:
                            mes_anterior = 12
                            anio_anterior = anio_elegido - 1
                        dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_elegido,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_anterior,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ])
                    tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # print(f"Pipeline desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                if len(arreglo) >= 2:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán al gráfico:
                    categories = ['Found Rate', 'Fulfillment Rate']
                    arrEleg = arreglo[0]
                    arrAnt = arreglo[1]
                    if arrEleg == [] or arrAnt == []:
                        return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
                    # print('Evaluación por KPI:')
                    # print(str('pipeline = '+str(pipeline)))
                    # print(str('arrAnt = '+str(arrAnt)))
                    # print(str('arrEleg = '+str(arrEleg)))
                    serie1 = [
                        round(float(arrAnt['found'])/float(arrAnt['ini']), 4), 
                        round(float(arrAnt['fin'])/float(arrAnt['ini']), 4), 
                    ] if 'ini' in arrAnt and arrAnt['ini'] is not None and arrAnt['ini'] != 0 else []
                    serie2 = [
                        round(float(arrEleg['found'])/float(arrEleg['ini']), 4), 
                        round(float(arrEleg['fin'])/float(arrEleg['ini']), 4), 
                    ] if 'ini' in arrEleg and arrEleg['ini'] is not None and arrEleg['ini'] != 0 else []
                    if len(serie1) == len(serie2):
                        for i in range(len(serie1)):
                            serie3.append(round((serie2[i] - serie1[i]), 4))
                    # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
                    if self.filtros.agrupador == 'semana':
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_elegida_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloElegida = arreglo_semana[0]['nSemDS']
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_anterior_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloAnterior = arreglo_semana[0]['nSemDS']
                    series = [
                        {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
                        {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'},
                        {'name': '% Dif', 'data':serie3, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'},
                    ]
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")
            else:
                hayResultados = "no"
                # print("No hay resultados 1")

        if self.titulo == 'Evaluación Pedido Perfecto por Lugar':
            if self.filtros.periodo != {}:
                # Desde el inicio de la clase puse el filtro por tienda, en su caso. Ahora el requerimiento es que solo para este gráfico el filtro llegue hasta zona, así que hay que hacer modificaciones:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
                    siguiente_lugar = 'tiendaNombre'
                    pipeline[1] = {'$match': {'sucursal.zona': lugar}}
                serie1 = []
                serie2 = []
                serie3 = []

                # pipeline.append(
                #     {'$match': {
                #         'fecha': {
                #             '$gte': self.fecha_ini_a12, 
                #             '$lt': self.fecha_fin_a12
                #         }
                #     }}
                # )
                # Vamos a crear 2 facets: uno para el periodo elegido y otro para el anterior. Creamos una plantilla para el facet:
                if clauseCatProveedor:
                    pipeline.append(clauseCatProveedor)
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                    {'$project': {
                        'perfecto': '$perfecto',
                        'Total_Pedidos': '$Total_Pedidos',
                        'lugar': '$sucursal.' + siguiente_lugar,
                        'periodo': {
                            '$cond': [
                                {'$and': []},
                                0,
                                1
                            ]
                        }
                    }},
                    {'$group': {
                        '_id': {
                            'lugar': '$lugar',
                            'periodo': '$periodo'
                        },
                        'perfecto': {
                            '$sum': '$perfecto'
                        },
                        'totales': {
                            '$sum': '$Total_Pedidos'
                        }
                    }},
                    {'$sort': {'_id.periodo': 1, '_id.lugar': 1}}
                ])
                # Creamos variables para manipular los diccionarios:
                match1 = pipeline[-4]['$match']['$expr']['$or'][0]['$and']
                match2 = pipeline[-4]['$match']['$expr']['$or'][1]['$and']
                cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']                
                
                # Modificamos los facets para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    if mes_elegido > 1:
                        mes_anterior = mes_elegido - 1
                        anio_anterior = anio_elegido
                    else:
                        mes_anterior = 12
                        anio_anterior = anio_elegido - 1
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]}
                    ])
                    tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Modificamos los facets para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
                    anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
                    if semana_elegida != 1:
                        semana_anterior = semana_elegida - 1
                        anio_anterior = anio_elegido
                    else:
                        anio_anterior = anio_elegido - 1
                        last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
                        semana_anterior = last_week.isocalendar()[1]
                    semana_elegida_txt = '0' + str(semana_elegida) if semana_elegida < 10 else str(semana_elegida)
                    semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
                    semana_elegida_txt = int(str(anio_elegido) + semana_elegida_txt)
                    semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
                    condicion_anterior = [
                        {'$eq': [
                            semana_elegida_txt,
                            '$idSemDS'
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            semana_anterior_txt,
                            '$idSemDS'
                        ]}
                    ])
                # Modificamos los facets para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    dia_elegido = self.filtros.periodo['dia']
                    if dia_elegido != 1:
                        dia_anterior = dia_elegido - 1
                        mes_anterior = mes_elegido
                        anio_anterior = anio_elegido
                    else:
                        if mes_elegido != 1:
                            mes_anterior = mes_elegido - 1
                            anio_anterior = anio_elegido
                        else:
                            mes_anterior = 12
                            anio_anterior = anio_elegido - 1
                        dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_elegido,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_anterior,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ])
                    tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # print(f"Pipeline desde Pedido Perfecto por Lugar en Ejes múltiples: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                if len(arreglo) >0:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán al gráfico:
                    arrAnt = [row for row in arreglo if row['_id']['periodo'] == 0]
                    arrEleg = [row for row in arreglo if row['_id']['periodo'] == 1]
                    if arrEleg == [] or arrAnt == []:
                        return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}                    
                    categories = []
                    # print("Arreglo en ejes multiples: "+str(arreglo))
                    # print("ArrEleg en ejes multiples: "+str(arrEleg))
                    for row in arrEleg:
                        # print('El dizque string: '+row['_id']['lugar'])
                        if 'lugar' in row['_id']:
                            categories.append(row['_id']['lugar'])
                            if row['totales'] > 0:
                                serie1.append(round((row['perfecto']/row['totales']), 4))
                            else:
                                serie1.append(0)
                    for row in arrAnt:
                        if 'lugar' in row['_id']:
                            if row['totales'] > 0:
                                serie2.append(round((row['perfecto']/row['totales']), 4))
                            else:
                                serie2.append(0)
                    # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
                    if self.filtros.agrupador == 'semana':
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_elegida_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloElegida = arreglo_semana[0]['nSemDS']
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_anterior_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloAnterior = arreglo_semana[0]['nSemDS']
                    series = [
                        {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
                        {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'}
                    ]
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")
            else:
                hayResultados = "no"
                # print("No hay resultados 1")

        if self.titulo == 'Motivos de Quejas':
            if self.filtros.periodo != {}:
                serie1 = []
                serie2 = []
                serie3 = []

                # pipeline.append(
                #     {'$match': {
                #         'fecha': {
                #             '$gte': self.fecha_ini_a12, 
                #             '$lt': self.fecha_fin_a12
                #         }
                #     }}
                # )
                # Vamos a crear 2 facets: uno para el periodo elegido y otro para el anterior. Creamos una plantilla para el facet:
                if clauseCatProveedor:
                    pipeline.append(clauseCatProveedor)
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                    {
                        '$unwind': '$quejas'
                    },
                    {'$project': {
                        'entregaFalso': '$quejas.entregaFalso',
                        'entregaIncompleta': '$quejas.entregaIncompleta',
                        'inconformidadProducto': '$quejas.inconformidadProducto',
                        'pedidoRetrasado': '$quejas.pedidoRetrasado',
                        'periodo': {
                            '$cond': [
                                {'$and': []},
                                0,
                                1
                            ]
                        }
                    }},
                    {'$group': {
                        '_id': '$periodo',
                        'entregaFalso': {
                            '$sum': '$entregaFalso'
                        },
                        'entregaIncompleta': {
                            '$sum': '$entregaIncompleta'
                        },
                        'inconformidadProducto': {
                            '$sum': '$inconformidadProducto'
                        },
                        'pedidoRetrasado': {
                            '$sum': '$pedidoRetrasado'
                        }
                    }},
                    {'$sort': {'_id': 1}}
                ])
                # Creamos variables para manipular los diccionarios:
                match1 = pipeline[-5]['$match']['$expr']['$or'][0]['$and']
                match2 = pipeline[-5]['$match']['$expr']['$or'][1]['$and']
                cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']                
                
                # Modificamos los facets para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    if mes_elegido > 1:
                        mes_anterior = mes_elegido - 1
                        anio_anterior = anio_elegido
                    else:
                        mes_anterior = 12
                        anio_anterior = anio_elegido - 1
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]}
                    ])
                    tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Modificamos los facets para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana_elegida_txt = self.filtros.periodo['semana']
                    semana_elegida = int(str(semana_elegida_txt)[4:6])
                    anio_elegido = int(str(semana_elegida_txt)[0:4])
                    if semana_elegida != 1:
                        semana_anterior = semana_elegida - 1
                        anio_anterior = anio_elegido
                    else:
                        anio_anterior = anio_elegido - 1
                        last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
                        semana_anterior = last_week.isocalendar()[1]
                    semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
                    semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
                    condicion_anterior = [
                        {'$eq': [
                            semana_elegida_txt,
                            '$idSemDS'
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            semana_anterior_txt,
                            '$idSemDS'
                        ]}
                    ])
                # Modificamos los facets para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    dia_elegido = self.filtros.periodo['dia']
                    if dia_elegido != 1:
                        dia_anterior = dia_elegido - 1
                        mes_anterior = mes_elegido
                        anio_anterior = anio_elegido
                    else:
                        if mes_elegido != 1:
                            mes_anterior = mes_elegido - 1
                            anio_anterior = anio_elegido
                        else:
                            mes_anterior = 12
                            anio_anterior = anio_elegido - 1
                        dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_elegido,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_anterior,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ])
                    tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # print(f"Query desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                # print(f"Arreglo desde EjesMultiples-> Motivos de quejas: {str(arreglo)}, que tiene len = {str(len(arreglo))}")
                if len(arreglo) >= 2:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán al gráfico:
                    categories = ['Pedido Retrasado', 'Inconformidad de Producto', 'Entrega Incompleta', 'Entrega en Falso']
                    arrEleg = arreglo[0]
                    arrAnt = arreglo[1]
                    if arrEleg == [] or arrAnt == []:
                        return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
                    # print('Evaluación por KPI:')
                    # print(str('pipeline = '+str(pipeline)))
                    # print(str('arrAnt = '+str(arrAnt)))
                    # print(str('arrEleg = '+str(arrEleg)))
                    serie1 = [
                        arrAnt['pedidoRetrasado'],
                        arrAnt['inconformidadProducto'], 
                        arrAnt['entregaIncompleta'], 
                        arrAnt['entregaFalso']
                    ]
                    serie2 = [
                        arrEleg['pedidoRetrasado'],
                        arrEleg['inconformidadProducto'], 
                        arrEleg['entregaIncompleta'], 
                        arrEleg['entregaFalso']
                    ]
                    # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
                    if self.filtros.agrupador == 'semana':
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_elegida_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloElegida = arreglo_semana[0]['nSemDS']
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_anterior_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloAnterior = arreglo_semana[0]['nSemDS']
                    series = [
                        {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'entero', 'color':'secondary'},
                        {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'entero', 'color':'primary'}
                    ]
                    # print (f"Pipeline de Motivos de Quejas en PedidoPerfecto: {str(pipeline)}")
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")
            else:
                hayResultados = "no"
                # print("No hay resultados 1")
        # print(f"Se va a devolver desde EjesMultiples -> PedidoPerfecto -> {self.titulo}: {str({'hayResultados':hayResultados,'categories':str(categories), 'series':str(series), 'pipeline': str(pipeline), 'lenArreglo':str(len(arreglo))})}")
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def OnTimeInFull(self):
        # print("Entró a Ejes Múltiples")
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idtienda'
                    lugar = int(self.filtros.tienda)
                    siguiente_lugar = 'tiendaNombre'
                    lugar_sql = f"AND ct.tienda = {self.filtros.tienda}"
                else:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
                    siguiente_lugar = 'tiendaNombre'
                    lugar_sql = f"AND ct.zona = {self.filtros.zona}"
            else:
                nivel = 'region'
                lugar = int(self.filtros.region)
                siguiente_lugar = 'zonaNombre'
                lugar_sql = f"AND ct.region = {self.filtros.region}"
        else:
            filtro_lugar = False
            lugar = ''
            siguiente_lugar = 'regionNombre'
            lugar_sql = ''

        pipeline = [{'$unwind': '$sucursal'}]
        if filtro_lugar:
            pipeline.extend([
                {'$match': {'sucursal.'+ nivel: lugar}}
            ])
        collection = conexion_mongo('report').report_pedidoPerfecto

        if self.titulo == 'Entrega a Tiempo vs. Fuera de Tiempo':
            if self.filtros.periodo != {}:
                series = []
                arreglo = []
                serie1 = []
                serie2 = []
                serie3 = []
                serie4 = []

                cnxn = conexion_sql('DWH')
                if self.filtros.agrupador == 'semana':
                    periodoNum = 'idSemDS'
                    periodoTxt = 'dt.nSemDS'
                if self.filtros.agrupador == 'mes':
                    periodoNum = 'num_mes'
                    periodoTxt = "CONCAT(dt.abrev_mes, ' ', anio)"
                if self.filtros.agrupador == 'dia':
                    periodoNum = 'id_fecha'
                    periodoTxt = "dt.descrip_fecha"
                print
                pipeline = f"""
                    select dt.{periodoNum} periodoNum, {periodoTxt} periodoTxt,
                    sum (case when ho.evaluacion = 'Despachado-Fuera de tiempo' then 1 else 0 end) Pickeado_Fuera_de_Tiempo,
                    sum (case when ho.evaluacion = 'Despachado-A tiempo' then 1 else 0 end) Pickeado_A_Tiempo,
                    sum (case when ho.evaluacion = 'Entregado-Fuera de tiempo' then 1 else 0 end) Entregado_Fuera_de_Tiempo,
                    sum (case when ho.evaluacion = 'Entregado-A tiempo' then 1 else 0 end) Entregado_A_Tiempo
                    from DWH.dbo.hecho_order ho
                    LEFT JOIN DWH.dbo.dim_tiempo dt on dt.fecha = CONVERT(date, creation_date)
                    LEFT JOIN DWH.artus.catTienda ct on ct.tienda=ho.store_num
                    WHERE dt.fecha BETWEEN '{self.filtros.fechas['fecha_ini'][:10]}' AND '{self.filtros.fechas['fecha_fin'][:10]}'
                    {lugar_sql}
                    GROUP BY dt.{periodoNum}, {periodoTxt}
                    ORDER BY min(dt.fecha)
                    """
                print('EjesMultiples -> OTIF -> Evaluación: '+pipeline)
                cursor = cnxn.cursor().execute(pipeline)
                arreglo = crear_diccionario(cursor)
                if len(arreglo) >0:
                    hayResultados = "si"
                    for registro in arreglo:
                        categories.append(registro['periodoTxt'])
                        Entregado_A_Tiempo = float(registro['Entregado_A_Tiempo'])
                        Entregado_Fuera_de_Tiempo = float(registro['Entregado_Fuera_de_Tiempo'])
                        Totales = Entregado_A_Tiempo + Entregado_Fuera_de_Tiempo
                        if Totales == 0:
                            hayResultados = 'no'
                        else:
                            serie1.append(Entregado_A_Tiempo / Totales)
                            serie2.append(Entregado_Fuera_de_Tiempo / Totales)
                    series = [
                        {'name': 'Entregado a Tiempo', 'data':serie1, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'success'},
                        {'name': 'Entregado Fuera de Tiempo', 'data':serie2, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'danger'}
                    ]
                else:
                    hayResultados = "no"
            else:
                hayResultados = "no"
                # print("No hay resultados 2")

        if self.titulo == 'Proceso con Retraso':
            if self.filtros.periodo != {}:
                series = []
                arreglo = []
                serie1 = []
                serie2 = []
                serie3 = []
                serie4 = []

                cnxn = conexion_sql('DWH')
                if self.filtros.agrupador == 'semana':
                    periodoNum = 'idSemDS'
                    periodoTxt = 'dt.nSemDS'
                    # # print(f"Filtro periodo desde EjesMultiples -> OTIF -> Evaluación: {self.filtros.periodo}")
                    # # print(f"self.filtros.periodo: {self.filtros.periodo}")
                    # sem2 = str(self.filtros.periodo['semana'])
                    # query = f"""
                    #     select idSemDS from DWH.dbo.dim_tiempo where fecha = (
                    #         select DATEADD(DAY, -7, (select CONVERT(varchar,(min(fecha))) from DWH.dbo.dim_tiempo where idSemDS = {sem2}))
                    #     )
                    # """
                    # cursor = cnxn.cursor().execute(query)
                    # arreglo = crear_diccionario(cursor)
                    # sem1 = arreglo[0]['idSemDS']
                    # where = f"dt.idSemDS in ('{sem1}', '{sem2}')"
                if self.filtros.agrupador == 'mes':
                    periodoNum = 'num_mes'
                    periodoTxt = "CONCAT(dt.abrev_mes, ' ', anio)"
                    # mesNum = int(self.filtros.periodo['mes'])
                    # mesTxt = '%02d' % (mesNum)
                    # anio = int(self.filtros.periodo['anio'])
                    # diasEnMes_fin = monthrange(anio, mesNum)[1]
                    # fecha_fin_txt = f"{str(anio)}-{mesTxt}-{diasEnMes_fin}"
                    # year, month, day = map(int, fecha_fin_txt.split('-'))
                    # if month > 1:
                    #     month -= 1
                    # else:
                    #     month = 12
                    #     year -= 1
                    # fecha_ini_txt = '%04d-%02d-01' % (year, month)
                    # where = f"dt.fecha BETWEEN '{fecha_ini_txt}' and '{fecha_fin_txt}'"
                if self.filtros.agrupador == 'dia':
                    periodoNum = 'id_fecha'
                    periodoTxt = "dt.descrip_fecha"
                    # day = int(self.filtros.periodo['dia'])
                    # month = int(self.filtros.periodo['mes'])
                    # year = int(self.filtros.periodo['anio'])
                    # fecha_fin_txt = '%04d-%02d-%02d' % (year, month, day)
                    # if day == 1 and month == 1:
                    #     fecha_ini_txt = str(year - 1) + "-12-31"
                    # elif day == 1:
                    #     fecha_ini_txt = str(year) + "-" + str(month - 1).zfill(2) + "-31"
                    # else:
                    #     fecha_ini_txt = str(year) + "-" + str(month).zfill(2) + "-" + str(day - 1).zfill(2)
                    # where = f"dt.fecha BETWEEN '{fecha_ini_txt}' and '{fecha_fin_txt}'"
                pipeline = f"""
                    select dt.{periodoNum} periodoNum, {periodoTxt} periodoTxt,
                    sum (case when ho.fin_picking > ho.timeslot_from then 1 else 0 end) Pickeado_Fuera_de_Tiempo,
                    sum (case when ho.fin_picking < ho.timeslot_from  and ho.fin_entrega > ho.timeslot_to then 1 else 0 end) Entregado_Fuera_de_Tiempo
                    from DWH.dbo.hecho_order ho
                    LEFT JOIN DWH.dbo.dim_tiempo dt on dt.fecha = CONVERT(date, creation_date)
                    LEFT JOIN DWH.artus.catTienda ct on ct.tienda=ho.store_num
                    left join DWH.dbo.dim_estatus de on de.id_estatus = ho.id_estatus
                    WHERE dt.fecha BETWEEN '{self.filtros.fechas['fecha_ini'][:10]}' AND '{self.filtros.fechas['fecha_fin'][:10]}'
                    and de.descrip_delviery_mode = 'domicilio'
                    and ho.evaluacion = 'Entregado-Fuera de tiempo'
                    {lugar_sql}
                    GROUP BY dt.{periodoNum}, {periodoTxt}
                    ORDER BY min(dt.fecha)
                    """
                # print('EjesMultiples -> OTIF -> Razón de Retraso: '+pipeline)
                # hayResultados = 'no'
                cursor = cnxn.cursor().execute(pipeline)
                arreglo = crear_diccionario(cursor)
                if len(arreglo) >0:
                    hayResultados = "si"
                    for registro in arreglo:
                        categories.append(registro['periodoTxt'])
                        Pickeado_Fuera_de_Tiempo = float(registro['Pickeado_Fuera_de_Tiempo'])
                        Entregado_Fuera_de_Tiempo = float(registro['Entregado_Fuera_de_Tiempo'])
                        Totales = Pickeado_Fuera_de_Tiempo + Entregado_Fuera_de_Tiempo
                        if Totales == 0:
                            hayResultados = 'no'
                        else:
                            serie1.append(Pickeado_Fuera_de_Tiempo / Totales)
                            serie2.append(Entregado_Fuera_de_Tiempo / Totales)
                    series = [
                        {'name': 'Pickeado Fuera de Tiempo', 'data':serie1, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'primary'},
                        {'name': 'Entregado Fuera de Tiempo', 'data':serie2, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'}
                    ]
                else:
                    hayResultados = "no"
            else:
                hayResultados = "no"
                # print("No hay resultados 2")

        elif self.titulo == 'Pedidos A Tiempo y Completos':
            # print("Entró a Pedidos Perfectos en Ejes Múltiples")
            serie1 = []
            serie2 = []
            pipeline.append(
                {'$match': {
                    'fecha': {
                        '$gte': self.fecha_ini_a12, 
                        '$lt': self.fecha_fin_a12
                    }
                }}
            )
            pipeline.extend([
                {'$group': {
                    '_id': {},
                    'totales': {'$sum': '$Total_Pedidos'},
                    'retrasados': {'$sum': '$retrasados'},
                    'incompletos': {'$sum': '$incompletos'}
                }}, 
                {'$project': {
                    '_id': '$_id',
                    'totales': '$totales',
                    'retrasados': '$retrasados',
                    'incompletos': '$incompletos',
                    'otif': {'$subtract': ['$totales', {'$add': ['$retrasados', '$incompletos']}]}
                }}, 
                {'$sort': {'_id.anio': 1}}
            ])
            # print(str(pipeline))
            grupo = pipeline[-3]['$group']['_id']
            sort = pipeline[-1]['$sort']
            # print("Agrupador en Pedidos Perfectos en Ejes Múltiples = "+self.filtros.agrupador)
            if self.filtros.agrupador == 'mes' or self.filtros.agrupador == 'dia' :
                grupo['anio'] = {'$year': '$fecha'}
                grupo['mes'] = {'$month': '$fecha'}
                sort['_id.anio'] = 1
                sort['_id.mes'] = 1
                if self.filtros.agrupador == 'dia':
                    grupo['dia'] = {'$dayOfMonth': '$fecha'}
                    sort['_id.dia'] = 1
            elif self.filtros.agrupador == 'semana':
                grupo['semana'] = '$idSemDS'
                sort['_id.semana'] = 1
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print("Pipeline de OTIF en Ejes Múltiples: "+str(pipeline))
            if len(arreglo) >0:
                hayResultados = "si"
                # print("Arreglo de Pedidos Perfectos en Ejes Múltiples: "+str(arreglo))
                for i in range(len(arreglo)):
                    if self.filtros.agrupador == 'mes' or self.filtros.agrupador == 'dia':
                        anio = arreglo[i]['_id']['anio']
                        mes = arreglo[i]['_id']['mes']
                        category = mesTexto(mes) + ' ' + str(anio)
                        if self.filtros.agrupador == 'dia':
                            category = str(arreglo[i]['_id']['dia']) + ' ' + category
                    elif self.filtros.agrupador == 'semana':
                        if arreglo[i]['_id']['semana'] != None:
                            cursor_semana = conexion_mongo('report').catTiempo.find({
                                'idSemDS': arreglo[i]['_id']['semana']
                            })
                            arreglo_semana = await cursor_semana.to_list(length=1)
                            category = arreglo_semana[0]['nSemDS']
                        else:
                            category = 'Semana no encontrada'
                    categories.append(category)
                    if arreglo[i]['totales'] > 0:
                        serie1.append(round((arreglo[i]['otif'] / arreglo[i]['totales']), 4))
                    else:
                        serie1.append(0)
                    serie2.append(round((serie1[i]-serie1[i-1]), 4)) if i > 0 else serie2.append(0)
                    
                series.extend([
                    {'name': '% ATYC', 'data':serie1, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'secondary'},
                    {'name': '% Dif', 'data':serie2, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'dark'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Evaluación por KPI A Tiempo y Completo':
            if self.filtros.periodo != {}:
                serie1 = []
                serie2 = []
                serie3 = []

                # pipeline.append(
                #     {'$match': {
                #         'fecha': {
                #             '$gte': self.fecha_ini_a12, 
                #             '$lt': self.fecha_fin_a12
                #         }
                #     }}
                # )
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                    {'$project': {
                        'retrasados': '$retrasados',
                        'incompletos': '$incompletos',
                        'Total_Pedidos': '$Total_Pedidos',
                        'periodo': {
                            '$cond': [
                                {'$and': []},
                                0,
                                1
                            ]
                        }
                    }},
                    {'$group': {
                        '_id': '$periodo',
                        'retrasados': {
                            '$sum': '$retrasados'
                        },
                        'incompletos': {
                            '$sum': '$incompletos'
                        },
                        'totales': {
                            '$sum': '$Total_Pedidos'
                        }
                    }},
                    {'$sort': {'_id': 1}}
                ])
                # Lo copiamos en el otro facet:
                # pipe_facet_elegida = deepcopy(pipe_facet_anterior)
                # Creamos variables para manipular los diccionarios:
                # match_facet_anterior = pipe_facet_anterior[-2]['$match']['$expr']['$and']
                match1 = pipeline[-4]['$match']['$expr']['$or'][0]['$and']
                match2 = pipeline[-4]['$match']['$expr']['$or'][1]['$and']
                cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']
                
                # Modificamos los facets para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    if mes_elegido > 1:
                        mes_anterior = mes_elegido - 1
                        anio_anterior = anio_elegido
                    else:
                        mes_anterior = 12
                        anio_anterior = anio_elegido - 1
                    condicion_anterior = [
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]}
                    ])
                    tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Modificamos los facets para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
                    anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
                    if semana_elegida != 1:
                        semana_anterior = semana_elegida - 1
                        anio_anterior = anio_elegido
                    else:
                        anio_anterior = anio_elegido - 1
                        last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
                        semana_anterior = last_week.isocalendar()[1]
                    semana_elegida_txt = '0' + str(semana_elegida) if semana_elegida < 10 else str(semana_elegida)
                    semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
                    semana_elegida_txt = int(str(anio_elegido) + semana_elegida_txt)
                    semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
                    condicion_anterior = [
                        {'$eq': [
                            semana_anterior_txt,
                            '$idSemDS'
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            semana_elegida_txt,
                            '$idSemDS'
                        ]}
                    ])
                # Modificamos los facets para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    dia_elegido = self.filtros.periodo['dia']
                    if dia_elegido != 1:
                        dia_anterior = dia_elegido - 1
                        mes_anterior = mes_elegido
                        anio_anterior = anio_elegido
                    else:
                        if mes_elegido != 1:
                            mes_anterior = mes_elegido - 1
                            anio_anterior = anio_elegido
                        else:
                            mes_anterior = 12
                            anio_anterior = anio_elegido - 1
                        dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
                    condicion_anterior = [
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_anterior,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_elegido,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ])
                    tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Agregamos los facets al pipeline:
                # print('Pipeline Evaluación por KPI A Tiempo y Completo: '+str(pipeline))
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                # print('Arreglo Evaluación por KPI A Tiempo y Completo: '+str(arreglo))
                if len(arreglo) >1:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán al gráfico:
                    categories = ['Retrasados', 'Incompletos', 'UpSells']
                    arrEleg = arreglo[1]
                    arrAnt = arreglo[0]
                    if arrEleg == [] or arrAnt == []:
                        return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
                    # print('Evaluación por KPI A Tiempo y Completo:')
                    # print(str('arrAnt = '+str(arrAnt)))
                    # print(str('arrEleg = '+str(arrEleg)))
                    if len(arrAnt) > 0:
                        if arrAnt['totales'] > 0:
                            serie1 = [
                                round(float(arrAnt['retrasados'])/float(arrAnt['totales']), 4), 
                                round(float(arrAnt['incompletos'])/float(arrAnt['totales']), 4),
                            ]
                        else:
                            serie1 = [0,0]
                    else:
                        serie1 = []
                    if len(arrEleg) > 0:
                        if arrEleg['totales'] > 0:
                            serie2 = [
                                round(float(arrEleg['retrasados'])/float(arrEleg['totales']), 4), 
                                round(float(arrEleg['incompletos'])/float(arrEleg['totales']), 4),
                            ]
                        else:
                            serie2 = [0,0]
                    else:
                        serie2 = []
                    if len(serie1) == len(serie2):
                        for i in range(len(serie1)):
                            serie3.append(round((serie2[i] - serie1[i]), 4))
                    # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
                    if self.filtros.agrupador == 'semana':
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_elegida_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloElegida = arreglo_semana[0]['nSemDS']
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_anterior_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloAnterior = arreglo_semana[0]['nSemDS']
                    series = [
                        {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
                        {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'},
                        {'name': '% Dif', 'data':serie3, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'},
                    ]
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")
            else:
                hayResultados = "no"
                # print("No hay resultados 1")

        if self.titulo == 'Evaluación por KPI':
            if self.filtros.periodo != {}:
                serie1 = []
                serie2 = []
                serie3 = []

                # pipeline.append(
                #     {'$match': {
                #         'fecha': {
                #             '$gte': self.fecha_ini_a12, 
                #             '$lt': self.fecha_fin_a12
                #         }
                #     }}
                # )
                # Vamos a crear 2 facets: uno para el periodo elegido y otro para el anterior. Creamos una plantilla para el facet:
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                    {'$project': {
                        'itemsFound': '$itemsFound',
                        'itemsFin': '$itemsFin',
                        'itemsIni': '$itemsIni',
                        'periodo': {
                            '$cond': [
                                {'$and': []},
                                0,
                                1
                            ]
                        }
                    }},
                    {'$group': {
                        '_id': '$periodo',
                        'found': {
                            '$sum': '$itemsFound'
                        },
                        'fin': {
                            '$sum': '$itemsFin'
                        },
                        'ini': {
                            '$sum': '$itemsIni'
                        }
                    }},
                    {'$sort': {'_id': 1}}
                ])
                # Creamos variables para manipular los diccionarios:
                match1 = pipeline[-4]['$match']['$expr']['$or'][0]['$and']
                match2 = pipeline[-4]['$match']['$expr']['$or'][1]['$and']
                cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']
                
                # Modificamos los facets para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    if mes_elegido > 1:
                        mes_anterior = mes_elegido - 1
                        anio_anterior = anio_elegido
                    else:
                        mes_anterior = 12
                        anio_anterior = anio_elegido - 1
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]}
                    ])
                    tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Modificamos los facets para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
                    anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
                    if semana_elegida != 1:
                        semana_anterior = semana_elegida - 1
                        anio_anterior = anio_elegido
                    else:
                        anio_anterior = anio_elegido - 1
                        last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
                        semana_anterior = last_week.isocalendar()[1]
                    semana_elegida_txt = '0' + str(semana_elegida) if semana_elegida < 10 else str(semana_elegida)
                    semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
                    semana_elegida_txt = int(str(anio_elegido) + semana_elegida_txt)
                    semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
                    condicion_anterior = [
                        {'$eq': [
                            semana_elegida_txt,
                            '$idSemDS'
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            semana_anterior_txt,
                            '$idSemDS'
                        ]}
                    ])
                # Modificamos los facets para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    dia_elegido = self.filtros.periodo['dia']
                    if dia_elegido != 1:
                        dia_anterior = dia_elegido - 1
                        mes_anterior = mes_elegido
                        anio_anterior = anio_elegido
                    else:
                        if mes_elegido != 1:
                            mes_anterior = mes_elegido - 1
                            anio_anterior = anio_elegido
                        else:
                            mes_anterior = 12
                            anio_anterior = anio_elegido - 1
                        dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
                    condicion_anterior = [
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_elegido,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_anterior,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ])
                    tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Agregamos los facets al pipeline:
                # print(str(pipeline))
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                if len(arreglo) > 1:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán al gráfico:
                    categories = ['Found Rate', 'Fulfillment Rate']
                    arrEleg = arreglo[0]
                    arrAnt = arreglo[1]
                    if arrEleg == [] or arrAnt == []:
                        return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
                    # print('Evaluación por KPI:')
                    # print(str('pipeline = '+str(pipeline)))
                    # print(str('arrAnt = '+str(arrAnt)))
                    # print(str('arrEleg = '+str(arrEleg)))
                    serie1 = [
                        round(float(arrAnt['found'])/float(arrAnt['ini']), 4), 
                        round(float(arrAnt['fin'])/float(arrAnt['ini']), 4), 
                    ] if 'ini' in arrAnt and arrAnt['ini'] is not None and arrAnt['ini'] != 0 else []
                    serie2 = [
                        round(float(arrEleg['found'])/float(arrEleg['ini']), 4), 
                        round(float(arrEleg['fin'])/float(arrEleg['ini']), 4), 
                    ] if 'ini' in arrEleg and arrEleg['ini'] is not None and arrEleg['ini'] != 0 else []
                    if len(serie1) == len(serie2):
                        for i in range(len(serie1)):
                            serie3.append(round((serie2[i] - serie1[i]), 4))
                    # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
                    if self.filtros.agrupador == 'semana':
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_elegida_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloElegida = arreglo_semana[0]['nSemDS']
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_anterior_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloAnterior = arreglo_semana[0]['nSemDS']
                    series = [
                        {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
                        {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'},
                        {'name': '% Dif', 'data':serie3, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'dark'},
                    ]
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")
            else:
                hayResultados = "no"
                # print("No hay resultados 1")

        if self.titulo == 'Evaluación A Tiempo y Completo por Lugar':
            if self.filtros.periodo != {}:
                # Desde el inicio de la clase puse el filtro por tienda, en su caso. Ahora el requerimiento es que solo para este gráfico el filtro llegue hasta zona, así que hay que hacer modificaciones:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
                    siguiente_lugar = 'tiendaNombre'
                    pipeline[1] = {'$match': {'sucursal.zona': lugar}}
                serie1 = []
                serie2 = []
                serie3 = []

                # pipeline.append(
                #     {'$match': {
                #         'fecha': {
                #             '$gte': self.fecha_ini_a12, 
                #             '$lt': self.fecha_fin_a12
                #         }
                #     }}
                # )
                # Vamos a crear 2 facets: uno para el periodo elegido y otro para el anterior. Creamos una plantilla para el facet:
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                    {'$project': {
                        'retrasados': '$retrasados',
                        'incompletos': '$incompletos',
                        'Total_Pedidos': '$Total_Pedidos',
                        'otif': {'$subtract': ['$Total_Pedidos', {'$add': ['$retrasados', '$incompletos']}]},
                        'lugar': '$sucursal.' + siguiente_lugar,
                        'periodo': {
                            '$cond': [
                                {'$and': []},
                                0,
                                1
                            ]
                        }
                    }},
                    {'$group': {
                        '_id': {
                            'lugar': '$lugar',
                            'periodo': '$periodo'
                        },
                        'otif': {
                            '$sum': '$otif'
                        },
                        'totales': {
                            '$sum': '$Total_Pedidos'
                        }
                    }},
                    {'$sort': {'_id.periodo': 1, '_id.lugar': 1}}
                ])
                # Creamos variables para manipular los diccionarios:
                match1 = pipeline[-4]['$match']['$expr']['$or'][0]['$and']
                match2 = pipeline[-4]['$match']['$expr']['$or'][1]['$and']
                cond_periodo = pipeline[-3]['$project']['periodo']['$cond'][0]['$and']                
                
                # Modificamos los facets para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    if mes_elegido > 1:
                        mes_anterior = mes_elegido - 1
                        anio_anterior = anio_elegido
                    else:
                        mes_anterior = 12
                        anio_anterior = anio_elegido - 1
                    condicion_anterior = [
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]}
                    ])
                    tituloElegida = mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # Modificamos los facets para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana_elegida = int(str(self.filtros.periodo['semana'])[4:6])
                    anio_elegido = int(str(self.filtros.periodo['semana'])[0:4])
                    if semana_elegida != 1:
                        semana_anterior = semana_elegida - 1
                        anio_anterior = anio_elegido
                    else:
                        anio_anterior = anio_elegido - 1
                        last_week = date(anio_anterior, 12, 28) # La lógica de esto está aquí: https://stackoverflow.com/questions/29262859/the-number-of-calendar-weeks-in-a-year
                        semana_anterior = last_week.isocalendar()[1]
                    semana_elegida_txt = '0' + str(semana_elegida) if semana_elegida < 10 else str(semana_elegida)
                    semana_anterior_txt = '0' + str(semana_anterior) if semana_anterior < 10 else str(semana_anterior)
                    semana_elegida_txt = int(str(anio_elegido) + semana_elegida_txt)
                    semana_anterior_txt = int(str(anio_anterior) + semana_anterior_txt)
                    condicion_anterior = [
                        {'$eq': [
                            semana_elegida_txt,
                            '$idSemDS'
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            semana_anterior_txt,
                            '$idSemDS'
                        ]}
                    ])
                # Modificamos los facets para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio_elegido = self.filtros.periodo['anio']
                    mes_elegido = self.filtros.periodo['mes']
                    dia_elegido = self.filtros.periodo['dia']
                    if dia_elegido != 1:
                        dia_anterior = dia_elegido - 1
                        mes_anterior = mes_elegido
                        anio_anterior = anio_elegido
                    else:
                        if mes_elegido != 1:
                            mes_anterior = mes_elegido - 1
                            anio_anterior = anio_elegido
                        else:
                            mes_anterior = 12
                            anio_anterior = anio_elegido - 1
                        dia_anterior = monthrange(anio_anterior, mes_anterior)[1] # La lógica de esto está aquí: https://stackoverflow.com/questions/42950/how-to-get-the-last-day-of-the-month
                    condicion_anterior = [
                        {'$eq': [
                            anio_anterior,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_anterior,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_anterior,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ]
                    match1.extend(condicion_anterior)
                    cond_periodo.extend(condicion_anterior)
                    match2.extend([
                        {'$eq': [
                            anio_elegido,
                            {'$year': '$fecha'}
                        ]},
                        {'$eq': [
                            mes_elegido,
                            {'$month': '$fecha'}
                        ]},
                        {'$eq': [
                            dia_elegido,
                            {'$dayOfMonth': '$fecha'}
                        ]}
                    ])
                    tituloElegida = str(dia_elegido) + ' ' + mesTexto(mes_elegido) + ' ' + str(anio_elegido)
                    tituloAnterior = str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
                # print(f"Pipeline desde A Tiempo y Completo por Lugar en Ejes múltiples: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=1000)
                if len(arreglo) >0:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán al gráfico:
                    arrAnt = [row for row in arreglo if row['_id']['periodo'] == 0]
                    arrEleg = [row for row in arreglo if row['_id']['periodo'] == 1]
                    if arrEleg == [] or arrAnt == []:
                        return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}                    
                    categories = []
                    # print("Arreglo en ejes multiples: "+str(arreglo))
                    # print("ArrEleg en ejes multiples: "+str(arrEleg))
                    for row in arrEleg:
                        # print('El dizque string: '+row['_id']['lugar'])
                        if 'lugar' in row['_id']:
                            categories.append(row['_id']['lugar'])
                            if row['totales'] is not None and row['totales'] != 0:
                                serie1.append(round((row['otif']/row['totales']), 4))
                            else:
                                serie1.append(0)
                    for row in arrAnt:
                        if 'lugar' in row['_id']:
                            if row['totales'] is not None and row['totales'] != 0:
                                serie2.append(round((row['otif']/row['totales']), 4))
                            else:
                                serie2.append(0)
                    # Obtener los títulos de las series cuando el agrupador sea por semana. Los sacamos de catTiempo por alguna razón
                    if self.filtros.agrupador == 'semana':
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_elegida_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloElegida = arreglo_semana[0]['nSemDS']
                        cursor_semana = conexion_mongo('report').catTiempo.find({
                            'idSemDS': semana_anterior_txt
                        })
                        arreglo_semana = await cursor_semana.to_list(length=1)
                        tituloAnterior = arreglo_semana[0]['nSemDS']
                    series = [
                        {'name': tituloAnterior, 'data':serie1, 'type': 'column','formato_tooltip':'porcentaje', 'color':'secondary'},
                        {'name': tituloElegida, 'data':serie2, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'primary'}
                    ]
                else:
                    hayResultados = "no"
                    # print("No hay resultados 2")
            else:
                hayResultados = "no"
                # print("No hay resultados 1")
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def FoundRateCornershop(self):
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                siguiente_nivel = 'tiendaNombre'
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'tienda'
                    lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                lugar = int(self.filtros.region)
                siguiente_nivel = 'zonaNombre'
        else:
            filtro_lugar = False
            lugar = ''
            siguiente_nivel = 'regionNombre'

        collection = conexion_mongo('report').report_skuConershopChedrauiDetalle
        pipeline = [
            {'$unwind': '$sucursal'},
            {'$unwind': '$articulo'}
        ]
        if filtro_lugar:
            pipeline.append({
                '$match': {
                    'sucursal.'+ nivel: lugar
                }
            })
        pipeline.append({
            '$match': {
                'fecha': {
                    '$gte': self.fecha_ini_a12, 
                    '$lt': self.fecha_fin_a12
                }
            }
        })

        if self.titulo == 'Found Rate Cornershop Vs. Chedraui':
            serie1 = []
            serie2 = []
            serie3 = []

            pipeline.append({
                '$group':{
                    '_id': {
                        'canal': '$canal'
                    }, 
                    'itemOri': {
                        '$sum': '$itemOri'
                    }, 
                    'itemFin': {
                        '$sum': '$itemFin'
                    }
                }
            })
            pipeline.append({
                '$project':{
                    'canal':'$_id.canal',
                    'foundRate': {'$divide': ['$itemFin', '$itemOri']}
                }
            })
            pipeline.append({'$sort':{'canal': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                categories = ['']
                foundrateCornershop = arreglo[1]['foundRate'] if len(arreglo) > 1 else 0
                serie1.append(round(arreglo[0]['foundRate'], 4))
                serie2.append(round(foundrateCornershop, 4))
                series.extend([
                    {
                        'name': 'Chedraui', 
                        'data':serie1, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'primary'
                    },
                    {
                        'name': 'Cornershop', 
                        'data':serie2, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'danger'
                    }
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Found Rate Cornershop Vs. Chedraui Por Lugar':
            serie1 = []
            serie2 = []
            serie3 = []

            pipeline.append({
                '$group':{
                    '_id': {
                        'canal': '$canal',
                        'lugar': '$sucursal.' + siguiente_nivel
                    }, 
                    'itemOri': {
                        '$sum': '$itemOri'
                    }, 
                    'itemFin': {
                        '$sum': '$itemFin'
                    }
                }
            })
            pipeline.extend([
                {'$project':{
                    'lugar':'$_id.lugar',
                    'canal':'$_id.canal',
                    'foundRate': {'$divide': ['$itemFin', '$itemOri']}
                }},
                {'$sort': {'lugar': 1}}
            ])
            pipeline.append({'$sort':{'canal': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    if row['lugar'] not in categories:
                        categories.append(row['lugar'])
                    if row['canal'] == 'Chedraui':
                        serie1.append(round((row['foundRate']), 4))
                    elif row['canal'] == 'Cornershop':
                        serie2.append(round((row['foundRate']), 4))
                series.extend([
                    {
                        'name': 'Chedraui', 
                        'data':serie1, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'primary'
                    },
                    {
                        'name': 'Cornershop', 
                        'data':serie2, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'danger'
                    }
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Found Rate Cornershop Vs. Chedraui Por Día':
            serie1 = []
            serie2 = []
            serie3 = []

            pipeline.extend([
                {'$project':{
                    'fecha': '$fecha',
                    'itemOriChedraui': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Chedraui'
                            ]},
                            '$itemOri',
                            0
                        ]
                    },
                    'itemFinChedraui': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Chedraui'
                            ]},
                            '$itemFin',
                            0
                        ]
                    },
                    'itemOriCornershop': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Cornershop'
                            ]},
                            '$itemOri',
                            0
                        ]
                    },
                    'itemFinCornershop': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Cornershop'
                            ]},
                            '$itemFin',
                            0
                        ]
                    }
                }},
                {'$group':{
                    '_id': {
                        'dia': {'$dayOfMonth': '$fecha'},
                        'mes': {'$month': '$fecha'},
                        'anio': {'$year': '$fecha'}
                    }, 
                    'itemOriChedraui': {'$sum': '$itemOriChedraui'},
                    'itemFinChedraui': {'$sum': '$itemFinChedraui'},
                    'itemOriCornershop': {'$sum': '$itemOriCornershop'},
                    'itemFinCornershop': {'$sum': '$itemFinCornershop'},
                }},
                {'$project': {
                    'dia': '$_id.dia',
                    'mes': '$_id.mes',
                    'anio': '$_id.anio',
                    'frChedraui': {
                        '$cond': [
                            {'$eq': ['$itemOriChedraui', 0]},
                            0,
                            {'$divide': ['$itemFinChedraui', '$itemOriChedraui']}
                        ]
                    },
                    'frCornershop': {
                        '$cond': [
                            {'$eq': ['$itemOriCornershop', 0]},
                            0,
                            {'$divide': ['$itemFinCornershop', '$itemOriCornershop']}
                        ]
                    }
                }},
                {'$sort': {
                    'anio': 1,
                    'mes': 1,
                    'dia': 1
                }}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categories.append(str(row['dia'])+' '+mesTexto(row['mes'])+' '+str(row['anio']))
                    serie1.append(round((row['frChedraui']), 4))
                    serie2.append(round((row['frCornershop']), 4))
                series.extend([
                    {
                        'name': 'Chedraui', 
                        'data':serie1, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'primary'
                    },
                    {
                        'name': 'Cornershop', 
                        'data':serie2, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'danger'
                    }
                ])
            else:
                hayResultados = "no"
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def Nps(self):
        categories = []
        series = []
        pipeline = []
        arreglo = []
        fecha_ini = self.filtros.fechas['fecha_ini'][0:10]
        fecha_fin = self.filtros.fechas['fecha_fin'][0:10]
        fecha_ini_datetime = fecha_ini + ' 00:00:00'
        fecha_fin_datetime = fecha_fin + ' 23:59:59'
        clauseCatProveedor = ""
        if len(self.filtros.provLogist) > 0:
            clauseCatProveedor = " AND ("
            contador = 0
            for prov in self.filtros.provLogist:
                if prov == 'Recursos Propios':
                    clauseCatProveedor += f" ho.tercero IS NULL "
                else:
                    clauseCatProveedor += f" ho.tercero = '{prov}' "
                if contador < len(self.filtros.provLogist) - 1:
                    clauseCatProveedor += f" OR "
                else:
                    clauseCatProveedor += f") "
                contador += 1
        clauseCatProveedor_tmp = " AND cp.proveedor is not null "
        if len(self.filtros.provLogist) > 0:
            clauseCatProveedor_tmp = " AND ("
            contador = 0
            for prov in self.filtros.provLogist:
                clauseCatProveedor_tmp += f" cp.proveedor = '{prov}' "
                if contador < len(self.filtros.provLogist) - 1:
                    clauseCatProveedor_tmp += f" OR "
                else:
                    clauseCatProveedor_tmp += f") "
                contador += 1
        clauseCatProveedor_tmp += f" AND ((cp.fecha_from = '2022-11-23' AND (cp.fecha_to is null OR cp.fecha_to <= '{fecha_fin}') OR (cp.fecha_from <= '{fecha_fin}' AND cp.fecha_to is null)))"
        hayResultados = 'no'
        # print(f"Desde {titulo}, periodo = {self.filtros.periodo}")
        if self.filtros.agrupador == 'dia':
            mes = int(self.filtros.periodo['mes'])
            mes = str(mes) if mes >= 10 else '0'+str(mes)
            dia = int(self.filtros.periodo['dia'])
            dia = str(dia) if dia >= 10 else '0'+str(dia)
            agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
        elif self.filtros.agrupador == "semana":
            semana_completa = str(self.filtros.periodo['semana'])
            num_semana = int(semana_completa[4:])
            anio = int(semana_completa[0:4])
            semana_query = anio*100+num_semana
            agrupador_where = f" dt.idSemDS={semana_query}"
        elif self.filtros.agrupador == "mes":
            agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"

        if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
            lugar_where = f""" and ct.tienda ='{self.filtros.tienda}' """
            lugar = f"tiendaNombre"
            lugar_select = f" ct.tienda, ct.tiendaNombre"
        elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
            lugar_where = f" and ct.zona='{self.filtros.zona}' "
            lugar = f"tiendaNombre"
            lugar_select = f"ct.tienda, ct.tiendaNombre"
        elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
            lugar_where = f" and ct.region ='{self.filtros.region}' "
            lugar = f"zonaNombre"
            lugar_select = f"ct.zona, ct.zonaNombre"
        else:
            lugar_where = f""
            lugar = f"regionNombre"
            lugar_select = f"ct.region, ct.regionNombre"

        if self.titulo == 'NPS por Periodo':
            serie1 = []
            serie2 = []
            if self.filtros.agrupador == 'dia':
                rango = "fecha"
            elif self.filtros.agrupador == "semana":
                rango = "n_sem_D_S"
            elif self.filtros.agrupador == "mes":
                rango = "abrev_mes"
            else:
                rango = "anio"
            pipeline = f"""select dt.{rango} as descrip_fecha,
                case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
                (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps,
            CONVERT(VARCHAR, MIN(dt.fecha), 20) as f_inicio_drilldown,
            CONVERT(VARCHAR, MAX(dt.fecha), 120) as f_fin_drilldown
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date) =dt.fecha
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            where ho.creation_date between '{fecha_ini_datetime}' and '{fecha_fin_datetime}' """
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                pipeline += f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                pipeline += f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                pipeline += f" and ct.region ='{self.filtros.region}' "
            pipeline += clauseCatProveedor
            pipeline += f" group by dt.{rango} order by f_inicio_drilldown"

            cnxn = conexion_sql('DWH')
            # print('NPS por Periodo desde EjesMultiples: '+pipeline)
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categories.append(arreglo[i]['descrip_fecha'])
                    nps_actual = float(arreglo[i]['nps']) / 100
                    serie1.append(round((nps_actual), 4))
                    if i==0:
                        serie2.append(0)
                    else:
                        nps_anterior = float(arreglo[i-1]['nps']) / 100
                        serie2.append(round((nps_actual - nps_anterior), 4))

                series = [
                    {
                        'name': 'NPS',
                        'data':serie1, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'primary'
                    }, {
                        'name': '% Dif',
                        'data':serie2, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'NPS por lugar':
            pipeline = f"""select {lugar_select}, case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps,
            sum(case when nd.calificacion in (9,10) then 1 else 0 end) promotores,
            sum(case when nd.calificacion<=6 then 1 else 0 end) detractores,
            sum(case when nd.calificacion in (7,8) then 1 else 0 end) pasivos
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date) = dt.fecha 
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            where {agrupador_where} {lugar_where} {clauseCatProveedor}
            group by {lugar_select}"""
            # print("query desde ejes multiples nps: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                promotores = []
                detractores = []
                pasivos = []
                for row in arreglo:
                    categories.append(row[lugar])
                    promotores_row = float(row['promotores'])
                    detractores_row = float(row['detractores'])
                    pasivos_row = float(row['pasivos'])
                    total = promotores_row + detractores_row + pasivos_row
                    promotores.append(round((promotores_row / total), 4))
                    detractores.append(round((detractores_row / total), 4))
                    pasivos.append(round((pasivos_row / total), 4))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores',
                        'data': detractores, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'danger'
                    },
                    {
                        'name': 'Pasivos',
                        'data': pasivos, 
                        'type': 'column',
                        'formato_tooltip':'porcentaje', 
                        'color':'warning'
                    },
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Percepción del servicio (n)':
            pipeline = f"""select min(ncp.id) id,ncp.descripcion, 
            sum(case when flujo='F1' then a.cant else 0 end) F1,
            sum(case when flujo='F2' then a.cant else 0 end) F2
            from DWH.limesurvey.nps_cat_preguntas ncp
            left join
            (
            select  id_pregunta,sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where {agrupador_where} {lugar_where} {clauseCatProveedor_tmp}
            group by id_pregunta
            ) a on ncp.id_pregunta =a.id_pregunta
            where ncp.tipo_respuesta ='R1'
            group by ncp.descripcion
            order by min(ncp.id)
                """
            # print("query ejesmultiples -> percepción del servicio (n): "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0 and arreglo[0]['F2'] is not None:
                hayResultados = "si"
                promotores = []
                detractoresYPasivos = []
                for row in arreglo:
                    categories.append(row['descripcion'])
                    promotores.append((row['F2']))
                    detractoresYPasivos.append((row['F1']))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores y Pasivos',
                        'data': detractoresYPasivos, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Percepción del servicio (%)':
            pipeline = f"""select min(ncp.id) id,ncp.descripcion,
            sum(case when flujo='F1' then a.cant else 0 end)*100/cast((select sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            where ncp.tipo_respuesta ='R1' and ncp.flujo = 'F1'
            and {agrupador_where} 
            {lugar_where} {clauseCatProveedor_tmp}
            ) as float) F1,
            sum(case when flujo='F2' then a.cant else 0 end)*100/cast((select sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where ncp.tipo_respuesta ='R1' and ncp.flujo = 'F2'
            and {agrupador_where}
            {lugar_where} {clauseCatProveedor_tmp}
            ) as float) F2
            from DWH.limesurvey.nps_cat_preguntas ncp
            left join
            (
            select id_pregunta,sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where {agrupador_where} 
            {lugar_where} {clauseCatProveedor_tmp}
            group by id_pregunta
            ) a on ncp.id_pregunta =a.id_pregunta
            where ncp.tipo_respuesta ='R1'
            group by ncp.descripcion
            order by min(ncp.id) 
            """

            # print("query ejesmultiples -> percepción del servicio (%): "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0 and arreglo[0]['F2'] is not None:
                hayResultados = "si"
                promotores = []
                detractoresYPasivos = []
                for row in arreglo:
                    categories.append(row['descripcion'])
                    promotores.append(round((float(row['F2'])/100), 4))
                    detractoresYPasivos.append(round((float(row['F1'])/100), 4))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores y Pasivos',
                        'data': detractoresYPasivos, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'danger'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Percepción del servicio (n) $categoria':
            pipeline = f"""select max(ncp.id) id,ncp.descripcion,
            isnull(sum(case when flujo='F1' then a.cant else 0 end),0) F1,
            isnull(sum(case when flujo='F2' then a.cant else 0 end),0) F2
            from DWH.limesurvey.nps_cat_preguntas ncp
            left join
            (
            select id_pregunta,sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where {agrupador_where} {lugar_where} {clauseCatProveedor_tmp}
            group by id_pregunta
            ) a on ncp.id_pregunta =a.id_pregunta
            where ncp.tipo_respuesta ='R2'
            and ncp.orden in (select orden
            from DWH.limesurvey.nps_cat_preguntas ncp
            where descripcion = '{self.filtros.nps}' and tipo_respuesta = 'R1'
            )
            group by ncp.descripcion
            order by min(ncp.id)
                """
            # print("Percepción del servicio (n) $categoria: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0 and arreglo[0]['F2'] is not None:
                hayResultados = "si"
                promotores = []
                detractoresYPasivos = []
                for row in arreglo:
                    categories.append(row['descripcion'])
                    promotores.append((row['F2']))
                    detractoresYPasivos.append((row['F1']))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores y Pasivos',
                        'data': detractoresYPasivos, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Percepción del servicio (%) $categoria':
            pipeline = f"""select max(ncp.id) id,ncp.descripcion,
            isnull(sum(case when flujo='F1' then a.cant else 0 end),0)*100/cast((select sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            where ncp.orden in (select orden
            from DWH.limesurvey.nps_cat_preguntas ncp
            where descripcion = '{self.filtros.nps}' and tipo_respuesta = 'R1' and flujo='F1'
            )
            and {agrupador_where} 
            {lugar_where} {clauseCatProveedor_tmp}
            and tipo_respuesta = 'R2' and flujo='F1') as float) F1,
            isnull(sum(case when flujo='F2' then a.cant else 0 end),0)*100/cast((select sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where ncp.orden in (select orden
            from DWH.limesurvey.nps_cat_preguntas ncp
            where descripcion = '{self.filtros.nps}' and tipo_respuesta = 'R1' and flujo='F2'
            )
            and {agrupador_where}
            {lugar_where} {clauseCatProveedor_tmp}
            and tipo_respuesta = 'R2' and flujo='F2') as float) F2
            from DWH.limesurvey.nps_cat_preguntas ncp
            left join
            (
            select id_pregunta,sum(cant) cant
            from DWH.limesurvey.nps_pregunta_respuesta npr
            left join DWH.dbo.dim_tiempo dt on npr.fecha = dt.fecha 
            left join DWH.artus.catTienda ct on npr.idtienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where {agrupador_where} 
            {lugar_where} {clauseCatProveedor_tmp}
            group by id_pregunta
            ) a on ncp.id_pregunta =a.id_pregunta
            where ncp.tipo_respuesta ='R2'
            and ncp.orden in (select orden
            from DWH.limesurvey.nps_cat_preguntas ncp
            where descripcion = '{self.filtros.nps}' and tipo_respuesta = 'R1'
            )
            group by ncp.descripcion
            order by min(ncp.id) 
            """

            # print("Percepción del servicio (%) $categoria: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0 and arreglo[0]['F2'] is not None:
                # print(f"Arreglo desde Percepción del servicio (%) $categoria: {str(arreglo)}")
                hayResultados = "si"
                promotores = []
                detractoresYPasivos = []
                for row in arreglo:
                    categories.append(row['descripcion'])
                    promotores.append(round((float(row['F2'])/100), 4)) if row['F2'] else promotores.append(0)
                    detractoresYPasivos.append(round((float(row['F1'])/100), 4)) if row['F1'] else detractoresYPasivos.append(0)

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores y Pasivos',
                        'data': detractoresYPasivos, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'danger'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == '% NPS Con o Sin Aduana':
            pipeline = f"""select isnull(ds.proyecto,'Sin Aduana') Aduana,
            case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps,
            sum(case when nd.calificacion in (9,10) then 1 else 0 end) promotores,
            sum(case when nd.calificacion<=6 then 1 else 0 end) detractores,
            sum(case when nd.calificacion in (7,8) then 1 else 0 end) pasivos
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            inner join DWH.dbo.dim_store ds on nmp.idtienda =ds.idtienda
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date) = dt.fecha 
            left join DWH.artus.catTienda ct on nmp.idtienda =ct.tienda
            where {agrupador_where} {lugar_where} {clauseCatProveedor}
            group by isnull(ds.proyecto,'Sin Aduana') """

            # print("query desde ejes multiples nps: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                promotores = []
                detractores = []
                pasivos = []
                nps = []
                for row in arreglo:
                    categories.append(row['Aduana'])
                    promotores.append(row['promotores'])
                    detractores.append(row['detractores'])
                    pasivos.append(row['pasivos'])
                    nps.append(round((float(row['nps'])/100), 4))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores',
                        'data': detractores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    },
                    {
                        'name': 'Pasivos',
                        'data': pasivos, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'warning'
                    },
                    {
                        'name': 'Nps',
                        'data': nps, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark'
                    }
                ]
            else:
                hayResultados = 'no'
                
        if self.titulo == '% NPS Con o Sin Aduana':
            # Rawa
            pipeline = f"""select isnull(ds.proyecto,'Sin Aduana') Aduana,
            case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps,
            sum(case when nd.calificacion in (9,10) then 1 else 0 end) promotores,
            sum(case when nd.calificacion<=6 then 1 else 0 end) detractores,
            sum(case when nd.calificacion in (7,8) then 1 else 0 end) pasivos
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            inner join DWH.dbo.dim_store ds on nmp.idtienda =ds.idtienda
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date) = dt.fecha 
            left join DWH.artus.catTienda ct on nmp.idtienda =ct.tienda
            where {agrupador_where} {lugar_where} {clauseCatProveedor}
            group by isnull(ds.proyecto,'Sin Aduana') """
            # print("query desde ejes multiples nps: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                promotores = []
                detractores = []
                pasivos = []
                nps = []
                for row in arreglo:
                    categories.append(row['Aduana'])
                    promotores.append(row['promotores'])
                    detractores.append(row['detractores'])
                    pasivos.append(row['pasivos'])
                    nps.append(round((float(row['nps'])/100), 4))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores',
                        'data': detractores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    },
                    {
                        'name': 'Pasivos',
                        'data': pasivos, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'warning'
                    },
                    {
                        'name': 'Nps',
                        'data': nps, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark'
                    }
                ]
            else:
                hayResultados = 'no'
                
        if self.titulo == '% NPS por Formato Tienda':
            pipeline = f"""select ds.formato_tienda,
            case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps,
            sum(case when nd.calificacion in (9,10) then 1 else 0 end) promotores,
            sum(case when nd.calificacion<=6 then 1 else 0 end) detractores,
            sum(case when nd.calificacion in (7,8) then 1 else 0 end) pasivos
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            inner join DWH.dbo.dim_store ds on nmp.idtienda =ds.idtienda
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date) = dt.fecha 
            left join DWH.artus.catTienda ct on nmp.idtienda =ct.tienda
            where {agrupador_where} {lugar_where} {clauseCatProveedor}
            group by ds.formato_tienda
            """

            # print(f"query desde ejes multiples {self.titulo}: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                promotores = []
                detractores = []
                pasivos = []
                nps = []
                for row in arreglo:
                    categories.append(row['formato_tienda'])
                    promotores.append(row['promotores'])
                    detractores.append(row['detractores'])
                    pasivos.append(row['pasivos'])
                    nps.append(round((float(row['nps'])/100), 4))

                series = [
                    {
                        'name': 'Promotores',
                        'data': promotores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Detractores',
                        'data': detractores, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    },
                    {
                        'name': 'Pasivos',
                        'data': pasivos, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'warning'
                    },
                    {
                        'name': 'Nps',
                        'data': nps, 
                        'type': 'spline',
                        'formato_tooltip':'porcentaje', 
                        'color':'dark'
                    }
                ]
            else:
                hayResultados = 'no'
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def Home(self):
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        serie1 = []
        serie2 = []
        serie3 = []
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'tienda'
                    lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                lugar = int(self.filtros.region)
        else:
            filtro_lugar = False
            lugar = ''
        if self.titulo == 'Fulfillment Rate y Found Rate':
            # print("Entrando a Home Ejes Múltiples")
            collection = conexion_mongo('report').report_foundRate
            if filtro_lugar:
                pipeline = [{'$unwind': '$sucursal'}]
                pipeline.append({'$match': {f'sucursal.{nivel}': lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$group':{'_id': {'fecha_interna': '$fechaUltimoCambio', 'fecha_mostrar': '$descrip_fecha'}, 'pedidos': {'$sum': '$n_pedido'}, 'items_ini': {'$sum': '$items_ini'}, 'items_fin': {'$sum': '$items_fin'}, 'items_found': {'$sum': '$items_found'}}})
            pipeline.append({'$project':{'_id':0, 'fecha_interna':'$_id.fecha_interna', 'fecha_mostrar':'$_id.fecha_mostrar', 'fulfillment_rate': {'$divide': ['$items_fin', '$items_ini']}, 'found_rate': {'$divide': ['$items_found', '$items_ini']}}})
            pipeline.append({'$sort':{'fecha_interna': 1}})
            # print(f"Pipeline desde Home -> fulfillment rate y found rate: {str(pipeline)}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categories.append(row['fecha_mostrar'])
                    serie2.append(round((row['fulfillment_rate']), 4))
                    serie3.append(round((row['found_rate']), 4))
                series.extend([
                    {'name': 'Fulfillment Rate', 'data':serie2, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'primary'},
                    {'name': 'Found Rate', 'data':serie3, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'secondary'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Pedidos Perfectos':
            if filtro_lugar:
                pipeline.append({'$unwind': '$sucursal'})
                pipeline.append({'$match': {f'sucursal.{nivel}': lugar}})
            collection = conexion_mongo('report').report_pedidoPerfecto
            pipeline.append(
                {'$match': {
                    'fecha': {
                        '$gte': self.fecha_ini_a12, 
                        '$lt': self.fecha_fin_a12
                    }
                }}
            )
            pipeline.extend([
                {'$group': {
                    '_id': {},
                    'totales': {'$sum': '$Total_Pedidos'},
                    'perfectos': {'$sum': '$perfecto'}
                }}, 
                {'$sort': {'_id.anio': 1}}
            ])
            # print(str(pipeline))
            grupo = pipeline[-2]['$group']['_id']
            sort = pipeline[-1]['$sort']
            grupo['anio'] = {'$year': '$fecha'}
            grupo['mes'] = {'$month': '$fecha'}
            sort['_id.anio'] = 1
            sort['_id.mes'] = 1
            grupo['dia'] = {'$dayOfMonth': '$fecha'}
            sort['_id.dia'] = 1
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                # print(str(pipeline))
                # print(str(arreglo))
                for i in range(len(arreglo)):
                    anio = arreglo[i]['_id']['anio']
                    mes = arreglo[i]['_id']['mes']
                    category = mesTexto(mes) + ' ' + str(anio)
                    category = str(arreglo[i]['_id']['dia']) + ' ' + category
                    categories.append(category)
                    if arreglo[i]['totales'] > 0:
                        serie1.append(round((arreglo[i]['perfectos']/arreglo[i]['totales']), 4))
                    else:
                        serie1.append(0)
                    serie2.append(round((serie1[i]-serie1[i-1]), 4)) if i > 0 else serie2.append(0)
                    
                series.extend([
                    {'name': '% ATYC', 'data':serie1, 'type': 'column', 'formato_tooltip':'porcentaje', 'color':'secondary'},
                    {'name': '% Dif', 'data':serie2, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'dark'}
                ])
            else:
                hayResultados = "no"

        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def ResultadoRFM(self):
        categories = []
        series = []
        serie1 = []
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]

        if self.titulo == 'Primeras Compras por Mes':
            anio_fin_trimestre = self.filtros.anioRFM * 10000
            mes_fin_trimestre = self.filtros.mesRFM * 100
            fin_trimestre = anio_fin_trimestre + mes_fin_trimestre + 100
            anio_ini_trimestre = anio_fin_trimestre if self.filtros.mesRFM >=3 else (self.filtros.anioRFM - 1) * 10000
            mes_ini_trimestre = self.filtros.mesRFM - 200 if self.filtros.mesRFM >= 3 else (10 + self.filtros.mesRFM) * 100
            ini_trimestre = anio_ini_trimestre + mes_ini_trimestre
            pipeline.extend([
                {'$match': {'primerCompra': {'$gt': ini_trimestre, '$lt': fin_trimestre}}},
                {'$group': {
                    '_id': {'mes': {'$month': '$Fini'}, 'anio': {'$year': '$Fini'}},
                    'cantClientes': {'$sum': 1}
                }},
                {'$sort': {'_id.anio': 1, '_id.mes': 1}}
            ])
            # print('Pipeline desde ResultadoRFM de EjesMultiples: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in (arreglo):
                    categories.append(mesTexto(int(row['_id']['mes'])))
                    serie1.append(row['cantClientes'])
                series = [
                    {
                        'name': 'Clientes Nuevos',
                        'data': serie1, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'primary'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Quejas por Segmento':
            pipeline.extend([
                        {'$group': {
                            '_id': '$tipoCliente', 
                            'cantQuejas': {
                                '$sum': '$cantQuejas'
                            }
                        }},
                        {'$sort': {'_id': 1}}
            ])
            # print('Pipeline desde Ctes por segmento en Tablas: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in (arreglo):
                    categories.append(row['_id'])
                    serie1.append(row['cantQuejas'])
                series = [
                    {
                        'name': 'Quejas',
                        'data': serie1, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'primary'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Fuera de Tiempo por Segmento':
            pipeline.extend([
                        {'$group': {
                            '_id': '$tipoCliente', 
                            'cantQuejas': {
                                '$sum': '$cantFueraTiempo'
                            }
                        }},
                        {'$sort': {'_id': 1}}
            ])
            # print('Pipeline desde Ctes por segmento en Tablas: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in (arreglo):
                    categories.append(row['_id'])
                    serie1.append(row['cantQuejas'])
                series = [
                    {
                        'name': 'Fuera de Tiempo',
                        'data': serie1, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'dark'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Cantidad de Clientes por Segmento y Calificación NPS':
            serie2 = []
            serie3 = []
            pipeline.extend([
                {'$match': {
                    'califNPS': {
                        '$ne': None
                    }
                }},
                {'$group': {
                    '_id': {
                        'califNPS': '$califNPS',
                        'segmento': '$tipoCliente'
                    }, 
                    'cantClientes': {
                        '$sum': 1
                    }
                }},
                {'$sort': {'_id.segmento': 1}}
            ])
            # print('Pipeline desde Ctes por segmento en Tablas: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde Quejas por Segmento y Calificación NPS en ejesMultiples: '+str(arreglo))
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    if row['_id']['segmento'] not in categories:
                        categories.append(row['_id']['segmento'])
                serie1 = [0 for i in range(len(categories))]
                serie2 = [0 for i in range(len(categories))]
                serie3 = [0 for i in range(len(categories))]
                for row in arreglo:
                    if row['_id']['califNPS'] == 'Promotores':
                        serie1[categories.index(row['_id']['segmento'])] = row['cantClientes']
                    elif row['_id']['califNPS'] == 'Pasivos':
                        serie2[categories.index(row['_id']['segmento'])] = row['cantClientes']
                    elif row['_id']['califNPS'] == 'Detractores':
                        serie3[categories.index(row['_id']['segmento'])] = row['cantClientes']
                series = [
                    {
                        'name': 'Promotores',
                        'data': serie1, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Pasivos',
                        'data': serie2, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'warning'
                    },
                    {
                        'name': 'Detractores',
                        'data': serie3, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Cantidad de Quejas por Segmento de clientes y Calificación NPS':
            serie2 = []
            serie3 = []
            pipeline.extend([
                {'$match': {
                    'califNPS': {
                        '$ne': None
                    }
                }},
                {'$group': {
                    '_id': {
                        'califNPS': '$califNPS',
                        'segmento': '$tipoCliente'
                    }, 
                    'cantQuejas': {
                        '$sum': '$cantQuejas'
                    }
                }},
                {'$sort': {'_id.segmento': 1}}
            ])
            # print('Pipeline desde Ctes por segmento en Tablas: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde Quejas por Segmento y Calificación NPS en ejesMultiples: '+str(arreglo))
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    if row['_id']['segmento'] not in categories:
                        categories.append(row['_id']['segmento'])
                serie1 = [0 for i in range(len(categories))]
                serie2 = [0 for i in range(len(categories))]
                serie3 = [0 for i in range(len(categories))]
                for row in arreglo:
                    if row['_id']['califNPS'] == 'Promotores':
                        serie1[categories.index(row['_id']['segmento'])] = row['cantQuejas']
                    elif row['_id']['califNPS'] == 'Pasivos':
                        serie2[categories.index(row['_id']['segmento'])] = row['cantQuejas']
                    elif row['_id']['califNPS'] == 'Detractores':
                        serie3[categories.index(row['_id']['segmento'])] = row['cantQuejas']
                series = [
                    {
                        'name': 'Promotores',
                        'data': serie1, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'success'
                    },
                    {
                        'name': 'Pasivos',
                        'data': serie2, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'warning'
                    },
                    {
                        'name': 'Detractores',
                        'data': serie3, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'danger'
                    }
                ]
            else:
                hayResultados = 'no'

        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def CostoPorPedido(self):
        anio = self.filtros.anio
        mes = self.filtros.mes
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        queryMetodoEnvio = f"and TiendaEnLinea = '{self.filtros.metodoEnvio}'" if self.filtros.metodoEnvio != '' and self.filtros.metodoEnvio != "False" and self.filtros.metodoEnvio != None else ''
        queryAnio = f"and Anio = {self.filtros.anio}" if self.filtros.anio != 0 else ''
        queryMes = f"and Mes = {self.filtros.mes}" if self.filtros.mes != 0 else ''
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            queryLugar2 = 'left join DWH.artus.catTienda ct on cf.Cebe = ct.tienda'
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    queryLugar1 = ', ct.tienda'
                    queryLugar3 = f'and ct.tienda = {self.filtros.tienda}'
                else:
                    queryLugar1 = ', ct.zona'
                    queryLugar3 = f'and ct.zona = {self.filtros.zona}'
            else:
                    queryLugar1 = ', ct.region'
                    queryLugar3 = f'and ct.region = {self.filtros.region}'
        else:
            queryLugar1 = queryLugar2 = queryLugar3 = ''
        if self.titulo == 'Costo por Método de envío':
            propios = []
            logistica = []
            zubale = []
            propiosParaZubale = []
            series = []
            query = f"""select * from  DWH.artus.catCostos"""
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            costosReferencia_tmp = crear_diccionario(cursor)
            costosReferencia = {}
            for row in costosReferencia_tmp:
                costosReferencia[row['descripCosto']] = row['Costo']
            pipeline = f"""select TiendaEnLinea, SUM(RH) as RH, SUM(pRH) as pRH, SUM(Reclutamiento) as Surtido, SUM(Envio) as Envio, SUM(Combustible) as Combustible, sum(pPickedUp) as pPickedUp, SUM(pEnviados) as pEnviados, SUM(pZubale) as pZubale, SUM(PagoXDistancia) as PagoXDistancia, SUM(pZub45) as pedSoloPickeo{queryLugar1}
            from dwh.report.consolidadoFinanzas cf
            {queryLugar2}
            where Mes <= 12
            {queryMetodoEnvio}
            {queryAnio}
            {queryMes}
            {queryLugar3}
            group by TiendaEnLinea{queryLugar1}
            """
            # print(f"Query desde EjesMultiples -> CostoPorPedido: {pipeline}")
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                # Vamos a hacer un arreglo de dos dimensiones, con parámetros que van a alimentar los indicadores. La primera dimensión es:
                # 0: Solo Rec. Propios, 1: Rec. Propios y Logística, 2: Zubale, 3: Rec. Propios para tiendas Zubale

                # La segunda dimensión es:
                # 0: RH, 1: Envio, 2: Combustible, 3: pRH(Tot Pedidos), 4: pPickedUp, 5: pEnviados, 6: Costo Picker, 7: Costo Envío, 8: End to End
                parm = [[0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0]]
                surtidoNoZubale = pickeoZubale = 0
                for row in arreglo:
                    parm[2][3] += row['pZubale']
                    parm[2][5] += row['pZubale']
                    if row['TiendaEnLinea'] == 'No es Zubale':
                        parm[0][0] += row['RH']
                        parm[0][1] += row['Envio']
                        parm[0][2] += row['Combustible']
                        parm[0][3] += row['pRH']
                        parm[0][4] += row['pPickedUp']
                        parm[0][5] += row['pEnviados']
                        surtidoNoZubale += row['Surtido']
                        pickeoZubale += row['pedSoloPickeo']
                    elif row['TiendaEnLinea'] == 'Zubale':
                        parm[3][0] += row['RH']
                        parm[3][1] += row['Envio']
                        parm[3][2] += row['Combustible']
                        parm[3][3] += row['pRH']
                        parm[3][4] += row['pPickedUp']
                        parm[3][5] += row['pEnviados']
                        parm[2][0] += row['Surtido']
                    elif row['TiendaEnLinea'] == 'Logística':
                        parm[1][0] += row['RH']
                        parm[1][1] += row['Envio']
                        parm[1][2] += row['Combustible']
                        parm[1][3] += row['pRH']
                        parm[1][4] += row['pPickedUp']
                        parm[1][5] += row['pEnviados']
                parm[0][6] = (parm[0][0] + surtidoNoZubale) / (parm[0][3] + pickeoZubale) if parm[0][3] != 0 else 0
                parm[0][7] = (parm[0][1] + parm[0][2]) / parm[0][5] if parm[0][5] != 0 else 0
                parm[0][8] = parm[0][6] + parm[0][7]
                parm[1][6] = parm[1][0] / parm[1][3] if parm[1][3] != 0 else 0
                parm[1][7] = (parm[1][1] + parm[1][2]) / parm[1][5] if parm[1][5] != 0 else 0
                parm[1][8] = parm[1][6] + parm[1][7]
                parm[2][8] = parm[2][0] / parm[2][5] if parm[2][5] != 0 else 0
                parm[2][6] = parm[2][8] * costosReferencia['Costo de Zubale para pickeo'] / costosReferencia['Costo de Zubale para envío']
                parm[2][7] = parm[2][8] - parm[2][6]
                parm[3][6] = parm[3][0] / parm[3][3] if parm[3][3] != 0 else 0
                parm[3][7] = (parm[3][1] + parm[3][2]) / parm[3][5] if parm[3][5] != 0 else 0
                parm[3][8] = parm[3][6] + parm[3][7]
                categories = ['Costo de Pickeo por Pedido', 'Costo Envío por Pedido', 'Costo End to End por Pedido']
                for i in range(6,9):
                    # print("Debug 5")
                    propios.append(parm[0][i])
                    logistica.append(parm[1][i])
                    zubale.append(parm[2][i])
                    propiosParaZubale.append(parm[3][i])
                # print(f"propios: {str(propios)}")
                # print(f"logistica: {str(logistica)}")
                # print(f"zubale: {str(zubale)}")
                series = [
                    {
                        'name': 'Solo Recursos Propios',
                        'data': propios, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'primary'
                    },
                    {
                        'name': 'Rec. Propios y Logística',
                        'data': logistica, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary'
                    },
                    {
                        'name': 'Solo Zubale',
                        'data': zubale, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'dark'
                    },
                    {
                        'name': 'Rec. Prop. para tiendas Zubale',
                        'data': propiosParaZubale, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'light'
                    },
                    {
                        'name': 'Meta',
                        'data': [costosReferencia['Meta de costo de pickeo'], costosReferencia['Meta de costo de envío'], costosReferencia['Meta de End To End']],
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'success'
                    }
                ]
            else:
                hayResultados = 'no'
                categories = []
                series = []
        # print(f"parm: {str(parm)}")
        # print(str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}))
        if self.titulo == 'Pedidos por Picker: Top 20':
            costosXPedido = []
            promedios = []
            pipeline = f"""select cf.Dec_CeBe, SUM(cf.pRH) as pedidos, SUM(cp.Ocupada) as pickers, SUM(cf.pRH)/SUM(cp.Ocupada) as pedidosXPicker
            from dwh.report.consolidadoFinanzas cf
            left join DWH.report.consolidadoFinanzasPicker cp on cp.CeBe = cf.Cebe
            where Mes <= 12
            {queryMetodoEnvio}
            {queryAnio}
            {queryMes}
            {queryLugar3}
            group by cf.Dec_CeBe
            order by SUM(cf.pRH)/SUM(cp.Ocupada) DESC
            """
            # print(f"Query desde EjesMultiples -> CostoPorPedido: {pipeline}")
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                # Vamos a hacer un arreglo de dos dimensiones, con parámetros que van a alimentar los indicadores. La primera dimensión es:
                # 0: Rec. Propios, 1: Rec. Propios/Logisitca, 2: Zubale
                # La segunda dimensión es:
                # 0: RH, 1: Envio, 2: Combustible, 3: pRH(Tot Pedidos), 4: pPickedUp, 5: pEnviados, 6: Costo Picker, 7: Costo Envío, 8: End to End
                parm = [[0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0]]
                surtidoNoZubale = pickeoZubale = 0
                for row in arreglo:
                    parm[2][1] += row['PagoXDistancia']
                    parm[2][3] += row['pZubale']
                    parm[2][5] += row['pZubale']
                    if row['TiendaEnLinea'] == 'Zubale' or row['TiendaEnLinea'] == 'No es Zubale':
                        parm[0][0] += row['RH']
                        parm[0][1] += row['Envio']
                        parm[0][2] += row['Combustible']
                        parm[0][3] += row['pRH']
                        parm[0][4] += row['pPickedUp']
                        parm[0][5] += row['pEnviados']
                        if row['TiendaEnLinea'] == 'Zubale':
                            parm[2][0] += row['Surtido']
                        else:
                            surtidoNoZubale += row['Surtido']
                            pickeoZubale += row['pedSoloPickeo']
                    elif row['TiendaEnLinea'] == 'Logística':
                        parm[1][0] += row['RH']
                        parm[1][1] += row['Envio']
                        parm[1][2] += row['Combustible']
                        parm[1][3] += row['pRH']
                        parm[1][4] += row['pPickedUp']
                        parm[1][5] += row['pEnviados']
                parm[2][8] = parm[2][0] / parm[2][5] if parm[2][5] != 0 else 0
                parm[2][6] = parm[2][8] * costosReferencia['Costo de Zubale para pickeo'] / costosReferencia['Costo de Zubale para envío']
                parm[2][7] = parm[2][8] - parm[2][6]
                parm[0][6] = (parm[0][0] + surtidoNoZubale) / (parm[0][3] + pickeoZubale) if parm[0][3] != 0 else 0
                parm[1][6] = parm[1][0] / parm[1][3] if parm[1][3] != 0 else 0
                parm[0][7] = (parm[0][1] + parm[0][2]) / parm[0][5] if parm[0][5] != 0 else 0
                parm[1][7] = (parm[1][1] + parm[1][2]) / parm[1][5] if parm[1][5] != 0 else 0
                parm[0][8] = parm[0][6] + parm[0][7]
                parm[1][8] = parm[1][6] + parm[1][7]
                categories = ['Costo de Pickeo por Pedido', 'Costo Envío por Pedido', 'Costo End to End por Pedido']
                for i in range(6,9):
                    # print("Debug 5")
                    propios.append(parm[0][i])
                    logistica.append(parm[1][i])
                    zubale.append(parm[2][i])
                    propiosParaZubale.append(parm[3][i])
                # print(f"propios: {str(propios)}")
                # print(f"logistica: {str(logistica)}")
                # print(f"zubale: {str(zubale)}")
                series = [
                    {
                        'name': 'Recursos Propios',
                        'data': propios, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'primary'
                    },
                    {
                        'name': 'Rec. Propios/Logística',
                        'data': logistica, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary'
                    },
                    {
                        'name': 'Zubale',
                        'data': zubale, 
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'dark'
                    },
                    {
                        'name': 'Meta',
                        'data': [costosReferencia['Meta de costo de pickeo'], costosReferencia['Meta de costo de envío'], costosReferencia['Meta de End To End']],
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'success'
                    }
                ]
            else:
                hayResultados = 'no'
                categories = []
                series = []
        # print(f"parm: {str(parm)}")
        # print(str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}))
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

    async def PedidosPendientes(self):
        anio = self.filtros.anio
        mes = self.filtros.mes
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        if self.titulo == 'Pedidos Programados para Siguientes Días':
            filtroFuturo = {
                '$match': {
                    'prioridad': {
                        '$eq': 'Futuro'
                    }
                }
            }
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''

            collection = conexion_mongo('report').report_pedidoPendientes
            pipeline.extend([{'$unwind': '$sucursal'}, filtroFuturo])
            if self.filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: self.lugar}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})
            # pipeline.append({'$match': {'estatus': 'pendientes'}})
            # pipeline.append({'$match': {'prioridad': {'$in': ['2 DIAS','ANTERIORES']}}})
            pipeline.append({
                '$group': {
                    '_id': "$fechaEntrega",
                    'Tienda': {
                        '$sum': {
                            '$cond': [
                                { '$eq': ["$metodoEntrega", "Tienda"] },
                                1,
                                0
                            ]
                        }
                    },
                    'Domicilio': {
                        '$sum': {
                            '$cond': [
                                { '$eq': ["$metodoEntrega", "Domicilio"] },
                                1,
                                0
                            ]
                        }
                    },
                    'Flete': {
                        '$sum': {
                            '$cond': [
                                { '$eq': ["$metodoEntrega", "Flete"] },
                                1,
                                0
                            ]
                        }
                    },
                    'DHL': {
                        '$sum': {
                            '$cond': [
                                { '$eq': ["$metodoEntrega", "DHL"] },
                                1,
                                0
                            ]
                        }
                    }
                }
            })
            pipeline.append({'$sort': {'_id': 1}})
            # print(f"Pipeline desde Tablas -> Tiendas con Pedidos Atrasados Mayores a 1 Día: {str(pipeline)}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            data = []
            Tienda = []
            Domicilio = []
            Flete = []
            DHL = []
            categories = []

            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    Tienda.append(dato['Tienda'])
                    Domicilio.append(dato['Domicilio'])
                    Flete.append(dato['Flete'])
                    DHL.append(dato['DHL'])
                    categories.append(fechaAbrevEspanol(dato['_id']))
                series = [
                    {
                        'name': 'Tienda',
                        'data': Tienda, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'black'
                    },
                    {
                        'name': 'Domicilio',
                        'data': Domicilio, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'darkgray'
                    },
                    {
                        'name': 'Flete',
                        'data': Flete, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'gray'
                    },
                    {
                        'name': 'DHL',
                        'data': DHL, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'lightgray'
                    }
                ]
            else:
                hayResultados = 'no'        

        # print(str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}))
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

@router.post("/{seccion}")
async def ejes_multiples (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = EjesMultiples(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}