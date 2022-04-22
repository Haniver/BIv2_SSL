from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/barras",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Barras():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def FoundRate(self):
        categorias = []
        series = []

        if self.titulo == 'Monto Original Vs. Final':
            serie1 = []
            serie2 = []

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
            pipeline = [{'$unwind': '$sucursal'}]
            if filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$group':{'_id':'$sucursal.'+siguiente_nivel, 'items_ini': {'$sum': '$items_ini'}, 'items_fin': {'$sum': '$items_fin'}, 'items_found': {'$sum': '$items_found'}}})
            pipeline.append({'$project':{'_id':'$_id', 'fulfillment_rate': {'$divide': ['$items_fin', '$items_ini']}, 'found_rate': {'$divide': ['$items_found', '$items_ini']}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(round((row['fulfillment_rate']), 4))
                    serie2.append(round((row['found_rate']), 4))
                series.extend([
                    {'name': 'Fulfillment Rate', 'data':serie1, 'color': 'primary'},                                
                    {'name': 'Found Rate', 'data':serie2, 'color': 'secondary'}
                ])
            else:
                hayResultados = "no"
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'categoria':self.filtros.categoria}

@router.post("/{seccion}")
async def barras (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = Barras(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}