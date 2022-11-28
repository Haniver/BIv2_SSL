from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import date, datetime, timedelta
from calendar import monthrange
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack

router = APIRouter(
    prefix="/tarjetas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Tarjetas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) - timedelta(seconds=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    self.nivel_lugar = 'tienda'
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
        collection = conexion_mongo('report').report_mktArtusDiario
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}])
    
        if self.titulo == 'Venta Total Tienda en Línea':
            pipeline.extend([{'$group': {'_id': None, 'ventaWeb': {'$sum': '$ventaWeb'}, 'ventaAppMovil': {'$sum': '$ventaAppMovil'}, 'ventaCallCenter': {'$sum': '$ventaCallCenter'}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['ventaAppMovil'] + objeto['ventaCallCenter'] + objeto['ventaWeb']

        if self.titulo == 'Ticket Promedio':
            # $respuesta['totalVenta'] = $totalVenta = $ventaAppMovil + $ventaCallCenter + $ventaWeb;
            # $respuesta['totalTicket'] = $totalTicket = $nTicketAppMovil + $nTicketCallCenter + $nTicketWeb;
            # $respuesta['ticketPromedio'] = $totalVenta / $totalTicket;
            pipeline.extend([{'$group': {'_id': None, 'ventaWeb': {'$sum': '$ventaWeb'}, 'ventaAppMovil': {'$sum': '$ventaAppMovil'}, 'ventaCallCenter': {'$sum': '$ventaCallCenter'}, 'nTicketWeb': {'$sum': '$nTicketWeb'}, 'nTicketAppMovil': {'$sum': '$nTicketAppMovil'}, 'nTicketCallCenter': {'$sum': '$nTicketCallCenter'}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                totalVenta = objeto['ventaAppMovil'] + objeto['ventaCallCenter'] + objeto['ventaWeb']
                totalTicket = objeto['nTicketAppMovil'] + objeto['nTicketCallCenter'] + objeto['nTicketWeb']
                res = totalVenta / totalTicket if totalTicket != 0 else '--'

        if self.titulo == 'Fullfilment Rate':
            # $respuesta['fulfillmentRate'] = $itemsFin / $itemsIni;
            pipeline.extend([{'$group': {'_id': None, 'itemsIni': {'$sum': '$itemsIni'}, 'itemsFin': {'$sum': '$itemsFin'}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['itemsFin'] / objeto['itemsIni'] if objeto['itemsIni'] != 0 else '--'

        if self.titulo == 'Found Rate':
            # $respuesta['foundRate'] = $itemsFound / $itemsIni;
            pipeline.extend([{'$group': {'_id': None, 'itemsIni': {'$sum': '$itemsIni'}, 'itemsFound': {'$sum': '$itemsFound'}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['itemsFound'] / objeto['itemsIni'] if objeto['itemsIni'] != 0 else '--'

        return {'hayResultados':hayResultados, 'res': res, 'pipeline': pipeline}

    async def VentaSinImpuesto(self):
        # Lo que sigue es para crear un arreglo con los canales seleccionados o disponibles
        collectionB = conexion_mongo('report').catCanal
        pipelineB = [{'$match':{'nombreColumna': {'$nin': [None]}}}, {'$match':{'tipo': {'$nin': [0]}}}] # Excluimos la tienda física o los registros que no tengan canal
        if self.filtros.canal != '' and self.filtros.canal != "False" and self.filtros.canal != None:
            pipelineB.append({'$match':{'tipo':int(self.filtros.canal)}})
        pipelineB.append({'$group':{'_id':'$nombreColumna'}})
        cursorB = collectionB.aggregate(pipelineB)
        arregloB = await cursorB.to_list(length=100)
        canales = []
        for fila in arregloB:
            canales.append(fila['_id'])
        collection = conexion_mongo('report').report_ventaDiaria
        pipeline = []
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
            pipeline.append({'$unwind':'$producto'})
            if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                pipeline.append({'$match':{'producto.subDepto': self.filtros.subDepto}})
            else:
                pipeline.append({'$match':{'producto.idDepto': self.filtros.depto}})

        if self.titulo == 'Venta $anio':
            pipeline.append({'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            diccionario_a_agrupar = {'_id':0} # Primer elemento del $group
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal} # Agregar al $group cada canal con la suma de todas sus ventas
            pipeline.append({'$group': diccionario_a_agrupar})
            canales = ['$'+canal for canal in canales] # Crear un arreglo con los canales como llaves
            pipeline.append({'$project': {'venta':{'$add': canales}}}) # Sumar todos los canales (suma de sumas)
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['venta']

        if self.titulo == 'Venta $anioPasado al $dia de $mes':
            fecha_ini = datetime(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
            fecha_fin = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
            pipeline.append({'$match': {'fecha': {'$gte': fecha_ini, '$lte': fecha_fin}}})
            pipeline.append({'$unwind': '$kpi'})
            diccionario_a_agrupar = {'_id':0} # Primer elemento del $group
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal} # Agregar al $group cada canal con la suma de todas sus ventas
            pipeline.append({'$group': diccionario_a_agrupar})
            canales = ['$'+canal for canal in canales] # Crear un arreglo con los canales como llaves
            pipeline.append({'$project': {'venta':{'$add': canales}}}) # Sumar todos los canales (suma de sumas)
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['venta']

        if self.titulo == 'Objetivo $anioActual al $dia de $mes':
            pipeline.append({'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            pipeline.append({'$group':{'_id':0, 'objetivo': {'$sum': '$kpi.objetivoTO'}}}) # Solo se toma en cuenta el objetivo, y no se consideran los filtros de canal
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['objetivo']

        if self.titulo == 'Variación $anioActual vs. $anioAnterior':
            pipeline.append({'$unwind': '$kpi'})
            diccionario_a_agrupar = {'_id':'$fecha'} # Primer elemento del $group
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal} # Agregar al $group cada canal con la suma de todas sus ventas
            pipeline.append({'$group': diccionario_a_agrupar})
            canales = ['$'+canal for canal in canales] # Crear un arreglo con los canales como llaves
            pipeline.append({'$project': {'_id': '$_id', 'venta':{'$add': canales}}}) # Sumar todos los canales (suma de sumas)
            fecha_ini_anterior = datetime(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
            fecha_fin_anterior = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
            pipeline.append({'$facet':{'anio_actual':[{'$match': {'_id': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}, {'$group':{'_id':0, 'venta':{'$sum':'$venta'}}}], 'anio_anterior':[{'$match': {'_id': {'$gte': fecha_ini_anterior, '$lte': fecha_fin_anterior}}}, {'$group':{'_id':0, 'venta':{'$sum':'$venta'}}}]}})

            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)

            if len(arreglo) > 0 and len(arreglo[0]['anio_actual']) >0 and len(arreglo[0]['anio_anterior']) >0:
                hayResultados = "si"
                objeto = arreglo[0]
                venta_actual = float(objeto['anio_actual'][0]['venta'])
                venta_anterior = float(objeto['anio_anterior'][0]['venta'])
                res = (venta_actual/venta_anterior) - 1 if venta_anterior != 0 else '--'
            else:
                hayResultados = "no"
                res = '--'

        if self.titulo == 'Variación Objetivo $anioActual':
            pipeline.append({'$unwind': '$kpi'})
            pipeline.append({'$group':{'_id':'$fecha', 'objetivo': {'$sum': '$kpi.objetivoTO'}}}) # Solo se toma en cuenta el objetivo, y no se consideran los filtros de canal
            fecha_ini_anterior = datetime(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
            fecha_fin_anterior = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
            pipeline.append({'$facet':{'anio_actual':[{'$match': {'_id': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}, {'$group':{'_id':0, 'objetivo':{'$sum':'$objetivo'}}}], 'anio_anterior':[{'$match': {'_id': {'$gte': fecha_ini_anterior, '$lte': fecha_fin_anterior}}}, {'$group':{'_id':0, 'objetivo':{'$sum':'$objetivo'}}}]}})

            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            arreglo[0]

            if len(arreglo) > 0 and len(arreglo[0]['anio_actual']) >0 and len(arreglo[0]['anio_anterior']) >0:
                hayResultados = "si"
                objeto = arreglo[0]
                objetivo_actual  = float(objeto['anio_actual'][0]['objetivo'])
                objetivo_anterior = float(objeto['anio_anterior'][0]['objetivo'])
                res = (objetivo_actual / objetivo_anterior) - 1 if objetivo_anterior != 0 else '--'
            else:
                hayResultados = "no"
                res = '--'

        if self.titulo == 'Venta $mes $anio':
            fecha_ini = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
            pipeline.append({'$match': {'fecha': {'$gte': fecha_ini, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            diccionario_a_agrupar = {'_id':0} # Primer elemento del $group
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal} # Agregar al $group cada canal con la suma de todas sus ventas
            pipeline.append({'$group': diccionario_a_agrupar})
            canales = ['$'+canal for canal in canales] # Crear un arreglo con los canales como llaves
            pipeline.append({'$project': {'venta':{'$add': canales}}}) # Sumar todos los canales (suma de sumas)
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['venta']

        if self.titulo == 'Objetivo $mes $anio':
            fecha_ini = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
            pipeline.append({'$match': {'fecha': {'$gte': fecha_ini, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            pipeline.append({'$group':{'_id':0, 'objetivo': {'$sum': '$kpi.objetivoTO'}}}) # Solo se toma en cuenta el objetivo, y no se consideran los filtros de canal
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['objetivo']

        if self.titulo == 'Proyección $mes $anio':
            fecha_ini = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
            pipeline.append({'$match': {'fecha': {'$gte': fecha_ini, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            diccionario_a_agrupar = {'_id':0} # Primer elemento del $group
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal} # Agregar al $group cada canal con la suma de todas sus ventas
            pipeline.append({'$group': diccionario_a_agrupar})
            canales = ['$'+canal for canal in canales] # Crear un arreglo con los canales como llaves
            pipeline.append({'$project': {'venta':{'$add': canales}}}) # Sumar todos los canales (suma de sumas)
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                dias_en_mes = monthrange(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month)[1]
                dia_del_mes = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day
                res = dias_en_mes*float(objeto['venta'])/dia_del_mes

        if self.titulo == 'Avance $mes $anio':
            fecha_ini = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
            pipeline.append({'$match': {'fecha': {'$gte': fecha_ini, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            # Desde aquí es para la venta del mes
            diccionario_a_agrupar = {'_id':0}
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal}
            pipeline_venta = [{'$group': diccionario_a_agrupar}]
            canales = ['$'+canal for canal in canales]
            pipeline_venta.append({'$project': {'venta':{'$add': canales}}})
            # Desde aquí es para el objetivo
            pipeline_objetivo = [{'$group':{'_id':0, 'objetivo': {'$sum': '$kpi.objetivoTO'}}}]
            # Aquí los juntas los dos
            pipeline.append({'$facet':{'venta':pipeline_venta, 'objetivo':pipeline_objetivo}})
            # print(pipeline)
            # hayResultados = 'no'
            # res = 3.1416
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) > 0 and len(arreglo[0]) > 0 and len(arreglo[0]['venta']) > 0 and len(arreglo[0]['objetivo']) > 0:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['venta'][0]['venta']/objeto['objetivo'][0]['objetivo'] if objeto['objetivo'][0]['objetivo'] != 0 else '--'
            else:
                hayResultados = "no"
                res = '--'

        if self.titulo == 'Alcance $mes $anio':
            fecha_ini = datetime(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
            pipeline.append({'$match': {'fecha': {'$gte': fecha_ini, '$lt': self.fecha_fin_a12}}})
            pipeline.append({'$unwind': '$kpi'})
            # Desde aquí es para la venta del mes
            diccionario_a_agrupar = {'_id':0}
            for canal in canales:
                diccionario_a_agrupar[canal] = {'$sum': '$kpi.'+canal}
            pipeline_venta = [{'$group': diccionario_a_agrupar}]
            canales = ['$'+canal for canal in canales]
            pipeline_venta.append({'$project': {'venta':{'$add': canales}}})
            # Desde aquí es para el objetivo
            pipeline_objetivo = [{'$group':{'_id':0, 'objetivo': {'$sum': '$kpi.objetivoTO'}}}]
            # Aquí los juntas los dos
            pipeline.append({'$facet':{'venta':pipeline_venta, 'objetivo':pipeline_objetivo}})
            # print(pipeline)
            # hayResultados = 'no'
            # res = 3.1416
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) > 0 and len(arreglo[0]) > 0 and len(arreglo[0]['venta']) > 0 and len(arreglo[0]['objetivo']) > 0:
                hayResultados = "si"
                dias_en_mes = monthrange(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month)[1]
                dia_del_mes = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day
                objeto = arreglo[0]
                res = (objeto['venta'][0]['venta']/objeto['objetivo'][0]['objetivo']) - 1 if objeto['objetivo'][0]['objetivo'] != 0 else '--'
            else:
                hayResultados = "no"
                res = '--'
        
        return {'hayResultados':hayResultados, 'res': res, 'pipeline': pipeline}

    async def ResultadoRFM(self):
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]

        if self.titulo == 'Clientes':
            pipeline.extend([
                {'$count': 'clientes'}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                objeto = arreglo[0]
                res = objeto['clientes']

        if self.titulo == '% Clientes Nuevos':
            # print('mesRFM: '+str(self.filtros.mesRFM))
            pipeline.extend([
                {'$facet': {
                    'clientesTotales': [
                        {'$count': 'clientes'},
                    ],
                    'clientesNuevos': [
                        {'$match': {'tipoUsuario': 'Nuevo'}},
                        {'$count': 'clientes'}
                    ]
                }}
            ])
            # print('pipeline desde % Clientes Nuevos en Tarjetas: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo[0]['clientesTotales']) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                totales = arreglo[0]['clientesTotales'][0]['clientes']
                nuevos = arreglo[0]['clientesNuevos'][0]['clientes']
                res = float(nuevos) / float(totales)

        if self.titulo == '% Clientes Recurrentes':
            pipeline.extend([
                {'$facet': {
                    'clientesTotales': [
                        {'$count': 'clientes'},
                    ],
                    'clientesRecurrentes': [
                        {'$match': {'tipoUsuario': 'Recurrente'}},
                        {'$count': 'clientes'}
                    ]
                }}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo[0]['clientesTotales']) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                totales = arreglo[0]['clientesTotales'][0]['clientes']
                nuevos = arreglo[0]['clientesRecurrentes'][0]['clientes']
                res = float(nuevos) / float(totales)

        if self.titulo == 'Ticket Promedio':
            pipeline.extend([
                {'$group': {
                    '_id': 0,
                    'montoTotalCompra': {'$sum': '$montoTotalCompra'},
                    'cantCompras': {'$sum': '$cantCompras'}
                }}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = '--'
            else:
                hayResultados = "si"
                # print(str(arreglo[0]))
                montoTotalCompra = arreglo[0]['montoTotalCompra']
                cantCompras = arreglo[0]['cantCompras']
                res = float(montoTotalCompra) / float(cantCompras)
                # print(str(res))

        return {'hayResultados':hayResultados, 'res': res, 'pipeline': pipeline}

    async def Temporada(self):
        hoyStr = datetime.today().strftime('%Y-%m-%d')
        hoyInt = int(hoyStr[0:4]) * 10000 + int(hoyStr[5:7]) * 100 + int(hoyStr[8:10])
        tituloMod = ''
        res = ''
        hayResultados = 'no'
        query = ''
        hayCanal = False if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '' else True
        if self.titulo == 'Venta Última Hora':
            query = f"""select hora, sum(ventaConImp) venta
                from DWH.report.pedido_hora ph
                where fechaCreacion = '{hoyStr}'
                and hora in (
                    select max(hora)
                    from DWH.report.pedido_hora 
                    where fechaCreacion = '{hoyStr}'
                )
                group by hora
            """
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                tituloMod += f"{self.titulo} (0{arreglo[0]['hora']}:00)" if int(arreglo[0]['hora']) < 10 else f"{self.titulo} ({arreglo[0]['hora']}:00)"
                res = arreglo[0]['venta']

        if self.titulo == 'Pedidos Última Hora':
            query = f"""select hora, sum(pedidos) pedidos
                from DWH.report.pedido_hora ph
                where fechaCreacion = '{hoyStr}'
                and hora in (
                    select max(hora)
                    from DWH.report.pedido_hora 
                    where fechaCreacion = '{hoyStr}'
                )
                group by hora
                """
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                tituloMod += f"{self.titulo} (0{arreglo[0]['hora']}:00)" if int(arreglo[0]['hora']) < 10 else f"{self.titulo} ({arreglo[0]['hora']}:00)"
                res = arreglo[0]['pedidos']

        if self.titulo == 'Venta Hoy':
            query = f"""select sum(ventaSinImpuestos) venta
                from DWH.artus.ventaDiariaHora vdh 
                where fecha = {hoyInt}
                and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
                """
            # print(f"query desde tarjetas.py -> Temporada -> Venta Hoy: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                res = arreglo[0]['venta']

        if self.titulo == '% Participación Venta Hoy':
            query = f"""select sum(ventaSinImpuestos)/(
                    select sum(ventaSinImpuestos)
                    from DWH.artus.ventaDiariaHora vdh 
                    where fecha = {hoyInt}
                    and idCanal in (0)
                ) porc_part
                from DWH.artus.ventaDiariaHora vdh 
                where fecha = {hoyInt}
                and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
                """
            # print(f"query desde tarjetas.py -> Temporada -> % Participación Venta Hoy: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                res = arreglo[0]['porc_part']

        if self.titulo == 'Ticket Promedio (sin imp)':
            query = f"""select sum(nTicket) pedidos, sum(ventaSinImpuestos) venta
            from DWH.artus.ventaDiariaHora vdh
            where fecha = {hoyInt}
            and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
            """
            # print(f"query desde tarjetas.py -> Temporada -> % Participación Venta Hoy: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                res = arreglo[0]['venta']/arreglo[0]['pedidos']

        if self.titulo == 'Artículos Promedio':
            query = f"""select SUM(item) / SUM(nTicket) artPromedio from DWH.artus.ventaDiariaHora vdh
            where fecha = {hoyInt}
            and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
            """
            # print(f"query desde tarjetas.py -> Temporada -> Artículos Promedio: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                # print(f"ARtículos promedio: {arreglo[0]['artPromedio']}")
                res = arreglo[0]['artPromedio']

        return {'hayResultados':hayResultados, 'res': res, 'pipeline': query, 'tituloMod': tituloMod}

@router.post("/{seccion}")
async def tarjetas (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    # print("El usuario desde tarjetas .py es: {str(user)}")
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        objeto = Tarjetas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        try:
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}        

