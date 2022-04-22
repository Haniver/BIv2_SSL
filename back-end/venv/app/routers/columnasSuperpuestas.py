from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/columnasSuperpuestas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class ColumnasSuperpuestas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

    async def ResultadoRFM(self):
        categories = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        serie1 = []
        serie2 = []
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]
        if self.titulo == 'Antigüedad del Cliente Vs. Venta':
            pipeline.extend([
                {'$group': {
                    '_id': '$tipoUsuario',
                    'cantClientes': {'$sum': 1},
                    'revenue': {'$sum': '$montoTotalCompra'}
                }}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categories.append(row['_id'])
                    serie1.append(round(row['revenue'], 2))
                    serie2.append(float(row['cantClientes']))
                series = [
                    {'name': 'Venta', 'data':serie1, 'color':'secondary', 'formato': 'moneda'},
                    {'name': 'Cantidad de clientes', 'data':serie2, 'color':'primary', 'formato': 'entero'}
                ]
            else:
                hayResultados = "no"

        if self.titulo == 'Estatus de Cuenta del Cliente Vs. Venta':
            pipeline.extend([
                {'$group': {
                    '_id': '$tipo',
                    'cantClientes': {'$sum': 1},
                    'revenue': {'$sum': '$montoTotalCompra'}
                }}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categories.append(row['_id'])
                    serie1.append(round(row['revenue'], 2))
                    serie2.append(row['cantClientes'])
                series = [
                    {'name': 'Venta', 'data':serie1, 'color':'secondary', 'formato': 'moneda'},
                    {'name': 'Cantidad de clientes', 'data':serie2, 'color':'primary', 'formato': 'entero'}
                ]
            else:
                hayResultados = "no"

        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'lenArreglo':len(arreglo)}

@router.post("/{seccion}")
async def columnas_superpuestas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = ColumnasSuperpuestas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
