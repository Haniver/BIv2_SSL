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
    prefix="/areaBasica",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class AreaBasica():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

    async def ResultadoRFM(self):
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        data = []
        categories = []
        tituloY = 'Cantidad de Usuarios'
        tituloX = ''
        color = 'primary'
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]
        if self.titulo == 'Usuarios por Frecuencia':
            pipeline.extend([
                {'$group': {
                    '_id': '$frecuencia', 
                    'usuarios': {
                        '$sum': 1
                    }
                }},
                {'$sort': {'_id': 1}}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde areaBasica: '+str(arreglo))
            categories = ['1-2', '3-5', '6-10', '11-20', '21+']
            color = 'secondary'
            if len(arreglo) >0:
                hayResultados = "si"
                tituloX = 'Frecuencia [pedidos]'
                for row in arreglo:
                    data.append(row['usuarios'])
                # print('data desde AreaBasica: '+str(data))
            else:
                hayResultados = "no"

        if self.titulo == 'Usuarios por Monto':
            pipeline.extend([
                {'$group': {
                    '_id': '$monetario', 
                    'usuarios': {
                        '$sum': 1
                    }
                }},
                {'$sort': {'_id': 1}}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde areaBasica: '+str(arreglo))
            categories = ['$0-$700', '$700-$1,000', '$1,000-$1,500', '$1,500-$2,000', '$2,000+']
            color = 'dark'
            if len(arreglo) >0:
                hayResultados = "si"
                tituloX = 'Monto [pesos]'
                for row in arreglo:
                    data.append(row['usuarios'])
                # print('data desde AreaBasica: '+str(data))
            else:
                hayResultados = "no"

        if self.titulo == 'Usuarios por Recencia':
            pipeline.extend([
                {'$group': {
                    '_id': '$recencia', 
                    'usuarios': {
                        '$sum': 1
                    }
                }},
                {'$sort': {'_id': 1}}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde areaBasica: '+str(arreglo))
            categories = ['0-6', '7-13', '14-20', '21-27', '28-35']
            color = 'primary'
            if len(arreglo) >0:
                hayResultados = "si"
                tituloX = 'Recencia [días]'
                for row in arreglo:
                    data.append(row['usuarios'])
                # print('data desde AreaBasica: '+str(data))
            else:
                hayResultados = "no"

        return  {'hayResultados':hayResultados, 'categories':categories, 'data': data, 'pipeline': pipeline, 'lenArreglo':len(arreglo), 'tituloX': tituloX, 'tituloY': tituloY, 'color': color}


@router.post("/{seccion}")
async def area_basica (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = AreaBasica(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}