from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import fechaAbrevEspanol
from app.servicios.formatoFechas import mesTexto
from datetime import datetime, date, timedelta
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/columnasApiladas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class ColumnasApiladas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def NivelesDeServicio(self):
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []
        serie5 = []
        serie6 = []

        if self.titulo == 'Estatus de Entrega y No Entrega por Área':
            if self.filtros.region != '' and self.filtros.region != "False":
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    nivel = 'zona'
                    siguiente_nivel = 'tienda'
                    lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    siguiente_nivel = 'zonaNombre'
                    lugar = int(self.filtros.region)
            else:
                filtro_lugar = False
                siguiente_nivel = 'regionNombre'
                lugar = ''

            collection = conexion_mongo('report').report_pedidoAtrasado
            if filtro_lugar:
                pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ nivel: lugar}}])
            pipeline.append({'$match': {'fechaEntrega': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria and self.filtros.categoria != "False":
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'xLabel':'$sucursal.'+siguiente_nivel, 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, 1, 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, 1, 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, 1, 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, 1, 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, 1, 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':'$xLabel', 'Entregado_Fuera_tiempo':{'$sum':'$Entregado_Fuera_tiempo'}, 'Entregado_tiempo':{'$sum':'$Entregado_tiempo'}, 'No_entregado_Fuera_tiempo':{'$sum':'$No_entregado_Fuera_tiempo'}, 'No_entregado_tiempo':{'$sum':'$No_entregado_tiempo'}, 'Despachado_Fuera_tiempo':{'$sum':'$Despachado_Fuera_tiempo'}, 'Despachado_tiempo':{'$sum':'$Despachado_tiempo'}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['Entregado_Fuera_tiempo'])
                    serie2.append(row['Entregado_tiempo'])
                    serie3.append(row['No_entregado_Fuera_tiempo'])
                    serie4.append(row['No_entregado_tiempo'])
                    serie5.append(row['Despachado_Fuera_tiempo'])
                    serie6.append(row['Despachado_tiempo'])
                series.extend([
                    {'name': 'Entregado-Fuera de tiempo', 'data':serie1, 'color': 'primary'},                                
                    {'name': 'Entregado-A tiempo', 'data':serie2, 'color': 'success'},
                    {'name': 'No entregado-Fuera de tiempo', 'data':serie3, 'color': 'danger'},
                    {'name': 'No entregado-A tiempo', 'data':serie4, 'color': 'warning'},
                    {'name': 'Despachado-Fuera de tiempo', 'data':serie5, 'color': 'dark'},
                    {'name': 'Despachado-A tiempo', 'data':serie6, 'color': 'info'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Pedidos Cancelados por Área':
            
            if self.filtros.region != '' and self.filtros.region != "False":
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    nivel = 'zona'
                    siguiente_nivel = 'tiendaNombre'
                    lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    siguiente_nivel = 'zonaNombre'
                    lugar = int(self.filtros.region)
            else:
                filtro_lugar = False
                siguiente_nivel = 'regionNombre'

            collection = conexion_mongo('report').report_pedidoCancelado
            pipeline.append({'$unwind': '$sucursal'})
            if filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria and self.filtros.categoria != "False":
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$group':{'_id':'$sucursal.'+siguiente_nivel, 'cancelados': {'$sum': '$pedidoCancelado'}, 'no_cancelados': {'$sum': '$pedidoNoCancelado'}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['cancelados'])
                    serie2.append(row['no_cancelados'])
                series.extend([
                    {'name': 'Pedidos Cancelados', 'data':serie1, 'color': 'danger'},
                    {'name': 'Pedidos No Cancelados', 'data':serie2, 'color': 'success'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Estatus de Entrega y No Entrega por Día':

            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        nivel = 'idTienda'
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

            collection = conexion_mongo('report').report_pedidoAtrasado
            if filtro_lugar:
                pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ nivel: lugar}}])
            pipeline.append({'$match': {'fechaEntrega': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria and self.filtros.categoria != "False":
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'xLabel':'$fechaEntrega', 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, 1, 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, 1, 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, 1, 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, 1, 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, 1, 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, 1, 0]}}})
            pipeline.append({'$group':{'_id': {'fecha_sin_formato': '$xLabel', 'fecha_formateada': {'$dateToString': {'format': "%d/%m/%Y", 'date': '$xLabel'}}}, 'Entregado_Fuera_tiempo':{'$sum':'$Entregado_Fuera_tiempo'}, 'Entregado_tiempo':{'$sum':'$Entregado_tiempo'}, 'No_entregado_Fuera_tiempo':{'$sum':'$No_entregado_Fuera_tiempo'}, 'No_entregado_tiempo':{'$sum':'$No_entregado_tiempo'}, 'Despachado_Fuera_tiempo':{'$sum':'$Despachado_Fuera_tiempo'}, 'Despachado_tiempo':{'$sum':'$Despachado_tiempo'}}})
            pipeline.append({'$sort': {'_id.fecha_sin_formato': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id']['fecha_formateada'])
                    serie1.append(row['Entregado_Fuera_tiempo'])
                    serie2.append(row['Entregado_tiempo'])
                    serie3.append(row['No_entregado_Fuera_tiempo'])
                    serie4.append(row['No_entregado_tiempo'])
                    serie5.append(row['Despachado_Fuera_tiempo'])
                    serie6.append(row['Despachado_tiempo'])
                series.extend([
                    {'name': 'Entregado-Fuera de tiempo', 'data':serie1, 'color': 'primary'},                                
                    {'name': 'Entregado-A tiempo', 'data':serie2, 'color': 'success'},
                    {'name': 'No entregado-Fuera de tiempo', 'data':serie3, 'color': 'danger'},
                    {'name': 'No entregado-A tiempo', 'data':serie4, 'color': 'warning'},
                    {'name': 'Despachado-Fuera de tiempo', 'data':serie5, 'color': 'dark'},
                    {'name': 'Despachado-A tiempo', 'data':serie6, 'color': 'info'}
                ])
            else:
                hayResultados = "no"
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'categoria':self.filtros.categoria}

    async def FoundRate(self):

        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []

        if self.titulo == 'Estatus Pedidos por Región':

            if self.filtros.region != '' and self.filtros.region != "False":
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    nivel = 'zona'
                    siguiente_nivel = 'tiendaNombre'
                    lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    siguiente_nivel = 'zonaNombre'
                    lugar = int(self.filtros.region)
            else:
                filtro_lugar = False
                siguiente_nivel = 'regionNombre'
                lugar = ''

            collection = conexion_mongo('report').report_foundRate
            pipeline.append({'$unwind': '$sucursal'})
            if filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria and self.filtros.categoria != "False":
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            pipeline.append({'$group':{'_id':'$sucursal.'+siguiente_nivel, 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['COMPLETO'])
                    serie2.append(row['INC_SIN_STOCK'])
                    serie3.append(row['INC_SUSTITUTOS'])
                    serie4.append(row['INCOMPLETO'])
                series.extend([
                    {'name': 'Completo', 'data':serie1, 'color': 'success'},                                
                    {'name': 'Incompleto Sin Stock', 'data':serie2, 'color': 'primary'},
                    {'name': 'Incompleto Sustitutos', 'data':serie3, 'color': 'warning'},
                    {'name': 'Incompleto', 'data':serie4, 'color': 'danger'}
                ])
            else:
                hayResultados = "no"

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'categoria':self.filtros.categoria}

    async def PedidosPendientes(self):

        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []
        serie5 = []

        if self.filtros.region != '' and self.filtros.region != "False":
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
                    nivel = 'idTienda'
                    siguiente_nivel = 'tiendaNombre'
                    lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    siguiente_nivel = 'tiendaNombre'
                    lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                siguiente_nivel = 'zonaNombre'
                lugar = int(self.filtros.region)
        else:
            filtro_lugar = False
            siguiente_nivel = 'regionNombre'
            lugar = ''

        collection = conexion_mongo('report').report_pedidoPendientes
        pipeline.append({'$unwind': '$sucursal'})
        if filtro_lugar:
            pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
        if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})

        if self.titulo == 'Estatus Pedidos por Área':
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$project': {'lugar': '$sucursal.'+siguiente_nivel, '2_DIAS': {'$cond': [{'$eq':['$prioridad', '2 DIAS']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, '1_DIA': {'$cond': [{'$eq':['$prioridad', '1 DIA']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}, 'ANTERIORES': {'$cond': [{'$eq':['$prioridad', 'ANTERIORES']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':'$lugar', '2_DIAS':{'$sum':'$2_DIAS'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, '1_DIA':{'$sum':'$1_DIA'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}, 'ANTERIORES':{'$sum':'$ANTERIORES'}}})
            pipeline.append({'$sort': {'_id': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['HOY_A_TIEMPO'])
                    serie2.append(row['HOY_ATRASADO'])
                    serie3.append(row['1_DIA'])
                    serie4.append(row['2_DIAS'])
                    serie5.append(row['ANTERIORES'])
                series.extend([
                    {'name': 'Hoy a tiempo', 'data':serie1, 'color': 'info'},
                    {'name': 'Hoy atrasado', 'data':serie2, 'color': 'dark'},
                    {'name': '1 día', 'data':serie3, 'color': 'warning'},
                    {'name': '2 días', 'data':serie4, 'color': 'primary'},
                    {'name': 'Anteriores', 'data':serie5, 'color': 'danger'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Pedidos del Día':
            pipeline.append({'$match': {'prioridad': {'$in': ['ENTREGADO', 'HOY ATRASADO', 'HOY A TIEMPO']}}})
            pipeline.append({'$project': {'rango': '$rango', 'ENTREGADO': {'$cond': [{'$eq':['$prioridad', 'ENTREGADO']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':'$rango', 'ENTREGADO':{'$sum':'$ENTREGADO'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}}})
            pipeline.append({'$sort': {'_id': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['ENTREGADO'])
                    serie2.append(row['HOY_A_TIEMPO'])
                    serie3.append(row['HOY_ATRASADO'])
                series.extend([
                    {'name': 'Entregado', 'data':serie1, 'color': 'success'},                                
                    {'name': 'Hoy a tiempo', 'data':serie2, 'color': 'info'},
                    {'name': 'Hoy atrasado', 'data':serie3, 'color': 'dark'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Estatus Pedidos por Fecha':
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$project': {'fecha_interna': '$fechaEntrega', 'fecha_mostrar': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}}, '2_DIAS': {'$cond': [{'$eq':['$prioridad', '2 DIAS']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, '1_DIA': {'$cond': [{'$eq':['$prioridad', '1 DIA']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}, 'ANTERIORES': {'$cond': [{'$eq':['$prioridad', 'ANTERIORES']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':{'fecha_interna':'$fecha_interna', 'fecha_mostrar': '$fecha_mostrar'}, '2_DIAS':{'$sum':'$2_DIAS'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, '1_DIA':{'$sum':'$1_DIA'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}, 'ANTERIORES':{'$sum':'$ANTERIORES'}}})
            pipeline.append({'$sort': {'_id.fecha_interna': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(fechaAbrevEspanol(row['_id']['fecha_interna']))
                    serie1.append(row['HOY_A_TIEMPO'])
                    serie2.append(row['HOY_ATRASADO'])
                    serie3.append(row['1_DIA'])
                    serie4.append(row['2_DIAS'])
                    serie5.append(row['ANTERIORES'])
                series.extend([
                    {'name': 'Hoy a tiempo', 'data':serie1, 'color': 'info'},
                    {'name': 'Hoy atrasado', 'data':serie2, 'color': 'dark'},
                    {'name': '1 día', 'data':serie3, 'color': 'warning'},
                    {'name': '2 días', 'data':serie4, 'color': 'primary'},
                    {'name': 'Anteriores', 'data':serie5, 'color': 'danger'}
                ])
            else:
                hayResultados = "no"

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}

    async def PedidoPerfecto(self):
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []

        collection = conexion_mongo('report').report_pedidoPerfecto

        if self.filtros.periodo == {}:
            return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': []}
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
            #         '$lt': self.fecha_fin_a12
            #     }
            # }},
            {'$match': {
                '$expr': {
                    '$and': []
                }
            }},
        ]
        if filtro_lugar:
            pipeline.extend([
                {'$unwind': '$sucursal'},
                {'$match': {'sucursal.'+ nivel: lugar}}
            ])

        if self.titulo == 'Evaluación de KPI Pedido Perfecto por Lugar':
            pipeline.extend([
                {'$group': {
                    '_id': {
                        'lugar': '$sucursal.'+siguiente_lugar,
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
            # Modificamos el pipeline para el caso de que el agrupador sea por semana:
            elif self.filtros.agrupador == 'semana':
                semana = self.filtros.periodo['semana']
                match.extend([
                    {'$eq': [
                        semana,
                        '$idSemDS'
                    ]}
                ])
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

            # Ejecutamos el query:
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    categorias.append(registro['_id']['lugar'])
                    serie1.append(round((float(registro['con_quejas'])/float(registro['totales'])), 4))
                    serie2.append(round((float(registro['retrasados'])/float(registro['totales'])), 4))
                    serie3.append(round((float(registro['cancelados'])/float(registro['totales'])), 4))
                    serie4.append(round((float(registro['incompletos'])/float(registro['totales'])), 4))
                series = [
                    {'name': 'Con quejas', 'data':serie1, 'color': 'danger'},
                    {'name': 'Retrasados', 'data':serie2, 'color': 'warning'},
                    {'name': 'Cancelados', 'data':serie3, 'color': 'dark'},
                    {'name': 'Incompletos', 'data':serie4, 'color': 'primary'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 2")

        elif self.titulo == 'Pedidos por Tipo de Entrega':
            pipeline.extend([
                {'$unwind': '$entrega'},
                    {'$match': {
                        '$expr': {
                            '$or': [
                                {'$and': []},
                                {'$and': []}
                            ]
                        }
                    }},
                {'$project': {
                    'itemsFound': '$entrega.domicilioATiempo',
                    'DHLATiempo': '$entrega.DHLATiempo',
                    'tiendaATiempo': '$entrega.tiendaATiempo',
                    'domicilioFueraTiempo': '$entrega.domicilioFueraTiempo',
                    'DHLFueraTiempo': '$entrega.DHLFueraTiempo',
                    'tiendaFueraATiempo': '$entrega.tiendaFueraATiempo',
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
                    'domicilioATiempo': {
                        '$sum': '$domicilioATiempo'
                    },
                    'DHLATiempo': {
                        '$sum': '$DHLATiempo'
                    },
                    'tiendaATiempo': {
                        '$sum': '$tiendaATiempo'
                    },
                    'domicilioFueraTiempo': {
                        '$sum': '$domicilioFueraTiempo'
                    },
                    'DHLFueraTiempo': {
                        '$sum': '$DHLFueraTiempo'
                    },
                    'tiendaFueraATiempo': {
                        '$sum': '$tiendaFueraATiempo'
                    }
                }},
                {'$sort': {'_id': 1}}
            ])

            # Creamos dos facets: para el periodo actual y el anterior
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
            # Ejecutamos el query:
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(str(arreglo))
            if len(arreglo) >0:
                hayResultados = "si"
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
                # LLenamos los arreglos que alimentarán el gráfico
                categorias = [tituloAnterior+'-DHL', tituloElegida+'-DHL', tituloAnterior+'-Domicilio', tituloElegida+'-Domicilio', tituloAnterior+'-Tienda', tituloElegida+'-Tienda']
                arrEleg = arreglo[0]
                arrAnt = arreglo[0]
                if arrEleg == [] or arrAnt == []:
                    return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
                serie1 = [
                    arrAnt['DHLATiempo'], 
                    arrEleg['DHLATiempo'], 
                    arrAnt['domicilioATiempo'], 
                    arrEleg['domicilioATiempo'],
                    arrAnt['tiendaATiempo'],
                    arrEleg['tiendaATiempo']
                ]
                serie2 = [
                    arrAnt['DHLFueraTiempo'], 
                    arrEleg['DHLFueraTiempo'], 
                    arrAnt['domicilioFueraTiempo'], 
                    arrEleg['domicilioFueraTiempo'],
                    arrAnt['tiendaFueraATiempo'],
                    arrEleg['tiendaFueraATiempo']
                ]
                series = [
                    {'name': 'Entregado a Tiempo', 'data':serie1, 'color': 'success'},
                    {'name': 'Entregado Fuera de Tiempo', 'data':serie2, 'color': 'danger'},
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 2")
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}

    async def Home(self):
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []

        if self.titulo == 'Pedidos del Día':
            collection = conexion_mongo('report').report_pedidoPendientes
            pipeline = [{'$unwind': '$sucursal'}]
            pipeline.append({'$match': {'sucursal.idTienda': int(self.filtros.tienda)}})
            pipeline.append({'$match': {'prioridad': {'$in': ['ENTREGADO', 'HOY ATRASADO', 'HOY A TIEMPO']}}})
            pipeline.append({'$project': {'rango': '$rango', 'ENTREGADO': {'$cond': [{'$eq':['$prioridad', 'ENTREGADO']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':'$rango', 'ENTREGADO':{'$sum':'$ENTREGADO'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}}})
            pipeline.append({'$sort': {'_id': 1}})
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(str(arreglo))
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['ENTREGADO'])
                    serie2.append(row['HOY_A_TIEMPO'])
                    serie3.append(row['HOY_ATRASADO'])
                series.extend([
                    {'name': 'Entregado', 'data':serie1, 'color': 'success'},                                
                    {'name': 'Hoy a tiempo', 'data':serie2, 'color': 'info'},
                    {'name': 'Hoy atrasado', 'data':serie3, 'color': 'dark'}
                ])
            else:
                hayResultados = "no"

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}
        # print('Lo que se devuelve desde columnasApiladas es: ' + str({'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}))
        # Return para debugging:
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': pipeline}

@router.post("/{seccion}")
async def columnas_apiladas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = ColumnasApiladas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
