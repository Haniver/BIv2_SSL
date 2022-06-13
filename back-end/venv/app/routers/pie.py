from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/pie",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Pie():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
        self.nivel_lugar = ''
        self.filtro_lugar = False
        self.lugar = ''
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    self.nivel_lugar = 'idTienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    self.nivel_lugar = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                self.nivel_lugar = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False

    async def VentaOmnicanal(self):
        pipeline = []
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}])
        if self.titulo == 'Venta por Canal':
            collection = conexion_mongo('report').report_mktArtusDiario
            pipeline.extend([{'$group': {'_id': None, 'ventaWeb': {'$sum': '$ventaWeb'}, 'ventaAppMovil': {'$sum': '$ventaAppMovil'}, 'ventaCallCenter': {'$sum': '$ventaCallCenter'}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = [
                    {'name': 'App Móvil', 'y': objeto['ventaAppMovil']},
                    {'name': 'Web', 'y': objeto['ventaWeb']},
                    {'name': 'Call Center', 'y': objeto['ventaCallCenter']}
                ]

        if self.titulo == 'Ticket Promedio por Canal':
            collection = conexion_mongo('report').report_mktArtusDiario
            pipeline.extend([{'$group': {'_id': None, 'ventaWeb': {'$sum': '$ventaWeb'}, 'ventaAppMovil': {'$sum': '$ventaAppMovil'}, 'ventaCallCenter': {'$sum': '$ventaCallCenter'}, 'nTicketWeb': {'$sum': '$nTicketWeb'}, 'nTicketAppMovil': {'$sum': '$nTicketAppMovil'}, 'nTicketCallCenter': {'$sum': '$nTicketCallCenter'}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                ticketPromedioWeb = objeto['ventaWeb'] / objeto['nTicketWeb'] if int(objeto['nTicketWeb']) != 0 else 0
                ticketPromedioAppMovil = objeto['ventaAppMovil'] / objeto['nTicketAppMovil'] if int(objeto['nTicketAppMovil']) != 0 else 0
                ticketPromedioCallCenter = objeto['ventaCallCenter'] / objeto['nTicketCallCenter'] if int(objeto['nTicketCallCenter']) != 0 else 0
                res = [
                    {'name': 'App Móvil', 'y': round(ticketPromedioAppMovil, 2)},
                    {'name': 'Web', 'y': round(ticketPromedioWeb, 2)},
                    {'name': 'Call Center', 'y': round(ticketPromedioCallCenter, 2)}
                ]
        return {'hayResultados':hayResultados, 'res': res, 'pipeline':pipeline}

    async def Faltantes(self):
        pipeline = []
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}])
        collection = conexion_mongo('report').report_pedidoFaltantes
        pipeline.extend([{ '$project': {
            '_id': 0,
            'justificados': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, 0, '$registro']},
            'sin_justificar': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, '$registro', 0]}
        }},
        { '$group': {
            '_id': 0,
            'justificados': {'$sum': '$justificados'},
            'sin_justificar': {'$sum': '$sin_justificar'}
        }}])
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=1)
        if len(arreglo) <= 0:
            hayResultados = "no"
            res = pipeline
        else:
            hayResultados = "si"
            objeto = arreglo[0]
            res = [
                {'name': 'Justificados', 'y': objeto['justificados']},
                {'name': 'Sin Justificar', 'y': objeto['sin_justificar']}
            ]
        return {'hayResultados':hayResultados, 'res': res, 'pipeline':pipeline}

    async def Home(self):
        # print("Entrando a Pie Home")
        pipeline = []
        if self.titulo == 'Estatus de Entrega y No Entrega por Área':
            print("Título es Estatus de Entrega y No Entrega por Área")
            collection = conexion_mongo('report').report_pedidoAtrasado
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.idTienda': int(self.filtros.tienda)}}])
            pipeline.append({'$match': {'fechaEntrega': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            if self.filtros.categoria and self.filtros.categoria != "False":
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, '$pedidos', 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, '$pedidos', 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, '$pedidos', 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, '$pedidos', 0]}}})
            pipeline.append({'$group':{'_id':0, 'Entregado_Fuera_tiempo':{'$sum':'$Entregado_Fuera_tiempo'}, 'Entregado_tiempo':{'$sum':'$Entregado_tiempo'}, 'No_entregado_Fuera_tiempo':{'$sum':'$No_entregado_Fuera_tiempo'}, 'No_entregado_tiempo':{'$sum':'$No_entregado_tiempo'}, 'Despachado_Fuera_tiempo':{'$sum':'$Despachado_Fuera_tiempo'}, 'Despachado_tiempo':{'$sum':'$Despachado_tiempo'}}})
            print(str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(str(arreglo))
        if len(arreglo) <= 0:
            print("No hubo resultados")
            hayResultados = "no"
            res = pipeline
        else:
            hayResultados = "si"
            objeto = arreglo[0]
            print('Desde Pie Home: '+str(objeto))
            res = [
                {'name': 'Entregado - Fuera de tiempo', 'y': objeto['Entregado_Fuera_tiempo']},
                {'name': 'Entregado - A tiempo', 'y': objeto['Entregado_tiempo']},
                {'name': 'No entregado - Fuera de tiempo', 'y': objeto['No_entregado_Fuera_tiempo']},
                {'name': 'No entregado - A tiempo', 'y': objeto['No_entregado_tiempo']},
                {'name': 'Despachado - Fuera de tiempo', 'y': objeto['Despachado_Fuera_tiempo']},
                {'name': 'Despachado - A tiempo', 'y': objeto['Despachado_tiempo']}
            ]
        return {'hayResultados':hayResultados, 'res': res, 'pipeline':pipeline}

    async def FoundRate(self):
        # print("Entrando a Pie Home")
        pipeline = []
        if self.titulo == 'Detalle Porcentaje Estatus por Lugar':
            collection = conexion_mongo('report').report_foundRate
            pipeline.append({'$unwind': '$sucursal'})
            pipeline.append({'$match': {'sucursal.tienda': int(self.filtros.tienda)}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$group':{'_id':'$sucursal.tiendaNombre', 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}, 'num_pedidos':{'$sum': '$n_pedido'}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                res = [
                        {'name': 'Completo', 'y':arreglo[0]['COMPLETO']},
                        {'name': 'Incompleto Sin Stock', 'y':arreglo[0]['INC_SIN_STOCK']},
                        {'name': 'Incompleto Sustitutos', 'y':arreglo[0]['INC_SUSTITUTOS']},
                        {'name': 'Incompleto', 'y':arreglo[0]['INCOMPLETO']}
                    ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Estatus de pedidos (Totales)':
            if self.filtros.region != '' and self.filtros.region != "False":
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
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
            if self.filtros.categoria and self.filtros.categoria != "False":
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            pipeline.append({'$group':{'_id':0, 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}}})
            pipeline.append({'$sort':{'_id': 1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) >0:
                hayResultados = "si"
                res = [
                    {'name': 'Completo', 'y': arreglo[0]['COMPLETO']},
                    {'name': 'Incompleto Sin Stock', 'y': arreglo[0]['INC_SIN_STOCK']},
                    {'name': 'Incompleto Sustitutos', 'y': arreglo[0]['INC_SUSTITUTOS']},
                    {'name': 'Incompleto', 'y': arreglo[0]['INCOMPLETO']}
                ]
            else:
                res = []
                hayResultados = "no"

        print(f"Res desde pie -> FoundRate: {str(res)}")
        return {'hayResultados':hayResultados, 'res': res, 'pipeline':pipeline}
        # return {'hayResultados':'no', 'res': '', 'pipeline':''}

@router.post("/{seccion}")
async def pie (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id, seccion):
        objeto = Pie(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}