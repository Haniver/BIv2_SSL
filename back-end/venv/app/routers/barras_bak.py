from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro

router = APIRouter(
    prefix="/barras",
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def barras (filtros: Filtro, titulo: str, seccion: str):
    categorias = []
    series = []
    if seccion == 'FoundRate':

        if titulo == 'Monto Original Vs. Final':
            serie1 = []
            serie2 = []

            if filtros.region != '' and filtros.region != "False" and filtros.region != None:
                filtro_lugar = True
                if filtros.zona != '' and filtros.zona != "False" and filtros.zona != None:
                    nivel = 'zona'
                    siguiente_nivel = 'tiendaNombre'
                    lugar = int(filtros.zona)
                else:
                    nivel = 'region'
                    siguiente_nivel = 'zonaNombre'
                    lugar = int(filtros.region)
            else:
                filtro_lugar = False
                siguiente_nivel = 'regionNombre'
                lugar = ''

            collection = conexion_mongo('report').report_foundRate
            pipeline = [{'$unwind': '$sucursal'}]
            if filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), '$lte': datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ')}}})
            pipeline.append({'$group':{'_id':'$sucursal.'+siguiente_nivel, 'items_ini': {'$sum': '$items_ini'}, 'items_fin': {'$sum': '$items_fin'}, 'items_found': {'$sum': '$items_found'}}})
            pipeline.append({'$project':{'_id':'$_id', 'fulfillment_rate': {'$divide': ['$items_fin', '$items_ini']}, 'found_rate': {'$divide': ['$items_found', '$items_ini']}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['fulfillment_rate'])
                    serie2.append(row['found_rate'])
                series.extend([
                    {'name': 'Fulfillment Rate', 'data':serie1, 'color': 'primary'},                                
                    {'name': 'Found Rate', 'data':serie2, 'color': 'secondary'}
                ])
            else:
                hayResultados = "no"

    return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'categoria':filtros.categoria}

