# ~ Se envía un arreglo "categorías" que contiene strings que corresponden al título de cada valor del eje x.
# ~ También se envía un diccionario "series" que contiene diccionarios que corresponden a cada barrita que se va apilando en cada punto del gráfico:
#     - Un string 'name' con el título de la barrita
#     - Un arreglo 'data' con los valores (eje y) de esa barrita para cada punto.
#     - Un string 'color' con el color de esa barrita, ya sea en formato "#FFCCDD" o "primary".

from copy import deepcopy
from time import strftime
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import fechaAbrevEspanol
from app.servicios.formatoFechas import mesTexto
from datetime import datetime, date, timedelta, time
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack

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
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
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
            if self.filtros.categoria and self.filtros.categoria != "False" and self.filtros.categoria != "" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "" and self.filtros.tipoEntrega != None:
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'xLabel':'$sucursal.'+siguiente_nivel, 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, '$pedidos', 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, '$pedidos', 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, '$pedidos', 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, '$pedidos', 0]}}})
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
            
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
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
            if self.filtros.categoria and self.filtros.categoria != "False" and self.filtros.categoria != "" and self.filtros.categoria != None:
                pipeline.append({'$match': {'categoria': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "" and self.filtros.tipoEntrega != None:
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            # pipeline.append({'$group':{'_id':'$sucursal.'+siguiente_nivel, 'cancelados': {'$sum': '$pedidoCancelado'}, 'no_cancelados': {'$sum': '$pedidoNoCancelado'}}})
            # print(f"Pipeline desde ColumnasApiladas -> NivelesDeServicio -> {self.titulo}: {pipeline}")
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
            if self.filtros.categoria and self.filtros.categoria != "False" and self.filtros.categoria != "" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "" and self.filtros.tipoEntrega != None:
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'xLabel':'$fechaEntrega', 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, '$pedidos', 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, '$pedidos', 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, '$pedidos', 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, '$pedidos', 0]}}})
            pipeline.append({'$group':{'_id': {'fecha_sin_formato': '$xLabel', 'fecha_formateada': {'$dateToString': {'format': "%d/%m/%Y", 'date': '$xLabel'}}}, 'Entregado_Fuera_tiempo':{'$sum':'$Entregado_Fuera_tiempo'}, 'Entregado_tiempo':{'$sum':'$Entregado_tiempo'}, 'No_entregado_Fuera_tiempo':{'$sum':'$No_entregado_Fuera_tiempo'}, 'No_entregado_tiempo':{'$sum':'$No_entregado_tiempo'}, 'Despachado_Fuera_tiempo':{'$sum':'$Despachado_Fuera_tiempo'}, 'Despachado_tiempo':{'$sum':'$Despachado_tiempo'}}})
            pipeline.append({'$sort': {'_id.fecha_sin_formato': 1}})
            # print(f"Pipeline desde ColumnasApiladas -> Niveles de Servicio: {str(pipeline)}")
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

        if self.titulo == 'Estatus Pedidos por Lugar':

            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    nivel = 'zona'
                    siguiente_nivel = '$sucursal.tiendaNombre'
                    lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    siguiente_nivel = '$sucursal.zonaNombre'
                    lugar = int(self.filtros.region)
            else:
                filtro_lugar = False
                siguiente_nivel = '$sucursal.regionNombre'
                lugar = ''

            collection = conexion_mongo('report').report_foundRate
            pipeline.append({'$unwind': '$sucursal'})
            if filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria != '' and self.filtros.categoria != "False" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            pipeline.append({'$group':{'_id':siguiente_nivel, 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}}})
            pipeline.append({'$sort':{'_id': 1}})
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

        if self.titulo == 'Estatus Pedidos por Día':
            collection = conexion_mongo('report').report_foundRate
            pipeline.append({'$unwind': '$sucursal'})
            pipeline.append({'$match': {'sucursal.tienda': int(self.filtros.tienda)}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria != '' and self.filtros.categoria != "False" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            pipeline.append({'$group':{'_id':{'dia': {'$dayOfMonth': '$fechaUltimoCambio'}, 'mes': {'$month':'$fechaUltimoCambio'}}, 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}}})
            pipeline.append({'$sort':{'_id': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(str(row['_id']['dia'])+' '+mesTexto(row['_id']['mes']))
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
        hayResultados = "no"
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []
        serie5 = []

        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
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

        filtroHoy = {
            '$match': {
                'prioridad': {
                    '$ne': 'Futuro'
                }
            }
        }
        collection = conexion_mongo('report').report_pedidoPendientes
        pipeline.extend([{'$unwind': '$sucursal'}, filtroHoy])
        if filtro_lugar:
            pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
        if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
        if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})

        if self.titulo == 'Pedidos Por Región':
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$project': {'lugar': '$sucursal.'+siguiente_nivel, '2_DIAS': {'$cond': [{'$eq':['$prioridad', '2 DIAS']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, '1_DIA': {'$cond': [{'$eq':['$prioridad', '1 DIA']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}, 'ANTERIORES': {'$cond': [{'$eq':['$prioridad', 'ANTERIORES']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':'$lugar', '2_DIAS':{'$sum':'$2_DIAS'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, '1_DIA':{'$sum':'$1_DIA'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}, 'ANTERIORES':{'$sum':'$ANTERIORES'}}})
            pipeline.append({'$sort': {'_id': 1}})
            cursor = collection.aggregate(pipeline)
            # print(f"Pipeline desde ColumnasApiladas -> PedidosPendientes -> Estatus Pedidos por Área: {str(pipeline)}")
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
                    {'name': 'Hoy a tiempo', 'data':serie1, 'color': 'secondary'},
                    {'name': 'Hoy atrasado', 'data':serie2, 'color': 'danger'},
                    {'name': '1 día', 'data':serie3, 'color': 'warning'},
                    {'name': '2 días', 'data':serie4, 'color': 'primary'},
                    {'name': 'Anteriores', 'data':serie5, 'color': '#FF3D51'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Entrega de pedidos por ventana de tiempo':
            pipeline.append({'$match': {'prioridad': {'$in': ['ENTREGADO', 'HOY ATRASADO', 'HOY A TIEMPO']}}})
            pipeline.append({'$project': {
                'rango': '$rango',
                'ENTREGADO': {'$cond': [
                    {'$and': [
                        {'$eq': ['$prioridad', 'ENTREGADO']},
                        {'$eq': [{'$dateToString': {'format': '%Y-%m-%d', 'date': '$fechaEntrega'}}, {'$dateToString': {'format': '%Y-%m-%d', 'date': datetime.now()}}]}
                    ]}, 1, 0]
                },
                'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]},
                'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}
            }})
            pipeline.append({'$group':{'_id':'$rango', 'ENTREGADO':{'$sum':'$ENTREGADO'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}}})
            pipeline.append({'$sort': {'_id': 1}})
            print(f"Pipeline desde columnasApiladas->{self.titulo}-> {pipeline}")
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
                    {'name': 'Hoy a tiempo', 'data':serie2, 'color': 'secondary'},
                    {'name': 'Hoy atrasado', 'data':serie3, 'color': 'danger'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Entrega de pedidos por fecha':
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$project': {'fecha_interna': '$fechaEntrega', 'fecha_mostrar': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}}, '2_DIAS': {'$cond': [{'$eq':['$prioridad', '2 DIAS']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, '1_DIA': {'$cond': [{'$eq':['$prioridad', '1 DIA']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}, 'ANTERIORES': {'$cond': [{'$eq':['$prioridad', 'ANTERIORES']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':{'fecha_interna':'$fecha_interna', 'fecha_mostrar': '$fecha_mostrar'}, '2_DIAS':{'$sum':'$2_DIAS'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, '1_DIA':{'$sum':'$1_DIA'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}, 'ANTERIORES':{'$sum':'$ANTERIORES'}}})
            pipeline.append({'$sort': {'_id.fecha_interna': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(f"Query desde columnasApiladas -> Estatus pedidos por fecha: {pipeline}")
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
                    {'name': 'Hoy a tiempo', 'data':serie1, 'color': 'secondary'},
                    {'name': 'Hoy atrasado', 'data':serie2, 'color': 'danger'},
                    {'name': '1 día', 'data':serie3, 'color': 'warning'},
                    {'name': '2 días', 'data':serie4, 'color': 'primary'},
                    {'name': 'Anteriores', 'data':serie5, 'color': '#FF3D51'}
                ])
            else:
                hayResultados = "no"

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}

    async def PedidoPerfecto(self):
        # esta condición está aquí porque a veces los filtros no terminan de cargar y ya está cargando la gráfica. Hay que verificar que los filtros hagan sentido.
        if not self.filtros.periodo or (self.filtros.agrupador == 'mes' and 'semana' in self.filtros.periodo) or (self.filtros.agrupador == 'semana' and not 'semana' in self.filtros.periodo) or (self.filtros.agrupador == 'dia' and not 'dia' in self.filtros.periodo):
            return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': []}       
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
        clauseCatTienda = False
        if len(self.filtros.provLogist) == 1:
            clauseCatTienda = {'$match': {'sucursal.Delivery': self.filtros.provLogist[0]}}
        elif len(self.filtros.provLogist) > 1:
            clauseCatTienda = {'$match': {
                '$expr': {
                    '$or': []
                }
            }}
            for prov in self.filtros.provLogist:
                clauseCatTienda['$match']['$expr']['$or'].append(
                    {'$eq': [
                        '$sucursal.Delivery',
                        prov
                    ]}
                )

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
                fecha_fin = monday + timedelta(days=5)
                fecha_ini = monday - timedelta(days=7)
            elif self.filtros.agrupador == 'dia':
                periodo = '$fecha'
                anio_elegido = self.filtros.periodo['anio']
                mes_elegido = self.filtros.periodo['mes']
                dia_elegido = self.filtros.periodo['dia']
                fecha_fin = datetime(anio_elegido, mes_elegido, dia_elegido)
                fecha_ini = fecha_fin - timedelta(days=1)
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59, microsecond=999999)

        if self.titulo == 'Evaluación de KPI Pedido Perfecto por Lugar':
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
                {'$unwind': '$sucursal'},
                {'$match': {'sucursal.region':{'$ne':None}}}
            ]
            if filtro_lugar:
                pipeline.extend([
                    {'$match': {'sucursal.'+ nivel: lugar}}
                ])
            if clauseCatTienda:
                pipeline.append(clauseCatTienda)

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
            # Modificamos los facets para el caso de que el agrupador sea por dÃ­a:
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
            # print(f"Pipeline desde ColumnasApiladas -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    categorias.append(registro['_id']['lugar'])
                    if registro['totales'] > 0:
                        serie1.append(round((float(registro['con_quejas'])/float(registro['totales'])), 4))
                        serie2.append(round((float(registro['retrasados'])/float(registro['totales'])), 4))
                        serie3.append(round((float(registro['cancelados'])/float(registro['totales'])), 4))
                        serie4.append(round((float(registro['incompletos'])/float(registro['totales'])), 4))
                    else:
                        serie1.append(0)
                        serie2.append(0)
                        serie3.append(0)
                        serie4.append(0)
                series = [
                    {'name': 'Con quejas', 'data':serie1, 'color': 'danger'},
                    {'name': 'Retrasados', 'data':serie2, 'color': 'warning'},
                    {'name': 'Cancelados', 'data':serie3, 'color': 'dark'},
                    {'name': 'Incompletos', 'data':serie4, 'color': 'primary'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 2")

        if self.titulo == 'Evaluación de KPI Pedido Perfecto por Periodo':
            pipeline = [
                {'$unwind': '$sucursal'},
                {'$match': {
                    'sucursal.region':{'$ne':None}
                }}
            ]
            if filtro_lugar:
                pipeline.extend([
                    {'$match': {'sucursal.'+ nivel: lugar}}
                ])
            if clauseCatTienda:
                pipeline.append(clauseCatTienda)

            pipeline.extend([
                {'$match': {
                    'fecha': {'$gte': fecha_ini}
                }},
                {'$match': {
                    'fecha': {'$lte': fecha_fin}
                }}
            ])
            # Modificamos el pipeline para el caso de que el agrupador sea por mes:
            if self.filtros.agrupador == 'mes':
                periodo = '$nMes'
            # Modificamos el pipeline para el caso de que el agrupador sea por semana:
            elif self.filtros.agrupador == 'semana':
                periodo = '$idSemDS'
            # Modificamos los facets para el caso de que el agrupador sea por dÃ­a:
            elif self.filtros.agrupador == 'dia':
                periodo = '$fecha'
            # return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': '', 'lenArreglo':0}
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
            
            # print(f"pipeline desde ColumnasApiladas -> PedidoPerfecto -> Evaluación de KPI Pedido Perfecto por Periodo: {str(pipeline)}")
            # Ejecutamos el query:
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    if self.filtros.agrupador == 'mes':
                        categorias.append(mesTexto(registro['_id']['periodo']))
                    elif self.filtros.agrupador == 'semana':
                        periodo = int(registro['_id']['periodo'])
                        anio = periodo // 100
                        numSem = periodo - anio * 100
                        categorias.append('Sem ' + str(numSem))
                    elif self.filtros.agrupador == 'dia':
                        fecha = registro['_id']['periodo']
                        categorias.append(str(fecha.day) + ' '+ mesTexto(fecha.month))
                    if registro['totales'] > 0:
                        serie1.append(round((float(registro['con_quejas'])/float(registro['totales'])), 4))
                        serie2.append(round((float(registro['retrasados'])/float(registro['totales'])), 4))
                        serie3.append(round((float(registro['cancelados'])/float(registro['totales'])), 4))
                        serie4.append(round((float(registro['incompletos'])/float(registro['totales'])), 4))
                    else:
                        serie1.append(0)
                        serie2.append(0)
                        serie3.append(0)
                        serie4.append(0)
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
                {'$unwind': '$sucursal'},
                {'$match': {'sucursal.region':{'$ne':None}}}
            ]
            if filtro_lugar:
                pipeline.extend([
                    {'$match': {'sucursal.'+ nivel: lugar}}
                ])
            if clauseCatTienda:
                pipeline.append(clauseCatTienda)

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
                    'domicilioATiempo': '$entrega.domicilioATiempo',
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
                condicion_elegido = [
                    {'$eq': [
                        anio_elegido,
                        {'$year': '$fecha'}
                    ]},
                    {'$eq': [
                        mes_elegido,
                        {'$month': '$fecha'}
                    ]}
                ]
                match1.extend(condicion_elegido)
                cond_periodo.extend(condicion_elegido)
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
                condicion_elegido = [
                    {'$eq': [
                        semana_elegida_txt,
                        '$idSemDS'
                    ]}
                ]
                match1.extend(condicion_elegido)
                cond_periodo.extend(condicion_elegido)
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
                condicion_elegido = [
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
                match1.extend(condicion_elegido)
                cond_periodo.extend(condicion_elegido)
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
            # print(f"Pipeline desde ColumnasApiladas -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
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
                arrAnt = arreglo[1]
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

    async def OnTimeInFull(self):
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
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'zona'
                    lugar = int(self.filtros.zona)
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
            {'$unwind': '$sucursal'},
            {'$match': {'sucursal.region':{'$ne':None}}}
        ]
        if filtro_lugar:
            pipeline.extend([
                {'$match': {'sucursal.'+ nivel: lugar}}
            ])

        if self.titulo == 'Evaluación de KPI A Tiempo y Completo por Lugar':
            pipeline.extend([
                {'$group': {
                    '_id': {
                        'lugar': '$sucursal.'+siguiente_lugar,
                    },
                    'retrasados': {
                        '$sum': '$retrasados'
                    },
                    'incompletos': {
                        '$sum': '$incompletos'
                    },
                    'totales': {
                        '$sum': '$Total_Pedidos'
                    },
                    'entregados': {
                        '$sum': '$Total_Entregados'
                    }
                }},
                {
                    '$sort': {'_id.lugar': 1}
                }
            ])

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
            # print(f"Pipeline ColumnasApiladas Otif: {pipeline}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    categorias.append(registro['_id']['lugar'])
                    if 'totales' in registro and registro['totales'] is not None and int(registro['totales']) != 0 and 'entregados' in registro and registro['entregados'] is not None and int(registro['entregados']) != 0:
                        serie2.append(round((float(registro['retrasados'])/float(registro['totales'])), 4))
                        serie4.append(round((float(registro['incompletos'])/float(registro['entregados'])), 4))
                    else:
                        serie2.append(0)
                        serie4.append(0)
                series = [
                    {'name': 'Retrasados', 'data':serie2, 'color': 'warning'},
                    {'name': 'Incompletos', 'data':serie4, 'color': 'primary'}
                ]
            else:
                hayResultados = "no"
                # print("No hay resultados 2")

        if self.titulo == 'Pedidos Completos vs. Incompletos':
            series = []
            arreglo = []
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []

            # print(f"self.filtros.periodo: {self.filtros.periodo}")
            cnxn = conexion_sql('DWH')
            if self.filtros.agrupador == 'semana':
                periodoNum = 'idSemDS'
                periodoTxt = 'dt.nSemDS'
                sem2 = str(self.filtros.periodo['semana'])
                query = f"""
                    select idSemDS from DWH.dbo.dim_tiempo where fecha = (
                        select DATEADD(DAY, -7, (select CONVERT(varchar,(min(fecha))) from DWH.dbo.dim_tiempo where idSemDS = {sem2}))
                    )
                """
                cursor = cnxn.cursor().execute(query)
                arreglo = crear_diccionario(cursor)
                sem1 = arreglo[0]['idSemDS']
                where = f"dt.idSemDS in ('{sem1}', '{sem2}')"
            if self.filtros.agrupador == 'mes':
                periodoNum = 'num_mes'
                periodoTxt = "CONCAT(dt.abrev_mes, ' ', anio)"
                mesNum = int(self.filtros.periodo['mes'])
                mesTxt = '%02d' % (mesNum)
                anio = int(self.filtros.periodo['anio'])
                diasEnMes_fin = monthrange(anio, mesNum)[1]
                fecha_fin_txt = f"{str(anio)}-{mesTxt}-{diasEnMes_fin}"
                year, month, day = map(int, fecha_fin_txt.split('-'))
                if month > 1:
                    month -= 1
                else:
                    month = 12
                    year -= 1
                fecha_ini_txt = '%04d-%02d-01' % (year, month)
                where = f"dt.fecha BETWEEN '{fecha_ini_txt}' and '{fecha_fin_txt}'"
            if self.filtros.agrupador == 'dia':
                periodoNum = 'id_fecha'
                periodoTxt = "dt.descrip_fecha"
                day = int(self.filtros.periodo['dia'])
                month = int(self.filtros.periodo['mes'])
                year = int(self.filtros.periodo['anio'])
                fecha_fin_txt = '%04d-%02d-%02d' % (year, month, day)
                if day == 1 and month == 1:
                    fecha_ini_txt = str(year - 1) + "-12-31"
                elif day == 1:
                    fecha_ini_txt = str(year) + "-" + str(month - 1).zfill(2) + "-31"
                else:
                    fecha_ini_txt = str(year) + "-" + str(month).zfill(2) + "-" + str(day - 1).zfill(2)
                where = f"dt.fecha BETWEEN '{fecha_ini_txt}' and '{fecha_fin_txt}'"
            pipeline = f"""
                select dt.{periodoNum} periodoNum, {periodoTxt} periodoTxt,
                sum (case when ho.tmp_n_estatus = 'COMPLETO' then 1 else 0 end) Completos,
                sum (case when ho.tmp_n_estatus = 'INCOMPLETO' then 1 else 0 end) Incompletos,
                sum (case when ho.tmp_n_estatus = 'INC_SUSTITITOS' then 1 else 0 end) Inc_Sustitutos,
                sum (case when ho.tmp_n_estatus = 'COMP_SUSTITUTOS' then 1 else 0 end) Comp_Sustitutos
                from DWH.dbo.hecho_order ho
                LEFT JOIN DWH.dbo.dim_tiempo dt on dt.fecha = CONVERT(date, creation_date)
                LEFT JOIN DWH.artus.catTienda ct on ct.tienda=ho.store_num
                WHERE {where}
                {lugar_sql}
                GROUP BY dt.{periodoNum}, {periodoTxt}
                """
            # print('ColumnasApiladas -> OTIF -> Estatus: '+pipeline)
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) >0:
                hayResultados = "si"
                for registro in arreglo:
                    categorias.append(registro['periodoTxt'])
                    Completos = float(registro['Completos'])
                    Incompletos = float(registro['Incompletos'])
                    Comp_Sustitutos = float(registro['Comp_Sustitutos'])
                    Inc_Sustitutos = float(registro['Inc_Sustitutos'])
                    Totales = Completos + Incompletos + Comp_Sustitutos + Inc_Sustitutos
                    if Totales == 0:
                        hayResultados = 'no'
                    else:
                        serie1.append(Completos / Totales)
                        serie2.append(Incompletos / Totales)
                        serie3.append(Comp_Sustitutos / Totales)
                        serie4.append(Inc_Sustitutos / Totales)
                series = [
                    {'name': 'Incompletos Con Sustitutos', 'data':serie4, 'color': 'primary'},
                    {'name': 'Completos Con Sustitutos', 'data':serie3, 'color': 'dark'},
                    {'name': 'Incompletos Sin Sustitutos', 'data':serie2, 'color': 'danger'},
                    {'name': 'Completos Sin Sustitutos', 'data':serie1, 'color': 'success'}
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
                    'domicilioATiempo': '$entrega.domicilioATiempo',
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
                condicion_elegido = [
                    {'$eq': [
                        anio_elegido,
                        {'$year': '$fecha'}
                    ]},
                    {'$eq': [
                        mes_elegido,
                        {'$month': '$fecha'}
                    ]}
                ]
                match1.extend(condicion_elegido)
                cond_periodo.extend(condicion_elegido)
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
                condicion_elegido = [
                    {'$eq': [
                        semana_elegida_txt,
                        '$idSemDS'
                    ]}
                ]
                match1.extend(condicion_elegido)
                cond_periodo.extend(condicion_elegido)
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
                condicion_elegido = [
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
                match1.extend(condicion_elegido)
                cond_periodo.extend(condicion_elegido)
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
            # print(f"Pipeline desde ColumnasApiladas -> A Tiempo y Completo: {str(pipeline)}")
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
                arrAnt = arreglo[1]
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

        if self.titulo == 'Entrega de pedidos por ventana de tiempo':
            collection = conexion_mongo('report').report_pedidoPendientes
            if filtro_lugar:
                pipeline = [{'$unwind': '$sucursal'}]
                pipeline.append({'$match': {f'sucursal.{nivel}': lugar}})
            pipeline.append({'$match': {'prioridad': {'$in': ['ENTREGADO', 'HOY ATRASADO', 'HOY A TIEMPO']}}})
            pipeline.append({'$project': {
                'rango': '$rango', 
                'ENTREGADO': {'$cond': [
                    {'$and': [
                        {'$eq': ['$prioridad', 'ENTREGADO']},
                        {'$eq': [{'$dateToString': {'format': '%Y-%m-%d', 'date': '$fechaEntrega'}}, {'$dateToString': {'format': '%Y-%m-%d', 'date': datetime.now()}}]}
                    ]}, 1, 0]
                },
                'HOY_ATRASADO': {
                    '$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]
                }, 
                'HOY_A_TIEMPO': {
                    '$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]
                }
            }})
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
                    {'name': 'Hoy a tiempo', 'data':serie2, 'color': 'secondary'},
                    {'name': 'Hoy atrasado', 'data':serie3, 'color': 'danger'}
                ])
            else:
                hayResultados = "no"

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}
        # print('Lo que se devuelve desde columnasApiladas es: ' + str({'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}))
        # Return para debugging:
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': pipeline}

    async def CostoPorPedido(self):
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        queryMetodoEnvio = f"and cf.TiendaEnLinea = '{self.filtros.metodoEnvio}'" if self.filtros.metodoEnvio != '' and self.filtros.metodoEnvio != "False" and self.filtros.metodoEnvio != None else ''
        if self.filtros.anio != 0 and self.filtros.anio != None:
            query1Anio = f"and cf.Anio = {self.filtros.anio}"
            query2Anio = f"and Anio = {self.filtros.anio}"
        else:
            query1Anio = query2Anio = ''
        if self.filtros.mes != 0 and self.filtros.mes != None:
            query1Mes = f"and cf.Mes = {self.filtros.mes}"
            query2Mes = f"and Mes = {self.filtros.mes}"
        else:
            query1Mes = query2Mes = ''
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    queryLugar = f""" and ct.tienda = {self.filtros.tienda} """
                    lugar = f"tiendaNombre"
                else:
                    queryLugar = f""" and ct.zona = {self.filtros.zona} """
                    lugar = f"tiendaNombre"
            else:
                queryLugar = f""" and ct.region = {self.filtros.region} """
                lugar = f"zonaNombre"
        else:
            queryLugar = ''
            lugar = f"regionNombre"

        if self.titulo == 'Costos Apilados':
            series = []
            data = []
            query = f"""select * from  DWH.artus.catCostos"""
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            costosReferencia_tmp = crear_diccionario(cursor)
            costosReferencia = {}
            for row in costosReferencia_tmp:
                costosReferencia[row['descripCosto']] = row['Costo']
            pipeline = f"""select {lugar} as lugar, sum(cf.pRH) pedidos, sum(cf.RH) RH, SUM(cf.Envio) Envio, SUM(cf.Combustible) Combustible from dwh.report.consolidadoFinanzas cf 
                left join DWH.artus.catTienda ct on cf.Cebe = ct.tienda 
                left join DWH.dbo.dim_tiempo dt on dt.id_fecha = cf.Anio * 10000 + cf.Mes * 100 + 1
                where Mes <= 12
                {queryMetodoEnvio}
                {query1Anio}
                {query1Mes}
                {queryLugar}
                group by {lugar}
                """
            # print(f"query desde tablas->CostoPorPedido->{self.titulo}->General: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    pedidos = float(row['pedidos'])
                    RH = float(row['RH']) if row['RH'] is not None else 0
                    Envio = float(row['Envio']) if row['Envio'] is not None else 0
                    Combustible = float(row['Combustible']) if row['Combustible'] is not None else 0
                    # print(f"DataSub: {str(dataSub)}")
                    RHxPedido = ((RH + Envio + Combustible) / pedidos) if pedidos != 0 else 0
                    data.append((RHxPedido, row['lugar'])) 
                # Lo ordenas según https://stackoverflow.com/questions/31942169/python-sort-array-of-arrays-by-multiple-conditions
                data = sorted(data)
                # Extraes los datos para las series y las categories
                for tupla in data:
                    series.append(tupla[0])
                    categorias.append(tupla[1])
                series = [
                    {
                        'name': 'Costo de RH por Pedido',
                        'data': series,
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary'
                    }
                ]
            else:
                hayResultados = 'no'
                series = []
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline}


@router.post("/{seccion}")
async def columnas_apiladas (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = ColumnasApiladas(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
