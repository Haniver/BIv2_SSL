from os import pipe
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.formatoFechas import mesTexto
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from copy import deepcopy
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso, crearLog
from inspect import stack

router = APIRouter(
    prefix="/distribucion3d",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Distribucion3D():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

    async def ResultadoRFM(self):
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        data = []
        tituloX = ''
        tituloY = ''
        tituloZ = ''
        minX = 0
        minY = 0
        minZ = 0
        maxX = 0
        maxY = 0
        maxZ = 0
        color = 'primary'
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]
        if self.titulo == '1000 Usuarios con Mayor Monto, vs. Frecuencia y Recencia' or self.titulo == '1000 Usuarios con Menor Monto, vs. Frecuencia y Recencia':
            if self.titulo == '1000 Usuarios con Mayor Monto, vs. Frecuencia y Recencia':
                orden = -1
            else:
                orden = 1
            pipeline.extend([
                {'$project': {
                    'frecuencia': '$cantCompras',
                    'monto': '$montoTotalCompra',
                    'recencia': '$difDias',
                }},
                {'$sort':{'monto': orden}}
            ])
            # print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print('Arreglo desde burbuja3d: '+str(arreglo))
            if len(arreglo) >0:
                hayResultados = "si"
                minX = float('inf')
                minY = float('inf')
                minZ = float('inf')
                maxX = 0
                maxY = 0
                maxZ = 0
                for row in arreglo:
                    frecuencia = row['frecuencia']
                    monto = row['monto']
                    recencia = row['recencia']
                    data.append(
                        [frecuencia, round(monto, 2), recencia]
                    )
                    if float(frecuencia) < minX:
                        minX = frecuencia
                    if float(monto) < minY:
                        minY = monto
                    if float(recencia) < minZ:
                        minZ = recencia
                    if float(frecuencia) > maxX:
                        maxX = frecuencia
                    if float(monto) > maxY:
                        maxY = monto
                    if float(recencia) > maxZ:
                        maxZ = recencia
                color = 'primary'
                tituloX = 'Frecuencia [compras]'
                tituloY = 'Monto [pesos]'
                tituloZ = 'Recencia [días]'

            else:
                hayResultados = "no"

        return  {'hayResultados':hayResultados, 'data':data, 'pipeline': pipeline, 'lenArreglo':len(arreglo), 'color': color, 'tituloX': tituloX, 'tituloY': tituloY, 'tituloZ': tituloZ,  'minX': minX, 'minY': minY, 'minZ': minZ, 'maxX': maxX, 'maxY': maxY, 'maxZ': maxZ}


@router.post("/{seccion}")
async def distribucion_3d (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    crearLog(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        objeto = Distribucion3D(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}