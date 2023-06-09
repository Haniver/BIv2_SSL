from asyncio.windows_events import NULL
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import ddmmyyyy
from datetime import datetime, timedelta, date, time
from calendar import monthrange, monthcalendar
from app.servicios.formatoFechas import mesTexto
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from copy import deepcopy
from numpy import zeros
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack
import json

router = APIRouter(
    prefix="/tablas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Tablas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

        if self.filtros.fechas != None:
            self.fecha_ini = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.max.time()) + timedelta(days=1) - timedelta(seconds=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
        # print('self.fecha_ini = '+str(fecha_ini))
        # print('fecha_fin = '+str(fecha_fin))
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
        data = []
        columns = []
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}}])
        if self.titulo == 'Detalle de Venta por Día':
            collection = conexion_mongo('report').report_mktHybrisDiario
            pipeline.extend([{'$group': {'_id': {'fecha_interna': '$fecha', 'fecha_mostrar': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fecha'}}}, 'pedidos': {'$sum': '$pedidos'}, 'usuarioInvitado': {'$sum': '$usuarioInvitado'}, 'usuarioInscrito': {'$sum': '$usuarioInscrito'}, 'totalUsuario': {'$sum': '$totalUsuario'}, 'vtaSinImp': {'$sum': '$vtaSinImp'}}},
            {'$project': {'fecha_interna': '$_id.fecha_interna', 'fecha_creacion': '$_id.fecha_mostrar', 'pedidos': '$pedidos', 'invitado': '$usuarioInvitado', 'registrado': '$usuarioInscrito', 'total_clientes': '$totalUsuario', 'pedidos_x_cliente': {'$divide': ['$pedidos', '$totalUsuario']}, 'monto_total_venta': '$vtaSinImp', 'ticket_promedio': {'$divide': ['$vtaSinImp', '$pedidos']}}},
            {'$sort': {'fecha_interna': 1}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) <= 0:
                hayResultados = "no"
                
            else:
                hayResultados = "si"
                columns = [
                    {'name': 'Fecha Creación', 'selector':'fecha_creacion', 'formato':'texto'},
                    {'name': 'Pedidos', 'selector':'pedidos', 'formato':'entero'},
                    {'name': 'Invitado', 'selector':'invitado', 'formato':'entero'},
                    {'name': 'Registrado', 'selector':'registrado', 'formato':'entero'},
                    {'name': 'Total Clientes', 'selector':'total_clientes', 'formato':'entero'},
                    {'name': 'Pedidos por Cliente', 'selector':'pedidos_x_cliente', 'formato':'decimales'},
                    {'name': 'Monto Total Venta', 'selector':'monto_total_venta', 'formato':'moneda'},
                    {'name': 'Ticket Promedio', 'selector':'ticket_promedio', 'formato':'moneda'}
                ]
                for dato in arreglo:
                    data.append(
                    # Te falta poner la data. Incluye un campo que sea el formato, como moneda.
                    # Después de eso, en Tabla.js, haz una función que transforme el selector de columns como lo tienes aquí en Python en una función de javascript row => row.selector y agregue el elemento sortable: true
                        {'fecha_creacion': dato['fecha_creacion'],
                        'pedidos': dato['pedidos'],
                        'invitado': dato['invitado'],
                        'registrado': dato['registrado'],
                        'pedidos': dato['pedidos'],
                        'total_clientes': dato['total_clientes'],
                        'pedidos': dato['pedidos'],
                        'pedidos_x_cliente': dato['pedidos_x_cliente'],
                        'monto_total_venta': dato['monto_total_venta'],
                        'ticket_promedio': dato['ticket_promedio']
                        })

        if self.titulo == 'Venta Top 200 Proveedores':
            collection = conexion_mongo('report').report_mktProveedores
            pipeline.extend([
                {'$unwind': '$articulo'},
                {'$group': {'_id': {'id': '$articulo.proveedor', 'nombre': '$articulo.proveedorNombre'}, 'monto': {'$sum': '$vtaSinImp'}}},
                {'$project': {'_id':0, 'id': '$_id.id', 'nombre': '$_id.nombre', 'monto': '$monto'}},
                {'$sort': {'monto': -1}},
                { '$limit': 200 }
            ])
            # print(f"Pipeline desde Tablas -> Venta Top 200 Proveedores: {str(pipeline)}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) <= 0:
                hayResultados = "no"
                
            else:
                hayResultados = "si"
                columns = [
                    {'name': 'lugar', 'selector':'lugar', 'formato':'entero'},
                    {'name': 'Nombre Proveedor', 'selector':'nombre', 'formato':'texto', 'ancho': '380px'},
                    {'name': 'ID Proveedor', 'selector':'id', 'formato':'entero'},
                    {'name': 'Monto Venta', 'selector':'monto', 'formato':'moneda'}
                ]
                lugar = 1
                for dato in arreglo:
                    nombre = dato['nombre'] if 'nombre' in dato and dato['nombre'] != '' and dato['nombre'] is not None else '--'
                    id = dato['id'] if 'id' in dato and dato['id'] != '' and dato['id'] is not None else '--'
                    monto = dato['monto'] if 'monto' in dato and dato['monto'] != '' and dato['monto'] is not None else '--'
                    data.append(
                        {'lugar': lugar,
                        'nombre': nombre,
                        'id': id,
                        'monto': monto
                    })
                    lugar += 1

        if self.titulo == 'Top 1,000 SKU':
            collection = conexion_mongo('report').report_mktProveedores
            pipeline.append({'$unwind': '$articulo'})
            if self.filtros.proveedor != 0 and self.filtros.proveedor != 1 and self.filtros.proveedor != None:
                pipeline.append({'$match': {'articulo.proveedor': self.filtros.proveedor}})
            pipeline.extend([
                {'$group': {'_id': {'sku': '$articulo.sku', 'descripcion': '$articulo.skuNombre', 'depto': '$articulo.deptoNombre', 'subDepto': '$articulo.subdeptoNombre', 'clase': '$articulo.claseNombre', 'subClase': '$articulo.subClaseNombre'}, 'monto': {'$sum': '$vtaSinImp'}, 'cantidad': {'$sum': '$cant'}}},
                {'$project': {'_id': 0, 'sku': '$_id.sku', 'descripcion': '$_id.descripcion', 'depto': '$_id.depto', 'subDepto': '$_id.subDepto', 'clase': '$_id.clase', 'subClase': '$_id.subClase', 'monto': '$monto', 'cantidad': '$cantidad'}},
                {'$sort': {'monto': -1}},
                { '$limit': 1000 }
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) <= 0:
                hayResultados = "no"
                
            else:
                hayResultados = "si"
                columns = [
                    {'name': 'lugar', 'selector':'lugar', 'formato':'entero'},
                    {'name': 'SKU', 'selector':'sku', 'formato':'entero'},
                    {'name': 'Descripción', 'selector':'descripcion', 'formato':'texto', 'ancho': '400px'},
                    {'name': 'Departamento', 'selector':'depto', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Sub-Departamento', 'selector':'subDepto', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Clase', 'selector':'clase', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Sub-Clase', 'selector':'subClase', 'formato':'texto', 'ancho': '300px'},
                    {'name': 'Cantidad', 'selector':'cantidad', 'formato':'entero'},
                    {'name': 'Monto', 'selector':'monto', 'formato':'moneda'}
                ]
                lugar = 1
                for dato in arreglo:
                    data.append({
                        'lugar': lugar,
                        'sku': dato['sku'],
                        'descripcion': dato['descripcion'],
                        'depto': dato['depto'],
                        'subDepto': dato['subDepto'],
                        'clase': dato['clase'],
                        'subClase': dato['subClase'],
                        'cantidad': dato['cantidad'],
                        'monto': dato['monto']
                    })
                    lugar += 1

        if self.titulo == 'Venta por día':
            collection = conexion_mongo('report').report_mktProveedores
            pipeline.append({'$unwind': '$articulo'})
            if self.filtros.proveedor != 0 and self.filtros.proveedor != 1 and self.filtros.proveedor != None:
                pipeline.append({'$match': {'articulo.proveedor': self.filtros.proveedor}})
            pipeline.extend([
                {'$group': {'_id': {'fecha_interna': '$fecha', 'fecha_mostrar': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fecha'}}}, 'pedidos': {'$sum': 1}, 'monto': {'$sum': '$vtaSinImp'}}},
                {'$project': {'_id': 0, 'fecha_interna': '$_id.fecha_interna', 'fecha_mostrar': '$_id.fecha_mostrar', 'pedidos': '$pedidos', 'monto': '$monto', 'ticket_promedio': {'$divide': ['$monto', '$pedidos']}}},
                {'$sort': {'fecha_interna': 1}}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) <= 0:
                hayResultados = "no"
            else:
                hayResultados = "si"
                columns = [
                    {'name': 'Fecha', 'selector':'fecha_mostrar', 'formato':'texto'},
                    {'name': 'Pedidos', 'selector':'pedidos', 'formato':'entero'},
                    {'name': 'Monto', 'selector':'monto', 'formato':'moneda'},
                    {'name': 'Ticket Promedio', 'selector':'ticket_promedio', 'formato':'moneda'}
                ]
                for dato in arreglo:
                    data.append({
                        'fecha_mostrar': dato['fecha_mostrar'],
                        'pedidos': dato['pedidos'],
                        'monto': dato['monto'],
                        'ticket_promedio': dato['ticket_promedio']
                    })
        # print(f"Se va a regresar pipeline desde Tablas -> VentaOmnicanal2: {str(pipeline)}")
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}


    async def FoundRate(self):
        pipeline = []
        data = []
        columns = []
        if self.titulo == 'Detalle Porcentaje Estatus por Lugar':
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    nivel = 'zona'
                    siguiente_nivel = 'tiendaNombre'
                    self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    siguiente_nivel = 'zonaNombre'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                siguiente_nivel = 'regionNombre'
                self.lugar = ''

            collection = conexion_mongo('report').report_foundRate
            pipeline.append({'$unwind': '$sucursal'})
            if self.filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: self.lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}})
            pipeline.append({'$group':{'_id':'$sucursal.'+siguiente_nivel, 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}, 'num_pedidos':{'$sum': '$n_pedido'}}})
            pipeline.append({'$project':{'_id':0, 'lugar':'$_id', 'COMPLETO': {'$divide':['$COMPLETO', '$num_pedidos']}, 'INC_SIN_STOCK': {'$divide':['$INC_SIN_STOCK', '$num_pedidos']}, 'INC_SUSTITUTOS': {'$divide':['$INC_SUSTITUTOS', '$num_pedidos']}, 'INCOMPLETO': {'$divide':['$INCOMPLETO', '$num_pedidos']}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'lugar': dato['lugar'],
                        'COMPLETO': dato['COMPLETO'],
                        'INC_SIN_STOCK': dato['INC_SIN_STOCK'],
                        'INC_SUSTITUTOS': dato['INC_SUSTITUTOS'],
                        'INCOMPLETO': dato['INCOMPLETO']
                    })
                columns = [
                        {'name': 'lugar', 'selector':'lugar', 'formato':'texto', 'ancho': '350px'},
                        {'name': 'Completo', 'selector':'COMPLETO', 'formato':'porcentaje'},
                        {'name': 'Incompleto Sin Stock', 'selector':'INC_SIN_STOCK', 'formato':'porcentaje'},
                        {'name': 'Incompleto Sustitutos', 'selector':'INC_SUSTITUTOS', 'formato':'porcentaje'},
                        {'name': 'Incompleto', 'selector':'INCOMPLETO', 'formato':'porcentaje'}
                    ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Estatus por Tienda':
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''

            collection = conexion_mongo('report').report_foundRate
            pipeline.append({'$unwind': '$sucursal'})
            if self.filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: self.lugar}})
            pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}})
            pipeline.append({'$group':{'_id':'$sucursal.tiendaNombre', 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}, 'num_pedidos':{'$sum': '$n_pedido'}}})
            pipeline.append({'$project':{'_id':0, 'Lugar':'$_id', 'COMPLETO': '$COMPLETO', 'INC_SIN_STOCK': '$INC_SIN_STOCK', 'INC_SUSTITUTOS': '$INC_SUSTITUTOS', 'INCOMPLETO': '$INCOMPLETO', 'COMPLETO_porc': {'$divide':['$COMPLETO', '$num_pedidos']}, 'INC_SIN_STOCK_porc': {'$divide':['$INC_SIN_STOCK', '$num_pedidos']}, 'INC_SUSTITUTOS_porc': {'$divide':['$INC_SUSTITUTOS', '$num_pedidos']}, 'INCOMPLETO_porc': {'$divide':['$INCOMPLETO', '$num_pedidos']}}})
            pipeline.append({'$sort':{'COMPLETO':-1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'Lugar': dato['Lugar'],
                        'COMPLETO': dato['COMPLETO'],
                        'COMPLETO_porc': dato['COMPLETO_porc'],
                        'INC_SIN_STOCK': dato['INC_SIN_STOCK'],
                        'INC_SIN_STOCK_porc': dato['INC_SIN_STOCK_porc'],
                        'INC_SUSTITUTOS': dato['INC_SUSTITUTOS'],
                        'INC_SUSTITUTOS_porc': dato['INC_SUSTITUTOS_porc'],
                        'INCOMPLETO': dato['INCOMPLETO'],
                        'INCOMPLETO_porc': dato['INCOMPLETO_porc']
                    })
                columns = [
                        {'name': 'Lugar', 'selector':'Lugar', 'formato':'texto', 'ancho': '350px'},
                        {'name': 'Cant. Completo', 'selector':'COMPLETO', 'formato':'entero'},
                        {'name': '% Completo', 'selector':'COMPLETO_porc', 'formato':'porcentaje'},
                        {'name': 'Cant. Incompleto Sin Stock', 'selector':'INC_SIN_STOCK', 'formato':'entero'},
                        {'name': '% Incompleto Sin Stock', 'selector':'INC_SIN_STOCK_porc', 'formato':'porcentaje'},
                        {'name': 'Cant. Incompleto Sustitutos', 'selector':'INC_SUSTITUTOS', 'formato':'entero'},
                        {'name': '% Incompleto Sustitutos', 'selector':'INC_SUSTITUTOS_porc', 'formato':'porcentaje'},
                        {'name': 'Cant. Incompleto', 'selector':'INCOMPLETO', 'formato':'entero'},
                        {'name': '% Incompleto', 'selector':'INCOMPLETO_porc', 'formato':'porcentaje'}
                    ]
            else:
                hayResultados = 'no'

        # if self.titulo == 'Tiendas Top 20 Estatus Incompleto':
        #     if self.filtros.region != '' and self.filtros.region != "False":
        #         self.filtro_lugar = True
        #         if self.filtros.zona != '' and self.filtros.zona != "False":
        #             nivel = 'zona'
        #             self.lugar = int(self.filtros.zona)
        #         else:
        #             nivel = 'region'
        #             self.lugar = int(self.filtros.region)
        #     else:
        #         self.filtro_lugar = False
        #         self.lugar = ''

        #     collection = conexion_mongo('report').report_foundRate
        #     pipeline.append({'$unwind': '$sucursal'})
        #     if self.filtro_lugar:
        #         pipeline.append({'$match': {'sucursal.'+ nivel: self.lugar}})
        #     pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}})
        #     pipeline.append({'$group':{'_id':'$sucursal.tiendaNombre', 'COMPLETO': {'$sum': '$COMPLETO'}, 'INC_SIN_STOCK': {'$sum': '$INC_SIN_STOCK'}, 'INC_SUSTITUTOS': {'$sum': '$INC_SUSTITUTOS'}, 'INCOMPLETO': {'$sum': '$INCOMPLETO'}, 'num_pedidos':{'$sum': '$n_pedido'}}})
        #     pipeline.append({'$project':{'_id':0, 'lugar':'$_id', 'COMPLETO': {'$divide':['$COMPLETO', '$num_pedidos']}, 'INC_SIN_STOCK': {'$divide':['$INC_SIN_STOCK', '$num_pedidos']}, 'INC_SUSTITUTOS': {'$divide':['$INC_SUSTITUTOS', '$num_pedidos']}, 'INCOMPLETO': {'$divide':['$INCOMPLETO', '$num_pedidos']}}})
        #     pipeline.append({'$sort':{'INCOMPLETO':-1}})
        #     cursor = collection.aggregate(pipeline)
        #     arreglo = await cursor.to_list(length=None)
        #     if len(arreglo) >0:
        #         hayResultados = "si"
        #         for dato in arreglo:
        #             data.append({
        #                 'lugar': dato['lugar'],
        #                 'COMPLETO': dato['COMPLETO'],
        #                 'INC_SIN_STOCK': dato['INC_SIN_STOCK'],
        #                 'INC_SUSTITUTOS': dato['INC_SUSTITUTOS'],
        #                 'INCOMPLETO': dato['INCOMPLETO']
        #             })
        #         columns = [
        #                 {'name': 'lugar', 'selector':'lugar', 'formato':'texto', 'ancho': '350px'},
        #                 {'name': 'Completo', 'selector':'COMPLETO', 'formato':'porcentaje'},
        #                 {'name': 'Incompleto Sin Stock', 'selector':'INC_SIN_STOCK', 'formato':'porcentaje'},
        #                 {'name': 'Incompleto Sustitutos', 'selector':'INC_SUSTITUTOS', 'formato':'porcentaje'},
        #                 {'name': 'Incompleto', 'selector':'INCOMPLETO', 'formato':'porcentaje'}
        #             ]
        #     else:
        #         hayResultados = 'no'

        if self.titulo == 'Detalle de Pedidos Tienda':
            collection = conexion_mongo('report').report_detallePedidos
            pipeline = [
                {'$match': {
                    'idtienda': int(self.filtros.tienda)
                }},
                {'$match': {
                    'fechaFR': {
                        '$gte': self.fecha_ini, 
                        '$lt': self.fecha_fin
                    }
                }},
                {'$project': {
                    'fechaFR': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaFR'}},
                    'ultimoCambio': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$ultimoCambio'}},
                    'idtienda': '$idtienda',
                    'nPedido': '$nPedido',
                    'nConsigna': '$nConsigna',
                    'fechaCreacion': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaCreacion'}},
                    'estatus': '$estatus',
                    'items_ini': '$items_ini',
                    'items_fin': '$items_fin',
                }},
                {'$sort': {
                    'fechaFR': -1
                }}
            ]
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    fechaFR = dato['fechaFR'] if 'fechaFR' in dato else '--'
                    ultimoCambio = dato['ultimoCambio'] if 'ultimoCambio' in dato else '--'
                    idtienda = dato['idtienda'] if 'idtienda' in dato else '--'
                    nPedido = dato['nPedido'] if 'nPedido' in dato else '--'
                    nConsigna = dato['nConsigna'] if 'nConsigna' in dato else '--'
                    fechaCreacion = dato['fechaCreacion'] if 'fechaCreacion' in dato else '--'
                    estatus = dato['estatus'] if 'estatus' in dato else '--'
                    items_ini = dato['items_ini'] if 'items_ini' in dato else '--'
                    items_fin = dato['items_fin'] if 'items_fin' in dato else '--'
                    data.append({
                        'fechaFR': fechaFR,
                        'ultimoCambio': ultimoCambio,
                        'idtienda': idtienda,
                        'nPedido': nPedido,
                        'nConsigna': nConsigna,
                        'fechaCreacion': fechaCreacion,
                        'estatus': estatus,
                        'items_ini': items_ini,
                        'items_fin': items_fin
                    })
                columns = [
                        {'name': 'Fecha', 'selector':'fechaFR', 'formato':'texto'},
                        {'name': 'Último Cambio', 'selector':'ultimoCambio', 'formato':'texto'},
                        {'name': 'No. de Tienda', 'selector':'idtienda', 'formato':'entero'},
                        {'name': 'No. de Orden', 'selector':'nPedido', 'formato':'sinComas'},
                        {'name': 'No. de Consigna', 'selector':'nConsigna', 'formato':'texto'},
                        {'name': 'Fecha Creación', 'selector':'fechaCreacion', 'formato':'texto'},
                        {'name': 'Estatus', 'selector':'estatus', 'formato':'texto'},
                        {'name': 'Items Ini', 'selector':'items_ini', 'formato':'entero'},
                        {'name': 'Items Fin', 'selector':'items_fin', 'formato':'entero'}
                    ]
            else:
                hayResultados = 'no'

        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}


    async def PedidosPendientes(self):
        pipeline = []
        data = []
        columns = []
        filtroHoy = {
            '$match': {
                'prioridad': {
                    '$ne': 'Futuro'
                }
            }
        }
        if self.titulo == 'Tiendas con Pedidos Atrasados Mayores a 1 Día':
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''

            collection = conexion_mongo('report').report_pedidoPendientes
            pipeline.extend([{'$unwind': '$sucursal'}, filtroHoy])
            if self.filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: self.lugar}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$match': {'prioridad': {'$in': ['2 DIAS','ANTERIORES']}}})
            pipeline.append({'$group': {'_id': {'region': '$sucursal.regionNombre', 'zona': '$sucursal.zonaNombre', 'tienda': '$sucursal.tiendaNombre'}, 'pedidos': {'$sum': 1}, 'fechaEntrega': {'$min':'$fechaEntrega'}}})
            pipeline.append({'$sort': {'pedidos': -1}})
            # print(f"Pipeline desde Tablas -> Tiendas con Pedidos Atrasados Mayores a 1 Día: {str(pipeline)}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            data = []
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    if 'region' in dato['_id']:
                        data.append({
                            'region': dato['_id']['region'],
                            'zona': dato['_id']['zona'],
                            'tienda': dato['_id']['tienda'],
                            'pedidos': dato['pedidos'],
                            'fecha': ddmmyyyy(dato['fechaEntrega'])
                        })
                    else:
                        data.append({
                            'region': '--',
                            'zona': '--',
                            'tienda': '--',
                            'pedidos': dato['pedidos'],
                            'fecha': ddmmyyyy(dato['fechaEntrega'])
                        })
            else:
                hayResultados = 'no'
            columns = [
                    {'name': 'Región', 'selector':'region', 'formato':'texto', 'ancho': '220px'},
                    {'name': 'Zona', 'selector':'zona', 'formato':'texto', 'ancho': '220px'},
                    {'name': 'Tienda', 'selector':'tienda', 'formato':'texto', 'ancho': '420px'},
                    {'name': 'Pedidos', 'selector':'pedidos', 'formato':'entero'},
                    {'name': 'Fecha', 'selector':'fecha', 'formato':'texto', 'ancho': '110px'}
                ]

        if self.titulo == 'Detalle de pedidos tienda $tienda':
            collection = conexion_mongo('report').report_pedidoPendientes
            pipeline.extend([{'$unwind': '$sucursal'}, filtroHoy])
            pipeline.append({'$match': {'sucursal.idTienda': self.lugar}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})
            pipeline.extend([{'$project': {
                'Tienda': '$sucursal.tiendaNombre',
                'NumOrden': '$pedido',
                'Consigna': '$consigna',
                'Prioridad': '$prioridad',
                'FechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}}
            }}, {'$sort': 
                {'Consigna': 1}
            }])
            # print(f"Pipeline desde Tablas -> PedidosPendientes -> {self.titulo}: {pipeline}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            data = []
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'Tienda': dato['Tienda'],
                        'NumOrden': dato['NumOrden'],
                        'Consigna': dato['Consigna'],
                        'Prioridad': dato['Prioridad'],
                        'FechaEntrega': dato['FechaEntrega']
                    })
            else:
                hayResultados = 'no'
            columns = [
                    {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '420px'},
                    {'name': 'NumOrden', 'selector':'NumOrden', 'formato':'entero'},
                    {'name': 'Consigna', 'selector':'Consigna', 'formato':'texto', 'ancho': '150px'},
                    {'name': 'Prioridad', 'selector':'Prioridad', 'formato':'texto', 'ancho': '150px'},
                    {'name': 'Fecha', 'selector':'FechaEntrega', 'formato':'texto', 'ancho': '110px'}
                ]
        if self.titulo == 'Detalle Pedidos Pendientes por Tienda':
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        nivel = 'idtienda'
                        self.lugar = int(self.filtros.tienda)
                    else:
                        nivel = 'zona'
                        self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''
            collection = conexion_mongo('report').report_pedidoPendientes # este era 48 horas
            pipeline = [{'$unwind': '$sucursal'}]
            if self.filtro_lugar:
                pipeline.append(
                    {'$match': {f'sucursal.{nivel}': self.lugar}}
                )
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})
            pipeline.extend([{'$project': {
                'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                'regionNombre': '$sucursal.regionNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'Entregado': {'$cond': [{'$eq': ["$Estatus_Consigna","Entregado"]}, 1, 0]},
                'PagoPendiente': {'$cond': [{'$eq': ["$Estatus_Consigna","Pago pendiente"]}, 1, 0]},
                'PendienteDeAuditoria': {'$cond': [{'$eq': ["$Estatus_Consigna","Pendiente de auditoría"]}, 1, 0]},
                'PickeadoPorFacturar': {'$cond': [{'$eq': ["$Estatus_Consigna","Pickeado por facturar"]}, 1, 0]},
                'EnPicking': {'$cond': [{'$eq': ["$Estatus_Consigna","En picking"]}, 1, 0]},
                'ListoParaRetirar': {'$cond': [{'$eq': ["$Estatus_Consigna","Listo para retirar"]}, 1, 0]},
                'ListoParaEnviar': {'$cond': [{'$eq': ["$Estatus_Consigna","Listo para enviar"]}, 1, 0]},
                'PendientePicking': {'$cond': [{'$eq': ["$Estatus_Consigna","Pendiente picking"]}, 1, 0]},
                'AuditoríaRechazada': {'$cond': [{'$eq': ["$Estatus_Consigna","Auditoría rechazada"]}, 1, 0]},
                'Despachado': {'$cond': [{'$eq': ["$Estatus_Consigna","Despachado"]}, 1, 0]},
                'AReprogramarEntrega': {'$cond': [{'$eq': ["$Estatus_Consigna","A reprogramar entrega"]}, 1, 0]},
                'SD': {'$cond': [{'$eq': ["$Estatus_Consigna","S/D"]}, 1, 0]},
                'HoyATiempo': {'$cond': [{'$eq': ["$prioridad","HOY A TIEMPO"]}, 1, 0]},
                'Atrasado': {'$cond': [{'$eq': ["$prioridad","HOY ATRASADO"]}, 1, 0]},
                'UnDia': {'$cond': [{'$eq': ["$prioridad","1 DIA"]}, 1, 0]},
                'DosDias': {'$cond': [{'$eq': ["$prioridad","2 DIAS"]}, 1, 0]},
                'Anteriores': {'$cond': [{'$eq': ["$prioridad","ANTERIORES"]}, 1, 0]},
                }},
                {'$group': {
                    '_id': {
                        'fechaEntrega': '$fechaEntrega',
                        'regionNombre': '$regionNombre',
                        'zonaNombre': '$zonaNombre',
                        'tiendaNombre': '$tiendaNombre',
                    },
                    'Entregado': {'$sum': '$Entregado'},
                    'PagoPendiente': {'$sum': '$PagoPendiente'},
                    'PendienteDeAuditoria': {'$sum': '$PendienteDeAuditoria'},
                    'PickeadoPorFacturar': {'$sum': '$PickeadoPorFacturar'},
                    'EnPicking': {'$sum': '$EnPicking'},
                    'ListoParaRetirar': {'$sum': '$ListoParaRetirar'},
                    'ListoParaEnviar': {'$sum': '$ListoParaEnviar'},
                    'PendientePicking': {'$sum': '$PendientePicking'},
                    'AuditoríaRechazada': {'$sum': '$AuditoríaRechazada'},
                    'Despachado': {'$sum': '$Despachado'},
                    'AReprogramarEntrega': {'$sum': '$AReprogramarEntrega'},
                    'SD': {'$sum': '$SD'},
                    'HoyATiempo': {'$sum': '$HoyATiempo'},
                    'Atrasado': {'$sum': '$Atrasado'},
                    'UnDia': {'$sum': '$UnDia'},
                    'DosDias': {'$sum': '$DosDias'},
                    'Anteriores': {'$sum': '$Anteriores'}
                }},
                {'$project': {
                    'fechaEntrega': '$_id.fechaEntrega',
                    'fechaOrdenar': {
                        '$dateFromString': {
                            'dateString': '$_id.fechaEntrega',
                            'format': "%d/%m/%Y"
                    }},
                    'regionNombre': '$_id.regionNombre',
                    'zonaNombre': '$_id.zonaNombre',
                    'tiendaNombre': '$_id.tiendaNombre',
                    'Entregado': {'$sum': '$Entregado'},
                    'PagoPendiente': {'$sum': '$PagoPendiente'},
                    'PendienteDeAuditoria': {'$sum': '$PendienteDeAuditoria'},
                    'PickeadoPorFacturar': {'$sum': '$PickeadoPorFacturar'},
                    'EnPicking': {'$sum': '$EnPicking'},
                    'ListoParaRetirar': {'$sum': '$ListoParaRetirar'},
                    'ListoParaEnviar': {'$sum': '$ListoParaEnviar'},
                    'PendientePicking': {'$sum': '$PendientePicking'},
                    'AuditoríaRechazada': {'$sum': '$AuditoríaRechazada'},
                    'Despachado': {'$sum': '$Despachado'},
                    'AReprogramarEntrega': {'$sum': '$AReprogramarEntrega'},
                    'SD': {'$sum': '$SD'},
                    'HoyATiempo': {'$sum': '$HoyATiempo'},
                    'Atrasado': {'$sum': '$Atrasado'},
                    'UnDia': {'$sum': '$UnDia'},
                    'DosDias': {'$sum': '$DosDias'},
                    'Anteriores': {'$sum': '$Anteriores'}
                }},
                {'$sort': {'fechaOrdenar': 1, 'regionNombre': 1, 'zonaNombre': 1, 'tiendaNombre': 1}}
            ])
            # print(f"Pipeline desde Tablas -> PedidosPendientes -> {self.titulo}: {pipeline}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            # print(f"Arreglo desde Tablas -> PedidosPendientes -> {self.titulo}: {arreglo}")
            data = []
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'fechaEntrega': dato['_id']['fechaEntrega'],
                        'regionNombre': dato['_id']['regionNombre'],
                        'zonaNombre': dato['_id']['zonaNombre'],
                        'tiendaNombre': dato['_id']['tiendaNombre'],
                        'Entregado': int(dato['Entregado']),
                        'PagoPendiente': int(dato['PagoPendiente']),
                        'PendienteDeAuditoria': int(dato['PendienteDeAuditoria']),
                        'PickeadoPorFacturar': int(dato['PickeadoPorFacturar']),
                        'EnPicking': int(dato['EnPicking']),
                        'ListoParaRetirar': int(dato['ListoParaRetirar']),
                        'ListoParaEnviar': int(dato['ListoParaEnviar']),
                        'PendientePicking': int(dato['PendientePicking']),
                        'AuditoríaRechazada': int(dato['AuditoríaRechazada']),
                        'Despachado': int(dato['Despachado']),
                        'AReprogramarEntrega': int(dato['AReprogramarEntrega']),
                        'HoyATiempo': int(dato['HoyATiempo']),
                        'Atrasado': int(dato['Atrasado']),
                        'UnDia': int(dato['UnDia']),
                        'DosDias': int(dato['DosDias']),
                        'Anteriores': int(dato['Anteriores']),
                        'SD': int(dato['SD']),
                        # 'Total': int(dato['Entregado']) + int(dato['PagoPendiente']) + int(dato['PendienteDeAuditoria']) + int(dato['PickeadoPorFacturar'] + int(dato['EnPicking']) + int(dato['ListoParaRetirar']) + int(dato['ListoParaEnviar']) + int(dato['PendientePicking']) + int(dato['AuditoríaRechazada']) + int(dato['Despachado']) + int(dato['AReprogramarEntrega']) + int(dato['SD']))
                        'Total': int(dato['HoyATiempo']) + int(dato['Atrasado']) + int(dato['UnDia']) + int(dato['DosDias'] + int(dato['Anteriores']))
                    })
            else:
                hayResultados = 'no'
            columns = [
                    {'name': 'Fecha de Entrega', 'selector':'fechaEntrega', 'formato':'texto'},
                    {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho': '360px'},
                    {'name': 'Hoy a Tiempo', 'selector':'HoyATiempo', 'formato':'entero'},
                    {'name': 'Atrasado', 'selector':'Atrasado', 'formato':'entero'},
                    {'name': 'Un Día', 'selector':'UnDia', 'formato':'entero'},
                    {'name': 'Dos Días', 'selector':'DosDias', 'formato':'entero'},
                    {'name': 'Anteriores', 'selector':'Anteriores', 'formato':'entero'},
                    {'name': 'S/D', 'selector':'SD', 'formato':'entero'},
                    {'name': 'Pago Pendiente', 'selector':'PagoPendiente', 'formato':'entero', 'ancho': '110px'},
                    {'name': 'Pendiente picking', 'selector':'PendientePicking', 'formato':'entero'},
                    {'name': 'En Picking', 'selector':'EnPicking', 'formato':'entero'},
                    {'name': 'Pendiente de Auditoría', 'selector':'PendienteDeAuditoria', 'formato':'entero'},
                    {'name': 'Pickeado por Facturar', 'selector':'PickeadoPorFacturar', 'formato':'entero'},
                    {'name': 'Auditoría Rechazada', 'selector':'AuditoríaRechazada', 'formato':'entero'},
                    {'name': 'A Reprogramar Entrega', 'selector':'AReprogramarEntrega', 'formato':'entero'},
                    {'name': 'Listo Para Retirar', 'selector':'ListoParaRetirar', 'formato':'entero'},
                    {'name': 'Listo Para Enviar', 'selector':'ListoParaEnviar', 'formato':'entero'},
                    {'name': 'Despachado', 'selector':'Despachado', 'formato':'entero'},
                    {'name': 'Entregado', 'selector':'Entregado', 'formato':'entero'},
                    {'name': 'Total', 'selector':'Total', 'formato':'entero'}
                ]
        if self.titulo == 'Pedidos No Entregados o No Cancelados Tienda $tienda':
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        nivel = 'idtienda'
                        self.lugar = int(self.filtros.tienda)
                    else:
                        nivel = 'zona'
                        self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''
            collection = conexion_mongo('report').report_pedidoPendientes # este era 48 horas
            pipeline = [{'$unwind': '$sucursal'}]
            if self.filtro_lugar:
                pipeline.append(
                    {'$match': {f'sucursal.{nivel}': self.lugar}}
                )
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})
            pipeline.extend([{'$project': {
                'fechaOrdenar': '$fechaEntrega',
                'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                'regionNombre': '$sucursal.regionNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'Estatus_Consigna': '$Estatus_Consigna',
                'pedido': '$pedido',
                'consigna': '$consigna',
                'metodoEntrega': '$metodoEntrega',
                'timeslot_from': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_from'}},
                'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_to'}},
                }},
                {'$sort': {'fechaOrdenar': 1, 'regionNombre': 1, 'zonaNombre': 1, 'tiendaNombre': 1}}
            ])
            # print(f"Pipeline desde Tablas -> PedidosPendientes -> {self.titulo}: {pipeline}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            data = []
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'fechaEntrega': dato['fechaEntrega'],
                        'regionNombre': dato['regionNombre'],
                        'zonaNombre': dato['zonaNombre'],
                        'tiendaNombre': dato['tiendaNombre'],
                        'pedido': dato['pedido'],
                        'consigna': dato['consigna'],
                        'timeslot_from': dato['timeslot_from'],
                        'timeslot_to': dato['timeslot_to'],
                        'Estatus_Consigna': dato['Estatus_Consigna'],
                        'metodoEntrega': dato['metodoEntrega'],
                    })
            else:
                hayResultados = 'no'
            columns = [
                    {'name': 'Fecha de Entrega', 'selector':'fechaEntrega', 'formato':'texto'},
                    {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho': '360px'},
                    {'name': 'Pedido', 'selector':'pedido', 'formato':'entero'},
                    {'name': 'Estatus', 'selector':'Estatus_Consigna', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Timeslot From', 'selector':'timeslot_from', 'formato':'texto'},
                    {'name': 'Timeslot To', 'selector':'timeslot_to', 'formato':'texto'},
                    {'name': 'consigna', 'selector':'consigna', 'formato':'texto'},
                    {'name': 'Método Entrega', 'selector':'metodoEntrega', 'formato':'texto'},
                ]
        # print(f"Se va a regresar desde Tablas -> PedidosPendientes -> {self.titulo}: {str({'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data})}")
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}


    async def VentaSinImpuesto(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.canal != '' and self.filtros.canal != "False" and self.filtros.canal != None:
            canal = self.filtros.canal
        else:
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute("select distinct tipo from DWH.artus.catCanal where descripTipo not in ('Tienda Fisica')")
            arreglo = crear_diccionario(cursor)
            canal = ",".join([str(elemento['tipo']) for elemento in arreglo])
        anioElegido = self.filtros.anio
        mesElegido = self.filtros.mes + 1
        # print(f"Mes elegido: {mesElegido}")
        ayer = date.today() - timedelta(days=1)
        if mesElegido == ayer.month and anioElegido == ayer.year:
            diaElegido = diaElegido = ayer.day
        else:
            last_day = date(anioElegido, mesElegido, 1).replace(
            month=mesElegido % 12 + 1, day=1) - timedelta(days=1)
            diaElegido = last_day.day
        # Get the last day of the given month
        last_day = date(int(anioElegido), int(mesElegido), 1).replace(month=mesElegido % 12 + 1, day=1) - timedelta(days=1)

        ayer = datetime(anioElegido, mesElegido, diaElegido).strftime('%Y-%m-%d')

        hoy = datetime.now()

        if self.titulo == 'Venta diaria por departamento':

            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                query_filtro_depto = f" and cd.idDepto = {self.filtros.depto} "
                campo_depto = 'subDeptoDescrip'
                titulo_nivel_producto = 'Sub Departamento'
            else:
                query_filtro_depto = ''
                campo_depto = 'deptoDescrip'
                titulo_nivel_producto = 'Departamento'
            pipeline=f"""SELECT  vd.fecha Fecha
            ,SUM(case WHEN cd.deptoDescrip = 'Electro-muebles' THEN isnull(ventaSinImpuestos,0) else 0 end) 'Electro_Muebles'
            ,SUM(case WHEN cd.deptoDescrip = 'Perecederos No Transformacion' THEN isnull(ventaSinImpuestos,0) else 0 end) 'Perecederos_No_Transformacion'
            ,SUM(case WHEN cd.deptoDescrip = 'PGC Comestible' THEN isnull(ventaSinImpuestos,0) else 0 end) 'PGC_Comestible'
            ,SUM(case WHEN cd.deptoDescrip = 'PGC No Comestible' THEN isnull(ventaSinImpuestos,0) else 0 end) 'PGC_No_Comestible'
            ,SUM(case WHEN cd.deptoDescrip = 'Ropa, Zapatería y Te' THEN isnull(ventaSinImpuestos,0) else 0 end) 'Ropa_Zapateria_y_Te'
            ,SUM(case WHEN cd.deptoDescrip = 'Transformacion y Alimentos' THEN isnull(ventaSinImpuestos,0) else 0 end) 'Transformacion_Y_Alimentos'
            ,SUM(case WHEN cd.deptoDescrip = 'Variedades' THEN isnull(ventaSinImpuestos,0) else 0 end) 'Variedades'
            FROM DWH.artus.ventaDiaria vd
            LEFT JOIN DWH.dbo.dim_tiempo dt
            ON vd.fecha = dt.id_fecha
            LEFT JOIN DWH.artus.cat_departamento cd
            ON vd.subDepto = cd.idSubDepto
            LEFT JOIN DWH.artus.catTienda ct
            ON vd.idTienda = ct.tienda
            LEFT JOIN DWH.artus.catCanal cc
            ON vd.idCanal = cc.idCanal
            WHERE dt.anio IN ({anioElegido})
            AND dt.num_mes in ({mesElegido})
            AND cc.tipo IN (1) """
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        pipeline += f""" and ct.tienda = {self.filtros.tienda} """
                    else:
                        pipeline += f""" and ct.zona = {self.filtros.zona} """
                else:
                    pipeline += f""" and ct.region = {self.filtros.region} """
            pipeline += f" group by vd.fecha "

            # print(f'Tablas -> VentaSinImpuesto -> {self.titulo}: {pipeline}')
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            data = []
            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    date_obj = datetime.strptime(str(arreglo[i]['Fecha']), "%Y%m%d")
                    data.append({
                        'Fecha': date_obj.strftime("%d/%m/%Y"),
                        'Electro_Muebles': arreglo[i]['Electro_Muebles'],
                        'Perecederos_No_Transformacion': arreglo[i]['Perecederos_No_Transformacion'],
                        'PGC_Comestible': arreglo[i]['PGC_Comestible'],
                        'PGC_No_Comestible': arreglo[i]['PGC_No_Comestible'],
                        'Ropa_Zapateria_y_Te': arreglo[i]['Ropa_Zapateria_y_Te'],
                        'Transformacion_Y_Alimentos': arreglo[i]['Transformacion_Y_Alimentos'],
                        'Variedades': arreglo[i]['Variedades']
                    })

                columns = [
                    {'name': 'Fecha', 'selector':'Fecha', 'formato':'texto'},
                    {'name': 'Electro Muebles', 'selector':'Electro_Muebles', 'formato':'moneda'},
                    {'name': 'Perecederos No Transformación', 'selector':'Perecederos_No_Transformacion', 'formato':'moneda'},
                    {'name': 'PGC Comestible', 'selector':'PGC_Comestible', 'formato':'moneda'},
                    {'name': 'PGC No Comestible', 'selector':'PGC_No_Comestible', 'formato':'moneda'},
                    {'name': 'Ropa Zapatería y Té', 'selector':'Ropa_Zapateria_y_Te', 'formato':'moneda'},
                    {'name': 'Transformación Y Alimentos', 'selector':'Transformacion_Y_Alimentos', 'formato':'moneda'},
                    {'name': 'Variedades', 'selector':'Variedades', 'formato':'moneda'}
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Venta acumulada mensual por departamento':

            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                query_filtro_depto = f" and cd.idDepto = {self.filtros.depto} "
                campo_depto = 'subDeptoDescrip'
                titulo_nivel_producto = 'Sub Departamento'
            else:
                query_filtro_depto = ''
                campo_depto = 'deptoDescrip'
                titulo_nivel_producto = 'Departamento'
            pipeline = f"""select cd.{campo_depto} '{titulo_nivel_producto}',
                sum(case when anio={anioElegido-1} and dt.fecha < convert(date,DATEADD(yy,-1,(GETDATE()))) then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
                sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
                sum(case when anio={anioElegido} then objetivo else 0 end) objetivoMensual,
                sum(case when anio={anioElegido} and dt.fecha <= '{ayer}' then objetivo else 0 end) objetivoDia
                from DWH.artus.ventaDiaria vd
                left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
                left join DWH.artus.cat_departamento cd on vd.subDepto=cd.idSubDepto
                left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
                left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
                where dt.anio in ({anioElegido-1},{anioElegido}) and cc.tipo in ({canal}) and dt.num_mes in({mesElegido}) {query_filtro_depto} """
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        pipeline += f""" and ct.tienda = {self.filtros.tienda} """
                    else:
                        pipeline += f""" and ct.zona = {self.filtros.zona} """
                else:
                    pipeline += f""" and ct.region = {self.filtros.region} """
            pipeline += f" group by cd.{campo_depto} "

            # print(f'Tablas -> VentaSinImpuesto -> {self.titulo}: {pipeline}')
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            data_tmp = []
            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    # if self.filtros.canal == '1':
                    objetivoMensual = arreglo[i]['objetivoMensual']
                    objetivoDia = arreglo[i]['objetivoDia']
                    # print(f'objetivoDia = {str(objetivoDia)}')
                    alcance = (arreglo[i]['AActual']/objetivoMensual) - 1 if objetivoMensual else '--'
                    alcanceDia = (arreglo[i]['AActual']/objetivoDia) - 1 if objetivoDia else '--'
                    # else:
                    #     alcance = '--'
                    #     objetivo = '--'
                    #     alcanceDia = '--'
                    #     objetivoDia = '--'
                    vsaa = (arreglo[i]['AActual'] / arreglo[i]['AAnterior']) - 1 if arreglo[i]['AAnterior'] != 0 else '--'
                    depto = arreglo[i][titulo_nivel_producto] if arreglo[i][titulo_nivel_producto] is not None else 'Otros'
                    data_tmp.append({
                        'depto': depto,
                        'objetivoMensual': objetivoMensual,
                        'venta': arreglo[i]['AActual'],
                        'alcance': alcance,
                        'venta_anterior': arreglo[i]['AAnterior'],
                        'vsaa': vsaa,
                        'objetivoDia': objetivoDia,
                        'alcanceDia': alcanceDia,
                    })
                # data_tmp = [{'depto': 'Ventas', 'name': 'John'}, {'depto': 'Marketing', 'name': 'Alice'}, {'depto': 'Otros', 'name': 'Bob'}, {'depto': 'Finanzas', 'name': 'Carlos'}, {'depto': 'Otros', 'name': 'Dave'}]

                data = sorted([i for i in data_tmp if i['depto'] != 'Otros'], key=lambda x: x['depto'])
                data.extend(sorted([i for i in data_tmp if i['depto'] == 'Otros'], key=lambda x: x['depto']))
                columns = [
                    {'name': titulo_nivel_producto, 'selector':'depto', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Objetivo '+mesTexto(mesElegido), 'selector':'objetivoMensual', 'formato':'moneda', 'ancho': '220px'},
                    {'name': 'Venta '+mesTexto(mesElegido)+' '+str(anioElegido), 'selector':'venta', 'formato':'moneda', 'ancho': '210px'},
                    {'name': 'Alcance al Objetivo '+mesTexto(mesElegido), 'selector':'alcance', 'formato':'porcentaje', 'ancho': '200px'},
                    {'name': 'Objetivo al '+str(diaElegido)+' de '+mesTexto(mesElegido)+' '+str(anioElegido), 'selector':'objetivoDia', 'formato':'moneda', 'ancho': '220px'},
                    {'name': 'Alcance al Objetivo '+str(diaElegido)+' de '+mesTexto(mesElegido)+' '+str(anioElegido), 'selector':'alcanceDia', 'formato':'porcentaje', 'ancho': '250px'},
                    {'name': 'Venta al '+str(diaElegido)+' '+mesTexto(mesElegido)+' '+str(anioElegido - 1), 'selector':'venta_anterior', 'formato':'moneda', 'ancho': '210px'},
                    {'name': 'Vs. '+str(anioElegido-1), 'selector':'vsaa', 'formato':'porcentaje'},
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo':
            mod_titulo_serie = ''
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []
            

            pipeline = f"""select dt.abrev_mes categoria,
            sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
            sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
            sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
            from DWH.artus.ventaDiaria vd
            left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
            left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
            left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
            left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
            where dt.anio in ({anioElegido},{anioElegido-1})
            and cc.tipo in ({canal}) """
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        pipeline += f""" and ct.tienda = {self.filtros.tienda} """
                    else:
                        pipeline += f""" and ct.zona = {self.filtros.zona} """
                else:
                    pipeline += f""" and ct.region = {self.filtros.region} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += " group by dt.abrev_mes,dt.num_mes order by dt.num_mes "
            # print(f"Query desde Venta anual por mes: $anioActual vs. $anioAnterior y Objetivo: {pipeline}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for fila in arreglo:
                    # print(f"fila: {fila}")
                    aActual = fila['AActual'] if fila['AActual'] is not None else 0
                    aAnterior = fila['AAnterior'] if fila['AAnterior'] is not None else 0
                    varActual = round((( aActual/ aAnterior)-1), 4) if aAnterior != 0 else '--'
                    objetivo = fila['objetivo'] if fila['objetivo'] is not None else 0
                    varObjetivo = (round(((aActual / objetivo)-1), 4)) if objetivo != 0 else '--'
                    objeto = {
                        'Mes': fila['categoria'],
                        'VentaAnioAnterior': round(aAnterior, 2),
                        'VentaAnioActual': round(aActual, 2),
                        'VarActual': varActual

                    }
                    if self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36':
                        objeto['Objetivo'] = (round(objetivo, 2))
                    else:
                        objeto['Objetivo'] = 0
                    if fila['objetivo'] != 0:
                        objeto['varObjetivo'] = varObjetivo
                    else:
                        objeto['varObjetivo'] = 0
                    data.append(objeto)
                columns = [
                    {'name': 'Mes', 'selector':'Mes', 'formato': 'texto'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'selector':'VentaAnioAnterior', 'formato': 'moneda'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'selector':'VentaAnioActual', 'formato': 'moneda'},
                    {'name': 'Var Actual', 'selector':'VarActual', 'formato': 'porcentaje'},
                    {'name': 'Objetivo', 'selector':'Objetivo', 'formato': 'moneda'},
                    {'name': 'Var Objetivo', 'selector':'varObjetivo', 'formato': 'porcentaje'}
                ]
            else:
                hayResultados = "no"

        if self.titulo == 'Venta anual por tienda: $anioActual vs. $anioAnterior y Objetivo':
            mod_titulo_serie = ''
            serie1 = []
            serie2 = []
            serie3 = []
            serie4 = []
            serie5 = []
            

            pipeline = f"""select vd.idTienda, ct.regionNombre, ct.zonaNombre, ct.tiendaNombre,
            sum(case when anio={anioElegido-1} then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior,
            sum(case when anio={anioElegido} then isnull (ventaSinImpuestos, 0) else 0 end) AActual,
            sum(case when anio={anioElegido} then objetivo else 0 end) objetivo
            from DWH.artus.ventaDiaria vd
            left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha
            left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
            left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
            left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
            where dt.anio in ({anioElegido},{anioElegido-1})
            and dt.num_mes in({mesElegido})
            and cc.tipo in ({canal}) """
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        pipeline += f""" and ct.tienda = {self.filtros.tienda} """
                    else:
                        pipeline += f""" and ct.zona = {self.filtros.zona} """
                else:
                    pipeline += f""" and ct.region = {self.filtros.region} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    pipeline += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    pipeline += f""" and cd.idDepto = {self.filtros.depto} """
            pipeline += """ group by ct.regionNombre, ct.zonaNombre, ct.tiendaNombre, vd.idTienda 
            order by ct.regionNombre, ct.zonaNombre, ct.tiendaNombre, vd.idTienda """
            # print(f"Query desde Venta anual por tienda: $anioActual vs. $anioAnterior y Objetivo: {pipeline}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for fila in arreglo:
                    # print(f"fila: {fila}")
                    varActual = round(((fila['AActual'] / fila['AAnterior'])-1), 4) if fila['AAnterior'] != 0 and fila['AAnterior'] is not None and fila['AActual'] is not None else '--'
                    varObjetivo = (round(((fila['AActual'] / fila['objetivo'])-1), 4)) if fila['objetivo'] != 0 and fila['objetivo'] is not None and fila['AActual'] is not None else '--'
                    ventaAnioAnterior = round((fila['AAnterior']), 2) if fila['AAnterior'] is not None else '--'
                    ventaAnioActual = round((fila['AActual']), 2) if fila['AActual'] is not None else '--'
                    objeto = {
                        'Region': fila['regionNombre'],
                        'Zona': fila['zonaNombre'],
                        'Tienda': fila['tiendaNombre'],
                        'VentaAnioAnterior': ventaAnioAnterior,
                        'VentaAnioActual': ventaAnioActual,
                        'VarActual': varActual

                    }
                    if (self.filtros.canal == '1' or self.filtros.canal == '35' or self.filtros.canal == '36') and fila['objetivo'] is not None:
                        objeto['Objetivo'] = (round((fila['objetivo']), 2))
                    else:
                        objeto['Objetivo'] = 0
                    if fila['objetivo'] != 0:
                        objeto['varObjetivo'] = varObjetivo
                    else:
                        objeto['varObjetivo'] = 0
                    data.append(objeto)
                columns = [
                    {'name': 'Región', 'selector':'Region', 'formato': 'texto', 'ancho': '210px'},
                    {'name': 'Zona', 'selector':'Zona', 'formato': 'texto', 'ancho': '210px'},
                    {'name': 'Tienda', 'selector':'Tienda', 'formato': 'texto', 'ancho': '390px'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido - 1), 'selector':'VentaAnioAnterior', 'formato': 'moneda', 'ancho': '130px'},
                    {'name': 'Venta '+mod_titulo_serie+str(anioElegido), 'selector':'VentaAnioActual', 'formato': 'moneda', 'ancho': '130px'},
                    {'name': 'Var Actual', 'selector':'VarActual', 'formato': 'porcentaje'},
                    {'name': 'Objetivo', 'selector':'Objetivo', 'formato': 'moneda', 'ancho': '150px'},
                    {'name': 'Var Objetivo', 'selector':'varObjetivo', 'formato': 'porcentaje', 'ancho': '150px'}
                ]
            else:
                hayResultados = "no"

        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}


    async def Faltantes(self):
        pipeline = []
        data = []
        columns = []
        # print('self.nivel_lugar = '+self.nivel_lugar)
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}}])
        collection = conexion_mongo('report').report_pedidoFaltantes

        # Como para cada combinación de justificación y periodo puede no haber valores, y en esos casos el query, en vez de regresar 0, no regresaría el registro y quebraría la tabla, hay que hacer un arreglo de 2 dimensiones con todas las justificaciones en un eje y todos los periodos en otro. Luego, llenar el valor de cada campo con los resultados del query, y donde no haya un valor, poner 0.
        # Para crear este arreglo de 2 dimensiones, vamos a hacer 2 queries: uno para las justificaciones y otro para los periodos, y al final, hacer otro query que es el que va a llenar el arreglo bidimensional.

        # Arreglo de periodos:
        if self.filtros.agrupador == 'mes':
            periodo = {'mes': {'$month': '$fecha'}, 'anio': {'$year':'$fecha'}}
        elif self.filtros.agrupador == 'semana':
            periodo = {'semana': {'$week': '$fecha'}, 'anio': {'$year':'$fecha'}}
        elif self.filtros.agrupador == 'dia':
            periodo = {'dia': {'$dayOfMonth': '$fecha'}, 'mes': {'$month': '$fecha'}, 'anio': {'$year':'$fecha'}}
        # else:
            # print("No jaló, porque el agrupador es "+ self.filtros.agrupador)
        pipeline_periodos = deepcopy(pipeline)
        pipeline_periodos.extend([
            {'$group':{
                '_id': {'periodo':periodo},
                'fecha':{'$min':'$fecha'}}
            },
            {'$sort':{'fecha': 1}}
        ])
        # print(pipeline_periodos)
        cursor = collection.aggregate(pipeline_periodos)
        arreglo_tmp = await cursor.to_list(length=None)
        if len(arreglo_tmp) <= 0: # Si no hay resultados, regresar pipeline a front end
            return {'hayResultados':'no', 'pipeline': pipeline_periodos, 'columns':[], 'data':[]}
        arreglo_periodos = []
        for periodo_en_arreglo in arreglo_tmp:
            if self.filtros.agrupador == 'mes':
                arreglo_periodos.append(mesTexto(periodo_en_arreglo['_id']['periodo']['mes'])+' '+str(periodo_en_arreglo['_id']['periodo']['anio']))
            elif self.filtros.agrupador == 'semana':
                arreglo_periodos.append('Sem ' + str(periodo_en_arreglo['_id']['periodo']['semana'])+' '+str(periodo_en_arreglo['_id']['periodo']['anio']))
            elif self.filtros.agrupador == 'dia':
                arreglo_periodos.append(str(periodo_en_arreglo['_id']['periodo']['dia'])+' '+mesTexto(periodo_en_arreglo['_id']['periodo']['mes'])+' '+str(periodo_en_arreglo['_id']['periodo']['anio']))
        # print(arreglo_periodos)

        if self.titulo == 'Justificaciones':
            # Arreglo de justificaciones:
            pipeline_justificaciones = deepcopy(pipeline)
            pipeline_justificaciones.extend([
                {'$group':{'_id': '$respuesta'}}
            ])
            cursor = collection.aggregate(pipeline_justificaciones)
            arreglo_tmp = await cursor.to_list(length=None)
            if len(arreglo_tmp) <= 0: # Si no hay resultados, regresar pipeline a front end
                return {'hayResultados':'no', 'pipeline': pipeline_justificaciones, 'columns':[], 'data':[]}
            arreglo_justificaciones = []
            for justificacion in arreglo_tmp:
                arreglo_justificaciones.append(justificacion['_id'])

            # Pipeline principal
            pipeline.append(
                {'$group': {
                        '_id': {
                            'justificacion':'$respuesta',
                            'periodo': periodo
                        },
                        'cantidad': {
                            "$sum": '$registro'
                        }
                    }
                }
            )
            
            cursor = collection.aggregate(pipeline)
            arreglo_resultados = await cursor.to_list(length=None)
            if len(arreglo_resultados) <= 0:
                hayResultados = "no"
            
            else:
                hayResultados = "si"
                # Populamos con ceros el arreglo que tiene dos dimensiones: justificaciones x periodos
                # tabla = [[0]*len(arreglo_periodos)]*len(arreglo_justificaciones) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                tabla = zeros((len(arreglo_justificaciones), len(arreglo_periodos) + 1)) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                # Para cada resultado del query principal, ponemos en nuestro arreglo-tabla los valores que sí tengamos:
                # print('len(arreglo_resultados) = '+str(len(arreglo_resultados)))
                for dato in arreglo_resultados:
                    x = arreglo_justificaciones.index(dato['_id']['justificacion'])
                    # print('x = '+str(x))
                    # La posición y será el índice del arreglo de periodos que tenga el nombre de periodo del dato actual:
                    if self.filtros.agrupador == 'mes':
                        y = arreglo_periodos.index(mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'semana':
                        y = arreglo_periodos.index('Sem ' + str(dato['_id']['periodo']['semana'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'dia':
                        y = arreglo_periodos.index(str(dato['_id']['periodo']['dia'])+' '+mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    # print('y = '+str(y))
                    # print('tabla['+str(x)+']['+str(y)+'] = '+str(dato['cantidad']))
                    tabla[x][y] = (dato['cantidad'])
                # Agregamos al final de cada fila de nuestro arreglo la suma de toda la fila, y además obtenemos una variable que es la suma de todas esas sumas:
                # print(tabla)
                granTotal = 0
                for row in tabla:
                    suma = sum(row)
                    row[len(arreglo_periodos)] = suma
                    granTotal += suma
                # print(tabla)

                # Ponemos los nombres de columna, que empiezan por la justificación:
                columns = [
                    {'name': 'Justificación', 'selector':'justificacion', 'formato':'texto', 'ancho': '330px'},
                ]
                # ...Siguen por cada nombre de periodo:
                for nombre_periodo in arreglo_periodos:
                    nombre_periodo_sin_whitespace = '_'+nombre_periodo.replace(" ", "_")
                    columns.append({'name': nombre_periodo, 'selector':nombre_periodo_sin_whitespace, 'formato':'entero'})
                # ... Y terminan con el total y el %ART:
                columns.extend([
                    {'name': 'Total', 'selector':'total', 'formato':'entero'},
                    {'name': '%ART', 'selector':'art', 'formato':'porcentaje'}
                ])
                # print(columns)
                # Metemos todos los datos:
                for i in range(len(arreglo_justificaciones)):
                    diccionario = {'justificacion': arreglo_justificaciones[i]}
                    for j in range(len(arreglo_periodos)):
                        nombre_periodo_sin_whitespace = '_'+arreglo_periodos[j].replace(" ", "_")
                        # diccionario['periodo'+str(j)] = tabla[i][j]
                        diccionario[nombre_periodo_sin_whitespace] = tabla[i][j]
                    diccionario['total'] = tabla[i][len(arreglo_periodos)]
                    diccionario['art'] = tabla[i][len(arreglo_periodos)] / granTotal
                    data.append(diccionario)
                # print(pipeline)

        if self.titulo == 'Justificados por Lugar':
            if self.filtro_lugar:
                if self.nivel_lugar == 'region':
                    siguiente_nivel = 'zonaNombre'
                    nombre_siguiente_nivel = 'Zona'
                else:
                    siguiente_nivel = 'tiendaNombre'
                    nombre_siguiente_nivel = 'Tienda'
            else:
                siguiente_nivel = 'regionNombre'
                nombre_siguiente_nivel = 'Región'

            # Arreglo de lugares:
            pipeline.append({'$unwind': '$sucursal'}) # Le pones el unwind al pipeline principal de una vez porque tanto el arreglo de lugares como el principal van a llevarlo.
            pipeline_lugares = deepcopy(pipeline)
            pipeline_lugares.extend([
                {'$group':{'_id': '$sucursal.'+siguiente_nivel}},
                {'$sort':{'_id': 1}}
            ])
            cursor = collection.aggregate(pipeline_lugares)
            arreglo_tmp = await cursor.to_list(length=None)
            if len(arreglo_tmp) <= 0: # Si no hay resultados, regresar pipeline a front end
                return {'hayResultados':'no', 'pipeline': pipeline_lugares, 'columns':[], 'data':[]}
            arreglo_lugares = []
            for lugar in arreglo_tmp:
                arreglo_lugares.append(lugar['_id'])

            # Pipeline principal
            pipeline.extend([
                {'$project': {
                    'lugar':'$sucursal.'+siguiente_nivel,
                    'periodo': periodo,
                    'justificados': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, 0, '$registro']},
                    'sin_justificar': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, '$registro', 0]}
                }},
                {'$group': {
                    '_id': {'lugar': '$lugar', 'periodo': '$periodo'},
                    'justificados': {'$sum': '$justificados'},
                    'sin_justificar': {'$sum': '$sin_justificar'}
                }},
                {'$project':{
                    '_id': '$_id',
                    'porc_justificados': {'$divide': ['$justificados', {'$add': ['$justificados', '$sin_justificar']}]},
                    'porc_sin_justificar': {'$divide': ['$sin_justificar', {'$add': ['$justificados', '$sin_justificar']}]}
                }}
            ])
            # print(pipeline)

            cursor = collection.aggregate(pipeline)
            arreglo_resultados = await cursor.to_list(length=None)
            # print(str(arreglo_resultados))
            if len(arreglo_resultados) <= 0:
                hayResultados = "no"
            
            else:
                hayResultados = "si"
                # Populamos con ceros el arreglo que tiene dos dimensiones: justificaciones x periodos
                tabla = zeros((len(arreglo_lugares), len(arreglo_periodos), 2)) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                # Para cada resultado del query principal, ponemos en nuestro arreglo-tabla los valores que sí tengamos:
                # print('len(arreglo_resultados) = '+str(len(arreglo_resultados)))
                for dato in arreglo_resultados:
                    x = arreglo_lugares.index(dato['_id']['lugar'])
                    # print('x = '+str(x))
                    # La posición y será el índice del arreglo de periodos que tenga el nombre de periodo del dato actual:
                    if self.filtros.agrupador == 'mes':
                        y = arreglo_periodos.index(mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'semana':
                        y = arreglo_periodos.index('Sem ' + str(dato['_id']['periodo']['semana'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'dia':
                        y = arreglo_periodos.index(str(dato['_id']['periodo']['dia'])+' '+mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    # print('y = '+str(y))
                    # print('tabla['+str(x)+']['+str(y)+'] = '+str(dato['cantidad']))
                    tabla[x][y][0] = (dato['porc_justificados'])
                    tabla[x][y][1] = (dato['porc_sin_justificar'])

                # Ponemos los nombres de columna, que empiezan por la justificación:
                columns = [
                    {'name': nombre_siguiente_nivel, 'selector':nombre_siguiente_nivel, 'formato':'texto', 'ancho': '400px'},
                ]
                # ...Siguen por cada nombre de periodo:
                for nombre_periodo in arreglo_periodos:
                    nombre_periodo_sin_whitespace = nombre_periodo.replace(" ", "_")
                    columns.extend([
                        {
                            'name': 'Justificados ' + nombre_periodo, 'selector':'Justificados_' + nombre_periodo_sin_whitespace, 'formato':'porcentaje'
                        },{
                            'name': 'Sin justificar ' + nombre_periodo, 'selector':'Sin_justificar_' + nombre_periodo_sin_whitespace, 'formato':'porcentaje'
                        }
                    ])
                # print(columns)
                # Metemos todos los datos:
                for i in range(len(arreglo_lugares)):
                    diccionario = {nombre_siguiente_nivel: arreglo_lugares[i]}
                    for j in range(len(arreglo_periodos)):
                        nombre_periodo_sin_whitespace = arreglo_periodos[j].replace(" ", "_")
                        # diccionario['periodo'+str(j)] = tabla[i][j]
                        diccionario['Justificados_' +nombre_periodo_sin_whitespace] = tabla[i][j][0]
                        diccionario['Sin_justificar_' +nombre_periodo_sin_whitespace] = tabla[i][j][1]
                    data.append(diccionario)
                # print(pipeline)

        if self.titulo == 'Justificados por Tienda':
            if self.filtro_lugar:
                if self.nivel_lugar == 'region':
                    siguiente_nivel = 'zonaNombre'
                    nombre_siguiente_nivel = 'Zona'
                else:
                    siguiente_nivel = 'tiendaNombre'
                    nombre_siguiente_nivel = 'Tienda'
            else:
                siguiente_nivel = 'regionNombre'
                nombre_siguiente_nivel = 'Región'

            # Arreglo de lugares:
            pipeline.append({'$unwind': '$sucursal'}) # Le pones el unwind al pipeline principal de una vez porque tanto el arreglo de lugares como el principal van a llevarlo.
            pipeline_lugares = deepcopy(pipeline)
            pipeline_lugares.extend([
                {'$group':{'_id': '$sucursal.tiendaNombre'}},
                {'$sort':{'_id': 1}}
            ])
            cursor = collection.aggregate(pipeline_lugares)
            arreglo_tmp = await cursor.to_list(length=None)
            if len(arreglo_tmp) <= 0: # Si no hay resultados, regresar pipeline a front end
                return {'hayResultados':'no', 'pipeline': pipeline_lugares, 'columns':[], 'data':[]}
            arreglo_lugares = []
            for lugar in arreglo_tmp:
                arreglo_lugares.append(lugar['_id'])

            # Pipeline principal
            pipeline.extend([
                {'$project': {
                    'lugar':'$sucursal.tiendaNombre',
                    'periodo': periodo,
                    'justificados': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, 0, '$registro']},
                    'sin_justificar': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, '$registro', 0]}
                }},
                {'$group': {
                    '_id': {'lugar': '$lugar', 'periodo': '$periodo'},
                    'justificados': {'$sum': '$justificados'},
                    'sin_justificar': {'$sum': '$sin_justificar'}
                }},
                {'$project':{
                    '_id': '$_id',
                    'porc_justificados': {'$divide': ['$justificados', {'$add': ['$justificados', '$sin_justificar']}]},
                    'porc_sin_justificar': {'$divide': ['$sin_justificar', {'$add': ['$justificados', '$sin_justificar']}]}
                }}
            ])
            # print(pipeline)

            cursor = collection.aggregate(pipeline)
            arreglo_resultados = await cursor.to_list(length=None)
            # print(str(arreglo_resultados))
            if len(arreglo_resultados) <= 0:
                hayResultados = "no"
            
            else:
                hayResultados = "si"
                # Populamos con ceros el arreglo que tiene dos dimensiones: justificaciones x periodos
                tabla = zeros((len(arreglo_lugares), len(arreglo_periodos), 2)) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                # Para cada resultado del query principal, ponemos en nuestro arreglo-tabla los valores que sí tengamos:
                # print('len(arreglo_resultados) = '+str(len(arreglo_resultados)))
                for dato in arreglo_resultados:
                    x = arreglo_lugares.index(dato['_id']['lugar'])
                    # print('x = '+str(x))
                    # La posición y será el índice del arreglo de periodos que tenga el nombre de periodo del dato actual:
                    if self.filtros.agrupador == 'mes':
                        y = arreglo_periodos.index(mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'semana':
                        y = arreglo_periodos.index('Sem ' + str(dato['_id']['periodo']['semana'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'dia':
                        y = arreglo_periodos.index(str(dato['_id']['periodo']['dia'])+' '+mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    # print('y = '+str(y))
                    # print('tabla['+str(x)+']['+str(y)+'] = '+str(dato['cantidad']))
                    tabla[x][y][0] = (dato['porc_justificados'])
                    tabla[x][y][1] = (dato['porc_sin_justificar'])

                # Ponemos los nombres de columna, que empiezan por la justificación:
                columns = [
                    {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '400px'},
                ]
                # ...Siguen por cada nombre de periodo:
                for nombre_periodo in arreglo_periodos:
                    nombre_periodo_sin_whitespace = nombre_periodo.replace(" ", "_")
                    columns.extend([
                        {
                            'name': 'Justificados ' + nombre_periodo, 'selector':'Justificados_' + nombre_periodo_sin_whitespace, 'formato':'porcentaje'
                        },{
                            'name': 'Sin justificar ' + nombre_periodo, 'selector':'Sin_justificar_' + nombre_periodo_sin_whitespace, 'formato':'porcentaje'
                        }
                    ])
                # print(columns)
                # Metemos todos los datos:
                for i in range(len(arreglo_lugares)):
                    diccionario = {'Tienda': arreglo_lugares[i]}
                    for j in range(len(arreglo_periodos)):
                        nombre_periodo_sin_whitespace = arreglo_periodos[j].replace(" ", "_")
                        # diccionario['periodo'+str(j)] = tabla[i][j]
                        diccionario['Justificados_' +nombre_periodo_sin_whitespace] = tabla[i][j][0]
                        diccionario['Sin_justificar_' +nombre_periodo_sin_whitespace] = tabla[i][j][1]
                    data.append(diccionario)
                # print(pipeline)

        if self.titulo == 'Justificados por Departamento':
            # Arreglo de departamentos:
            pipeline_departamentos = deepcopy(pipeline)
            pipeline_departamentos.extend([
                {'$group':{'_id': '$DescripDepto'}}
            ])
            cursor = collection.aggregate(pipeline_departamentos)
            arreglo_tmp = await cursor.to_list(length=None)
            if len(arreglo_tmp) <= 0: # Si no hay resultados, regresar pipeline a front end
                return {'hayResultados':'no', 'pipeline': pipeline_departamentos, 'columns':[], 'data':[]}
            arreglo_departamentos = []
            for departamento in arreglo_tmp:
                arreglo_departamentos.append(departamento['_id'])

            # Pipeline principal
            pipeline.append(
                {'$group': {
                        '_id': {
                            'departamento':'$DescripDepto',
                            'periodo': periodo
                        },
                        'cantidad': {
                            "$sum": '$registro'
                        }
                    }
                }
            )
            
            cursor = collection.aggregate(pipeline)
            arreglo_resultados = await cursor.to_list(length=None)
            if len(arreglo_resultados) <= 0:
                hayResultados = "no"
            else:
                hayResultados = "si"
                # Populamos con ceros el arreglo que tiene dos dimensiones: justificaciones x periodos
                # tabla = [[0]*len(arreglo_periodos)]*len(arreglo_justificaciones) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                tabla = zeros((len(arreglo_departamentos), len(arreglo_periodos) + 1))
                # Para cada resultado del query principal, ponemos en nuestro arreglo-tabla los valores que sí tengamos:
                # print('len(arreglo_resultados) = '+str(len(arreglo_resultados)))
                for dato in arreglo_resultados:
                    x = arreglo_departamentos.index(dato['_id']['departamento']) if 'departamento' in dato['_id'] else '--'
                    # print('x = '+str(x))
                    # La posición y será el índice del arreglo de periodos que tenga el nombre de periodo del dato actual:
                    if self.filtros.agrupador == 'mes':
                        y = arreglo_periodos.index(mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'semana':
                        y = arreglo_periodos.index('Sem ' + str(dato['_id']['periodo']['semana'])+' '+str(dato['_id']['periodo']['anio']))
                    elif self.filtros.agrupador == 'dia':
                        y = arreglo_periodos.index(str(dato['_id']['periodo']['dia'])+' '+mesTexto(dato['_id']['periodo']['mes'])+' '+str(dato['_id']['periodo']['anio']))
                    # print('y = '+str(y))
                    # print('Desde tablas -> Faltantes, tabla['+str(x)+']['+str(y)+'] = '+str(dato['cantidad']))
                    if x != '--':
                        tabla[x][y] = (dato['cantidad'])
                # Agregamos al final de cada fila de nuestro arreglo la suma de toda la fila, y además obtenemos una variable que es la suma de todas esas sumas:
                # print(tabla)
                granTotal = 0
                for row in tabla:
                    suma = sum(row)
                    row[len(arreglo_periodos)] = suma
                    granTotal += suma
                # print(tabla)

                # Ponemos los nombres de columna, que empiezan por la justificación:
                columns = [
                    {'name': 'Departamento', 'selector':'Departamento', 'formato':'texto', 'ancho': '220px'},
                ]
                # ...Siguen por cada nombre de periodo:
                for nombre_periodo in arreglo_periodos:
                    nombre_periodo_sin_whitespace = '_'+nombre_periodo.replace(" ", "_")
                    columns.append({'name': nombre_periodo, 'selector':nombre_periodo_sin_whitespace, 'formato':'entero'})
                # ... Y terminan con el total y el %ART:
                columns.extend([
                    {'name': 'Total', 'selector':'total', 'formato':'entero'},
                    {'name': '%ART', 'selector':'art', 'formato':'porcentaje'}
                ])
                # print(columns)
                # Metemos todos los datos:
                for i in range(len(arreglo_departamentos)):
                    diccionario = {'Departamento': arreglo_departamentos[i]}
                    for j in range(len(arreglo_periodos)):
                        nombre_periodo_sin_whitespace = '_'+arreglo_periodos[j].replace(" ", "_")
                        # diccionario['periodo'+str(j)] = tabla[i][j]
                        diccionario[nombre_periodo_sin_whitespace] = tabla[i][j]
                    diccionario['total'] = tabla[i][len(arreglo_periodos)]
                    diccionario['art'] = tabla[i][len(arreglo_periodos)] / granTotal
                    data.append(diccionario)
                # print(pipeline)

            # pipeline.extend([
            #     {'$project': {
            #         '_id':'$DescripDepto',
            #         'justificados': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, 0, '$registro']},
            #         'sin_justificar': {'$cond': [{'$eq': ["$respuesta","Sin justificar"]}, '$registro', 0]}
            #     }},
            #     {'$group': {
            #         '_id': '$_id',
            #         'justificados': {'$sum': '$justificados'},
            #         'sin_justificar': {'$sum': '$sin_justificar'}
            #     }},
            #     {'$sort':{
            #         '_id':1
            #     }}
            # ])
            # cursor = collection.aggregate(pipeline)
            # arreglo = await cursor.to_list(length=None)
            # if len(arreglo) <= 0:
            #     hayResultados = "no"
            #     res = pipeline
            # else:
            #     hayResultados = "si"
            #     columns = [
            #         {'name': 'Departamento', 'selector':'Departamento', 'formato':'texto'},
            #         {'name': 'Justificados', 'selector':'Justificados', 'formato':'entero'},
            #         {'name': 'Sin Justificar', 'selector':'Sin_Justificar', 'formato':'entero'}
            #     ]
            #     data = []
            #     for registro in arreglo:
            #         data.append({
            #             'Departamento': registro['_id'],
            #             'Justificados': registro['justificados'],
            #             'Sin_Justificar': registro['sin_justificar']
            #         })
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def PedidoPerfecto(self):
        if not self.filtros.periodo or (self.filtros.agrupador == 'mes' and 'semana' in self.filtros.periodo) or (self.filtros.agrupador == 'semana' and not 'semana' in self.filtros.periodo) or (self.filtros.agrupador == 'dia' and not 'dia' in self.filtros.periodo):
            return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        pipeline = []
        data = []
        columns = []
        fecha_fin = self.filtros.fechas['fecha_fin'][0:10] + ' 23:59:59'
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
        if self.titulo == 'Tiendas por % Pedido Perfecto más bajo':
            if self.filtros.periodo != {}:
                collection = conexion_mongo('report').report_pedidoPerfecto
                if self.filtros.region != '' and self.filtros.region != "False":
                    # print('Sí hay región, y es: '+self.filtros.region)
                    filtro_lugar = True
                    if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                        if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                            nivel = 'idtienda'
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
                    # print('No hay filtro_lugar')
                pipeline = [
                    {'$unwind': '$sucursal'},
                    {'$match': {
                        'fecha': {
                            '$lte': fecha_fin
                        }
                    }}
                ]
                if filtro_lugar:
                    pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
                else:
                    pipeline.append({'$match': {
                        'sucursal.region': { 
                            '$exists': True,
                            '$ne': None
                        }
                    }})

                # print("self.filtros.periodo desde Tabla: "+str(self.filtros.periodo))
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$and': []
                        }
                    }},
                    {'$group': {
                        '_id': {
                            'regionNombre': '$sucursal.regionNombre',
                            'zonaNombre': '$sucursal.zonaNombre',
                            'tiendaNombre': '$sucursal.tiendaNombre',
                            'region': '$sucursal.region',
                            'zona': '$sucursal.zona',
                            'idtienda': '$sucursal.idtienda'
                        },
                        'totales': {
                            '$sum': '$Total_Pedidos'
                        },
                        'quejas': {
                            '$sum': '$con_queja'
                        },
                        'retrasados': {
                            '$sum': '$retrasados'
                        },
                        'cancelados': {
                            '$sum': '$Cancelados'
                        },
                        'entregados': {
                            '$sum': '$Total_Entregados'
                        },
                        'incompletos': {
                            '$sum': '$incompletos'
                        },
                        'perfectos': {
                            '$sum': '$perfecto'
                        },
                        'upSells': {
                            '$sum': '$upSells'
                        },
                        'nps': {
                            '$sum': '$nps'
                        },
                        'otros_no_perfecto': {
                            '$sum': '$otros_no_perfecto'
                        },
                        'objetivoPP': {
                            '$avg': '$objetivoPP'
                        },
                    }},
                    {'$project': {
                        '_id': '$_id',
                        'totales': '$totales',
                        'quejas': '$quejas',
                        'porc_quejas':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$quejas', '$totales']}]},
                        'retrasados': '$retrasados',
                        'porc_retrasados':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$retrasados', '$totales']}]},
                        'cancelados': '$cancelados',
                        'porc_cancelados':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$cancelados', '$totales']}]},
                        'entregados': '$entregados',
                        'incompletos': '$incompletos',
                        'porc_incompletos':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$incompletos', '$totales']}]},
                        'incidentes': '$nps',
                        'porc_incidentes':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$nps', '$totales']}]},
                        'perfectos': '$perfectos',
                        'porc_perfectos':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$perfectos', '$totales']}]},
                        'upSells': '$upSells',
                        'porc_upSells':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$upSells', '$totales']}]},
                        'no_imputable': '$otros_no_perfecto',
                        'porc_no_imputable':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$otros_no_perfecto', '$totales']}]},
                        'porc_objetivo': '$objetivoPP'
                    }},
                    {'$sort': {
                        'porc_perfectos': 1
                    }}
                ])
                # Creamos variables para manipular los diccionarios:
                match = pipeline[-4]['$match']['$expr']['$and']
                
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
                # Modificamos el pipeline para el caso de que el agrupador sea por día:
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
                # print(f"Pipeline desde Tablas -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=None)
                # print(str(arreglo))
                if len(arreglo) >0:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán la tabla:
                    columns = [
                        {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho': '220px'},
                        {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho': '220px'},
                        {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '420px'},
                        {'name': 'Ver Detalle de Tienda', 'selector':'sibling', 'formato':'sibling'},
                        {'name': 'Total Pedidos', 'selector':'Totales', 'formato':'entero'},
                        {'name': 'Con Queja', 'selector':'Quejas', 'formato':'entero'},
                        {'name': '% Con Queja', 'selector':'Porc_Quejas', 'formato':'porcentaje'},
                        {'name': 'Retrasados', 'selector':'Retrasados', 'formato':'entero'},
                        {'name': '% Retrasados', 'selector':'Porc_Retrasados', 'formato':'porcentaje'},
                        {'name': 'Cancelados', 'selector':'Cancelados', 'formato':'entero'},
                        {'name': '% Cancelados', 'selector':'Porc_Cancelados', 'formato':'porcentaje'},
                        {'name': 'Entregados', 'selector':'Entregados', 'formato':'entero'},
                        {'name': 'Incompletos', 'selector':'Incompletos', 'formato':'entero'},
                        {'name': '% Incompletos', 'selector':'Porc_Incompletos', 'formato':'porcentaje'},
                        {'name': 'Incidentes', 'selector':'Incidentes', 'formato':'entero'},
                        {'name': '% Incidentes', 'selector':'Porc_Incidentes', 'formato':'porcentaje'},
                        {'name': 'Perfectos', 'selector':'Perfectos', 'formato':'entero'},
                        {'name': '% Perfectos', 'selector':'Porc_Perfectos', 'formato':'porcentaje'},
                        {'name': 'UpSells', 'selector':'UpSells', 'formato':'entero'},
                        {'name': '% UpSells', 'selector':'Porc_UpSells', 'formato':'porcentaje'},
                        {'name': 'No Imputable a Tienda', 'selector':'No_Imputable_a_Tienda', 'formato':'entero'},
                        {'name': '% No Imputable a Tienda', 'selector':'Porc_No_Imputable_a_Tienda', 'formato':'porcentaje'},
                        {'name': '% Objetivo PP', 'selector':'Porc_Objetivo_PP', 'formato':'porcentaje'}
                    ]
                    data = []
                    for row in arreglo:
                        incidentes = row['incidentes'] if row['incidentes'] != None else 0
                        porc_incidentes = row['porc_incidentes'] if row['porc_incidentes'] != None else 0
                        upSells = row['upSells'] if row['upSells'] != None else 0
                        porc_upSells = row['porc_upSells'] if row['porc_upSells'] != None else 0
                        no_imputable = row['no_imputable'] if row['no_imputable'] != None else 0
                        porc_no_imputable = row['porc_no_imputable'] if row['porc_no_imputable'] != None else 0
                        porc_objetivo = float(row['porc_objetivo']) / 100 if row['porc_objetivo'] != None else 0
                        cambiar_lugar = json.dumps({
                            'region': {
                                'label': row['_id']['regionNombre'],
                                'value': row['_id']['region']
                            },
                            'zona': {
                                'label': row['_id']['zonaNombre'],
                                'value': row['_id']['zona']
                            },
                            'tienda': {
                                'label': row['_id']['tiendaNombre'],
                                'value': row['_id']['idtienda']
                            }
                        }).replace('"', '""')
                        data.append({
                            'Region': row['_id']['regionNombre'],
                            'Zona': row['_id']['zonaNombre'],
                            'Tienda': row['_id']['tiendaNombre'],
                            'sibling': cambiar_lugar,
                            # 'Tienda': row['_id']['tiendaNombre'],
                            'Totales': row['totales'],
                            'Quejas': row['quejas'],
                            'Porc_Quejas': row['porc_quejas'],
                            'Retrasados': row['retrasados'],
                            'Porc_Retrasados': row['porc_retrasados'],
                            'Cancelados': row['cancelados'],
                            'Porc_Cancelados': row['porc_cancelados'],
                            'Entregados': row['entregados'],
                            'Incompletos': row['incompletos'],
                            'Porc_Incompletos': row['porc_incompletos'],
                            'Incidentes': incidentes,
                            'Porc_Incidentes': porc_incidentes,
                            'Perfectos': row['perfectos'],
                            'Porc_Perfectos': row['porc_perfectos'],
                            'UpSells': upSells,
                            'Porc_UpSells': porc_upSells,
                            'No_Imputable_a_Tienda': no_imputable,
                            'Porc_No_Imputable_a_Tienda': porc_no_imputable,
                            'Porc_Objetivo_PP': porc_objetivo
                        })
                else:
                    hayResultados = 'no'
            else:
                hayResultados = 'no'

        if self.titulo == '$Tienda':
            if self.filtros.periodo != {}:
                # Crear una función que, para un año determinado, devuelva la fecha inicial y final del horario de verano, que comienza el primer domingo de abril y termina el último domingo de octubre a las 2:00 a.m.
                def verano(anio):
                    mesIni = monthcalendar(anio, 4)
                    mesFin = monthcalendar(anio, 10)
                    diaIni = mesIni[0][-1] # El 0 es la primera semana, y el -1 es el domingo
                    diaFin = max(mesFin[-1][-1], mesFin[-2][-1]) # El primer -1 es la última semana del calendario, y el segundo -1 es el domingo, pero si la última semana del calendario no hubo domingo, se utiliza la penúltima
                    return [datetime(anio, 4, diaIni, 2, 0, 0, 0), datetime(anio, 10, diaFin, 2, 0, 0, 0)]
                collection = conexion_mongo('report').report_detallePedidos
                # print("self.filtros.periodo desde Tabla: "+str(self.filtros.periodo))
                pipeline = [{'$match': {'idtienda': int(self.filtros.tienda)}}]
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$and': []
                        }
                    }},
                    {'$project': {
                        'fechaPP': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaPP'}},
                        'nPedido': '$nPedido',
                        'nConsigna': '$nConsigna',
                        # Vamos a cambiar esto para restar 6 horas a las fechas que vienen en la bd (5 en horario de verano)
                        'timeslot_from': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_from'}},
                        'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_to'}},
                        # 'timeslot_from': { 
                        #     '$cond': []
                        # },
                        # 'timeslot_to': { 
                        #     '$cond': []
                        # },
                        'metodoEntrega': '$metodoEntrega',
                        'estatusConsigna': '$estatusConsigna',
                        'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                        'fechaDespacho': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaDespacho'}},
                        'evaluacion': '$evaluacion',
                        'motivo_cancelacion': '$motivo_cancelacion',
                        'quejas': '$quejas',
                        'Entregados': '$Entregados',
                        'incidendiasNPS': '$incidendiasNPS',
                        'perfecto': '$perfecto',
                        'noImputableTienda': '$noImputableTienda',
                        'objetivoPP': '$objetivoPP'
                    }},
                    {'$sort': {
                        'nPedido': 1
                    }}
                ])
                # Pon las condiciones anidadas para cada año de 2020 a la fecha, para saber si le restas 5 horas a la fecha o 6.
                # condicionFrom = pipeline[-2]['$project']['timeslot_from']['$cond']
                # condicionTo = pipeline[-2]['$project']['timeslot_to']['$cond']
                # for anio in range(2020, date.today().year + 1):
                #     condicionFrom.extend([
                #         {'$eq': [{'$year': '$timeslot_from'}, anio]},
                #         {'$cond': [
                #             {'$and': [
                #                 {'$gte': [
                #                     '$timeslot_from',
                #                     verano(anio)[0]
                #                 ]},
                #                 {'$lte': [
                #                     '$timeslot_from',
                #                     verano(anio)[1]
                #                 ]},
                #             ]},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_from',
                #                     'unit': 'hour',
                #                     'amount': 5
                #                 }
                #             }}},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_from',
                #                     'unit': 'hour',
                #                     'amount': 6
                #                 }
                #             }}}
                #         ]},
                #         {'$cond': []}
                #     ])
                #     condicionFrom = condicionFrom[-1]['$cond']
                #     condicionTo.extend([
                #         {'$eq': [{'$year': '$timeslot_to'}, anio]},
                #         {'$cond': [
                #             {'$and': [
                #                 {'$gte': [
                #                     '$timeslot_to',
                #                     verano(anio)[0]
                #                 ]},
                #                 {'$lte': [
                #                     '$timeslot_to',
                #                     verano(anio)[1]
                #                 ]},
                #             ]},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_to',
                #                     'unit': 'hour',
                #                     'amount': 5
                #                 }
                #             }}},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_to',
                #                     'unit': 'hour',
                #                     'amount': 6
                #                 }
                #             }}}
                #         ]},
                #         {'$cond': []}
                #     ])
                #     condicionTo = condicionTo[-1]['$cond']
                # condicionFrom.extend([
                #     True, 
                #     {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #         '$dateSubtract': {
                #             'startDate': '$timeslot_from',
                #             'unit': 'hour',
                #             'amount': 6
                #         }
                #     }}},
                #     None
                # ])
                # condicionTo.extend([
                #     True, 
                #     {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #         '$dateSubtract': {
                #             'startDate': '$timeslot_to',
                #             'unit': 'hour',
                #             'amount': 6
                #         }
                #     }}},
                #     None
                # ])

                # Creamos variables para manipular los diccionarios:
                match = pipeline[-3]['$match']['$expr']['$and']
                
                # Modificamos el pipeline para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio = self.filtros.periodo['anio']
                    mes = self.filtros.periodo['mes']
                    match.extend([
                        {'$eq': [
                            anio,
                            {'$year': '$fechaPP'}
                        ]},
                        {'$eq': [
                            mes,
                            {'$month': '$fechaPP'}
                        ]}
                    ])
                # Modificamos el pipeline para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana = self.filtros.periodo['semana']
                    match.extend([
                        {'$eq': [
                            semana,
                            '$idSemDSPP'
                        ]}
                    ])
                # Modificamos el pipeline para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio = self.filtros.periodo['anio']
                    mes = self.filtros.periodo['mes']
                    dia = self.filtros.periodo['dia']
                    match.extend([
                        {'$eq': [
                            anio,
                            {'$year': '$fechaPP'}
                        ]},
                        {'$eq': [
                            mes,
                            {'$month': '$fechaPP'}
                        ]},
                        {'$eq': [
                            dia,
                            {'$dayOfMonth': '$fechaPP'}
                        ]}
                    ])
                # print(f"Pipeline desde Tablas -> PedidoPerfecto -> {self.titulo}: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=None)
                # print(f"Arreglo desde Tablas -> PedidoPerfecto -> {self.titulo}: {str(arreglo)}")
                if len(arreglo) >0:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán la tabla:
                    columns = [
                        {'name': 'Fecha', 'selector':'Fecha', 'formato':'texto'},
                        {'name': 'No. Pedido', 'selector':'NumPedido', 'formato':'sinComas'},
                        {'name': 'No. Consigna', 'selector':'NumConsigna', 'formato':'texto', 'ancho': '140px'},
                        {'name': 'Timeslot From', 'selector':'TimeslotFrom', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Timeslot To', 'selector':'TimeslotTo', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Método de Entrega', 'selector':'MetodoEntrega', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Estatus Consigna', 'selector':'EstatusConsigna', 'formato':'texto', 'ancho': '180px'},
                        {'name': 'Fecha de Entrega', 'selector':'FechaEntrega', 'formato':'texto'},
                        {'name': 'Fecha de Despacho', 'selector':'FechaDespacho', 'formato':'texto'},
                        {'name': 'Evaluación', 'selector':'Evaluacion', 'formato':'texto', 'ancho': '240px'},
                        {'name': 'Cancelados', 'selector':'Cancelados', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Quejas', 'selector':'Quejas', 'formato':'texto', 'ancho': '250px'},
                        {'name': 'Entregados', 'selector':'Entregados', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Incidencias NPS', 'selector':'IncidentesNPS', 'formato':'texto'},
                        {'name': 'Perfectos', 'selector':'Perfectos', 'formato':'texto'},
                        {'name': 'No Imputable a Tienda', 'selector':'NoImputableATienda', 'formato':'texto'},
                        {'name': '% Objetivo PP', 'selector':'ObjetivoPP', 'formato':'porcentaje'}
                    ]
                    data = []
                    for row in arreglo:
                        fechaPP = row['fechaPP'] if 'fechaPP' in row else '--'
                        nPedido = row['nPedido'] if 'nPedido' in row else '--'
                        nConsigna = row['nConsigna'] if 'nConsigna' in row else '--'
                        timeslot_from = row['timeslot_from'] if 'timeslot_from' in row else '--'
                        timeslot_to = row['timeslot_to'] if 'timeslot_to' in row else '--'
                        metodoEntrega = row['metodoEntrega'] if 'metodoEntrega' in row else '--'
                        estatusConsigna = row['estatusConsigna'] if 'estatusConsigna' in row else '--'
                        fechaEntrega = row['fechaEntrega'] if 'fechaEntrega' in row else '--'
                        fechaDespacho = row['fechaDespacho'] if 'fechaDespacho' in row else '--'
                        evaluacion = row['evaluacion'] if 'evaluacion' in row else '--'
                        motivo_cancelacion = row['motivo_cancelacion'] if 'motivo_cancelacion' in row else '--'
                        quejas = row['quejas'] if 'quejas' in row else '--'
                        Entregados = row['Entregados'] if 'Entregados' in row else '--'
                        incidendiasNPS = row['incidendiasNPS'] if 'incidendiasNPS' in row else '--'
                        perfecto = row['perfecto'] if 'perfecto' in row else '--'
                        noImputableTienda = row['noImputableTienda'] if 'noImputableTienda' in row else '--'
                        objetivoPP = float(row['objetivoPP']) / 100 if 'objetivoPP' in row else '--'

                        data.append({
                            'Fecha': fechaPP,
                            'NumPedido': nPedido,
                            'NumConsigna': nConsigna,
                            'TimeslotFrom': timeslot_from,
                            'TimeslotTo': timeslot_to,
                            'MetodoEntrega': metodoEntrega,
                            'EstatusConsigna': estatusConsigna,
                            'FechaEntrega': fechaEntrega,
                            'FechaDespacho': fechaDespacho,
                            'Evaluacion': evaluacion,
                            'Cancelados': motivo_cancelacion,
                            'Quejas': quejas,
                            # 'Atrasados
                            'Entregados': Entregados,
                            # 'Incompletos
                            'IncidentesNPS': incidendiasNPS,
                            'Perfectos': perfecto,
                            'NoImputableATienda': noImputableTienda,
                            'ObjetivoPP': objetivoPP
                        })
                else:
                    hayResultados = 'no'
            else:
                hayResultados = 'no'
        # print(f"Query desde tabla {self.titulo} en pedidoPerfecto: {str(pipeline)}")
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def OnTimeInFull(self):
        pipeline = []
        data = []
        columns = []
        hayResultados = 'sí'
        if self.titulo == 'Pedidos Fuera de Tiempo':
            if self.filtros.periodo == {}:
                return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': []}
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False"  and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        lugar_sql = f"AND ct.tienda = {self.filtros.tienda}"
                    else:
                        lugar_sql = f"AND ct.zona = {self.filtros.zona}"
                else:
                    lugar_sql = f"AND ct.region = {self.filtros.region}"
            else:
                lugar_sql = ''
            cnxn = conexion_sql('DWH')
            if self.filtros.agrupador == 'semana':
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
            select ct.regionNombre, ct.zonaNombre, ct.tiendaNombre, ho.ultimo_cambio, ho.order_number, de.descrip_delviery_mode, ho.fin_picking, ho.timeslot_from, ho.fin_entrega, ho.timeslot_to
                from DWH.dbo.hecho_order ho
                LEFT JOIN DWH.artus.catTienda ct on ct.tienda=ho.store_num
                left join DWH.dbo.dim_estatus de on de.id_estatus = ho.id_estatus
                LEFT JOIN DWH.dbo.dim_tiempo dt on dt.fecha = CONVERT(date, creation_date)
                where ho.evaluacion = 'Entregado-Fuera de tiempo'
                AND {where}
                {lugar_sql}
                order by ho.ultimo_cambio desc
            """
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            # print(str(arreglo))
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    ultimo_cambio = row['ultimo_cambio'].strftime("%d/%m/%Y %H:%M") if row['ultimo_cambio'] is not None else '--'
                    fin_picking = row['fin_picking'].strftime("%d/%m/%Y %H:%M") if row['fin_picking'] is not None else '--'
                    timeslot_from = row['timeslot_from'].strftime("%d/%m/%Y %H:%M") if row['timeslot_from'] is not None else '--'
                    fin_entrega = row['fin_entrega'].strftime("%d/%m/%Y %H:%M") if row['fin_entrega'] is not None else '--'
                    timeslot_to = row['timeslot_to'].strftime("%d/%m/%Y %H:%M") if row['timeslot_to'] is not None else '--'
                    data.append({
                        'Region': row['regionNombre'],
                        'Zona': row['zonaNombre'],
                        'Tienda': row['tiendaNombre'],
                        'UltimoCambio': ultimo_cambio,
                        'NumeroDeOrden': row['order_number'],
                        'ModoDeEntrega': row['descrip_delviery_mode'],
                        'FinDePicking': fin_picking,
                        'InicioTimeslot': timeslot_from,
                        'FinDeEntrega': fin_entrega,
                        'FinTimeslot': timeslot_to,
                    })
                    columns = [
                        {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho': '220px'},
                        {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho': '220px'},
                        {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '420px'},
                        {'name': 'Último Cambio', 'selector':'UltimoCambio', 'formato':'texto'},
                        {'name': 'Número De Orden', 'selector':'NumeroDeOrden', 'formato':'entero'},
                        {'name': 'Modo De Entrega', 'selector':'ModoDeEntrega', 'formato':'texto'},
                        {'name': 'Fin De Picking', 'selector':'FinDePicking', 'formato':'texto'},
                        {'name': 'Inicio Timeslot', 'selector':'InicioTimeslot', 'formato':'texto'},
                        {'name': 'Fin De Entrega', 'selector':'FinDeEntrega', 'formato':'texto'},
                        {'name': 'Fin Timeslot', 'selector':'FinTimeslot', 'formato':'texto'},
                    ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Tiendas por % A Tiempo y Completo más bajo':
            if self.filtros.periodo != {}:
                collection = conexion_mongo('report').report_pedidoPerfecto
                if self.filtros.region != '' and self.filtros.region != "False":
                    # print('Sí hay región, y es: '+self.filtros.region)
                    filtro_lugar = True
                    if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                        if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                            nivel = 'idtienda'
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
                    # print('No hay filtro_lugar')
                pipeline = [{'$unwind': '$sucursal'}]
                if filtro_lugar:
                    pipeline.extend([
                        {'$match': {'sucursal.'+ nivel: lugar}}
                    ])
                # print("self.filtros.periodo desde Tabla: "+str(self.filtros.periodo))
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$and': []
                        }
                    }},
                    {'$group': {
                        '_id': {
                            'regionNombre': '$sucursal.regionNombre',
                            'zonaNombre': '$sucursal.zonaNombre',
                            'tiendaNombre': '$sucursal.tiendaNombre',
                            'region': '$sucursal.region',
                            'zona': '$sucursal.zona',
                            'idtienda': '$sucursal.idtienda'
                        },
                        'totales': {
                            '$sum': '$Total_Pedidos'
                        },
                        'retrasados': {
                            '$sum': '$retrasados'
                        },
                        'cancelados': {
                            '$sum': '$Cancelados'
                        },
                        'entregados': {
                            '$sum': '$Total_Entregados'
                        },
                        'incompletos': {
                            '$sum': '$incompletos'
                        },
                        'upSells': {
                            '$sum': '$upSells'
                        }
                    }},
                    {'$project': {
                        '_id': '$_id',
                        'totales': '$totales',
                        'quejas': '$quejas',
                        'retrasados': '$retrasados',
                        'porc_retrasados':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$retrasados', '$totales']}]},
                        'entregados': '$entregados',
                        'incompletos': '$incompletos',
                        'porc_incompletos':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$incompletos', '$totales']}]},
                        'otif': {'$subtract': ['$totales', {'$add': ['$incompletos', '$retrasados']}]},
                        'porc_otif':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': [{'$subtract': ['$totales', {'$add': ['$incompletos', '$retrasados']}]}, '$totales']}]},
                        'upSells': '$upSells',
                        'porc_upSells':  { '$cond': [ { '$eq': [ "$totales", 0 ] }, "--", {'$divide': ['$upSells', '$totales']}]},
                        # 'porc_objetivo': 90 # Parece que no se puede poner un número dentro de un aggregation de MongoDB
                    }},
                    {'$sort': {
                        'porc_otif': 1
                    }}
                ])
                # Creamos variables para manipular los diccionarios:
                match = pipeline[-4]['$match']['$expr']['$and']
                
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
                # Modificamos el pipeline para el caso de que el agrupador sea por día:
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
                # print(str(pipeline))
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=None)
                # print(str(arreglo))
                if len(arreglo) >0:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán la tabla:
                    columns = [
                        {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho': '220px'},
                        {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho': '220px'},
                        {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '420px'},
                        {'name': 'Ver Detalle de Tienda', 'selector':'sibling', 'formato':'sibling'},
                        {'name': 'Total Pedidos', 'selector':'Totales', 'formato':'entero'},
                        {'name': 'Retrasados', 'selector':'Retrasados', 'formato':'entero'},
                        {'name': '% Retrasados', 'selector':'Porc_Retrasados', 'formato':'porcentaje'},
                        {'name': 'Entregados', 'selector':'Entregados', 'formato':'entero'},
                        {'name': 'Incompletos', 'selector':'Incompletos', 'formato':'entero'},
                        {'name': '% Incompletos', 'selector':'Porc_Incompletos', 'formato':'porcentaje'},
                        {'name': 'ATYC', 'selector':'ATYC', 'formato':'entero'},
                        {'name': '% ATYC', 'selector':'Porc_ATYC', 'formato':'porcentaje'},
                        {'name': 'UpSells', 'selector':'UpSells', 'formato':'entero'},
                        {'name': '% UpSells', 'selector':'Porc_UpSells', 'formato':'porcentaje'},
                        {'name': '% Objetivo ATYC', 'selector':'Porc_Objetivo_ATYC', 'formato':'porcentaje'}
                    ]
                    data = []
                    for row in arreglo:
                        upSells = row['upSells'] if row['upSells'] != None else 0
                        porc_upSells = row['porc_upSells'] if row['porc_upSells'] != None else 0
                        # porc_objetivo = float(row['porc_objetivo']) / 100 if row['porc_objetivo'] != None else 0
                        porc_objetivo = 0.9
                        if 'regionNombre' in row['_id']:
                            cambiar_lugar = json.dumps({
                                'region': {
                                    'label': row['_id']['regionNombre'],
                                    'value': row['_id']['region']
                                },
                                'zona': {
                                    'label': row['_id']['zonaNombre'],
                                    'value': row['_id']['zona']
                                },
                                'tienda': {
                                    'label': row['_id']['tiendaNombre'],
                                    'value': row['_id']['idtienda']
                                }
                            }).replace('"', '""')
                            data.append({
                                'Region': row['_id']['regionNombre'],
                                'Zona': row['_id']['zonaNombre'],
                                'Tienda': row['_id']['tiendaNombre'],
                                'sibling': cambiar_lugar,
                                # 'Tienda': row['_id']['tiendaNombre'],
                                'Totales': row['totales'],
                                'Retrasados': row['retrasados'],
                                'Porc_Retrasados': row['porc_retrasados'],
                                'Entregados': row['entregados'],
                                'Incompletos': row['incompletos'],
                                'Porc_Incompletos': row['porc_incompletos'],
                                'ATYC': row['otif'],
                                'Porc_ATYC': row['porc_otif'],
                                'UpSells': upSells,
                                'Porc_UpSells': porc_upSells,
                                'Porc_Objetivo_ATYC': porc_objetivo
                            })
                        else:
                            hayResultados = 'no'
                else:
                    hayResultados = 'no'
            else:
                hayResultados = 'no'

        if self.titulo == '$Tienda':
            if self.filtros.periodo != {}:
                # Crear una función que, para un año determinado, devuelva la fecha inicial y final del horario de verano, que comienza el primer domingo de abril y termina el último domingo de octubre a las 2:00 a.m.
                def verano(anio):
                    mesIni = monthcalendar(anio, 4)
                    mesFin = monthcalendar(anio, 10)
                    diaIni = mesIni[0][-1] # El 0 es la primera semana, y el -1 es el domingo
                    diaFin = max(mesFin[-1][-1], mesFin[-2][-1]) # El primer -1 es la última semana del calendario, y el segundo -1 es el domingo, pero si la última semana del calendario no hubo domingo, se utiliza la penúltima
                    return [datetime(anio, 4, diaIni, 2, 0, 0, 0), datetime(anio, 10, diaFin, 2, 0, 0, 0)]
                collection = conexion_mongo('report').report_detallePedidos
                # print("self.filtros.periodo desde Tabla: "+str(self.filtros.periodo))
                pipeline = [{'$match': {'idtienda': int(self.filtros.tienda)}}]
                pipeline.extend([
                    {'$match': {
                        '$expr': {
                            '$and': []
                        }
                    }},
                    {'$project': {
                        'fechaATYC': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaPP'}},
                        'nPedido': '$nPedido',
                        'nConsigna': '$nConsigna',
                        # Vamos a cambiar esto para restar 6 horas a las fechas que vienen en la bd (5 en horario de verano)
                        'timeslot_from': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_from'}},
                        'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_to'}},
                        # 'timeslot_from': { 
                        #     '$cond': []
                        # },
                        # 'timeslot_to': { 
                        #     '$cond': []
                        # },
                        'metodoEntrega': '$metodoEntrega',
                        'estatusConsigna': '$estatusConsigna',
                        'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                        'fechaDespacho': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaDespacho'}},
                        'Entregados': '$Entregados',
                        'evaluacion': '$evaluacion',
                        'objetivoPP': '$objetivoPP',
                        'otif': {
                            '$cond': [
                                {
                                    '$and': [
                                        {'$eq': ['$Entregados', 'COMPLETO']}, 
                                        {'$or': [
                                            {'$eq': ['$evaluacion', 'Despachado-A tiempo']},
                                            {'$eq': ['$evaluacion', 'Entregado-A tiempo']}
                                        ]} 
                                    ]
                                },
                                'Sí', 
                                'No'
                            ]
                        }
                    }},
                    {'$sort': {
                        'nPedido': 1
                    }}
                ])
                # Pon las condiciones anidadas para cada año de 2020 a la fecha, para saber si le restas 5 horas a la fecha o 6.
                # condicionFrom = pipeline[-2]['$project']['timeslot_from']['$cond']
                # condicionTo = pipeline[-2]['$project']['timeslot_to']['$cond']
                # for anio in range(2020, date.today().year + 1):
                #     condicionFrom.extend([
                #         {'$eq': [{'$year': '$timeslot_from'}, anio]},
                #         {'$cond': [
                #             {'$and': [
                #                 {'$gte': [
                #                     '$timeslot_from',
                #                     verano(anio)[0]
                #                 ]},
                #                 {'$lte': [
                #                     '$timeslot_from',
                #                     verano(anio)[1]
                #                 ]},
                #             ]},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_from',
                #                     'unit': 'hour',
                #                     'amount': 5
                #                 }
                #             }}},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_from',
                #                     'unit': 'hour',
                #                     'amount': 6
                #                 }
                #             }}}
                #         ]},
                #         {'$cond': []}
                #     ])
                #     condicionFrom = condicionFrom[-1]['$cond']
                #     condicionTo.extend([
                #         {'$eq': [{'$year': '$timeslot_to'}, anio]},
                #         {'$cond': [
                #             {'$and': [
                #                 {'$gte': [
                #                     '$timeslot_to',
                #                     verano(anio)[0]
                #                 ]},
                #                 {'$lte': [
                #                     '$timeslot_to',
                #                     verano(anio)[1]
                #                 ]},
                #             ]},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_to',
                #                     'unit': 'hour',
                #                     'amount': 5
                #                 }
                #             }}},
                #             {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #                 '$dateSubtract': {
                #                     'startDate': '$timeslot_to',
                #                     'unit': 'hour',
                #                     'amount': 6
                #                 }
                #             }}}
                #         ]},
                #         {'$cond': []}
                #     ])
                #     condicionTo = condicionTo[-1]['$cond']
                # condicionFrom.extend([
                #     True, 
                #     {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #         '$dateSubtract': {
                #             'startDate': '$timeslot_from',
                #             'unit': 'hour',
                #             'amount': 6
                #         }
                #     }}},
                #     None
                # ])
                # condicionTo.extend([
                #     True, 
                #     {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': {
                #         '$dateSubtract': {
                #             'startDate': '$timeslot_to',
                #             'unit': 'hour',
                #             'amount': 6
                #         }
                #     }}},
                #     None
                # ])

                # Creamos variables para manipular los diccionarios:
                match = pipeline[-3]['$match']['$expr']['$and']
                
                # Modificamos el pipeline para el caso de que el agrupador sea por mes:
                if self.filtros.agrupador == 'mes':
                    anio = self.filtros.periodo['anio']
                    mes = self.filtros.periodo['mes']
                    match.extend([
                        {'$eq': [
                            anio,
                            {'$year': '$fechaATYC'}
                        ]},
                        {'$eq': [
                            mes,
                            {'$month': '$fechaATYC'}
                        ]}
                    ])
                # Modificamos el pipeline para el caso de que el agrupador sea por semana:
                elif self.filtros.agrupador == 'semana':
                    semana = self.filtros.periodo['semana']
                    match.extend([
                        {'$eq': [
                            semana,
                            '$idSemDSPP'
                        ]}
                    ])
                # Modificamos el pipeline para el caso de que el agrupador sea por día:
                elif self.filtros.agrupador == 'dia':
                    anio = self.filtros.periodo['anio']
                    mes = self.filtros.periodo['mes']
                    dia = self.filtros.periodo['dia']
                    match.extend([
                        {'$eq': [
                            anio,
                            {'$year': '$fechaATYC'}
                        ]},
                        {'$eq': [
                            mes,
                            {'$month': '$fechaATYC'}
                        ]},
                        {'$eq': [
                            dia,
                            {'$dayOfMonth': '$fechaATYC'}
                        ]}
                    ])
                # print(f"pipeline desde tablas -> OnTimeInFull -> $Tienda: {str(pipeline)}")
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=None)
                # print(str(arreglo))
                if len(arreglo) >0:
                    hayResultados = "si"
                    # Creamos los arreglos que alimentarán la tabla:
                    columns = [
                        {'name': 'Fecha', 'selector':'Fecha', 'formato':'texto'},
                        {'name': 'No. Pedido', 'selector':'NumPedido', 'formato':'sinComas'},
                        {'name': 'No. Consigna', 'selector':'NumConsigna', 'formato':'texto', 'ancho': '120px'},
                        {'name': 'Timeslot From', 'selector':'TimeslotFrom', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Timeslot To', 'selector':'TimeslotTo', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Método de Entrega', 'selector':'MetodoEntrega', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Estatus Consigna', 'selector':'EstatusConsigna', 'formato':'texto', 'ancho': '180px'},
                        {'name': 'Fecha de Entrega', 'selector':'FechaEntrega', 'formato':'texto'},
                        {'name': 'Fecha de Despacho', 'selector':'FechaDespacho', 'formato':'texto'},
                        {'name': 'Entregados', 'selector':'Entregados', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Evaluación', 'selector':'Evaluacion', 'formato':'texto', 'ancho': '250px'},
                        {'name': 'ATYC', 'selector':'ATYC', 'formato':'texto'},
                        {'name': '% Objetivo ATYC', 'selector':'Objetivo', 'formato':'porcentaje'}
                    ]
                    data = []
                    for row in arreglo:
                        fechaATYC = row['fechaATYC'] if 'fechaATYC' in row else '--'
                        nPedido = row['nPedido'] if 'nPedido' in row else '--'
                        nConsigna = row['nConsigna'] if 'nConsigna' in row else '--'
                        timeslot_from = row['timeslot_from'] if 'timeslot_from' in row else '--'
                        timeslot_to = row['timeslot_to'] if 'timeslot_to' in row else '--'
                        metodoEntrega = row['metodoEntrega'] if 'metodoEntrega' in row else '--'
                        estatusConsigna = row['estatusConsigna'] if 'estatusConsigna' in row else '--'
                        fechaEntrega = row['fechaEntrega'] if 'fechaEntrega' in row else '--'
                        fechaDespacho = row['fechaDespacho'] if 'fechaDespacho' in row else '--'
                        Entregados = row['Entregados'] if 'Entregados' in row else '--'
                        evaluacion = row['evaluacion'] if 'evaluacion' in row else '--'
                        otif = row['otif'] if 'otif' in row else '--'
                        noImputableTienda = row['noImputableTienda'] if 'noImputableTienda' in row else '--'
                        # objetivoPP = float(row['objetivoPP']) / 100 if 'objetivoPP' in row else '--'
                        objetivo = 0.9

                        data.append({
                            'Fecha': fechaATYC,
                            'NumPedido': nPedido,
                            'NumConsigna': nConsigna,
                            'TimeslotFrom': timeslot_from,
                            'TimeslotTo': timeslot_to,
                            'MetodoEntrega': metodoEntrega,
                            'EstatusConsigna': estatusConsigna,
                            'FechaEntrega': fechaEntrega,
                            'FechaDespacho': fechaDespacho,
                            # 'Atrasados
                            'Entregados': Entregados,
                            'Evaluacion': evaluacion,
                            # 'Incompletos
                            'ATYC': otif,
                            'Objetivo': objetivo
                        })
                else:
                    hayResultados = 'no'
            else:
                hayResultados = 'no'
        # print(f"Query desde tabla {self.titulo} en pedidoPerfecto: {str(pipeline)}")
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def TablaMapas(self):
        data = []
        columns = []
        pipeline = "select nombre, url from DWH.report.mapas where estatus=1 order by nombre"
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(pipeline)
        arreglo = crear_diccionario(cursor)
        # print(str(arreglo))
        if len(arreglo) > 0:
            hayResultados = "si"
            for row in arreglo:
                data.append({
                    'Nombre': row['nombre'],
                    'url': row['url']
                })
                columns = [
                    {'name': 'Nombre', 'selector':'Nombre', 'formato':'texto'},
                    {'name': 'Vínculo', 'selector':'url', 'formato':'url'}
                ]
        else:
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def ReporteFaltantes(self):
        pipeline = []
        data = []
        columns = []
        self.fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        pipeline = f"""select fs.fecha, ct.tienda, ct.regionNombre, ct.zonaNombre, fs.descrip_tienda, fs.sku, fs.Descripcion, fs.DescripDepto, fs.DescripSubdepto,
                fs.DescripClase, fs.pedido_completo, fs.pedido_incompleto, fs.total_pedido, fs.items_ori, fs.items_fin, (fs.FillRate_online*100) FillRate_online,
                fs.items_ori_cornershop, fs.items_fin_cornershop, fs.FillRate_cornershop, fs.vtapzs_tienda, fs.vtapzs_total,
                fs.InvFinUni, fs.pzaDif, fs.InvAnterior, fs.id_respuesta,mfr.respuesta
                from DWH.report.faltante_sku fs
                left join DJANGO.php.motivo_faltante_respuesta mfr on fs.id_respuesta =mfr.id_respuesta
                left join DWH.dbo.dim_store ds on fs.descrip_tienda = ds.descrip_tienda
                left join DWH.artus.catTienda ct on fs.store_num = ct.tienda 
                left join DWH.artus.catMARA cm on fs.sku = cm.SKU 
                where fs.fecha = '{self.fecha_ini}'"""
        if self.filtros.region != '' and self.filtros.region != None:
            pipeline += f" and ct.region = {self.filtros.region}"
        if self.filtros.zona != '' and self.filtros.zona != None:
            pipeline += f" and ct.zona = {self.filtros.zona}"
        if self.filtros.tienda != '' and self.filtros.tienda != None:
            pipeline += f" and ct.tienda = {self.filtros.tienda}"
        if self.filtros.depto != '' and self.filtros.depto != None:
            pipeline += f" and cm.DEPTO = {self.filtros.depto}"
        if self.filtros.subDepto != '' and self.filtros.subDepto != None:
            pipeline += f" and cm.SUBDEPTO = {self.filtros.subDepto}"
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(pipeline)
        arreglo = crear_diccionario(cursor)
        # print(str(arreglo))
        if len(arreglo) > 0:
            hayResultados = "si"
            for row in arreglo:
                data.append({
                    'Fecha': row['fecha'],
                    'IdTienda': row['tienda'],
                    'Region': row['regionNombre'],
                    'Zona': row['zonaNombre'],
                    'Tienda': row['descrip_tienda'],
                    'SKU': row['sku'],
                    'Articulo': row['Descripcion'],
                    'Departamento': row['DescripDepto'],
                    'SubDepartamento': row['DescripSubdepto'],
                    'Clase': row['DescripClase'],
                    'PedidosCompletos': row['pedido_completo'],
                    'PedidosIncompletos': row['pedido_incompleto'],
                    'TotalPedidos': row['total_pedido'],
                    'ItemsIni': row['items_ori'],
                    'ItemsFin': row['items_fin'],
                    'FillRateOnline': row['FillRate_online'],
                    'VtaPzaTienda': row['vtapzs_tienda'],
                    'VtaPzaTotal': row['vtapzs_total'],
                    'InventarioDelDía': row['InvFinUni'],
                    'PzaDiferencia': row['pzaDif'],
                    'InventarioDiaDespues': row['InvAnterior'],
                    'MotivoFaltante': row['respuesta'],
                    # 'CambiarMotivo': {'tienda': row['tienda'], 'sku': row['sku'], 'articulo': row['Descripcion'], 'fecha': row['fecha']}
                    'CambiarMotivo': 0
                })
                columns = [
                    {'name': 'Fecha', 'selector':'Fecha', 'formato':'texto', 'ancho':'110px'},
                    {'name': 'ID Tienda', 'selector':'IdTienda', 'formato':'entero', 'ancho':'70px'},
                    {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho':'220px'},
                    {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho':'220px'},
                    {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho':'420px'},
                    {'name': 'SKU', 'selector':'SKU', 'formato':'entero'},
                    {'name': 'Artículo', 'selector':'Articulo', 'formato':'texto', 'ancho':'400px'},
                    {'name': 'Departamento', 'selector':'Departamento', 'formato':'texto', 'ancho':'220px'},
                    {'name': 'Sub Departamento', 'selector':'SubDepartamento', 'formato':'texto', 'ancho':'250px'},
                    {'name': 'Clase', 'selector':'Clase', 'formato':'texto', 'ancho':'250px'},
                    {'name': 'Pedidos Completos', 'selector':'PedidosCompletos', 'formato':'entero'},
                    {'name': 'Pedidos Incompletos', 'selector':'PedidosIncompletos', 'formato':'entero'},
                    {'name': 'Total de Pedidos', 'selector':'TotalPedidos', 'formato':'entero'},
                    {'name': 'Items Ini', 'selector':'ItemsIni', 'formato':'entero'},
                    {'name': 'Items Fin', 'selector':'ItemsFin', 'formato':'entero'},
                    {'name': 'Fill Rate Online', 'selector':'FillRateOnline', 'formato':'porcentaje'},
                    {'name': 'Vta Pza Tienda', 'selector':'VtaPzaTienda', 'formato':'entero'},
                    {'name': 'Vta Pza Total', 'selector':'VtaPzaTotal', 'formato':'entero'},
                    {'name': 'Inventario del Día', 'selector':'InventarioDelDía', 'formato':'entero'},
                    {'name': 'Pza Diferencia', 'selector':'PzaDiferencia', 'formato':'entero'},
                    {'name': 'Inventario Día Después', 'selector':'InventarioDiaDespues', 'formato':'entero'},
                    {'name': 'Motivo Faltante', 'selector':'MotivoFaltante', 'formato':'texto', 'ancho': '300px'},
                    {'name': 'Cambiar Motivo', 'selector':'CambiarMotivo', 'formato':'botonProducto'}
                ]
        else:
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def PedidoTimeslot(self):
        pipeline = []
        data = []
        columns = []
        if self.titulo == 'Ocupación de Timeslot':
            zona_query = 'Todas'
            tienda_query = 'Todas'
            detalle = 'Día' if self.filtros.detalle == 'dia' else '$timeslot'
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                zona_query = '$zonaNombre'
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    tienda_query = '$tiendaNombre'
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        nivel = 'idtienda'
                        self.lugar = int(self.filtros.tienda)
                    else:
                        nivel = 'zona'
                        self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''
            pipeline_fechas = [
                {'$match': {
                    'fechaEntrega': {
                        '$gte': self.fecha_ini, 
                        '$lt': self.fecha_fin
                    }
                }},
                {'$group': {
                    '_id': '$fechaEntrega'
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            collection = conexion_mongo('report').report_pedidoTimeslot
            cursor_fechas = collection.aggregate(pipeline_fechas)
            resultado_fechas = await cursor_fechas.to_list(length=500)
            pipeline = [
                {'$match': {
                    'fechaEntrega': {
                        '$gte': self.fecha_ini, 
                        '$lt': self.fecha_fin
                    }
                }},
                {'$match': {
                    'tipoEntrega': self.filtros.tipoEntrega2
                }}
            ]
            if self.filtro_lugar:
                pipeline.append(
                    {'$match': {nivel: self.lugar}}
                )
            pipeline.extend([
                {'$project': {
                    'idtienda': '$idtienda',
                    'tiendaNombre': '$tiendaNombre',
                    'zona': '$zona',
                    'zonaNombre': '$zonaNombre',
                    'region': '$region',
                    'regionNombre': '$regionNombre',
                    'timeslot': '$timeslot',
                    'nPedido': '$nPedido',
                    'limit': '$limit'
                    # Aquí falta insertarle los nPedido y limite para cada día
                }},
                {'$group': {
                    '_id': {
                        'Region': '$regionNombre',
                        'Zona': zona_query,
                        'Tienda': tienda_query,
                        'Detalle': detalle
                    },
                    'Capacidad': {'$max': '$limit'}
                    # Aquí falta insertarle la suma de nPedido y limite para cada día
                }},
                {'$project': {
                    '_id': '$_id',
                    # Aquí falta insertarle la capacidad para cada día, que es una división: {'$divide': ['$nPedido', '$limit']}
                    'Capacidad': '$Capacidad'
                    }
                },
                {'$sort': {
                    '_id.Region': 1,
                    '_id.Zona': 1,
                    '_id.Tienda': 1,
                    '_id.Detalle': 1,
                }}
            ])
            fechas = []
            for i in range(len(resultado_fechas)):
                diaActual = resultado_fechas[i]['_id']
                diaSiguiente = diaActual + timedelta(days=1)
                fechas.append({'name': str(diaActual.day) + ' ' + mesTexto(diaActual.month) + ' ' + str(diaActual.year), 'selector': '_'+ str(diaActual.day) + '_' + mesTexto(diaActual.month) + '_' + str(diaActual.year)})
                pipeline[-4]['$project']['p'+str(i)] = {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$gte': ['$fechaEntrega', datetime.combine(diaActual, datetime.min.time())]}, {'$lt': ['$fechaEntrega', datetime.combine(diaSiguiente, datetime.min.time())]}
                            ]
                        }, 
                        'then': {'$sum': '$nPedido'},
                        'else': 0
                    }
                }
                pipeline[-4]['$project']['l'+str(i)] = {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$gte': ['$fechaEntrega', datetime.combine(diaActual, datetime.min.time())]}, {'$lt': ['$fechaEntrega', datetime.combine(diaSiguiente, datetime.min.time())]}
                            ]
                        }, 
                        'then': {'$sum': '$limit'},
                        'else': 0
                    }
                }
                pipeline[-3]['$group']['p'+str(i)] = {'$sum': '$p'+str(i)}
                pipeline[-3]['$group']['l'+str(i)] = {'$sum': '$l'+str(i)}
                pipeline[-2]['$project'][str(i)] = {
                    '$cond': {
                        'if': {'$gt': ['$l'+str(i), 0]},
                        'then': {'$divide': ['$p'+str(i), '$l'+str(i)]},
                        'else': 0
                    }
                }
            # print(str(pipeline))
            # Ejecutamos el query:
            collection = conexion_mongo('report').report_pedidoTimeslot
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            # print(str(arreglo))
            if len(arreglo) >0:
                hayResultados = "si"
                # Creamos los arreglos que alimentarán la tabla:
                columns = [
                    {'name': 'Región', 'selector':'Region', 'formato':'texto', 'colores': False, 'ancho':'220px'},
                    {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'colores': False, 'ancho':'220px'},
                    {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'colores': False, 'ancho':'420px'},
                    {'name': 'Detalle', 'selector':'Detalle', 'formato':'texto', 'colores': False, 'ancho':'70px'},
                    {'name': 'Tipo de Entrega', 'selector':'TipoDeEntrega', 'formato':'texto', 'colores': False, 'ancho':'150px'},
                    {'name': 'Capacidad', 'selector':'Capacidad', 'formato':'entero', 'colores': False}
                    # A esto falta agregarle los días agregados dinámicamente
                ]
                for i in range(len(fechas)):
                    columns.append({'name': fechas[i]['name'], 'selector':fechas[i]['selector'], 'formato':'porcentaje', 'colores': True})
                data = []
                for row in arreglo:
                    diccionario = {
                        'Region': row['_id']['Region'],
                        'Zona': row['_id']['Zona'],
                        'Tienda': row['_id']['Tienda'],
                        'Detalle': row['_id']['Detalle'],
                        'TipoDeEntrega': self.filtros.tipoEntrega2,
                        'Capacidad': row['Capacidad'],
                        # A esto falta agregarle los días agregados dinámicamente
                    }
                    for i in range(len(fechas)):
                        diccionario[fechas[i]['selector']] = row[str(i)]
                    data.append(diccionario)
                # print("Columns desde tablas: "+str(columns))
                # print("Data desde tablas: "+str(data))
                # Cuando colores != [], en el front end se activa una función que pinta las celdas que tengan el valor 'colores': True de la siguiente forma:
                # Si el valor es menor o igual a colores[1], rojo. Si es mayor o igual a colores[2], verde, y amarillo en cualquier otro caso. Eso en el caso de que colores[0] sea 'normal'
                # En el caso de que colores[0] sea 'invertido', es verde si es <= colores[1] y rojo si es >= colores[2]
                # Si 
                # Nota: los porcentajes tienen que estar ya multiplicados por 100
                colores = ['invertido', 60, 80]
            else:
                hayResultados = 'no'
                colores = []
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data, 'colores': colores}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def PedidoDiario(self):
        pipeline = []
        data = []
        columns = []
        if self.titulo == 'Pedido Diario':
            zona_query = 'Todas'
            tienda_query = 'Todas'
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                self.filtro_lugar = True
                zona_query = '$zonaNombre'
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    tienda_query = '$tiendaNombre'
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        nivel = 'tienda'
                        self.lugar = int(self.filtros.tienda)
                    else:
                        nivel = 'zona'
                        self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''
            pipeline_fechas = [
                {'$match': {
                    'fecha': {
                        '$gte': self.fecha_ini, 
                        '$lt': self.fecha_fin
                    }
                }},
                {'$group': {
                    '_id': '$fecha'
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            collection = conexion_mongo('report').report_pedidoDiario
            cursor_fechas = collection.aggregate(pipeline_fechas)
            resultado_fechas = await cursor_fechas.to_list(length=500)
            pipeline = [
                {'$match': {
                    'fecha': {
                        '$gte': self.fecha_ini, 
                        '$lt': self.fecha_fin
                    }
                }},
                {
                    '$unwind': '$sucursal'
                }
            ]
            if self.filtros.tipoEntrega3 != '' and self.filtros.tipoEntrega3 != "False" and self.filtros.tipoEntrega3 != None:
                pipeline.append(
                    {'$match': {'metodoEntrega': self.filtros.tipoEntrega3}}
                )
            if self.filtros.estatus != '' and self.filtros.estatus != "False" and self.filtros.estatus != None:
                pipeline.append(
                    {'$match': {'estatus': self.filtros.estatus}}
                )
            if self.filtro_lugar:
                pipeline.append(
                    {'$match': {'sucursal.'+nivel: self.lugar}}
                )
            pipeline.extend([
                {'$project': {
                    'tienda': '$sucursal.tienda',
                    'tiendaNombre': '$sucursal.tiendaNombre',
                    'zona': '$sucursal.zona',
                    'zonaNombre': '$sucursal.zonaNombre',
                    'region': '$sucursal.region',
                    'regionNombre': '$sucursal.regionNombre',
                    'estatus': '$estatus',
                    'metodoEntrega': '$metodoEntrega',
                    'nPedido': '$nPedido'
                    # Aquí falta insertarle los nPedido para cada día
                }},
                {'$group': {
                    '_id': {
                        'Region': '$regionNombre',
                        'Zona': zona_query,
                        'Tienda': tienda_query,
                        'Estatus': '$estatus',
                        'TipoDeEntrega': '$metodoEntrega'
                    }
                    # Aquí falta insertarle la suma de nPedido para cada día
                }},
                {'$sort': {
                    '_id.Region': 1,
                    '_id.Zona': 1,
                    '_id.Tienda': 1,
                    '_id.Estatus': 1,
                    '_id.TipoDeEntrega': 1
                }}
            ])
            # print(f"Pipeline desde Tablas -> PedidoDiario: {str(pipeline)}")
            fechas = []
            for i in range(len(resultado_fechas)):
                diaActual = resultado_fechas[i]['_id']
                diaSiguiente = diaActual + timedelta(days=1)
                fechas.append({'name': str(diaActual.day) + ' ' + mesTexto(diaActual.month) + ' ' + str(diaActual.year), 'selector': '_'+ str(diaActual.day) + '_' + mesTexto(diaActual.month) + '_' + str(diaActual.year)})
                pipeline[-3]['$project'][str(i)] = {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$gte': ['$fecha', datetime.combine(diaActual, datetime.min.time())]}, {'$lt': ['$fecha', datetime.combine(diaSiguiente, datetime.min.time())]}
                            ]
                        }, 
                        'then': {'$sum': '$nPedido'},
                        'else': 0
                    }
                }
                pipeline[-2]['$group'][str(i)] = {'$sum': '$'+str(i)}
            # print(str(pipeline))
            # Ejecutamos el query:
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            # print(str(arreglo))
            if len(arreglo) >0:
                hayResultados = "si"
                # Creamos los arreglos que alimentarán la tabla:
                columns = [
                    {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho':'220px'},
                    {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho':'220px'},
                    {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho':'420px'},
                    {'name': 'Estatus', 'selector':'Estatus', 'formato':'texto', 'ancho':'150px'},
                    {'name': 'Tipo de Entrega', 'selector':'TipoDeEntrega', 'formato':'texto', 'ancho':'150px'}
                    # A esto falta agregarle los días agregados dinámicamente
                ]
                for i in range(len(fechas)):
                    columns.append({'name': fechas[i]['name'], 'selector':fechas[i]['selector'], 'formato':'entero'})
                data = []
                for row in arreglo:
                    diccionario = {
                        'Region': row['_id']['Region'],
                        'Zona': row['_id']['Zona'],
                        'Tienda': row['_id']['Tienda'],
                        'Estatus': row['_id']['Estatus'],
                        'TipoDeEntrega': row['_id']['TipoDeEntrega']
                        # A esto falta agregarle los días agregados dinámicamente
                    }
                    for i in range(len(fechas)):
                        diccionario[fechas[i]['selector']] = row[str(i)]
                    data.append(diccionario)
                # print("Columns desde tablas: "+str(columns))
                # print("Data desde tablas: "+str(data))
                # print(f"Pipeline desde tablas -> PedidoDiario: {str(pipeline)}")
            else:
                hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def NPSDetalle(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idtienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
            self.lugar = ''
        pipeline = [
            {'$unwind': '$sucursal'},
            {'$match': {
                '$expr': {
                    '$and': [
                        {'$gte': [
                            {'$dateFromString': {
                                'dateString': '$fechaCreacion',
                                'format': '%Y-%m-%d'
                            }},
                            self.fecha_ini
                        ]},
                        {'$lt': [
                            {'$dateFromString': {
                                'dateString': '$fechaCreacion',
                                'format': '%Y-%m-%d'
                            }},
                            self.fecha_fin
                        ]}
                    ]
                }
            }}
        ]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {'sucursal.'+nivel: self.lugar}}
            )
        caminos = ['R1', 'R1A', 'R1B', 'R1C', 'R1D', 'R1E', 'R1F', 'R1G', 'R1H', 'R1I', 'R1J', 'R2', 'R2A', 'R2B', 'R2C', 'R2D', 'R2E', 'R2F', 'R2G', 'R2H', 'R2I', 'R3', 'R3A', 'R3B', 'R3C', 'R3D', 'R3E', 'R3F', 'R3G', 'R4', 'R4A', 'R4B', 'R4C', 'R4D', 'R4E', 'R4F', 'R5', 'R5A', 'R5B', 'R5C', 'R5D', 'R5E', 'R5F', 'R5G', 'R5H', 'R6', 'R6A', 'R6B', 'R6C', 'R6D', 'R6E', 'R6F', 'R6G', 'R7', 'R7A', 'R7B', 'R7C', 'R7D', 'R7E', 'R7F', 'R7G', 'R7H', 'R7I', 'R8', 'R8A', 'R8B', 'R8C', 'R8D', 'R8E', 'R8F', 'R8G', 'R8H', 'R8I', 'R9', 'R9A', 'R9B', 'R9C', 'R9D', 'R9E', 'R9F', 'R10']
        pipeline.append({
            '$project': {
                'TipoCliente': '$TipoCliente',
                'calificacion': '$calificacion',
                'canal': '$canal',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'regionNombre': '$sucursal.regionNombre',
                'nombreCliente': '$name',
                'pedido': '$pedido',
                'timeslot_from': '$timeslot_from',
                'timeslot_to': '$timeslot_to',
                'MetodoEntrega': '$MetodoEntrega',
                'EstatusPedido': '$EstatusPedido',
                'FechaCreacion': '$fechaCreacion',
                'FechaEntrega': '$FechaEntrega',
                'FechaDespacho': '$FechaDespacho',
                'EvaluacionEntrega': '$EvaluacionEntrega',
                'Queja': '$Queja',
                'estatus': '$estatus',
                'NPS': '$NPS',
                'TipoPedido': '$TipoPedido',
                'NoImputableTienda': '$NoImputableTienda',
                'comentario': '$comentario',
                'FechaEnvio': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$FechaEnvio'}},
                'id_encuesta': '$id_encuesta'
            }
        })
        # print(f"pipeline[-1]['$project'] desde tablas -> NPSDetalle: {str(pipeline[-1]['$project'])}")
        for camino in caminos:
            # print(f"'$' + camino desde tablas -> NPSDetalle: {'$' + camino}")
            pipeline[-1]['$project'][camino] = '$' + camino
            # print(f"pipeline[-1]['$project'][camino] desde tablas -> NPSDetalle: {str(pipeline[-1]['$project'][camino])}")
        # print(f"pipeline desde tablas -> NPSDetalle: {str(pipeline)}")
        # Ejecutamos el query:
        collection = conexion_mongo('report').report_pedidoDetalleNPS
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=None)
        # print(str(arreglo))
        if len(arreglo) >0:
            hayResultados = "si"
            # Creamos los arreglos que alimentarán la tabla:
            columns = [
                {'name': 'Tipo Cliente', 'selector':'TipoCliente', 'formato':'texto', 'ancho': '150px'},
                {'name': 'Calificación', 'selector':'calificacion', 'formato':'entero'},
                {'name': 'Canal', 'selector':'canal', 'formato':'texto'},
                {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho':'420px'},
                {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho':'220px'},
                {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho':'220px'},
                {'name': 'Nombre Cliente', 'selector':'nombreCliente', 'formato':'texto'},
                {'name': 'Pedido', 'selector':'pedido', 'formato':'sinComas', 'ancho': '140px'},
                {'name': 'Timeslot From', 'selector':'timeslot_from', 'formato':'texto', 'ancho': '170px'},
                {'name': 'Timeslot To', 'selector':'timeslot_to', 'formato':'texto', 'ancho': '170px'},
                {'name': 'Método Entrega', 'selector':'MetodoEntrega', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Estatus Pedido', 'selector':'EstatusPedido', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Fecha Creación', 'selector':'FechaCreacion', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Fecha Entrega', 'selector':'FechaEntrega', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Fecha Despacho', 'selector':'FechaDespacho', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Evaluación Entrega', 'selector':'EvaluacionEntrega', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Queja', 'selector':'Queja', 'formato':'texto'},
                {'name': 'Estatus', 'selector':'estatus', 'formato':'texto', 'ancho': '200px'},
                {'name': 'NPS', 'selector':'NPS', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Tipo Pedido', 'selector':'TipoPedido', 'formato':'texto', 'ancho': '200px'},
                {'name': 'No Imputable a Tienda', 'selector':'NoImputableTienda', 'formato':'texto', 'ancho': '200px'}
            ]
            for camino in caminos:
                columns.append({'name': camino, 'selector':camino, 'formato':'texto', 'ancho': '350px'})
            columns.extend([
                {'name': 'Comentario', 'selector':'comentario', 'formato':'texto', 'ancho': '1000px'},
                {'name': 'Fecha de Envío', 'selector':'FechaEnvio', 'formato':'texto', 'ancho': '150px'},
                {'name': 'ID Encuesta', 'selector':'id_encuesta', 'formato':'entero'}
            ])
            data = []
            for row in arreglo:
                TipoCliente = row['TipoCliente'] if 'TipoCliente' in row else '--'
                calificacion = row['calificacion'] if 'calificacion' in row else '--'
                canal = row['canal'] if 'canal' in row else '--'
                tiendaNombre = row['tiendaNombre'] if 'tiendaNombre' in row else '--'
                zonaNombre = row['zonaNombre'] if 'zonaNombre' in row else '--'
                regionNombre = row['regionNombre'] if 'regionNombre' in row else '--'
                nombreCliente = row['nombreCliente'] if 'nombreCliente' in row else '--'
                pedido = row['pedido'] if 'pedido' in row else '--'
                timeslot_from = row['timeslot_from'] if 'timeslot_from' in row else '--'
                timeslot_to = row['timeslot_to'] if 'timeslot_to' in row else '--'
                MetodoEntrega = row['MetodoEntrega'] if 'MetodoEntrega' in row else '--'
                EstatusPedido = row['EstatusPedido'] if 'EstatusPedido' in row else '--'
                FechaEntrega = row['FechaEntrega'] if 'FechaEntrega' in row else '--'
                FechaCreacion = row['FechaCreacion'] if 'FechaCreacion' in row else '--'
                FechaDespacho = row['FechaDespacho'] if 'FechaDespacho' in row else '--'
                EvaluacionEntrega = row['EvaluacionEntrega'] if 'EvaluacionEntrega' in row else '--'
                Queja = row['Queja'] if 'Queja' in row else '--'
                estatus = row['estatus'] if 'estatus' in row else '--'
                nps = row['NPS'] if 'NPS' in row else '--'
                TipoPedido = row['TipoPedido'] if 'TipoPedido' in row else '--'
                NoImputableTienda = row['NoImputableTienda'] if 'NoImputableTienda' in row else '--'
                comentario = row['comentario'] if 'comentario' in row else '--'
                FechaEnvio = row['FechaEnvio'] if 'FechaEnvio' in row else '--'
                id_encuesta = row['id_encuesta'] if 'id_encuesta' in row else '--'

                data_i = {
                    'TipoCliente': TipoCliente,
                    'calificacion': calificacion,
                    'canal': canal,
                    'tiendaNombre': tiendaNombre,
                    'zonaNombre': zonaNombre,
                    'regionNombre': regionNombre,
                    'nombreCliente': nombreCliente,
                    'pedido': pedido,
                    'timeslot_from': timeslot_from,
                    'timeslot_to': timeslot_to,
                    'MetodoEntrega': MetodoEntrega,
                    'EstatusPedido': EstatusPedido,
                    'FechaCreacion': FechaCreacion,
                    'FechaEntrega': FechaEntrega,
                    'FechaDespacho': FechaDespacho,
                    'EvaluacionEntrega': EvaluacionEntrega,
                    'Queja': Queja,
                    'estatus': estatus,
                    'NPS': nps,
                    'TipoPedido': TipoPedido,
                    'NoImputableTienda': NoImputableTienda,
                    'comentario': comentario,
                    'FechaEnvio': FechaEnvio,
                    'id_encuesta': id_encuesta
                }
                for camino in caminos:
                    camino_tmp = row[camino] if camino in row else '--'
                    data_i[camino] = camino_tmp
                    # print(f"Camino: {camino}")
                data.append(data_i)
            # print("Columns desde tablas: "+str(columns))
            # print("Data desde tablas: "+str(data))
        else:
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        
    async def PedidosDevolucion(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idTienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
            self.lugar = ''
        if self.filtros.formato != '' and self.filtros.formato != "False" and self.filtros.formato != None:
            filtro_formato = True
        else:
            filtro_formato = False
        pipeline = [
            {'$unwind': '$sucursal'},
            {'$match': {
                'fechaEntrega': {
                    '$gte': self.fecha_ini, 
                    '$lt': self.fecha_fin
                }
            }}
        ]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {'sucursal.'+nivel: self.lugar}}
            )
        if filtro_formato:
            pipeline.append(
                {'$match': {'sucursal.formato': int(self.filtros.formato)}}
            )
        caminos = []
        pipeline.append({
            '$project': {
                'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                'fechaCreacion': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaCreacion'}},
                'orderNumber': '$orderNumber',
                'consignmentNumber': '$consignmentNumber',
                'idTienda': '$sucursal.idTienda',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'regionNombre': '$sucursal.regionNombre',
                'formatoNombre': '$sucursal.formatoNombre',
                'itemsIni': '$itemsIni',
                'estatusConsigna': '$estatusConsigna',
                'metodoEntrega': '$metodoEntrega',
                'mes': '$mes',
                'entregaProgramada': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$entregaProgramada'}},
                'consignmentAmount': '$consignmentAmount',
                'montoDevolucion': '$montoDevolucion',
                'vtaConImp': '$vtaConImp',
                'vtaSinImp': '$vtaSinImp',
                'estatus': '$estatus',
                'devolucion': '$devolucion'
            }
        })
        # Ejecutamos el query:
        collection = conexion_mongo('report').report_pedidoDevolucion
        # print(f"pipeline desde PedidosDevolución: {str(pipeline)}")
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=None)
        # print(str(arreglo))
        if len(arreglo) >0:
            hayResultados = "si"
            # Creamos los arreglos que alimentarán la tabla:
            columns = [
                {'name': 'Fecha Entrega', 'selector':'fechaEntrega', 'formato':'texto'},
                {'name': 'Fecha Creación', 'selector':'fechaCreacion', 'formato':'texto'},
                {'name': 'Número de Orden', 'selector':'orderNumber', 'formato':'entero'},
                {'name': 'Número de Consignación', 'selector':'consignmentNumber', 'formato':'texto'},
                {'name': 'ID Tienda', 'selector':'idTienda', 'formato':'entero'},
                {'name': 'Nombre de la Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho':'420px'},
                {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho':'220px'},
                {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho':'220px'},
                {'name': 'Formato de Tienda', 'selector':'formatoNombre', 'formato':'texto', 'ancho':'200px'},
                {'name': 'Artículos Iniciales', 'selector':'itemsIni', 'formato':'entero'},
                {'name': 'Estatus de Consigna', 'selector':'estatusConsigna', 'formato':'texto', 'ancho':'180px'},
                {'name': 'Método de Entrega', 'selector':'metodoEntrega', 'formato':'texto', 'ancho':'180px'},
                {'name': 'Mes', 'selector':'mes', 'formato':'texto'},
                {'name': 'Entrega Programada', 'selector':'entregaProgramada', 'formato':'texto'},
                {'name': 'Monto de la Consigna', 'selector':'consignmentAmount', 'formato':'moneda'},
                {'name': 'Monto de la Devolución', 'selector':'montoDevolucion', 'formato':'moneda'},
                {'name': 'Venta Con Impuesto', 'selector':'vtaConImp', 'formato':'moneda'},
                {'name': 'Venta Sin Impuesto', 'selector':'vtaSinImp', 'formato':'moneda'},
                {'name': 'Estatus', 'selector':'estatus', 'formato':'texto'},
                {'name': 'Devolución', 'selector':'devolucion', 'formato':'texto', 'ancho':'250px'}
            ]
            data = []
            for row in arreglo:
                fechaEntrega = row['fechaEntrega'] if 'fechaEntrega' in row else '--'
                fechaCreacion = row['fechaCreacion'] if 'fechaCreacion' in row else '--'
                orderNumber = row['orderNumber'] if 'orderNumber' in row else '--'
                consignmentNumber = row['consignmentNumber'] if 'consignmentNumber' in row else '--'
                idTienda = row['idTienda'] if 'idTienda' in row else '--'
                tiendaNombre = row['tiendaNombre'] if 'tiendaNombre' in row else '--'
                zonaNombre = row['zonaNombre'] if 'zonaNombre' in row else '--'
                regionNombre = row['regionNombre'] if 'regionNombre' in row else '--'
                formatoNombre = row['formatoNombre'] if 'formatoNombre' in row else '--'
                itemsIni = row['itemsIni'] if 'itemsIni' in row else '--'
                estatusConsigna = row['estatusConsigna'] if 'estatusConsigna' in row else '--'
                metodoEntrega = row['metodoEntrega'] if 'metodoEntrega' in row else '--'
                mes = row['mes'] if 'mes' in row else '--'
                entregaProgramada = row['entregaProgramada'] if 'entregaProgramada' in row else '--'
                consignmentAmount = row['consignmentAmount'] if 'consignmentAmount' in row else '--'
                montoDevolucion = row['montoDevolucion'] if 'montoDevolucion' in row else '--'
                vtaConImp = row['vtaConImp'] if 'vtaConImp' in row else '--'
                vtaSinImp = row['vtaSinImp'] if 'vtaSinImp' in row else '--'
                estatus = row['estatus'] if 'estatus' in row else '--'
                devolucion = row['devolucion'] if 'devolucion' in row else '--'

                data.append({
                    'fechaEntrega': fechaEntrega,
                    'fechaCreacion': fechaCreacion,
                    'orderNumber': orderNumber,
                    'consignmentNumber': consignmentNumber,
                    'idTienda': idTienda,
                    'tiendaNombre': tiendaNombre,
                    'zonaNombre': zonaNombre,
                    'regionNombre': regionNombre,
                    'formatoNombre': formatoNombre,
                    'itemsIni': itemsIni,
                    'estatusConsigna': estatusConsigna,
                    'metodoEntrega': metodoEntrega,
                    'mes': mes,
                    'entregaProgramada': entregaProgramada,
                    'consignmentAmount': consignmentAmount,
                    'montoDevolucion': montoDevolucion,
                    'vtaConImp': vtaConImp,
                    'vtaSinImp': vtaSinImp,
                    'estatus': estatus,
                    'devolucion': devolucion
                })
            # print("Columns desde tablas: "+str(columns))
            # print("Data desde tablas: "+str(data))
        else:
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        
    async def PedidosSKU(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'tienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
            self.lugar = ''
        filtro_sku = True if self.filtros.sku != '' and self.filtros.sku != "False" and self.filtros.sku != None else False
        pipeline = [
            {'$unwind': '$sucursal'},
            {'$match': {
                'creation_date': {
                    '$gte': self.fecha_ini, 
                    '$lt': self.fecha_fin
                }
            }}
        ]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {'sucursal.'+nivel: self.lugar}}
            )
        if filtro_sku:
            pipeline.append(
                {'$match': {'sku': int(self.filtros.sku)}}
            )
        caminos = []
        pipeline.append({
            '$project': {
                'tiendaNombre': '$sucursal.tiendaNombre',
                'regionNombre': '$sucursal.regionNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'order_number': '$order_number',
                'consignment_number': '$consignment_number',
                'creation_date': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$creation_date'}},
                'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$timeslot_to'}},
                'sku': '$sku',
                'descripcion': '$descripcion',
                'estatusConsigna': '$estatusConsigna',
                'metodoEntrega': '$metodoEntrega',
                'cantidad': '$cantidad',
                'totalPrecio': '$totalPrecio'
            }
        })
        # Ejecutamos el query:
        collection = conexion_mongo('report').report_pedidoSKU
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=None)
        # print(str(arreglo))
        if len(arreglo) >0:
            hayResultados = "si"
            # Creamos los arreglos que alimentarán la tabla:
            columns = [
                {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho':'420px'},
                {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho': '220px'},
                {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho': '220px'},
                {'name': 'No. Orden', 'selector':'order_number', 'formato':'entero', 'ancho':'120px'},
                {'name': 'Consigna', 'selector':'consignment_number', 'formato':'texto', 'ancho':'120px'},
                {'name': 'Fecha Creación', 'selector':'creation_date', 'formato':'texto', 'ancho': '110px'},
                {'name': 'Fecha Entrega', 'selector':'timeslot_to', 'formato':'texto', 'ancho': '110px'},
                {'name': 'SKU', 'selector':'sku', 'formato':'entero'},
                {'name': 'Descripción', 'selector':'descripcion', 'formato':'texto', 'ancho':'350px'},
                {'name': 'Estatus Consigna', 'selector':'estatusConsigna', 'formato':'texto', 'ancho':'170px'},
                {'name': 'Método de Entrega', 'selector':'metodoEntrega', 'formato':'texto', 'ancho':'150px'},
                {'name': 'Cantidad', 'selector':'cantidad', 'formato':'entero'},
                {'name': 'Total Precio', 'selector':'totalPrecio', 'formato':'moneda'}
            ]
            data = []
            for row in arreglo:
                tiendaNombre = row['tiendaNombre'] if 'tiendaNombre' in row else '--'
                regionNombre = row['regionNombre'] if 'regionNombre' in row else '--'
                zonaNombre = row['zonaNombre'] if 'zonaNombre' in row else '--'
                order_number = row['order_number'] if 'order_number' in row else '--'
                consignment_number = row['consignment_number'] if 'consignment_number' in row else '--'
                creation_date = row['creation_date'] if 'creation_date' in row else '--'
                timeslot_to = row['timeslot_to'] if 'timeslot_to' in row else '--'
                sku = row['sku'] if 'sku' in row else '--'
                descripcion = row['descripcion'] if 'descripcion' in row else '--'
                estatusConsigna = row['estatusConsigna'] if 'estatusConsigna' in row else '--'
                metodoEntrega = row['metodoEntrega'] if 'metodoEntrega' in row else '--'
                cantidad = row['cantidad'] if 'cantidad' in row else '--'
                totalPrecio = row['totalPrecio'] if 'totalPrecio' in row else '--'

                data.append({
                    'tiendaNombre': tiendaNombre,
                    'regionNombre': regionNombre,
                    'zonaNombre': zonaNombre,
                    'order_number': order_number,
                    'consignment_number': consignment_number,
                    'creation_date': creation_date,
                    'timeslot_to': timeslot_to,
                    'sku': sku,
                    'descripcion': descripcion,
                    'estatusConsigna': estatusConsigna,
                    'metodoEntrega': metodoEntrega,
                    'cantidad': cantidad,
                    'totalPrecio': totalPrecio
                })
            # print("Columns desde tablas: "+str(columns))
            # print("Data desde tablas: "+str(data))
        else:
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        
    async def SkuCornershopChedraui(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False"and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False"and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idtienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
            self.lugar = ''
        if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
            filtro_producto = True
            if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                nivel_producto = 'subDepto'
                detalle_producto = int(self.filtros.subDepto)
            else:
                nivel_producto = 'depto'
                detalle_producto = int(self.filtros.depto)
        else:
            filtro_producto = False
        filtro_canal2 = True if self.filtros.canal2 != '' and self.filtros.canal2 != "False" and self.filtros.canal2 != None else False
        filtro_e3 = True if self.filtros.e3 != '' and self.filtros.e3 != "False" and self.filtros.e3 != None else False
        pipeline = [
            {'$unwind': '$sucursal'},
            {'$unwind': '$articulo'},
            {'$match': {
                'fecha': {
                    '$gte': self.fecha_ini, 
                    '$lt': self.fecha_fin
                }
            }}
        ]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {'sucursal.'+nivel: self.lugar}}
            )
        if filtro_producto:
            pipeline.append(
                {'$match': {'articulo.'+nivel_producto: detalle_producto}}
            )
        if filtro_e3:
            pipeline.append(
                {'$match': {'articulo.e3': int(self.filtros.e3)}}
            )
        if filtro_canal2:
            pipeline.append(
                {'$match': {'canal': self.filtros.canal2}}
            )
        caminos = []
        pipeline.append({
            '$project': {
                'canal': '$canal',
                'regionNombre': '$sucursal.regionNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'sku': '$articulo.sku',
                'skuNombre': '$articulo.skuNombre',
                'deptoNombre': '$articulo.deptoNombre',
                'subDeptoNombre': '$articulo.subDeptoNombre',
                'e3': '$articulo.e3',
                'itemOri': '$itemOri',
                'itemFin': '$itemFin',
                'foundRate': {'$cond': [{'$eq': ['$itemFin', 0 ]}, "--", {'$divide': ['$itemOri', '$itemFin']}]}
            }
        })
        # Ejecutamos el query:
        collection = conexion_mongo('report').report_skuConershopChedraui
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=None)
        # print(str(arreglo))
        if len(arreglo) >0:
            # print('Sí hay resultados: '+str(arreglo))
            hayResultados = "si"
            # Creamos los arreglos que alimentarán la tabla:
            columns = [
                {'name': 'Canal', 'selector':'canal', 'formato':'texto', 'ancho': '130px'},
                {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho': '220px'},
                {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho': '220px'},
                {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho': '420px'},
                {'name': 'SKU', 'selector':'sku', 'formato':'entero', 'ancho': '100px'},
                {'name': 'Artículo', 'selector':'skuNombre', 'formato':'texto', 'ancho': '400px'},
                {'name': 'Departamento', 'selector':'deptoNombre', 'formato':'texto', 'ancho': '280px'},
                {'name': 'SubDepartamento', 'selector':'subDeptoNombre', 'formato':'texto', 'ancho': '300px'},
                {'name': 'E3', 'selector':'e3', 'formato':'texto'},
                {'name': 'Ítem Ori', 'selector':'itemOri', 'formato':'entero'},
                {'name': 'Ítem Fin', 'selector':'itemFin', 'formato':'entero'},
                {'name': 'Found Rate', 'selector':'foundRate', 'formato':'texto'},
            ]
            data = []
            for row in arreglo:
                canal = row['canal'] if 'canal' in row else '--'
                regionNombre = row['regionNombre'] if 'regionNombre' in row else '--'
                zonaNombre = row['zonaNombre'] if 'zonaNombre' in row else '--'
                tiendaNombre = row['tiendaNombre'] if 'tiendaNombre' in row else '--'
                sku = row['sku'] if 'sku' in row else '--'
                skuNombre = row['skuNombre'] if 'skuNombre' in row else '--'
                deptoNombre = row['deptoNombre'] if 'deptoNombre' in row else '--'
                subDeptoNombre = row['subDeptoNombre'] if 'subDeptoNombre' in row else '--'
                e3 = row['e3'] if 'e3' in row else '--'
                itemOri = row['itemOri'] if 'itemOri' in row else '--'
                itemFin = row['itemFin'] if 'itemFin' in row else '--'
                foundRate = row['foundRate'] if 'foundRate' in row else '--'

                data.append({
                'canal': canal,
                'regionNombre': regionNombre,
                'zonaNombre': zonaNombre,
                'tiendaNombre': tiendaNombre,
                'sku': sku,
                'skuNombre': skuNombre,
                'deptoNombre': deptoNombre,
                'subDeptoNombre': subDeptoNombre,
                'e3': e3,
                'itemOri': itemOri,
                'itemFin': itemFin,
                'foundRate': foundRate
                })
            # print("Columns desde tablas: "+str(columns))
            # print("Data desde tablas: "+str(data))
        else:
            # print('No hay resultados, arreglo = '+str(arreglo))
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        
    async def FoundRateCornershop(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idtienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
            self.lugar = ''

        pipeline = [
            {'$unwind': '$sucursal'},
            {'$unwind': '$articulo'},
            {'$match': {
                'fecha': {
                    '$gte': self.fecha_ini, 
                    '$lt': self.fecha_fin
                }
            }}
        ]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {'sucursal.'+nivel: self.lugar}}
            )
        if self.titulo == 'Detalle Found Rate por Departamento':
            pipeline.extend([
                {'$match': {
                    'articulo.deptoNombre': {
                        '$ne': None
                    }
                }},
                {'$group': {
                    '_id': {
                        'deptoNombre': '$articulo.deptoNombre',
                        'canal': '$canal'
                    },
                    'itemOri': {'$sum': '$itemOri'},
                    'itemFin': {'$sum': '$itemFin'}
                }},
                {'$project': {
                    'canal': '$_id.canal',
                    'deptoNombre': '$_id.deptoNombre',
                    'foundRate': {'$divide': ['$itemFin', '$itemOri']}
                }},
                {'$sort': {
                    'deptoNombre': 1
                }}
            ])
            # Ejecutamos el query:
            collection = conexion_mongo('report').report_skuConershopChedrauiDetalle
            # print(f'Pipeline desde Tablas -> {self.titulo}: {str(pipeline)}')
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            # print(str(arreglo))
            if len(arreglo) >0:
                # print(f'Arreglo desde Tablas -> {self.titulo}: {str(arreglo)}')
                hayResultados = "si"
                # Creamos los arreglos que alimentarán la tabla:
                columns = [
                    {'name': 'Departamento', 'selector':'deptoNombre', 'formato':'texto', 'ancho': '280px'},
                    {'name': 'Chedraui', 'selector':'frChedraui', 'formato':'porcentaje'},
                    {'name': 'Cornershop', 'selector':'frCornershop', 'formato':'porcentaje'},
                    {'name': '% Dif', 'selector':'dif', 'formato':'porcentaje'}
                ]
                data = []
                deptos = []
                frChedraui = []
                frCornershop = []
                for row in arreglo:
                    if 'deptoNombre' in row:
                        foundRate = row['foundRate']
                        if row['canal'] == 'Chedraui':
                            deptos.append(row['deptoNombre'] )
                            frChedraui.append(foundRate)
                        elif row['canal'] == 'Cornershop':
                            frCornershop.append(foundRate)
                for i in range(len(deptos)):
                    frCornershopNum = frCornershop[i] if len(frCornershop) - 1 > i else 0
                    data.append({
                        'deptoNombre': deptos[i],
                        'frChedraui': frChedraui[i],
                        'frCornershop': frCornershopNum,
                        'dif': frChedraui[i] - frCornershopNum,
                    })
                # print("Columns desde tablas: "+str(columns))
                # print("Data desde tablas: "+str(data))
            else:
                # print('No hay resultados, arreglo = '+str(arreglo))
                hayResultados = 'no'
        
        if self.titulo == 'Top 10 Tiendas con mejor Found Rate Chedraui' or  self.titulo=='Top 10 Tiendas con mejor Found Rate Cornershop':
            ordenamiento = 'frChedraui' if self.titulo == 'Top 10 Tiendas con mejor Found Rate Chedraui' else 'frCornershop'
            pipeline.extend([
                {'$project':{
                    'tiendaNombre': '$sucursal.tiendaNombre',
                    'itemOriChedraui': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Chedraui'
                            ]},
                            '$itemOri',
                            0
                        ]
                    },
                    'itemFinChedraui': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Chedraui'
                            ]},
                            '$itemFin',
                            0
                        ]
                    },
                    'itemOriCornershop': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Cornershop'
                            ]},
                            '$itemOri',
                            0
                        ]
                    },
                    'itemFinCornershop': {
                        '$cond': [{
                            '$eq': [
                                '$canal', 'Cornershop'
                            ]},
                            '$itemFin',
                            0
                        ]
                    }
                }},
                {'$group': {
                    '_id': {
                        'tiendaNombre': '$tiendaNombre'
                    },
                    'itemOriChedraui': {'$sum': '$itemOriChedraui'},
                    'itemFinChedraui': {'$sum': '$itemFinChedraui'},
                    'itemOriCornershop': {'$sum': '$itemOriCornershop'},
                    'itemFinCornershop': {'$sum': '$itemFinCornershop'},
                }},
                {'$project': {
                    'canal': '$_id.canal',
                    'tiendaNombre': '$_id.tiendaNombre',
                    'frChedraui': {
                        '$cond': [
                            {'$eq': ['$itemOriChedraui', 0]},
                            0,
                            {'$divide': ['$itemFinChedraui', '$itemOriChedraui']}
                        ]
                    },
                    'frCornershop': {
                        '$cond': [
                            {'$eq': ['$itemOriCornershop', 0]},
                            0,
                            {'$divide': ['$itemFinCornershop', '$itemOriCornershop']}
                        ]
                    }
                }},
                {'$sort': {
                    ordenamiento: -1,
                }}
            ])
            # print("Pipeline desde Tablas: "+str(pipeline))
            # Ejecutamos el query:
            collection = conexion_mongo('report').report_skuConershopChedrauiDetalle
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=10)
            # print(str(arreglo))
            if len(arreglo) >0:
                # print('Sí hay resultados: '+str(arreglo))
                hayResultados = "si"
                # Creamos los arreglos que alimentarán la tabla:
                columns = [
                    {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho': '280px', 'ancho':'420px'},
                    {'name': 'Chedraui', 'selector':'frChedraui', 'formato':'porcentaje'},
                    {'name': 'Cornershop', 'selector':'frCornershop', 'formato':'porcentaje'},
                    {'name': '% Dif', 'selector':'dif', 'formato':'porcentaje'}
                ]
                data = []
                for row in arreglo:
                    data.append({
                        'tiendaNombre': row['tiendaNombre'],
                        'frChedraui': row['frChedraui'],
                        'frCornershop': row['frCornershop'],
                        'dif': row['frChedraui'] - row['frCornershop'],
                    })
                # print("Columns desde tablas: "+str(columns))
                # print("Data desde tablas: "+str(data))
            else:
                # print('No hay resultados, arreglo = '+str(arreglo))
                hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        
    async def Nps(self):
        # print(f"provLogist desde Tablas->NPS: {str(self.filtros.provLogist)}")
        pipeline = []
        data = []
        columns = []
        fecha_ini = self.filtros.fechas['fecha_ini'][0:10]
        fecha_fin = self.filtros.fechas['fecha_fin'][0:10]
        fecha_ini_datetime = fecha_ini + ' 00:00:00'
        fecha_fin_datetime = fecha_fin + ' 23:59:59'
        clauseCatProveedor = ''
        if len(self.filtros.provLogist) > 0:
            clauseCatProveedor = " AND ("
            contador = 0
            for prov in self.filtros.provLogist:
                if prov == 'Recursos Propios':
                    clauseCatProveedor += f" ho.tercero IS NULL "
                else:
                    clauseCatProveedor += f" ho.tercero = '{prov}' "
                if contador < len(self.filtros.provLogist) - 1:
                    clauseCatProveedor += f" OR "
                else:
                    clauseCatProveedor += f") "
                contador += 1
        clauseCatProveedor_tmp = " AND cp.proveedor is not null "
        if len(self.filtros.provLogist) > 0:
            clauseCatProveedor_tmp = " AND ("
            contador = 0
            for prov in self.filtros.provLogist:
                clauseCatProveedor_tmp += f" cp.proveedor = '{prov}' "
                if contador < len(self.filtros.provLogist) - 1:
                    clauseCatProveedor_tmp += f" OR "
                else:
                    clauseCatProveedor_tmp += f") "
                contador += 1
        clauseCatProveedor_tmp += f" AND ((cp.fecha_from = '2022-11-23' AND (cp.fecha_to is null OR cp.fecha_to <= '{fecha_fin}') OR (cp.fecha_from <= '{fecha_fin}' AND cp.fecha_to is null)))"
        if self.titulo == 'Evaluación NPS por Día':
            data = []
            esMes = False
            if self.filtros.agrupador == 'dia':
                # Rawa
                # rango = "nmp.fecha"
                rango = "ho.creation_date"
            elif self.filtros.agrupador == "semana":
                rango = "n_sem_D_S"
            elif self.filtros.agrupador == "mes":
                rango = "dt.abrev_mes"
                esMes = True
            else:
                rango = "anio"
            pipeline = f"""SELECT COUNT(1) as cantidad, nd.calificacion, {rango} as rango {', (dt.anio * 100 + dt.num_mes) as mesNum' if esMes else ''}
            from DWH.limesurvey.nps_mail_pedido nmp
            left join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nmp.nEncuesta=nd.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            LEFT JOIN DWH.dbo.hecho_order ho
            ON ho.order_number =nmp.pedido"""
            if self.filtros.agrupador != "dia":
                pipeline += " left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date) = dt.fecha "
            pipeline += f""" where ho.creation_date BETWEEN '{fecha_ini_datetime}' AND '{fecha_fin_datetime}'"""
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                pipeline += f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                pipeline += f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                pipeline += f" and ct.region ='{self.filtros.region}' "
            pipeline += clauseCatProveedor
            pipeline += f" group by nd.calificacion, {rango} {', (dt.anio * 100 + dt.num_mes)' if esMes else ''} order by {rango if not esMes else '(dt.anio * 100 + dt.num_mes) '}"

            print('Query Evaluación NPS por Día desde Tabla: '+str(pipeline))
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            # print(f"Arreglo desde Tablas -> {self.titulo}: {str(arreglo)}")

            if len(arreglo) > 0:
                hayResultados = "si"
                # Crear nuevo arreglo de fechas y cambiar formato de fechas
                rangos = []
                for fila in arreglo:
                    if self.filtros.agrupador == "dia":
                        fila['rango'] = fila['rango'].strftime('%d/%m/%Y')
                    if fila['rango'] not in rangos and fila['rango'] is not None:
                        rangos.append(fila['rango'])
                tabla_presentacion = [["Contactados", "Respuestas", "% Tasa", "Promotores", "Pasivos", "Detractores", "% NPS"]]
                # Declarar las variables para la última columna de totales
                total_contactados = total_respuestas = total_promotores = total_pasivos = total_detractores = 0
                # Por cada fecha, llenar su columna con base en la información del arreglo de resultados
                for rango in rangos:
                    contactados = respuestas = sin_respuesta = tasa_respuesta = promotores = pasivos = detractores = nps = 0
                    for fila in arreglo:
                        if fila['rango'] == rango:
                            contactados+=int(fila['cantidad'])
                            if fila['calificacion'] == None:
                                sin_respuesta+=int(fila['cantidad'])
                            elif int(fila['calificacion']) >= 9:
                                promotores+=int(fila['cantidad'])
                            elif int(fila['calificacion']) >= 7:
                                pasivos+=int(fila['cantidad'])
                            else:
                                detractores+=int(fila['cantidad'])
                    respuestas = contactados - sin_respuesta
                    tasa_respuesta = f'{(100*respuestas/contactados):.2f}%' if contactados != 0 else 0
                    if respuestas != 0:
                        tasa_promotores_num = promotores / respuestas
                        tasa_promotores = f'{(100 * tasa_promotores_num):.2f}%'
                        tasa_pasivos = f'{(100 * pasivos / respuestas):.2f}%'
                        tasa_detractores_num = detractores / respuestas
                        tasa_detractores = f'{(100 * tasa_detractores_num):.2f}%'
                    else:
                        tasa_promotores = tasa_pasivos = tasa_detractores = '--'
                        tasa_promotores_num = tasa_detractores_num = 0
                    # print(f"Promotores: {promotores}. Detractores: {detractores}. Respuestas: {respuestas}. nps: {100 * (promotores - detractores) / respuestas}")
                    nps = f'{(100 * (promotores - detractores) / respuestas):.2f}%' if respuestas > 0 else '--'
                    tabla_presentacion.append([f'{(contactados):,}', f'{(respuestas):,}', tasa_respuesta, tasa_promotores, tasa_pasivos, tasa_detractores, nps])
                    total_contactados += contactados
                    total_respuestas += respuestas
                    total_promotores += promotores
                    total_detractores += detractores
                    total_pasivos += pasivos

                total_tasa = f'{(100* total_respuestas / total_contactados):.2f}%' if total_contactados != 0 else '--'
                total_promotores_porcentaje = f'{(100 * total_promotores / total_respuestas):.2f}%' if total_respuestas != 0 else '--'
                total_detractores_porcentaje = f'{(100 * total_detractores / total_respuestas):.2f}%' if total_respuestas != 0 else '--'
                total_pasivos_porcentaje = f'{(100 * total_pasivos / total_respuestas):.2f}%' if total_respuestas != 0 else '0'
                total_nps_porcentaje = f'{(100 * (total_promotores - total_detractores) / total_respuestas):.2f}%' if total_respuestas != 0 else '--'
                tabla_presentacion.append([f'{(total_contactados):,}', f'{(total_respuestas):,}', total_tasa, total_promotores_porcentaje, total_pasivos_porcentaje, total_detractores_porcentaje, total_nps_porcentaje])

                columns = [
                    {'name': 'Concepto', 'selector':'Concepto', 'formato':'texto', 'ancho': '120px'}
                ]
                for rango in rangos:
                    columns.append({
                        'name': rango, 'selector': '_'+rango.replace('/', '_'), 'formato': 'texto'
                    })
                columns.extend([
                    {'name': 'Total', 'selector': 'Total', 'formato': 'texto'}
                ])
                for i in range(len(tabla_presentacion[0])):
                    diccionario = {'Concepto': tabla_presentacion[0][i]}
                    j = 1
                    for rango in rangos:
                        diccionario['_'+rango.replace('/', '_')] = tabla_presentacion[j][i]
                        j += 1
                    diccionario['Total'] = tabla_presentacion[j][i]
                    data.append(diccionario)
            else:
                hayResultados = 'no'

        if self.titulo == 'Top 20 respuestas Promotores':
            if self.filtros.agrupador == 'dia':
                mes = int(self.filtros.periodo['mes'])
                mes = str(mes) if mes >= 10 else '0'+str(mes)
                dia = int(self.filtros.periodo['dia'])
                dia = str(dia) if dia >= 10 else '0'+str(dia)
                agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
            elif self.filtros.agrupador == "semana":
                semana_completa = str(self.filtros.periodo['semana'])
                num_semana = int(semana_completa[4:])
                anio = int(semana_completa[0:4])
                semana_query = anio*100+num_semana
                agrupador_where = f" dt.idSemDS={semana_query}"
            elif self.filtros.agrupador == "mes":
                agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                lugar_where = f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                lugar_where = f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                lugar_where = f" and ct.region ='{self.filtros.region}' "
            else:
                lugar_where = ""

            pipeline = f"""select top 20 ncp.responsable ,ncp2.descripcion as categoria,ncp.descripcion,
            sum(case when ncp.flujo='F2' then npr.cant else 0 end) RF2
            from DWH.limesurvey.nps_pregunta_respuesta npr
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            inner join DWH.limesurvey.nps_cat_preguntas ncp2 on ncp.orden =ncp2.id
            left join DWH.artus.catTienda ct on npr.idTienda =ct.tienda
            left join DWH.dbo.dim_tiempo dt on npr.fecha=dt.fecha
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where ncp.tipo_respuesta = 'R2' and {agrupador_where} {lugar_where} {clauseCatProveedor_tmp}
            group by ncp.responsable,ncp.descripcion,ncp2.descripcion
            order by sum(case when ncp.flujo='F2' then npr.cant else 0 end) desc"""

            # print("query desde tablas promotores: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                columns = [
                    {'name': 'Responsable', 'selector':'Responsable', 'formato':'texto', 'ancho': '180px'},
                    {'name': 'Categoría', 'selector':'Categoria', 'formato':'texto', 'ancho': '120px', 'ancho': '400px'},
                    {'name': 'Respuesta', 'selector':'Respuesta', 'formato':'texto', 'ancho': '120px', 'ancho': '400px'},
                    {'name': 'Cantidad', 'selector':'Cantidad', 'formato':'texto', 'ancho': '120px'}
                ]
                for row in arreglo:
                    data.append({
                        'Responsable': row['responsable'],
                        'Categoria': row['categoria'],
                        'Respuesta': row['descripcion'],
                        'Cantidad': row['RF2']
                    })
            else:
                hayResultados = 'no'

        if self.titulo == 'Top 20 respuestas Pasivos y Detractores':
            if self.filtros.agrupador == 'dia':
                mes = int(self.filtros.periodo['mes'])
                mes = str(mes) if mes >= 10 else '0'+str(mes)
                dia = int(self.filtros.periodo['dia'])
                dia = str(dia) if dia >= 10 else '0'+str(dia)
                agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
            elif self.filtros.agrupador == "semana":
                semana_completa = str(self.filtros.periodo['semana'])
                num_semana = int(semana_completa[4:])
                anio = int(semana_completa[0:4])
                semana_query = anio*100+num_semana
                agrupador_where = f" dt.idSemDS={semana_query}"
            elif self.filtros.agrupador == "mes":
                agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                lugar_where = f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                lugar_where = f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                lugar_where = f" and ct.region ='{self.filtros.region}' "
            else:
                lugar_where = ""

            pipeline = f"""select top 20 ncp.responsable ,ncp2.descripcion as categoria,ncp.descripcion,
            sum(case when ncp.flujo='F1' then npr.cant else 0 end) RF1
            from DWH.limesurvey.nps_pregunta_respuesta npr
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            inner join DWH.limesurvey.nps_cat_preguntas ncp2 on ncp.orden =ncp2.id
            left join DWH.artus.catTienda ct on npr.idTienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            left join DWH.dbo.dim_tiempo dt on npr.fecha=dt.fecha
            where ncp.tipo_respuesta = 'R2' and {agrupador_where} {lugar_where} {clauseCatProveedor_tmp}
            group by ncp.responsable,ncp.descripcion,ncp2.descripcion
            order by sum(case when ncp.flujo='F1' then npr.cant else 0 end) desc"""

            # print("query desde tablas pasivos y detractores: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                columns = [
                    {'name': 'Responsable', 'selector':'Responsable', 'formato':'texto', 'ancho': '180px'},
                    {'name': 'Categoría', 'selector':'Categoria', 'formato':'texto', 'ancho': '400px'},
                    {'name': 'Respuesta', 'selector':'Respuesta', 'formato':'texto', 'ancho': '400px'},
                    {'name': 'Cantidad', 'selector':'Cantidad', 'formato':'texto', 'ancho': '120px'}
                ]
                for row in arreglo:
                    data.append({
                        'Responsable': row['responsable'],
                        'Categoria': row['categoria'],
                        'Respuesta': row['descripcion'],
                        'Cantidad': row['RF1']
                    })
            else:
                hayResultados = 'no'

        if self.titulo == 'Resumen NPS por tienda':
            if self.filtros.agrupador == 'dia':
                mes = int(self.filtros.periodo['mes'])
                mes = str(mes) if mes >= 10 else '0'+str(mes)
                dia = int(self.filtros.periodo['dia'])
                dia = str(dia) if dia >= 10 else '0'+str(dia)
                agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
            elif self.filtros.agrupador == "semana":
                semana_completa = str(self.filtros.periodo['semana'])
                num_semana = int(semana_completa[4:])
                anio = int(semana_completa[0:4])
                semana_query = anio*100+num_semana
                agrupador_where = f" dt.idSemDS={semana_query}"
            elif self.filtros.agrupador == "mes":
                agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                lugar_where = f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                lugar_where = f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                lugar_where = f" and ct.region ='{self.filtros.region}' "
            else:
                lugar_where = ""

            pipeline = f"""select CONCAT(nmp.idtienda,' - ',nmp.descrip_tienda) tienda,nmp.region,nmp.zona,
            sum(case when nd.calificacion in (9,10) then 1 else 0 end) promotores,
            sum(case when nd.calificacion<=6 then 1 else 0 end) detractores,
            sum(case when nd.calificacion in (7,8) then 1 else 0 end) pasivos,
            case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            LEFT JOIN DWH.dbo.hecho_order ho
            ON ho.order_number = nmp.pedido
            LEFT JOIN DWH.dbo.dim_tiempo dt
            ON CONVERT(date, ho.creation_date) = dt.fecha
            where {agrupador_where} {lugar_where} {clauseCatProveedor}
            group by CONCAT(nmp.idtienda,' - ',nmp.descrip_tienda),nmp.region,nmp.zona
            order by case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end"""

            print(f"query desde tablas NPS {self.titulo}: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                columns = [
                    {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '380px'},
                    {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho': '220px'},
                    {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho': '180px', 'ancho': '220px'},
                    {'name': 'Promotores', 'selector':'Promotores', 'formato':'entero'},
                    {'name': 'Detractores', 'selector':'Detractores', 'formato':'entero'},
                    {'name': 'Pasivos', 'selector':'Pasivos', 'formato':'entero'},
                    {'name': '% NPS', 'selector':'NPS', 'formato':'porcentaje'}
                ]
                for row in arreglo:
                    data.append({
                        'Tienda': row['tienda'],
                        'Region': row['region'],
                        'Zona': row['zona'],
                        'Promotores': row['promotores'],
                        'Detractores': row['detractores'],
                        'Pasivos': row['pasivos'],
                        'NPS': float(row['nps']) / 100
                    })
            else:
                hayResultados = 'no'

        if self.titulo == 'Detalle Encuesta NPS':
            if self.filtros.agrupador == 'dia':
                mes = int(self.filtros.periodo['mes'])
                mes = str(mes) if mes >= 10 else '0'+str(mes)
                dia = int(self.filtros.periodo['dia'])
                dia = str(dia) if dia >= 10 else '0'+str(dia)
                agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
            elif self.filtros.agrupador == "semana":
                semana_completa = str(self.filtros.periodo['semana'])
                num_semana = int(semana_completa[4:])
                anio = int(semana_completa[0:4])
                semana_query = anio*100+num_semana
                agrupador_where = f" dt.idSemDS={semana_query}"
            elif self.filtros.agrupador == "mes":
                agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                lugar_where = f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                lugar_where = f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                lugar_where = f" and ct.region ='{self.filtros.region}' "
            else:
                lugar_where = ""

            pipeline = f"""select top 500 nd.calificacion,nmp.canal,concat(nmp.idtienda,'-',nmp.descrip_tienda) tienda,nmp.zona,nmp.region,nmp.pedido,
            b.timeslot_from,b.timeslot_to,MetodoEntrega,EstatusPedido, b.FechaEntrega,
            b.FechaDespacho,nmp.evaluacion as EvaluacionEntrega,b.Queja,nmp.estatus,
            b.NPS,b.Tipo,b.NoImputableTienda, nd.comentario,nmp.fecha as FechaEnvio,convert(date, ho.creation_date) as FechaCreacion
            from DWH.limesurvey.nps_detalle nd
            inner join dwh.limesurvey.nps_mail_pedido nmp on nd.id_encuesta=nmp.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join ( select ho.order_number,store_num,
            format(ho.timeslot_from,'dd/MM/yyyy HH:mm') timeslot_from,
            format(ho.timeslot_to,'dd/MM/yyyy HH:mm') timeslot_to,
            case when ho.timeslot_to is null then 'DHL' else de2.descrip_delviery_mode end as MetodoEntrega,de2.descrip_consignment_status as EstatusPedido,
            format(isnull(CASE WHEN de2.descrip_delviery_mode in ('premium-gross') THEN DATEADD(HH,isnull(ds.zona_horaria,0),ho.fecha_entrega_terceros)
            ELSE NULL END,CASE WHEN de2.descrip_consignment_status in ('Delivery Completed','Picked Up')
            THEN DATEADD(HH,isnull(ds.zona_horaria,0),ho.ultimo_cambio) ELSE NULL END),'dd/MM/yyyy HH:mm:ss') FechaEntrega,
            format(CASE WHEN de2.descrip_delviery_mode in ('premium-gross') THEN DATEADD(HH,isnull(ds.zona_horaria,0),ho.hybris_tienda_entrega)
            ELSE DATEADD(HH,isnull(ds.zona_horaria,0),isnull(ho.fin_picking,ho.hybris_tienda_entrega)) END ,'dd/MM/yyyy HH:mm:ss') FechaDespacho,
            dez.etiq_descripcion Queja, case when de2.descrip_consignment_status not like '%Cancel%' and isnull(ho.tmp_n_estatus,'VALIDO') in ('COMPLETO','VALIDO')
            and ho.evaluacion in ('Entregado-A tiempo','Despachado-A tiempo','No entregado-A tiempo') and ho.id_ticket_zendesk_queja is null
            and nda.pedido is null then 'Perfecto' else null end Tipo, ho.otros_no_perfecto as NoImputableTienda, case when nda.pedido is not null then 'La entrega de mi pedido' end nps
            from DWH.dbo.hecho_order ho
            left join DWH.dbo.dim_estatus de2 on ho.id_estatus =de2.id_estatus
            left join DWH.dbo.dim_store ds on ho.store_num =ds.idtienda
            left join DWH.dbo.hecho_ticket_zendesk htz on ho.id_ticket_zendesk_queja=htz.id and htz.id_campo = 360028982073 and htz.formulario = 'Incidencia'
            left join DWH.dbo.dim_etiquetas_zendesk dez on htz.campo=dez.etiqueta left join (select nmp.pedido,nmp.idtienda from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta and nd.X5X64NPSP1R7F1 is not null where nmp.pedido is not null) nda
            on ho.order_number=nda.pedido and nda.idtienda=ho.store_num
            and ho.tmp_n_estatus is not null ) b on nmp.pedido =b.order_number and nmp.idtienda =b.store_num
            left join DWH.artus.catTienda ct on nmp.idtienda =ct.tienda
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on convert(date,ho.creation_date)=dt.fecha
            where {agrupador_where} {lugar_where} {clauseCatProveedor}
            order by ho.creation_date desc,calificacion"""

            # print(f"query desde tablas NPS {self.titulo}: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                columns = [
                    {'name': 'Calificación', 'selector':'calificacion', 'formato':'entero', 'ancho': '100px'},
                    {'name': 'Canal', 'selector':'canal', 'formato':'texto', 'ancho': '100px'},
                    {'name': 'Tienda', 'selector':'tienda', 'formato':'texto', 'ancho': '400px'},
                    {'name': 'Zona', 'selector':'zona', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Región', 'selector':'region', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Comentario', 'selector':'comentario', 'formato':'texto', 'ancho': '1800px'},
                    {'name': 'Pedido', 'selector':'pedido', 'formato':'texto'},
                    {'name': 'Timeslot From', 'selector':'timeslot_from', 'formato':'texto', 'ancho': '220px'},
                    {'name': 'Timeslot To', 'selector':'timeslot_to', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Método entrega', 'selector':'MetodoEntrega', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Estatus del Pedido', 'selector':'EstatusPedido', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Fecha Entrega', 'selector':'FechaEntrega', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Fecha Despacho', 'selector':'FechaDespacho', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Evaluación Entrega', 'selector':'EvaluacionEntrega', 'formato':'texto', 'ancho': '220px'},
                    {'name': 'Queja', 'selector':'Queja', 'formato':'texto', 'ancho': '250px'},
                    {'name': 'Estatus', 'selector':'estatus', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'NPS', 'selector':'NPS', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Tipo', 'selector':'Tipo', 'formato':'texto'},
                    {'name': 'No imputable a tienda', 'selector':'NoImputableTienda', 'formato':'texto'},
                    {'name': 'Fecha Envío', 'selector':'FechaEnvio', 'formato':'texto', 'ancho': '180px'},
                    {'name': 'Fecha Creación', 'selector':'FechaCreacion', 'formato':'texto', 'ancho': '200px'}
                ]
                for row in arreglo:
                    data.append({
                        'calificacion': row['calificacion'],
                        'canal': row['canal'],
                        'tienda': row['tienda'],
                        'zona': row['zona'],
                        'region': row['region'],
                        'comentario': row['comentario'],
                        'pedido': row['pedido'],
                        'timeslot_from': row['timeslot_from'],
                        'timeslot_to': row['timeslot_to'],
                        'MetodoEntrega': row['MetodoEntrega'],
                        'EstatusPedido': row['EstatusPedido'],
                        'FechaEntrega': row['FechaEntrega'],
                        'FechaDespacho': row['FechaDespacho'],
                        'EvaluacionEntrega': row['EvaluacionEntrega'],
                        'Queja': row['Queja'],
                        'estatus': row['estatus'],
                        'NPS': row['NPS'],
                        'Tipo': row['Tipo'],
                        'NoImputableTienda': row['NoImputableTienda'],
                        'FechaEnvio': row['FechaEnvio'].strftime('%d/%m/%Y'),
                        'FechaCreacion': row['FechaCreacion'].strftime('%d/%m/%Y')
                    })
            else:
                hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def ComparativoVentaXCanal(self):
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idTienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                nivel = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
            self.lugar = ''

        pipeline = [{'$match': {'descrip_tienda': {'$ne': None}}}]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {nivel: self.lugar}}
            )
        pipeline.extend([
            {'$project': {
                'region': '$regionNombre',
                'zona': '$zonaNombre',
                'descrip_tienda': '$descrip_tienda',
                'MesActualTiendaFisica': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesActual"]},
                            {'$eq': ["$medio", "Tienda Fisica"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesAnteriorTiendaFisica': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesAnterior"]},
                            {'$eq': ["$medio", "Tienda Fisica"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'AnioAnteriorTiendaFisica': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "AnioAnterior"]},
                            {'$eq': ["$medio", "Tienda Fisica"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesActualRappi': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesActual"]},
                            {'$eq': ["$medio", "Rappi"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesAnteriorRappi': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesAnterior"]},
                            {'$eq': ["$medio", "Rappi"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'AnioAnteriorRappi': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "AnioAnterior"]},
                            {'$eq': ["$medio", "Rappi"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesActualTiendaOnline': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesActual"]},
                            {'$eq': ["$medio", "Tienda Online"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesAnteriorTiendaOnline': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesAnterior"]},
                            {'$eq': ["$medio", "Tienda Online"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'AnioAnteriorTiendaOnline': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "AnioAnterior"]},
                            {'$eq': ["$medio", "Tienda Online"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesActualCornershop': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesActual"]},
                            {'$eq': ["$medio", "Cornershop"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'MesAnteriorCornershop': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "MesAnterior"]},
                            {'$eq': ["$medio", "Cornershop"]}
                        ]},
                        '$venta',
                        0
                    ]
                },
                'AnioAnteriorCornershop': {
                    '$cond': [
                        {'$and': [
                            {'$eq': ["$descripPeriodo", "AnioAnterior"]},
                            {'$eq': ["$medio", "Cornershop"]}
                        ]},
                        '$venta',
                        0
                    ]
                }
            }},
            {'$group': {
                '_id': {
                    'descrip_tienda': '$descrip_tienda', 
                    'region': '$region', 
                    'zona': '$zona'
                }, 
                'MesActualTiendaFisica': {'$sum': '$MesActualTiendaFisica'},
                'MesAnteriorTiendaFisica': {'$sum': '$MesAnteriorTiendaFisica'},
                'AnioAnteriorTiendaFisica': {'$sum': '$AnioAnteriorTiendaFisica'},
                'MesActualRappi': {'$sum': '$MesActualRappi'},
                'MesAnteriorRappi': {'$sum': '$MesAnteriorRappi'},
                'AnioAnteriorRappi': {'$sum': '$AnioAnteriorRappi'},
                'MesActualTiendaOnline': {'$sum': '$MesActualTiendaOnline'},
                'MesAnteriorTiendaOnline': {'$sum': '$MesAnteriorTiendaOnline'},
                'AnioAnteriorTiendaOnline': {'$sum': '$AnioAnteriorTiendaOnline'},
                'MesActualCornershop': {'$sum': '$MesActualCornershop'},
                'MesAnteriorCornershop': {'$sum': '$MesAnteriorCornershop'},
                'AnioAnteriorCornershop': {'$sum': '$AnioAnteriorCornershop'},
            }},
            {'$sort': {'_id.region': 1, '_id.zona': 1, '_id.descrip_tienda': 1}}
        ])
        pipeline_labels = [
            {'$match': {'descrip_tienda': {'$ne': None}}},
            {'$group': {'_id': {'periodo': '$periodo', 'descripPeriodo': '$descripPeriodo'}}}
        ]
        # Ejecutamos el query de labels:
        collection = conexion_mongo('report').report_comparativaVentaCanal
        cursor = collection.aggregate(pipeline_labels)
        arreglo_labels = await cursor.to_list(length=None)
        for row in arreglo_labels:
            if row['_id']['descripPeriodo'] == 'MesActual':
                mesActual = row['_id']['periodo']
            elif row['_id']['descripPeriodo'] == 'MesAnterior':
                mesAnterior = row['_id']['periodo']
            if row['_id']['descripPeriodo'] == 'AnioAnterior':
                anioAnterior = row['_id']['periodo']
        lblTiendaFisicaMesActual = 'Tienda Física '+mesActual
        selectorTiendaFisicaMesActual = lblTiendaFisicaMesActual.replace(' ', '_').replace('í', 'i')
        lblTiendaFisicaMesAnterior = 'Tienda Física '+mesAnterior
        selectorTiendaFisicaMesAnterior = lblTiendaFisicaMesAnterior.replace(' ', '_').replace('í', 'i')
        lblTiendaFisicaAnioAnterior = 'Tienda Física '+anioAnterior
        selectorTiendaFisicaAnioAnterior = lblTiendaFisicaAnioAnterior.replace(' ', '_').replace('í', 'i')
        lblRappiMesActual = 'Rappi '+mesActual
        selectorRappiMesActual = lblRappiMesActual.replace(' ', '_')
        lblRappiMesAnterior = 'Rappi '+mesAnterior
        selectorRappiMesAnterior = lblRappiMesAnterior.replace(' ', '_')
        lblRappiAnioAnterior = 'Rappi '+anioAnterior
        selectorRappiAnioAnterior = lblRappiAnioAnterior.replace(' ', '_')
        lblTiendaOnlineMesActual = 'Tienda Online '+mesActual
        selectorTiendaOnlineMesActual = lblTiendaOnlineMesActual.replace(' ', '_')
        lblTiendaOnlineMesAnterior = 'Tienda Online '+mesAnterior
        selectorTiendaOnlineMesAnterior = lblTiendaOnlineMesAnterior.replace(' ', '_')
        lblTiendaOnlineAnioAnterior = 'Tienda Online '+anioAnterior
        selectorTiendaOnlineAnioAnterior = lblTiendaOnlineAnioAnterior.replace(' ', '_')
        lblCornershopMesActual = 'Cornershop '+mesActual
        selectorCornershopMesActual = lblCornershopMesActual.replace(' ', '_')
        lblCornershopMesAnterior = 'Cornershop '+mesAnterior
        selectorCornershopMesAnterior = lblCornershopMesAnterior.replace(' ', '_')
        lblCornershopAnioAnterior = 'Cornershop '+anioAnterior
        selectorCornershopAnioAnterior = lblCornershopAnioAnterior.replace(' ', '_')
        lblTiendaFisicaMesActualVsMesAnterior = f'Tienda Física {mesActual} vs {mesAnterior}'
        selectorTiendaFisicaMesActualVsMesAnterior = lblTiendaFisicaMesActualVsMesAnterior.replace(' ', '_').replace('í', 'i')
        lblRappiMesActualVsMesAnterior = f'Rappi {mesActual} vs {mesAnterior}'
        selectorRappiMesActualVsMesAnterior = lblRappiMesActualVsMesAnterior.replace(' ', '_')
        lblTiendaOnlineMesActualVsMesAnterior = f'Tienda Online {mesActual} vs {mesAnterior}'
        selectorTiendaOnlineMesActualVsMesAnterior = lblTiendaOnlineMesActualVsMesAnterior.replace(' ', '_')
        lblCornershopMesActualVsMesAnterior = f'Cornershop {mesActual} vs {mesAnterior}'
        selectorCornershopMesActualVsMesAnterior = lblCornershopMesActualVsMesAnterior.replace(' ', '_')
        lblTiendaFisicaMesActualVsAnioAnterior = f'Tienda Física {mesActual} vs {anioAnterior}'
        selectorTiendaFisicaMesActualVsAnioAnterior = lblTiendaFisicaMesActualVsAnioAnterior.replace(' ', '_').replace('í', 'i')
        lblRappiMesActualVsAnioAnterior = f'Rappi {mesActual} vs {anioAnterior}'
        selectorRappiMesActualVsAnioAnterior = lblRappiMesActualVsAnioAnterior.replace(' ', '_')
        lblTiendaOnlineMesActualVsAnioAnterior = f'Tienda Online {mesActual} vs {anioAnterior}'
        selectorTiendaOnlineMesActualVsAnioAnterior = lblTiendaOnlineMesActualVsAnioAnterior.replace(' ', '_')
        lblCornershopMesActualVsAnioAnterior = f'Cornershop {mesActual} vs {anioAnterior}'
        selectorCornershopMesActualVsAnioAnterior = lblCornershopMesActualVsAnioAnterior.replace(' ', '_')
        columns = [
            {'name': 'region', 'selector': 'Region', 'formato': 'texto', 'ancho': '250px', 'colores': False},
            {'name': 'zona', 'selector': 'Zona', 'formato': 'texto', 'ancho': '220px', 'colores': False},
            {'name': 'descrip_tienda', 'selector': 'Tienda', 'formato': 'texto', 'ancho': '400px', 'colores': False},
            {'name': lblTiendaFisicaMesActual, 'selector': selectorTiendaFisicaMesActual, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblTiendaFisicaMesAnterior, 'selector': selectorTiendaFisicaMesAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblTiendaFisicaAnioAnterior, 'selector': selectorTiendaFisicaAnioAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblRappiMesActual, 'selector': selectorRappiMesActual, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblRappiMesAnterior, 'selector': selectorRappiMesAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblRappiAnioAnterior, 'selector': selectorRappiAnioAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblTiendaOnlineMesActual, 'selector': selectorTiendaOnlineMesActual, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblTiendaOnlineMesAnterior, 'selector': selectorTiendaOnlineMesAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblTiendaOnlineAnioAnterior, 'selector': selectorTiendaOnlineAnioAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblCornershopMesActual, 'selector': selectorCornershopMesActual, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblCornershopMesAnterior, 'selector': selectorCornershopMesAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblCornershopAnioAnterior, 'selector': selectorCornershopAnioAnterior, 'formato': 'moneda', 'ancho': '130px', 'colores': False},
            {'name': lblTiendaFisicaMesActualVsMesAnterior, 'selector': selectorTiendaFisicaMesActualVsMesAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblRappiMesActualVsMesAnterior, 'selector': selectorRappiMesActualVsMesAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblTiendaOnlineMesActualVsMesAnterior, 'selector': selectorTiendaOnlineMesActualVsMesAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblCornershopMesActualVsMesAnterior, 'selector': selectorCornershopMesActualVsMesAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblTiendaFisicaMesActualVsAnioAnterior, 'selector': selectorTiendaFisicaMesActualVsAnioAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblRappiMesActualVsAnioAnterior, 'selector': selectorRappiMesActualVsAnioAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblTiendaOnlineMesActualVsAnioAnterior, 'selector': selectorTiendaOnlineMesActualVsAnioAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
            {'name': lblCornershopMesActualVsAnioAnterior, 'selector': selectorCornershopMesActualVsAnioAnterior, 'formato': 'porcentaje', 'ancho': '130px', 'colores': True},
        ]
        # Ejecutamos el query principal:
        # print('Pipeline desde tabla ComparativoVentaXCanal: '+str(pipeline))
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=None)
        # print(str(arreglo))
        if len(arreglo) >0:
            # print('Sí hay resultados: '+str(arreglo))
            hayResultados = "si"
            # Creamos los arreglos que alimentarán la tabla:
            data = []
            for row in arreglo:
                MesActualTiendaFisica = row['MesActualTiendaFisica']
                MesAnteriorTiendaFisica = row['MesAnteriorTiendaFisica']
                AnioAnteriorTiendaFisica = row['AnioAnteriorTiendaFisica']
                MesActualRappi = row['MesActualRappi']
                MesAnteriorRappi = row['MesAnteriorRappi']
                AnioAnteriorRappi = row['AnioAnteriorRappi']
                MesActualTiendaOnline = row['MesActualTiendaOnline']
                MesAnteriorTiendaOnline = row['MesAnteriorTiendaOnline']
                AnioAnteriorTiendaOnline = row['AnioAnteriorTiendaOnline']
                MesActualCornershop = row['MesActualCornershop']
                MesAnteriorCornershop = row['MesAnteriorCornershop']
                AnioAnteriorCornershop = row['AnioAnteriorCornershop']
                vsMesAnteriorTiendaFisica = (MesActualTiendaFisica / MesAnteriorTiendaFisica)-1 if MesAnteriorTiendaFisica != 0 else '--'
                vsMesAnteriorRappi = (MesActualRappi / MesAnteriorRappi)-1 if MesAnteriorRappi != 0 else '--'
                vsMesAnteriorTiendaOnline = (MesActualTiendaOnline / MesAnteriorTiendaOnline)-1 if MesAnteriorTiendaOnline != 0 else '--'
                vsMesAnteriorCornershop = (MesActualCornershop / MesAnteriorCornershop)-1 if MesAnteriorCornershop != 0 else '--'
                vsAnioAnteriorTiendaFisica = (MesActualTiendaFisica / AnioAnteriorTiendaFisica)-1 if AnioAnteriorTiendaFisica != 0 else '--'
                vsAnioAnteriorRappi = (MesActualRappi / AnioAnteriorRappi)-1 if AnioAnteriorRappi != 0 else '--'
                vsAnioAnteriorTiendaOnline = (MesActualTiendaOnline / AnioAnteriorTiendaOnline)-1 if AnioAnteriorTiendaOnline != 0 else '--'
                vsAnioAnteriorCornershop = (MesActualCornershop / AnioAnteriorCornershop)-1 if AnioAnteriorCornershop != 0 else '--'
                data.append({
                    'Region': row['_id']['region'],
                    'Zona': row['_id']['zona'],
                    'Tienda': row['_id']['descrip_tienda'],
                    selectorTiendaFisicaMesActual: MesActualTiendaFisica,
                    selectorTiendaFisicaMesAnterior: MesAnteriorTiendaFisica,
                    selectorTiendaFisicaAnioAnterior: AnioAnteriorTiendaFisica,
                    selectorRappiMesActual: MesActualRappi,
                    selectorRappiMesAnterior: MesAnteriorRappi,
                    selectorRappiAnioAnterior: AnioAnteriorRappi,
                    selectorTiendaOnlineMesActual: MesActualTiendaOnline,
                    selectorTiendaOnlineMesAnterior: MesAnteriorTiendaOnline,
                    selectorTiendaOnlineAnioAnterior: AnioAnteriorTiendaOnline,
                    selectorCornershopMesActual: MesActualCornershop,
                    selectorCornershopMesAnterior: MesAnteriorCornershop,
                    selectorCornershopAnioAnterior: AnioAnteriorCornershop,
                    selectorTiendaFisicaMesActualVsMesAnterior: vsMesAnteriorTiendaFisica,
                    selectorRappiMesActualVsMesAnterior: vsMesAnteriorRappi,
                    selectorTiendaOnlineMesActualVsMesAnterior: vsMesAnteriorTiendaOnline,
                    selectorCornershopMesActualVsMesAnterior: vsMesAnteriorCornershop,
                    selectorTiendaFisicaMesActualVsAnioAnterior: vsAnioAnteriorTiendaFisica,
                    selectorRappiMesActualVsAnioAnterior: vsAnioAnteriorRappi,
                    selectorTiendaOnlineMesActualVsAnioAnterior: vsAnioAnteriorTiendaOnline,
                    selectorCornershopMesActualVsAnioAnterior: vsAnioAnteriorCornershop
                })
            # print("Columns desde tablas: "+str(columns))
            # print("Data desde tablas: "+str(data))
        else:
            # print('No hay resultados, arreglo = '+str(arreglo))
            hayResultados = 'no'
        colores = ['normal', 0, 50]
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data, 'colores': colores}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}
        
    async def ResultadoRFM(self):
        # print('Entró a ResultadoRFM')
        pipeline = []
        arreglo = []
        hayResultados = 'no'
        data = []
        columns = []
        collection = conexion_mongo('report').report_detalleRFM
        pipeline = [
            {'$match': {'anio': self.filtros.anioRFM}},
            {'$match': {'mes': self.filtros.mesRFM}},
        ]
        if self.titulo == 'Clientes por Segmento':
            # print('Entró a Ctes por segmento en Tablas')
            pipeline.extend([
                {'$facet': {
                    'totales': [
                        {'$count': 'usuarios'},
                    ],
                    'segmentados': [
                        {'$group': {
                            '_id': '$tipoCliente', 
                            'usuarios': {
                                '$sum': 1
                            }
                        }},
                        {'$sort': {'_id': 1}}
                    ]
                }}
            ])
            # print('Pipeline desde Ctes por segmento en Tablas: '+str(pipeline))
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            # print('Arreglo desde Ctes por segmento en Tablas: '+str(arreglo))
            if len(arreglo[0]['segmentados']) >0:
                # print('Sí hay resultados: '+str(arreglo))
                hayResultados = "si"
                # Creamos los arreglos que alimentarán la tabla:
                columns = [
                    {'name': 'Segmento', 'selector':'Segmento', 'formato':'texto', 'ancho': '220px'},
                    {'name': 'Usuarios', 'selector':'Usuarios', 'formato':'entero'},
                    {'name': '% del Total', 'selector':'Porcentaje', 'formato':'porcentaje'}
                ]
                data = []
                totales = arreglo[0]['totales'][0]['usuarios']
                for row in arreglo[0]['segmentados']:
                    porcentaje = float(float(row['usuarios'] / totales)) if int(row['usuarios']) != 0 else '--'
                    data.append({
                        'Segmento': row['_id'],
                        'Usuarios': row['usuarios'],
                        'Porcentaje': porcentaje
                    })
                # print("Columns desde tablas: "+str(columns))
                # print("Data desde tablas: "+str(data))
            else:
                # print('No hay resultados, arreglo = '+str(arreglo))
                hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def AltaUsuarios(self):
        pipeline = []
        data = []
        columns = []
        # self.fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        pipeline = f"""SELECT us.usuario, us.nombre, us.estatus, ct.tiendasNombre, n.nombre nivel, us.id
        from DJANGO.php.usuarios us
        left join DWH.artus.catTienda ct on us.idTienda = ct.tienda
        left join DJANGO.php.niveles n on n.id = us.nivel
        where us.estatus is not null and us.estatus not in ('activo')
        ORDER BY us.estatus, us.usuario DESC"""
        # pipeline = f"""SELECT us.usuario, us.nombre, r.rol, ct.tienda, us.estatus
        # from DJANGO.php.usuarios us
        # left join DWH.artus.catTienda ct on us.id_rol = ct.tienda
        # left join DJANGO.php.rol r on us.idTienda = r.id
        # where us.estatus is not null and us.estatus not in ('activo')"""
        cnxn = conexion_sql('DJANGO')
        cursor = cnxn.cursor().execute(pipeline)
        arreglo = crear_diccionario(cursor)
        # print(f'arreglo desde AltaUsuarios: {str(arreglo)}')
        if len(arreglo) > 0:
            hayResultados = "si"
            for row in arreglo:
                query = f"""SELECT a.nombre from DJANGO.php.usuariosAreas ua
                    left join DJANGO.php.areas a
                    on a.id = ua.area
                    WHERE ua.id_usuario = {row['id']}"""
                cursor = cnxn.cursor().execute(query)
                areas_dic = crear_diccionario(cursor)
                areas_arr = []
                for area in areas_dic:
                    areas_arr.append(area['nombre'])
                data.append({
                    'Email': row['usuario'],
                    'Nombre': row['nombre'],
                    'Areas': ', '.join(areas_arr),
                    'Nivel': row['nivel'],
                    'Tienda': row['tiendasNombre'],
                    'Estatus': row['estatus'],
                    'CambiarEstatus': 0,
                    'Editar': 0,
                })
            columns = [
                {'name': 'Email', 'selector':'Email', 'formato':'texto', 'ancho':'240px'},
                {'name': 'Nombre', 'selector':'Nombre', 'formato':'texto', 'ancho':'300px'},
                {'name': 'Áreas', 'selector':'Areas', 'formato':'texto', 'ancho':'400px'},
                {'name': 'Nivel', 'selector':'Nivel', 'formato':'texto'},
                {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho':'450px'},
                {'name': 'Estatus', 'selector':'Estatus', 'formato':'texto', 'ancho':'120px'},
                {'name': 'Editar', 'selector':'Editar', 'formato':'botonUsuario'}
            ]
        else:
            hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def PedidosPicker(self):
        pipeline = []
        data = []
        columns = []
        self.fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        self.fecha_fin = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                self.nivel_lugar = 'tienda'
                self.filtro_lugar = f" and ct.zona = '{self.filtros.zona}' "
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    self.nivel_lugar = 'tienda'
                    self.filtro_lugar = f" and ct.tienda = '{self.filtros.tienda}' "
                else:
                    self.nivel_lugar = 'tienda'
                    self.filtro_lugar = f" and ct.zona = '{self.filtros.zona}' "
            else:
                self.nivel_lugar = 'zona'
                self.filtro_lugar = f" and ct.region = '{self.filtros.region}' "
        else:
            self.nivel_lugar = 'region'
            self.filtro_lugar = ''

        if self.titulo == 'Pedido Diario':
            pipeline = f"""SELECT dy.{self.nivel_lugar} lugar,dy.Pedidos,isnull(dy.Pedidos_picker,0) Pedidos_picker, isnull(dx.picker_oficial,0) picker_oficial, isnull(dx.picker_general,0) picker_general,
            isnull(ROUND(CAST(dy.Pedidos_picker AS FLOAT)/CAST(dx.picker_general AS FLOAT),0),0) Pedidos_por_picker,dy.Pedidos_picker/cast(dy.n_dias as float) Pedidos_dia,
            dy.sku
            FROM (
                    select pp.{self.nivel_lugar},sum(n_pedido) Pedidos,sum(pedidos_picker) Pedidos_picker,count(DISTINCT fecha_ultimo_cambio) n_dias,
                    sum(case when nombre is not null then skus_enviados else 0 end) sku
                    from DWH.report.pedido_picker_productividad pp
                    left join DWH.artus.catTienda ct on ct.tienda = pp.idtienda 
                    where fecha_ultimo_cambio BETWEEN '{self.fecha_ini}' AND '{self.fecha_fin}'
                    {self.filtro_lugar}
                    group by pp.{self.nivel_lugar}
                ) dy
            LEFT JOIN
                (
                    select dx.{self.nivel_lugar}, sum(case WHEN dx.rol like 'SURTIDOR%' THEN 1 ELSE 0 END) picker_oficial, count(1) picker_general
                    from (select DISTINCT pp.{self.nivel_lugar},nombre,rol
                    from DWH.report.pedido_picker_productividad pp
                    left join DWH.artus.catTienda ct on ct.tienda = pp.idtienda 
                    where fecha_ultimo_cambio BETWEEN '{self.fecha_ini}' AND '{self.fecha_fin}'
                    {self.filtro_lugar}
                    and nombre is not null) dx
                    group by dx.{self.nivel_lugar}
                ) dx on dy.{self.nivel_lugar} = dx.{self.nivel_lugar}"""
            # print(f"query desde tablas->Faltantes->PedidosPicker: {str(pipeline)}")
            lugarMayus = self.nivel_lugar[:1].upper() + self.nivel_lugar[1:]
            cnxn = conexion_sql('DJANGO')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    data.append({
                        lugarMayus: row['lugar'],
                        'PedidosEntregados': row['Pedidos'],
                        'PedidosPicker': row['Pedidos_picker'],
                        'PickerOficial': row['picker_oficial'],
                        'PickerGeneral': row['picker_general'],
                        'ItemPicker': row['sku'],
                        'PedidosPorPicker': row['Pedidos_por_picker'],
                        'PedidosPorDia': row['Pedidos_dia']
                    })
                columns = [
                    {'name': lugarMayus, 'selector':lugarMayus, 'formato':'texto', 'ancho': '350px'},
                    {'name': 'Pedidos Entregados', 'selector':'PedidosEntregados', 'formato':'entero'},
                    {'name': 'Pedidos Picker', 'selector':'PedidosPicker', 'formato':'entero'},
                    {'name': 'Picker Oficial', 'selector':'PickerOficial', 'formato':'entero'},
                    {'name': 'Picker General', 'selector':'PickerGeneral', 'formato':'entero'},
                    {'name': 'Item Picker', 'selector':'ItemPicker', 'formato':'entero'},
                    {'name': 'Pedidos Por Picker', 'selector':'PedidosPorPicker', 'formato':'entero'},
                    {'name': 'Pedidos Por Día', 'selector':'PedidosPorDia', 'formato':'decimales'}
                ]
            else:
                hayResultados = 'no'
                
        elif self.titulo == 'Pedidos Picker por Agente':
            pipeline = f"""select nombre, rol, nomina, sum(comision) comision, sum(pedidos_picker) pedidos_picker,count(DISTINCT fecha_ultimo_cambio) dias_trab,sum(pedidos_picker)*100/cast((count(DISTINCT fecha_ultimo_cambio)*10) as float) productividad,
            sum(skus_enviados) sku
            from DWH.report.pedido_picker_productividad pp
            left join DWH.artus.catTienda ct on ct.tienda = pp.idtienda 
            where nombre is not null
            and fecha_ultimo_cambio BETWEEN '{self.fecha_ini}' AND '{self.fecha_fin}'
            and ct.tienda = '{self.filtros.tienda}'
            group by  nombre, rol, nomina"""
            # print(f"query desde tablas->Faltantes->PedidosPicker: {str(pipeline)}")
            lugarMayus = self.nivel_lugar[:1].upper() + self.nivel_lugar[1:]
            cnxn = conexion_sql('DJANGO')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    data.append({
                        # Aquí métele el id del agente, o lo que sea basado en lo que tienes en el BI Actual
                        'detalleAgente': row['nombre'],
                        'IDNomina': row['nomina'],
                        'Agente': row['nombre'],
                        'Rol': row['rol'],
                        'PedidosPicker': row['pedidos_picker'],
                        'ItemPicker': row['sku'],
                        'DiasTrabajados': row['dias_trab'],
                        'Porc_Productividad': float(row['productividad']) / 100,
                        'Comision': row['comision']
                    })
                columns = [
                    {'name': 'Ver Detalle', 'selector':'detalleAgente', 'formato':'detalleAgente'},
                    {'name': 'ID Nómina', 'selector':'IDNomina', 'formato':'texto'},
                    {'name': 'Agente', 'selector':'Agente', 'formato':'texto', 'ancho': '300px'},
                    {'name': 'Rol', 'selector':'Rol', 'formato':'texto', 'ancho': '300px'},
                    {'name': 'Pedidos Picker', 'selector':'PedidosPicker', 'formato':'entero'},
                    {'name': 'Item Picker', 'selector':'ItemPicker', 'formato':'entero'},
                    {'name': 'Días Trabajados', 'selector':'DiasTrabajados', 'formato':'entero'},
                    {'name': '% Productividad', 'selector':'Porc_Productividad', 'formato':'porcentaje'},
                    {'name': 'Comisión', 'selector':'Comision', 'formato':'moneda'}
                ]
            else:
                hayResultados = 'no'
                
        elif self.titulo == 'Pedidos por Día para $agente':
            pipeline = f"""select fecha_ultimo_cambio, sum(comision) comision,sum(pedidos_picker) pedidos_picker,sum(pedidos_picker)*100/cast(10 as float) productividad,
            sum(skus_enviados) sku
            from DWH.report.pedido_picker_productividad
            where nombre is not null
            and fecha_ultimo_cambio BETWEEN '{self.fecha_ini}' AND '{self.fecha_fin}'
            and nombre = '{self.filtros.fromSibling}'
            group by  fecha_ultimo_cambio, rol
            order by fecha_ultimo_cambio"""
            # print(f"query desde tablas->Faltantes->PedidosPicker: {str(pipeline)}")
            lugarMayus = self.nivel_lugar[:1].upper() + self.nivel_lugar[1:]
            cnxn = conexion_sql('DJANGO')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:

                    data.append({
                        # Aquí métele el id del agente, o lo que sea basado en lo que tienes en el BI Actual
                        'Fecha': row['fecha_ultimo_cambio'].strftime("%d/%m/%Y"),
                        'PedidosPicker': row['pedidos_picker'],
                        'ItemPicker': row['sku'],
                        'Porc_Productividad': float(row['productividad']) / 100,
                        'Comision': row['comision']
                    })
                columns = [
                    {'name': 'Fecha', 'selector':'Fecha', 'formato':'texto'},
                    {'name': 'Pedidos Picker', 'selector':'PedidosPicker', 'formato':'entero'},
                    {'name': 'Item Picker', 'selector':'ItemPicker', 'formato':'entero'},
                    {'name': '% Productividad', 'selector':'Porc_Productividad', 'formato':'porcentaje'},
                    {'name': 'Comisión', 'selector':'Comision', 'formato':'moneda'}
                ]
            else:
                hayResultados = 'no'
                
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def Temporada(self):
        pipeline = []
        data = []
        columns = []
        hayResultados = 'no'
        self.fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        self.fecha_fin = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        fecha_ini_str = self.filtros.fechas['fecha_ini'][:10]
        fecha_ini_int = int(fecha_ini_str[0:4]) * 10000 + int(fecha_ini_str[5:7]) * 100 + int(fecha_ini_str[8:10])
        fecha_fin_str = self.filtros.fechas['fecha_fin'][:10]
        fecha_fin_int = int(fecha_fin_str[0:4]) * 10000 + int(fecha_fin_str[5:7]) * 100 + int(fecha_fin_str[8:10])


        hayCanal = False if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '' else True

        nMes = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').month
        nMes = '0'+ str(nMes) if nMes < 10 else f'{nMes}'

        if self.titulo != 'Venta por Tienda':
            if self.titulo == 'Detalle Departamentos':
                agrupador = 'a.depto,b.DEPTO_NOMBRE'
                anterior = 'No hay'
                tituloColumnas = 'Departamento'
                campoA = 'depto'
                campoB = 'DEPTO_NOMBRE'
            if self.titulo == 'Detalle Sub-Departamentos para Depto $depto':
                agrupador = 'a.SUBDEPTO, b.SUBDEPTO_NOMBRE'
                anterior = 'DEPTO'
                tituloColumnas = 'SubDepartamento'
                campoA = 'SUBDEPTO'
                campoB = 'SUBDEPTO_NOMBRE'
            if self.titulo == 'Detalle Clases para SubDepto $subDepto':
                agrupador = 'a.CLASE, b.CLASE_NOMBRE'
                anterior = 'SUBDEPTO'
                tituloColumnas = 'Clase'
                campoA = 'CLASE'
                campoB = 'CLASE_NOMBRE'
            if self.titulo == 'Detalle Sub-Clases para Clase $clase':
                agrupador = 'a.SUBCLASE, b.SUBCLASE_NOMBRE'
                anterior = 'CLASE'
                tituloColumnas = 'SubClase'
                campoA = 'SUBCLASE'
                campoB = 'SUBCLASE_NOMBRE'
            if self.titulo == 'Detalle Formatos para SubClase $subClase':
                agrupador = 'c.FORMATONOMBRE'
                anterior = 'SUBCLASE'
                tituloColumnas = 'Formato'
                campoB = 'FORMATONOMBRE'

            pipeline = f"""
            -- para canal a.idTipo <> 0 reemplazar por a.idTipo = 1 o 35,36,38
            -- para canal cc.tipo <>0 reemplazar por cc.tipo = 1 o 35,36,38
            select {agrupador}, ---se cambia el agrupador
            sum(case when dt2.fecha = convert(date,GETDATE()) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) DiaActual_AnioActual,
            sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE())) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) DiaActual_AnioAnterior,
            sum(case when dt.fecha = convert(date,GETDATE()) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) DiaComparable_AnioAnterior,
            case when sum(case when dt2.fecha = convert(date,GETDATE()) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) = 0 then 0 else
            sum(case when dt2.fecha = convert(date,GETDATE()) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) /
            sum(case when dt2.fecha = convert(date,GETDATE()) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) end porc_part_dia_actual,
            case when sum(case when dt.fecha = convert(date,GETDATE()) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) = 0 then 0 else
            sum(case when dt.fecha = convert(date,GETDATE()) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) /
            sum(case when dt.fecha = convert(date,GETDATE()) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) end DiaComparable_AnioAnteriorTF,
            case when sum(case when dt2.fecha = convert(date,GETDATE()) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end)= 0 then 0 else
            (sum(case when dt2.fecha = convert(date,GETDATE()) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) /
            sum(case when dt2.fecha = convert(date,GETDATE()) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end)) end -
            case when sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE())) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end)=0 then 0 ELSE
            (sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE())) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end) /
            sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE())) and a.idTipo = 0 and a.hora < DATEPART( hh,GETDATE()) - 1 then vtaSinImp else 0 end)) end porcParDiff,
            max(case when dt2.fecha =convert(date,GETDATE()) then co.Objetivo end) objetivo,
            sum(case when dt2.fecha = convert(date,GETDATE()-1) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) DiaVencidoAnioActual,
            sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE()-1)) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) DiaVencidoAnioAnterior,
            sum(case when dt.fecha = convert(date,GETDATE()-1) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) DiaAyerComparable_AnioAnterior, --se agrego está columna y debe de ver se después de venta ayer AA
            case when sum(case when dt2.fecha = convert(date,GETDATE()-1) and a.idTipo = 0 then vtaSinImp else 0 end)= 0 then 0 else
            sum(case when dt2.fecha = convert(date,GETDATE()-1) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) /
            sum(case when dt2.fecha = convert(date,GETDATE()-1) and a.idTipo = 0 then vtaSinImp else 0 end) end porc_part_dia_vencido,
            case when sum(case when dt2.fecha = convert(date,GETDATE()-1) and a.idTipo = 0 then vtaSinImp else 0 end)= 0 then 0 else
            (sum(case when dt2.fecha = convert(date,GETDATE()-1) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) /
            sum(case when dt2.fecha = convert(date,GETDATE()-1) and a.idTipo = 0 then vtaSinImp else 0 end)) end -
            case when sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE()-1)) and a.idTipo = 0 then vtaSinImp else 0 end)=0 then 0 else
            (sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE()-1)) and {'a.idTipo <> 0' if not hayCanal else 'a.idTipo = '+self.filtros.canal} then vtaSinImp else 0 end) /
            sum(case when dt2.fecha = convert(date,DATEADD(yy,-1,GETDATE()-1)) and a.idTipo = 0 then vtaSinImp else 0 end)) end porcParDiffVencido,
            max(case when dt2.fecha = convert(date,GETDATE()) and a.hora < DATEPART( hh,GETDATE()) - 1 then hora end) hora
            from DWH.artus.ventaDiarioHoraSubClase a
            left join DWH.dbo.dim_tiempo dt on a.fecha =dt.fechaComparacion
            left join DWH.dbo.dim_tiempo dt2 on a.fecha =dt2.id_fecha
            left join (select DISTINCT tipo,esOmnicanal
            from DWH.artus.catCanal) cc on a.idTipo =cc.tipo
            left join DWH.artus.catObjetivo co on cc.esOmnicanal =co.idTipo and co.nMes = format(GETDATE(),'yyyyMM') and {'cc.tipo <>0' if not hayCanal else 'cc.tipo = '+self.filtros.canal}
            left join (select distinct SUBCLASE,SUBCLASE_NOMBRE,DEPTO_NOMBRE,SUBDEPTO_NOMBRE,CLASE_NOMBRE
            from DWH.artus.catMARA cm )b on a.subClase = b.subClase
            left join (select distinct formato,formatoNombre
            from DWH.artus.catTienda) c on a.formato=c.formato
            where (dt2.fecha BETWEEN convert(date,GETDATE()-1) and convert(date,GETDATE())
            or dt.fecha BETWEEN convert(date,GETDATE()-1) and convert(date,GETDATE())
            or dt2.fecha BETWEEN convert(date,DATEADD(yy,-1,GETDATE()-1)) and convert(date,DATEADD(yy,-1,GETDATE())))
            {'and a.'+anterior + ' = ' + self.filtros.fromSibling if anterior != 'No hay' else ''}
            --- se agrega el filtro del nivel que quieren consultar
            group by {agrupador} ---se cambia el agrupador
            order by {'c.' if self.titulo == 'Detalle Formatos para SubClase $subClase' else 'b.'}{campoB}"""
            # print(f"query desde tablas->Temporada->{self.titulo}: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                maxHora = 0
                if self.titulo == 'Detalle Departamentos':
                    totales = {'DiaActual_AnioActual': 0, 'DiaActual_AnioAnterior': 0, 'DiaComparable_AnioAnterior': 0, 'porc_part_dia_actual': 0, 'DiaComparable_AnioAnteriorTF': 0, 'porcParDiff': 0, 'DiaVencidoAnioActual': 0, 'DiaVencidoAnioAnterior': 0, 'porc_part_dia_vencido': 0, 'porcParDiffVencido': 0, 'DiaAyerComparable_AnioAnterior': 0}
                for row in arreglo:
                    dicc = {
                        tituloColumnas+'Nombre': row[campoB],
                        'VentaHoy': row['DiaActual_AnioActual'],
                        'VentaHoyAA': row['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': row['DiaComparable_AnioAnterior'],
                        # 'PorcVsDiaComparable': f"{row['DiaActual_AnioActual']}/{row['DiaComparable_AnioAnterior']}",
                        'PorcVsDiaComparable': float(row['DiaActual_AnioActual']/row['DiaComparable_AnioAnterior']) if row['DiaComparable_AnioAnterior'] != 0 else '--',
                        'PorcPartHoy': row['porc_part_dia_actual'],
                        'DiaComparable_AnioAnteriorTF': row['DiaComparable_AnioAnteriorTF'],
                        'PorcPartHoyVsAA': row['porcParDiff'],
                        'VentaAyer': row['DiaVencidoAnioActual'],
                        'VentaAyerAA': row['DiaVencidoAnioAnterior'],
                        'DiaAyerComparable_AnioAnterior': row['DiaAyerComparable_AnioAnterior'],
                        'PorcPartAyer': row['porc_part_dia_vencido'],
                        'PorcPartAyerVsAA': row['porcParDiffVencido']
                    }
                    if self.titulo != 'Detalle Formatos para SubClase $subClase':
                        dicc['detalle'+tituloColumnas] = ''
                        dicc['Id'+tituloColumnas] = row[campoA]
                    data.append(dicc)
                    maxHora = int(row['hora']) if row['hora'] is not None and maxHora < int(row['hora']) else maxHora
                    if self.titulo == 'Detalle Departamentos':
                        totales['DiaActual_AnioActual'] += float(row['DiaActual_AnioActual'])
                        totales['DiaActual_AnioAnterior'] += float(row['DiaActual_AnioAnterior'])
                        totales['DiaComparable_AnioAnterior'] += float(row['DiaComparable_AnioAnterior'])
                        # totales['porc_part_dia_actual'] += float(row['porc_part_dia_actual'])
                        # totales['DiaComparable_AnioAnteriorTF'] += float(row['DiaComparable_AnioAnteriorTF'])
                        # totales['porcParDiff'] += float(row['porcParDiff'])
                        totales['DiaVencidoAnioActual'] += float(row['DiaVencidoAnioActual'])
                        totales['DiaVencidoAnioAnterior'] += float(row['DiaVencidoAnioAnterior'])
                        totales['DiaAyerComparable_AnioAnterior'] += float(row['DiaAyerComparable_AnioAnterior'])
                        # totales['porc_part_dia_vencido'] += float(row['porc_part_dia_vencido'])
                        # totales['porcParDiffVencido'] += float(row['porcParDiffVencido'])
                if self.titulo == 'Detalle Departamentos':
                    data.append({
                        'detalleDepartamento': '',
                        'IdDepartamento': '--',
                        'DepartamentoNombre': 'Total:',
                        'VentaHoy': totales['DiaActual_AnioActual'],
                        'VentaHoyAA': totales['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': totales['DiaComparable_AnioAnterior'],
                        'PorcVsDiaComparable': '--',
                        # 'PorcPartHoy': totales['porc_part_dia_actual'],
                        'PorcPartHoy': '--',
                        # 'DiaComparable_AnioAnteriorTF': totales['DiaComparable_AnioAnteriorTF'],
                        'DiaComparable_AnioAnteriorTF': '--',
                        # 'PorcPartHoyVsAA': totales['porcParDiff'],
                        'PorcPartHoyVsAA': '--',
                        'VentaAyer': totales['DiaVencidoAnioActual'],
                        'VentaAyerAA': totales['DiaVencidoAnioAnterior'],
                        'DiaAyerComparable_AnioAnterior': totales['DiaAyerComparable_AnioAnterior'],
                        # 'PorcPartAyer': totales['porc_part_dia_vencido'],
                        'PorcPartAyer': '--',
                        # 'PorcPartAyerVsAA': totales['porcParDiffVencido']
                        'PorcPartAyerVsAA': '--'
                        })
                columns = []
                if self.titulo != 'Detalle Formatos para SubClase $subClase':
                    columns.extend([
                        {'name': 'Ver Detalle', 'selector':'detalle'+tituloColumnas, 'formato':'detalle'+tituloColumnas},
                        {'name': 'ID '+tituloColumnas, 'selector':'Id'+tituloColumnas, 'formato':'entero'}
                    ])
                columns.extend([
                    {'name': 'Nombre '+tituloColumnas, 'selector': tituloColumnas+'Nombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Venta Hoy ('+str(maxHora)+':00)', 'selector':'VentaHoy', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Hoy AA', 'selector':'VentaHoyAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Día Comparable', 'selector':'DiaComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Vs. Día Comparable', 'selector':'PorcVsDiaComparable', 'formato':'porcentaje'},
                    {'name': '% Part Hoy', 'selector':'PorcPartHoy', 'formato':'porcentaje'},
                    {'name': '% Part Comparable', 'selector':'DiaComparable_AnioAnteriorTF', 'formato':'porcentaje'},
                    {'name': '% Part Hoy Vs. AA', 'selector':'PorcPartHoyVsAA', 'formato':'porcentaje'},
                    {'name': 'Venta Ayer', 'selector':'VentaAyer', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer AA', 'selector':'VentaAyerAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer Comparable', 'selector':'DiaAyerComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Ayer', 'selector':'PorcPartAyer', 'formato':'porcentaje'},
                    {'name': '% Part Ayer Vs. AA', 'selector':'PorcPartAyerVsAA', 'formato':'porcentaje'}
                ])
            else:
                hayResultados = 'no'
                
        elif self.titulo == 'Venta por Tienda':
            query = f"""select ct.regionNombre, ct.zonaNombre, ct.tiendaNombre,
                sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) ventaActual,
                case when sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end)=0 then 0 else round(((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) /
                sum(case when year(DATEADD(yy,-1,GETDATE()))=year(dt2.fecha) then a.ventaSinImpuestos else 0 end))-1)*100,2) end PartvsAA,
                round((sum(case when year(GETDATE())=year(dt2.fecha) then a.ventaSinImpuestos else 0 end) / (select sum(ventaSinImpuestos) vTF
                from DWH.artus.ventaxdia vxd
                left join DWH.dbo.dim_tiempo dtt on dtt.id_fecha = vxd.fecha
                where vxd.fecha BETWEEN '{fecha_ini_int}' and '{fecha_fin_int}' and idCanal = 0))*100,2) PartvsTF,max(co.Objetivo) Objetivo
                from DWH.artus.ventaDiaria a
                left join DWH.artus.catTienda ct on a.idTienda = ct.tienda
                left join DWH.dbo.dim_tiempo dt on a.fecha =dt.fechaComparacion
                left join DWH.dbo.dim_tiempo dt2 on a.fecha =dt2.id_fecha
                left join DWH.artus.catCanal cc on a.idCanal =cc.idCanal
                left join DWH.artus.catObjetivo co on co.idTipo = cc.{'esOmnicanal' if not hayCanal else 'idCanal'} and format(dt2.fecha,'yyyyMM')=co.nMes
                where (dt2.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}'
                or dt.fecha BETWEEN '{fecha_ini_str}' and '{fecha_fin_str}')
                and cc.tipo {'= '+self.filtros.canal if hayCanal else 'not in (0)'}
                group by ct.regionNombre, ct.zonaNombre, ct.tiendaNombre
                order by ct.regionNombre, ct.zonaNombre, ct.tiendaNombre
                """
            # print (f"query desde ejesMultiples->Temporada -> Venta por tienda: {str(query)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    data.append({
                        'Region': row['regionNombre'] if row['regionNombre'] is not None else '--',
                        'Zona': row['zonaNombre'] if row['zonaNombre'] is not None else '--',
                        'Tienda': row['tiendaNombre'] if row['tiendaNombre'] is not None else '--',
                        'VentaActual': row['ventaActual'] if row['ventaActual'] is not None else '--',
                        'PartvsTF': row['PartvsTF'] if row['PartvsTF'] is not None else '--',
                        'Objetivo': row['Objetivo'] if row['Objetivo'] is not None else '--',
                        'Diferencia': float(row['PartvsTF']) - float(row['Objetivo']) if row['PartvsTF'] is not None and row['Objetivo'] is not None else '--'
                    })
                columns.extend([
                    {'name': 'Región', 'selector': 'Region', 'formato': 'texto', 'ancho': '220px'},                                
                    {'name': 'Zona', 'selector': 'Zona', 'formato': 'texto', 'ancho': '220px'},                                
                    {'name': 'Tienda', 'selector': 'Tienda', 'formato': 'texto', 'ancho': '400px'},                                
                    {'name': 'Venta Actual', 'selector': 'VentaActual', 'formato': 'moneda', 'ancho': '130px'},                                
                    {'name': 'Part Vs Tienda Física', 'selector': 'PartvsTF', 'formato': 'porcentaje'},                                
                    {'name': 'Objetivo', 'selector': 'Objetivo', 'formato': 'porcentaje'},                                
                    {'name': 'Diferencia', 'selector': 'Diferencia', 'formato': 'porcentaje'}
                ])
            else:
                hayResultados = 'no'

        # print(f"Data desde Tablas -> Temporada: {str(data)}")
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}

    async def NivelesDeServicio(self):
        pipeline = []
        columns = []
        data = []
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
            pipeline.append({'$match': {'fechaEntrega': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}})
            if self.filtros.categoria and self.filtros.categoria != "False" and self.filtros.categoria != "" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "" and self.filtros.tipoEntrega != None:
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'xLabel':'$sucursal.'+siguiente_nivel, 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, '$pedidos', 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, '$pedidos', 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, '$pedidos', 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, '$pedidos', 0]}}})
            pipeline.append({'$group':{'_id':'$xLabel', 'Entregado_Fuera_tiempo':{'$sum':'$Entregado_Fuera_tiempo'}, 'Entregado_tiempo':{'$sum':'$Entregado_tiempo'}, 'No_entregado_Fuera_tiempo':{'$sum':'$No_entregado_Fuera_tiempo'}, 'No_entregado_tiempo':{'$sum':'$No_entregado_tiempo'}, 'Despachado_Fuera_tiempo':{'$sum':'$Despachado_Fuera_tiempo'}, 'Despachado_tiempo':{'$sum':'$Despachado_tiempo'}}})
            pipeline.append({'$sort':{'_id':1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    data.append({
                        'Lugar': row['_id'],
                        'Entregado_Fuera_tiempo': row['Entregado_Fuera_tiempo'],
                        'Entregado_tiempo': row['Entregado_tiempo'],
                        'No_entregado_Fuera_tiempo': row['No_entregado_Fuera_tiempo'],
                        'No_entregado_tiempo': row['No_entregado_tiempo'],
                        'Despachado_Fuera_tiempo': row['Despachado_Fuera_tiempo'],
                        'Despachado_tiempo': row['Despachado_tiempo'],
                    })
                columns.extend([
                    {'name': 'Lugar', 'selector': 'Lugar', 'formato': 'texto', 'ancho': '420px'},                                
                    {'name': 'Entregado-Fuera de tiempo', 'selector': 'Entregado_Fuera_tiempo', 'formato': 'texto'},                                
                    {'name': 'Entregado-A tiempo', 'selector': 'Entregado_tiempo', 'formato': 'texto'},
                    {'name': 'No entregado-Fuera de tiempo', 'selector': 'No_entregado_Fuera_tiempo', 'formato': 'texto'},
                    {'name': 'No entregado-A tiempo', 'selector': 'No_entregado_tiempo', 'formato': 'texto'},
                    {'name': 'Despachado-Fuera de tiempo', 'selector': 'Despachado_Fuera_tiempo', 'formato': 'texto'},
                    {'name': 'Despachado-A tiempo', 'selector': 'Despachado_tiempo', 'formato': 'texto'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Estatus de Entrega y No Entrega por Tienda':
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
            pipeline.append({'$match': {'fechaEntrega': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}})
            if self.filtros.categoria and self.filtros.categoria != "False" and self.filtros.categoria != "" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "" and self.filtros.tipoEntrega != None:
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$project':{'xLabel':'$sucursal.tienda', 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, '$pedidos', 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, '$pedidos', 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, '$pedidos', 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, '$pedidos', 0]}}})
            pipeline.append({'$group':{'_id':'$xLabel', 'Entregado_Fuera_tiempo':{'$sum':'$Entregado_Fuera_tiempo'}, 'Entregado_tiempo':{'$sum':'$Entregado_tiempo'}, 'No_entregado_Fuera_tiempo':{'$sum':'$No_entregado_Fuera_tiempo'}, 'No_entregado_tiempo':{'$sum':'$No_entregado_tiempo'}, 'Despachado_Fuera_tiempo':{'$sum':'$Despachado_Fuera_tiempo'}, 'Despachado_tiempo':{'$sum':'$Despachado_tiempo'}}})
            pipeline.append({'$sort':{'_id':1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    data.append({
                        'Lugar': row['_id'],
                        'Entregado_Fuera_tiempo': row['Entregado_Fuera_tiempo'],
                        'Entregado_tiempo': row['Entregado_tiempo'],
                        'No_entregado_Fuera_tiempo': row['No_entregado_Fuera_tiempo'],
                        'No_entregado_tiempo': row['No_entregado_tiempo'],
                        'Despachado_Fuera_tiempo': row['Despachado_Fuera_tiempo'],
                        'Despachado_tiempo': row['Despachado_tiempo'],
                    })
                columns.extend([
                    {'name': 'Lugar', 'selector': 'Lugar', 'formato': 'texto', 'ancho': '420px'},                                
                    {'name': 'Entregado-Fuera de tiempo', 'selector': 'Entregado_Fuera_tiempo', 'formato': 'texto'},                                
                    {'name': 'Entregado-A tiempo', 'selector': 'Entregado_tiempo', 'formato': 'texto'},
                    {'name': 'No entregado-Fuera de tiempo', 'selector': 'No_entregado_Fuera_tiempo', 'formato': 'texto'},
                    {'name': 'No entregado-A tiempo', 'selector': 'No_entregado_tiempo', 'formato': 'texto'},
                    {'name': 'Despachado-Fuera de tiempo', 'selector': 'Despachado_Fuera_tiempo', 'formato': 'texto'},
                    {'name': 'Despachado-A tiempo', 'selector': 'Despachado_tiempo', 'formato': 'texto'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Detalle de pedidos $tienda':
            collection = conexion_mongo('report').report_detallePedidos
            pipeline.append({'$match': {'idtienda': int(self.filtros.tienda)}})
            pipeline.append({'$match': {'fechaEntregaProgramadaNS': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}})
            pipeline.append({'$match': {'estatusConsigna': {'$not': {'$eq': 'Canceled'}}}})
            if self.filtros.categoria and self.filtros.categoria != "False" and self.filtros.categoria != "" and self.filtros.categoria != None:
                pipeline.append({'$match': {'tercero': self.filtros.categoria}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "" and self.filtros.tipoEntrega != None:
                pipeline.append({'$match': {'tipoEntrega': self.filtros.tipoEntrega}})
            # pipeline.append({'$project':{'xLabel':'$sucursal.tienda', 'Entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'Entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','Entregado-A tiempo']}, '$pedidos', 0]}, 'No_entregado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-Fuera de tiempo']}, '$pedidos', 0]}, 'No_entregado_tiempo': {'$cond': [{'$eq':['$evaluacion','No entregado-A tiempo']}, '$pedidos', 0]}, 'Despachado_Fuera_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-Fuera de tiempo']}, '$pedidos', 0]}, 'Despachado_tiempo': {'$cond': [{'$eq':['$evaluacion','Despachado-A tiempo']}, '$pedidos', 0]}}})
            pipeline.append({'$project':{
                'nPedido':'$nPedido', 
                'ultimoCambio': {'$dateToString': {'format': '%d/%m/%Y %H:%M:%S', 'date': '$ultimoCambio'}}, 
                'nConsigna': '$nConsigna', 
                'metodoEntrega': '$metodoEntrega', 
                'descrip_paymentmode': '$descrip_paymentmode', 
                'fechaCreacion': {'$dateToString': {'format': '%d/%m/%Y %H:%M:%S', 'date': '$fechaCreacion'}}, 
                'timeslot_from': {'$dateToString': {'format': '%d/%m/%Y %H:%M:%S', 'date': '$timeslot_from'}}, 
                'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y %H:%M:%S', 'date': '$timeslot_to'}}, 
                'Minutos_tarde': '$Minutos_tarde', 
                'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y %H:%M:%S', 'date': '$fechaEntrega'}},
                'fechaDespacho': {'$dateToString': {'format': '%d/%m/%Y %H:%M:%S', 'date': '$fechaDespacho'}},
                'estatusConsigna': '$estatusConsigna',
                'evaluacion': '$evaluacion'
            }})
            pipeline.append({'$sort':{'nPedido':1}})
            print(f'Pipeline desde Tablas -> NivelesDeServicio -> Detalle de pedidos $tienda: {str(pipeline)}')
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=None)
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    minutos_tarde = str(row['Minutos_tarde']) if 'Minutos_tarde' in row and row['Minutos_tarde'] is not None else '0'
                    timeslot_from = row['timeslot_from'] if 'timeslot_from' in row and row['timeslot_from'] is not None else '--'
                    timeslot_to = row['timeslot_to'] if 'timeslot_to' in row and row['timeslot_to'] is not None else '--'
                    fechaDespacho = row['fechaDespacho'] if 'fechaDespacho' in row and row['fechaDespacho'] is not None else '--'
                    fechaEntrega = row['fechaEntrega'] if 'fechaEntrega' in row and row['fechaEntrega'] is not None else '--'
                    evaluacion = row['evaluacion'] if 'evaluacion' in row and row['evaluacion'] is not None else '--'
                    # print(f"timeslot_from es {str(timeslot_from)}")
                    data.append({
                        'ultimoCambio': row['ultimoCambio'],
                        'nPedido': row['nPedido'],
                        'nConsigna': row['nConsigna'],
                        'descrip_paymentmode': row['descrip_paymentmode'],
                        'metodoEntrega': row['metodoEntrega'],
                        'fechaCreacion': row['fechaCreacion'],
                        'timeslot_from': timeslot_from,
                        'timeslot_to': timeslot_to,
                        'Minutos_tarde': minutos_tarde,
                        'fechaEntrega': fechaEntrega,
                        'fechaDespacho': fechaDespacho,
                        'estatusConsigna': row['estatusConsigna'],
                        'evaluacion': evaluacion
                    })
                columns.extend([
                    {'name': 'Último Cambio', 'selector': 'ultimoCambio', 'formato': 'texto', 'ancho': '180px'},                                
                    {'name': 'No. de Orden', 'selector': 'nPedido', 'formato': 'sinComas', 'ancho': '120px'},
                    {'name': 'No. de Consigna', 'selector': 'nConsigna', 'formato': 'texto', 'ancho': '120px'},
                    {'name': 'Método de Entrega', 'selector': 'metodoEntrega', 'formato': 'texto', 'ancho': '160px'},
                    {'name': 'Método de Pago', 'selector': 'descrip_paymentmode', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Fecha Creación', 'selector': 'fechaCreacion', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Timeslot Incio', 'selector': 'timeslot_from', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Timeslot Fin', 'selector': 'timeslot_to', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Minutos Tarde', 'selector': 'Minutos_tarde', 'formato': 'texto'},
                    {'name': 'Fecha Entrega', 'selector': 'fechaEntrega', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Fecha Despacho', 'selector': 'fechaDespacho', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Estaus Consigna', 'selector': 'estatusConsigna', 'formato': 'texto', 'ancho': '180px'},
                    {'name': 'Evaluación', 'selector': 'evaluacion', 'formato': 'texto', 'ancho': '190px'}
                ])
            else:
                hayResultados = "no"

        # print(f"Data desde Tablas -> Temporada: {str(data)}")
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}

@router.post("/{seccion}")
async def tablas (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = Tablas(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso"}

