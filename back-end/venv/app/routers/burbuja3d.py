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
    prefix="/burbuja3d",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Burbuja3D():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

    async def ResultadoRFM(self):
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        data = []
        categoriesX = []
        categoriesY = []
        tituloX = ''
        tituloY = ''
        color = 'primary'
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]
        if self.titulo == 'Frecuencia por Monto':
            pipeline.extend([
                {'$facet': {
                    'clientesTotales': [
                        {'$count': 'clientes'},
                    ],
                    'categorias': [
                        {'$group': {
                            '_id': {
                                'F': '$frecuencia', 
                                'M': '$monetario'
                            }, 
                            'usuarios': {
                                '$sum': 1
                            }
                        }},
                        {'$sort': {'_id.F': 1, '_id.M': 1}}
                    ]
                }}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde burbuja3d: '+str(arreglo))
            categoriesX = ['$0-$700', '$700-$1,000', '$1,000-$1,500', '$1,500-$2,000', '$2,000+']
            categoriesY = ['1-2', '3-5', '6-10', '11-20', '21+']
            if len(arreglo[0]['clientesTotales']) >0:
                hayResultados = "si"
                clientesTotales = float(arreglo[0]['clientesTotales'][0]['clientes'])
                for row in arreglo[0]['categorias']:
                    data.append([int(row['_id']['M'])-1, int(row['_id']['F'])-1, round((100 * float(row['usuarios']) / clientesTotales), 2)])
                color = 'primary'
                tituloX = 'Monto [pesos]'
                tituloY = 'Frecuencia [compras]'
            else:
                hayResultados = "no"

        if self.titulo == 'Frecuencia por Recencia':
            pipeline.extend([
                {'$facet': {
                    'clientesTotales': [
                        {'$count': 'clientes'},
                    ],
                    'categorias': [
                        {'$group': {
                            '_id': {
                                'F': '$frecuencia', 
                                'R': '$recencia'
                            }, 
                            'usuarios': {
                                '$sum': 1
                            }
                        }},
                        {'$sort': {'_id.F': 1, '_id.M': 1}}
                    ]
                }}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde burbuja3d: '+str(arreglo))
            categoriesX = ['0-6', '7-13', '14-20', '21-27', '28-35']
            categoriesY = ['1-2', '3-5', '6-10', '11-20', '21+']
            if len(arreglo[0]['clientesTotales']) >0:
                hayResultados = "si"
                clientesTotales = float(arreglo[0]['clientesTotales'][0]['clientes'])
                for row in arreglo[0]['categorias']:
                    data.append([int(row['_id']['R'])-1, int(row['_id']['F'])-1, round((100 * float(row['usuarios']) / clientesTotales), 2)])
                color = 'secondary'
                tituloX = 'Recencia [días]'
                tituloY = 'Frecuencia [compras]'
            else:
                hayResultados = "no"

        if self.titulo == 'Recencia por Monto':
            pipeline.extend([
                {'$facet': {
                    'clientesTotales': [
                        {'$count': 'clientes'},
                    ],
                    'categorias': [
                        {'$group': {
                            '_id': {
                                'R': '$recencia', 
                                'M': '$monetario'
                            }, 
                            'usuarios': {
                                '$sum': 1
                            }
                        }},
                        {'$sort': {'_id.F': 1, '_id.M': 1}}
                    ]
                }}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde burbuja3d: '+str(arreglo))
            categoriesX = ['$0-$700', '$700-$1,000', '$1,000-$1,500', '$1,500-$2,000', '$2,000+']
            categoriesY = ['0-6', '7-13', '14-20', '21-27', '28-35']
            if len(arreglo[0]['clientesTotales']) >0:
                hayResultados = "si"
                clientesTotales = float(arreglo[0]['clientesTotales'][0]['clientes'])
                for row in arreglo[0]['categorias']:
                    data.append([int(row['_id']['M'])-1, int(row['_id']['R'])-1, round((100 * float(row['usuarios']) / clientesTotales), 2)])
                color = 'dark'
                tituloX = 'Monto [pesos]'
                tituloY = 'Recencia [días]'
            else:
                hayResultados = "no"

        return  {'hayResultados':hayResultados, 'categoriesX':categoriesX, 'categoriesY':categoriesY, 'data':data, 'pipeline': pipeline, 'lenArreglo':len(arreglo), 'color': color, 'tituloX': tituloX, 'tituloY': tituloY}


@router.post("/{seccion}")
async def burbuja_3d (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id, seccion):
        objeto = Burbuja3D(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}