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
    prefix="/ejesMultiplesApilados",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class EjesMultiplesApilados():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None

    async def Temporada(self):
        categories = []
        yAxis = []
        series = []
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        serie1 = []
        serie2 = []
        serie3 = []
        if self.titulo == 'Pedidos Levantados Hoy':
            hayResultados = 'si'
            print('Entrando a EjesMultiplesApilados - Pedidos LEcantadosHoy')
            yAxis = [
                {'formato': 'entero', 'titulo': 'Pedidos', 'color': 'success', 'opposite': False},
                {'formato': 'moneda', 'titulo': '', 'color': 'primary', 'opposite': True},
                {'formato': 'moneda', 'titulo': 'Pesos', 'color': 'dark', 'opposite': True}
            ]
            series = [
                {'name': 'Entegados a Tiempo', 'data':[387,430,430,385,177,139,466,380,66,627], 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'success'},
                {'name': 'Entregados Fuera de Tiempo', 'data':[356,375,356,410,231,101,228,340,90,366], 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'warning'},
                {'name': 'No Entregados a Tiempo', 'data':[322,453,515,300,123,196,185,368,42,446], 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'info'},
                {'name': 'No Entregados Fuera de Tiempo', 'data':[332,353,550,302,246,189,359,396,74,525], 'type': 'column', 'yAxis': 0, 'formato_tooltip':'entero', 'color':'danger'},
                {'name': 'Venta', 'data':[374832, 207465, 703913, 910591, 751787, 172506, 288074, 661736, 235141, 952214], 'type': 'spline', 'yAxis': 1, 'formato_tooltip':'moneda', 'color':'primary'},
                {'name': 'Ticket Promedio', 'data':[348.18, 365.62, 515.61, 563.31, 456.64, 535.17, 545.61, 594.79, 637.79, 716.98], 'type': 'spline', 'yAxis': 2, 'formato_tooltip':'moneda', 'color':'dark'},
            ]
            categories = [
                '03:00',
                '04:00',
                '05:00',
                '06:00',
                '07:00',
                '08:00',
                '09:00',
                '10:00',
                '11:00',
                '12:00',
            ]

            # collection = conexion_mongo('report').report_foundRate
            # pipeline = [{'$unwind': '$sucursal'}]
            # if filtro_lugar:
            #     pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
            # pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            # pipeline.append({'$group':{'_id': {'fecha_interna': '$fechaUltimoCambio', 'fecha_mostrar': '$descrip_fecha'}, 'pedidos': {'$sum': '$n_pedido'}, 'items_ini': {'$sum': '$items_ini'}, 'items_fin': {'$sum': '$items_fin'}, 'items_found': {'$sum': '$items_found'}}})
            # pipeline.append({'$project':{'_id':0, 'fecha_interna':'$_id.fecha_interna', 'fecha_mostrar':'$_id.fecha_mostrar', 'pedidos': '$pedidos', 'fulfillment_rate': {'$divide': ['$items_fin', '$items_ini']}, 'found_rate': {'$divide': ['$items_found', '$items_ini']}}})
            # pipeline.append({'$sort':{'fecha_interna': 1}})
            # cursor = collection.aggregate(pipeline)
            # arreglo = await cursor.to_list(length=1000)
            # if len(arreglo) >0:
            #     hayResultados = "si"
            #     for row in arreglo:
            #         categories.append(row['fecha_mostrar'])
            #         serie1.append(row['pedidos'])
            #         serie2.append(round(row['fulfillment_rate'],4))
            #         serie3.append(round(row['found_rate'], 4))
            #     series.extend([
            #         {'name': 'Pedidos', 'data':serie1, 'type': 'column', 'formato_tooltip':'entero', 'color':'dark'},
            #         {'name': 'Fulfillment Rate', 'data':serie2, 'type': 'spline', 'formato_tooltip':'porcentaje', 'color':'primary'},
            #         {'name': 'Found Rate', 'data':serie3, 'type': 'spline','formato_tooltip':'porcentaje', 'color':'secondary'}
            #     ])
            # else:
            #     hayResultados = "no"
        print(f"Lo que vamos a regresar desde ejesMultiplesApilados: {str({'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'yAxis': yAxis})}")
        return  {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'yAxis': yAxis}

@router.post("/{seccion}")
async def ejes_multiples_apilados (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = EjesMultiplesApilados(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}