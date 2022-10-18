from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import fechaAbrevEspanol
from app.servicios.formatoFechas import mesTexto
from datetime import datetime, date, timedelta
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/barrasApiladas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class BarrasApiladas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def PedidoPerfecto(self):
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []
        modTitulo = 'Sin Periodo'

        collection = conexion_mongo('report').report_pedidoPerfecto

        if self.filtros.periodo == {}:
            return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': [], 'modTitulo': ''}
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False"  and self.filtros.zona != None:
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

        pipeline = [
            # {'$match': {
            #     'fecha': {
            #         '$gte': self.fecha_ini_a12, 
            #         '$lte': self.fecha_fin_a12
            #     }
            # }},
            {'$match': {
                '$expr': {
                    '$and': []
                }
            }},
            {'$unwind': '$sucursal'},
            {'$match': {
                'sucursal.region': {'$ne': None}
            }}
        ]
        if filtro_lugar:
            pipeline.extend([
                {'$match': {'sucursal.'+ nivel: lugar}},
                {'$unwind': '$quejas'},
            ])

        if self.titulo == 'Quejas por lugar $periodo2':
            pipeline.extend([
                {'$group': {
                    '_id': {
                        'lugar': '$sucursal.'+siguiente_lugar,
                    },
                    'entregaFalso': {
                        '$sum': '$quejas.entregaFalso'
                    },
                    'entregaIncompleta': {
                        '$sum': '$quejas.entregaIncompleta'
                    },
                    'inconformidadProducto': {
                        '$sum': '$quejas.inconformidadProducto'
                    },
                    'pedidoRetrasado': {
                        '$sum': '$quejas.pedidoRetrasado'
                    }
                }},
                {
                    '$sort': {'_id.lugar': 1}
                }
            ])

            # Esto es un copy/paste de ejesMultiples. Burra el comentario cuando termines de modificarlo.
            match = pipeline[0]['$match']['$expr']['$and']
            
            # Modificamos el pipeline para el caso de que el agrupador sea por mes:
            if self.filtros.agrupador == 'mes':
                anio = self.filtros.periodo['anio']
                mes = self.filtros.periodo['mes']
                match.extend([
                    {'$eq': [
                        anio,
                        {'$year': '$fecha'}
                    ]},
                    {'$eq': [
                        mes,
                        {'$month': '$fecha'}
                    ]}
                ])
                modTitulo = 'Quejas por lugar ' + mesTexto(mes) + ' ' + str(anio)
            # Modificamos el pipeline para el caso de que el agrupador sea por semana:
            elif self.filtros.agrupador == 'semana':
                semana = self.filtros.periodo['semana']
                match.extend([
                    {'$eq': [
                        semana,
                        '$idSemDS'
                    ]}
                ])
                modTitulo = 'Quejas por lugar Sem ' + str(semana)[4:6] + ' ' + str(semana)[0:4]
            # Modificamos los facets para el caso de que el agrupador sea por día:
            elif self.filtros.agrupador == 'dia':
                anio = self.filtros.periodo['anio']
                mes = self.filtros.periodo['mes']
                dia = self.filtros.periodo['dia']
                match.extend([
                    {'$eq': [
                        anio,
                        {'$year': '$fecha'}
                    ]},
                    {'$eq': [
                        mes,
                        {'$month': '$fecha'}
                    ]},
                    {'$eq': [
                        dia,
                        {'$dayOfMonth': '$fecha'}
                    ]}
                ])
                modTitulo = 'Quejas por lugar ' + str(dia) + ' ' + mesTexto(mes) + ' ' + str(anio)
            # Ejecutamos el query:
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    categorias.append(registro['_id']['lugar'])
                    serie1.append(registro['pedidoRetrasado'])
                    serie2.append(registro['inconformidadProducto'])
                    serie3.append(registro['entregaIncompleta'])
                    serie4.append(registro['entregaFalso'])
                series = [
                    {'name': 'Pedido Retrasado', 'data':serie1, 'color': 'primary'},
                    {'name': 'Inconformidad de Producto', 'data':serie2, 'color': 'secondary'},
                    {'name': 'Entrega Incompleta', 'data':serie3, 'color': 'dark'},
                    {'name': 'Entrega en Falso', 'data':serie4, 'color': 'danger'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 2")

        elif self.titulo == 'Quejas por lugar $periodo1':
            pipeline.extend([
                {'$group': {
                    '_id': {
                        'lugar': '$sucursal.'+siguiente_lugar,
                    },
                    'entregaFalso': {
                        '$sum': '$quejas.entregaFalso'
                    },
                    'entregaIncompleta': {
                        '$sum': '$quejas.entregaIncompleta'
                    },
                    'inconformidadProducto': {
                        '$sum': '$quejas.inconformidadProducto'
                    },
                    'pedidoRetrasado': {
                        '$sum': '$quejas.pedidoRetrasado'
                    }
                }},
                {
                    '$sort': {'_id.lugar': 1}
                }
            ])

            # Esto es un copy/paste de ejesMultiples. Burra el comentario cuando termines de modificarlo.
            match = pipeline[0]['$match']['$expr']['$and']
            
            # Modificamos el pipeline para el caso de que el agrupador sea por mes:
            if self.filtros.agrupador == 'mes':
                anio_elegido = self.filtros.periodo['anio']
                mes_elegido = self.filtros.periodo['mes']
                if mes_elegido > 1:
                    mes_anterior = mes_elegido - 1
                    anio_anterior = anio_elegido
                else:
                    mes_anterior = 12
                    anio_anterior = anio_elegido - 1
                match.extend([
                    {'$eq': [
                        anio_anterior,
                        {'$year': '$fecha'}
                    ]},
                    {'$eq': [
                        mes_anterior,
                        {'$month': '$fecha'}
                    ]}
                ])
                modTitulo = 'Quejas por lugar ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
            # Modificamos el pipeline para el caso de que el agrupador sea por semana:
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
                match.extend([
                    {'$eq': [
                        semana_anterior_txt,
                        '$idSemDS'
                    ]}
                ])
                modTitulo = 'Quejas por lugar Sem ' + str(semana_anterior_txt)[4:6] + ' ' + str(anio_anterior)[0:4]
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
                match.extend([
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
                modTitulo = 'Quejas por lugar ' + str(dia_anterior) + ' ' + mesTexto(mes_anterior) + ' ' + str(anio_anterior)
            # Ejecutamos el query:
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    categorias.append(registro['_id']['lugar'])
                    serie1.append(registro['pedidoRetrasado'])
                    serie2.append(registro['inconformidadProducto'])
                    serie3.append(registro['entregaIncompleta'])
                    serie4.append(registro['entregaFalso'])
                series = [
                    {'name': 'Pedido Retrasado', 'data':serie1, 'color': 'primary'},
                    {'name': 'Inconformidad de Producto', 'data':serie2, 'color': 'secondary'},
                    {'name': 'Entrega Incompleta', 'data':serie3, 'color': 'dark'},
                    {'name': 'Entrega en Falso', 'data':serie4, 'color': 'danger'}
                ]
                # print(f"Pipeline Quejas Por Lugar $lugar1 en barrasApiladas: {pipeline}")
            else:
                hayResultados = "no"
                # print("No hay resultados 2")
        else:
            hayResultados = "no"
            # print("No hay resultados 1")
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'modTitulo': modTitulo}
        # print('Lo que se devuelve desde columnasApiladas es: ' + str({'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}))
        # Return para debugging:
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': pipeline}

    async def CatalogoArticulos(self):
        series = []
        serie1 = []
        serie2 = []
        categorias = []
        modTitulo = ''

        if self.filtros.periodo == {}:
            return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': [], 'modTitulo': ''}
        if self.filtros.agrupador == 'semana':
            filtroAgrupador = f" where idSemDS = {self.filtros.periodo['semana']} "
        else:
            filtroAgrupador = f" where idSemDS is not null "
        if self.filtros.grupoDeptos != '' and self.filtros.grupoDeptos != 'False' and self.filtros.grupoDeptos is not None:
            if self.filtros.deptoAgrupado != '' and self.filtros.deptoAgrupado != 'False' and self.filtros.deptoAgrupado is not None:
                lugar = 'Subdepartamento'
                if self.filtros.subDeptoAgrupado != '' and self.filtros.subDeptoAgrupado != 'False' and self.filtros.subDeptoAgrupado is not None:
                    filtroLugar = f" and Subdepartamento='{self.filtros.subDeptoAgrupado}' "
                else:
                    filtroLugar = f" and departamento='{self.filtros.deptoAgrupado}' "
            else:
                lugar = 'departamento'
                filtroLugar = f" and grupo='{self.filtros.grupoDeptos}' "
        else:
            lugar = 'departamento'
            filtroLugar = ''
        if self.titulo == 'Aprobados y No Aprobados por Departamento':
            query = f"""
            select {lugar}, sum(noVisible) as sumNoVisible, sum(VisibleTL) as sumVisibleTL
            from DWH.report.catalogoUXConsolidado
            {filtroAgrupador}
            {filtroLugar}
            group by {lugar}
            """
            # print(f"query desde barrasApiladas : {query}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            resultados = crear_diccionario(cursor)
            # print(f"resultados desde sankey: {str(resultados)}")
            if len(resultados) > 0:
                hayResultados = "si"
                for row in resultados:
                    categorias.append(row[lugar])
                    serie1.append(row['sumVisibleTL'])
                    serie2.append(row['sumNoVisible'])
                series = [
                    {'name': 'Aprobados en TL', 'data':serie1, 'color': 'primary'},
                    {'name': 'No Aprobados', 'data':serie2, 'color': 'dark'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 1")
        elif self.titulo == 'Porcentaje CMV':
            query = f"""
            select {lugar}, sum(CMV) as sumCMV, sum(totalCMV) as sumTotalCMV
            from DWH.report.catalogoUXConsolidado
            {filtroAgrupador}
            {filtroLugar}
            group by {lugar}
            """
            # print(f"query para Porcentaje CMV: {query}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            resultados = crear_diccionario(cursor)
            # print(f"resultados desde sankey: {str(resultados)}")
            if len(resultados) > 0:
                hayResultados = "si"
                for row in resultados:
                    categorias.append(row[lugar])
                    serie1.append(row['sumCMV'])
                    serie2.append(int(row['sumTotalCMV'])-int(row['sumCMV']))
                series = [
                    {'name': 'CMV', 'data':serie1, 'color': 'primary'},
                    {'name': 'No CMV', 'data':serie2, 'color': 'dark'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 1")

        elif self.titulo == 'Porcentaje CDB':
            query = f"""
            select {lugar}, sum(CDB) as sumCDB, sum(totalCDB) as sumTotalCDB
            from DWH.report.catalogoUXConsolidado
            {filtroAgrupador}
            {filtroLugar}
            group by {lugar}
            """
            # print(f"query para Porcentaje CDB: {query}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            resultados = crear_diccionario(cursor)
            # print(f"resultados desde sankey: {str(resultados)}")
            if len(resultados) > 0:
                hayResultados = "si"
                for row in resultados:
                    categorias.append(row[lugar])
                    serie1.append(row['sumCDB'])
                    serie2.append(int(row['sumTotalCDB'])-int(row['sumCDB']))
                series = [
                    {'name': 'CDB', 'data':serie1, 'color': 'primary'},
                    {'name': 'No CDB', 'data':serie2, 'color': 'dark'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 1")

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': query, 'modTitulo': modTitulo}
        # print('Lo que se devuelve desde columnasApiladas es: ' + str({'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}))
        # Return para debugging:
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': pipeline}

@router.post("/{seccion}")
async def barras_apiladas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id, seccion):
        objeto = BarrasApiladas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}