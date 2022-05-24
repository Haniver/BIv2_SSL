from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import ddmmyyyy
from datetime import datetime, timedelta
from calendar import monthrange
from app.servicios.formatoFechas import mesTexto
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from copy import deepcopy
from numpy import zeros
from app.servicios.permisos import tienePermiso
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
            self.fecha_fin = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
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
            arreglo = await cursor.to_list(length=1000)
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
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}


    async def VentaOmnicanal2(self):
        pipeline = []
        data = []
        columns = []
        collection = conexion_mongo('report').report_mktProveedores
        if self.filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ self.nivel_lugar: self.lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini, '$lt': self.fecha_fin}}}])

        if self.titulo == 'Venta Top 200 Proveedores':
            pipeline.extend([
                {'$unwind': '$articulo'},
                {'$group': {'_id': {'id': '$articulo.proveedor', 'nombre': '$articulo.proveedorNombre'}, 'monto': {'$sum': '$vtaSinImp'}}},
                {'$project': {'_id':0, 'id': '$_id.id', 'nombre': '$_id.nombre', 'monto': '$monto'}},
                {'$sort': {'monto': -1}},
                { '$limit': 200 }
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
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
                    data.append(
                        {'lugar': lugar,
                        'nombre': dato['nombre'],
                        'id': dato['id'],
                        'monto': dato['monto']
                    })
                    lugar += 1

        if self.titulo == 'Top 1,000 SKU':
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
            arreglo = await cursor.to_list(length=1000)
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
            pipeline.append({'$unwind': '$articulo'})
            if self.filtros.proveedor != 0 and self.filtros.proveedor != 1 and self.filtros.proveedor != None:
                pipeline.append({'$match': {'articulo.proveedor': self.filtros.proveedor}})
            pipeline.extend([
                {'$group': {'_id': {'fecha_interna': '$fecha', 'fecha_mostrar': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fecha'}}}, 'pedidos': {'$sum': 1}, 'monto': {'$sum': '$vtaSinImp'}}},
                {'$project': {'_id': 0, 'fecha_interna': '$_id.fecha_interna', 'fecha_mostrar': '$_id.fecha_mostrar', 'pedidos': '$pedidos', 'monto': '$monto', 'ticket_promedio': {'$divide': ['$monto', '$pedidos']}}},
                {'$sort': {'fecha_interna': 1}}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
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
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}


    async def FoundRate(self):
        pipeline = []
        data = []
        columns = []
        if self.titulo == 'Detalle Porcentaje Estatus por Lugar':
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
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
            arreglo = await cursor.to_list(length=1000)
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

        if self.titulo == 'Tiendas Top 20 Estatus Completo':
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
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
            pipeline.append({'$project':{'_id':0, 'lugar':'$_id', 'COMPLETO': {'$divide':['$COMPLETO', '$num_pedidos']}, 'INC_SIN_STOCK': {'$divide':['$INC_SIN_STOCK', '$num_pedidos']}, 'INC_SUSTITUTOS': {'$divide':['$INC_SUSTITUTOS', '$num_pedidos']}, 'INCOMPLETO': {'$divide':['$INCOMPLETO', '$num_pedidos']}}})
            pipeline.append({'$sort':{'COMPLETO':-1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=20)
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

        if self.titulo == 'Tiendas Top 20 Estatus Incompleto':
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
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
            pipeline.append({'$project':{'_id':0, 'lugar':'$_id', 'COMPLETO': {'$divide':['$COMPLETO', '$num_pedidos']}, 'INC_SIN_STOCK': {'$divide':['$INC_SIN_STOCK', '$num_pedidos']}, 'INC_SUSTITUTOS': {'$divide':['$INC_SUSTITUTOS', '$num_pedidos']}, 'INCOMPLETO': {'$divide':['$INCOMPLETO', '$num_pedidos']}}})
            pipeline.append({'$sort':{'INCOMPLETO':-1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=20)
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
            arreglo = await cursor.to_list(length=1000)
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
        if self.titulo == 'Tiendas con Pedidos Atrasados Mayores a 1 Día':
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    nivel = 'zona'
                    self.lugar = int(self.filtros.zona)
                else:
                    nivel = 'region'
                    self.lugar = int(self.filtros.region)
            else:
                self.filtro_lugar = False
                self.lugar = ''

            collection = conexion_mongo('report').report_pedidoPendientes
            pipeline.append({'$unwind': '$sucursal'})
            if self.filtro_lugar:
                pipeline.append({'$match': {'sucursal.'+ nivel: self.lugar}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$match': {'prioridad': {'$in': ['2 DIAS','ANTERIORES']}}})
            pipeline.append({'$group': {'_id': {'region': '$sucursal.regionNombre', 'zona': '$sucursal.zonaNombre', 'tienda': '$sucursal.tiendaNombre'}, 'pedidos': {'$sum': 1}, 'fechaEntrega': {'$min':'$fechaEntrega'}}})
            pipeline.append({'$sort': {'pedidos': -1}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            data = []
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'region': dato['_id']['region'],
                        'zona': dato['_id']['zona'],
                        'tienda': dato['_id']['tienda'],
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
            pipeline.append({'$unwind': '$sucursal'})
            pipeline.append({'$match': {'sucursal.idTienda': self.lugar}})
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            pipeline.extend([{'$project': {
                'Tienda': '$sucursal.tiendaNombre',
                'NumOrden': '$pedido',
                'Consigna': '$consigna',
                'Prioridad': '$prioridad',
                'FechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}}
            }}, {'$sort': 
                {'Consigna': 1}
            }])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
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
                    {'name': 'Consigna', 'selector':'Consigna', 'formato':'texto', 'ancho': '120px'},
                    {'name': 'Prioridad', 'selector':'Prioridad', 'formato':'texto', 'ancho': '150px'},
                    {'name': 'Fecha', 'selector':'FechaEntrega', 'formato':'texto', 'ancho': '110px'}
                ]
        if self.titulo == 'Pedidos No Entregados o No Cancelados':
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
            collection = conexion_mongo('report').report_pedidoPendientes48horas
            pipeline = [{'$unwind': '$sucursal'}]
            if self.filtro_lugar:
                pipeline.append(
                    {'$match': {f'sucursal.{nivel}': self.lugar}}
                )
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            pipeline.extend([{'$project': {
                'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                'regionNombre': '$sucursal.regionNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'Delivering': {'$cond': [{'$eq': ["$estatus","Delivering"]}, 1, 0]},
                'PickPack': {'$cond': [{'$eq': ["$estatus","Pick Pack"]}, 1, 0]},
                'Ready': {'$cond': [{'$eq': ["$estatus","Ready"]}, 1, 0]},
                'ReadyForPickUp': {'$cond': [{'$eq': ["$estatus","Ready for Pick Up"]}, 1, 0]}
                }},
                {'$group': {
                    '_id': {
                        'fechaEntrega': '$fechaEntrega',
                        'regionNombre': '$regionNombre',
                        'zonaNombre': '$zonaNombre',
                        'tiendaNombre': '$tiendaNombre',
                    },
                    'Delivering': {'$sum': '$Delivering'},
                    'PickPack': {'$sum': '$PickPack'},
                    'Ready': {'$sum': '$Ready'},
                    'ReadyForPickUp': {'$sum': '$ReadyForPickUp'}
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
                    'Delivering': {'$sum': '$Delivering'},
                    'PickPack': {'$sum': '$PickPack'},
                    'Ready': {'$sum': '$Ready'},
                    'ReadyForPickUp': {'$sum': '$ReadyForPickUp'}
                }},
                {'$sort': {'fechaOrdenar': 1, 'regionNombre': 1, 'zonaNombre': 1, 'tiendaNombre': 1}}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            data = []
            if len(arreglo) >0:
                hayResultados = "si"
                for dato in arreglo:
                    data.append({
                        'fechaEntrega': dato['_id']['fechaEntrega'],
                        'regionNombre': dato['_id']['regionNombre'],
                        'zonaNombre': dato['_id']['zonaNombre'],
                        'tiendaNombre': dato['_id']['tiendaNombre'],
                        'Delivering': dato['Delivering'],
                        'PickPack': dato['PickPack'],
                        'Ready': dato['Ready'],
                        'ReadyForPickUp': dato['ReadyForPickUp']
                    })
            else:
                hayResultados = 'no'
            columns = [
                    {'name': 'Fecha de Entrega', 'selector':'fechaEntrega', 'formato':'texto'},
                    {'name': 'Región', 'selector':'regionNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Zona', 'selector':'zonaNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Tienda', 'selector':'tiendaNombre', 'formato':'texto', 'ancho': '360px'},
                    {'name': 'Delivering', 'selector':'Delivering', 'formato':'entero'},
                    {'name': 'Pick Pack', 'selector':'PickPack', 'formato':'entero', 'ancho': '110px'},
                    {'name': 'Ready', 'selector':'Ready', 'formato':'entero'},
                    {'name': 'Ready for Pick Up', 'selector':'ReadyForPickUp', 'formato':'entero'}
                ]
        if self.titulo == 'Pedidos No Entregados o No Cancelados Tienda $tienda':
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
            collection = conexion_mongo('report').report_pedidoPendientes48horas
            pipeline = [{'$unwind': '$sucursal'}]
            if self.filtro_lugar:
                pipeline.append(
                    {'$match': {f'sucursal.{nivel}': self.lugar}}
                )
            if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
            pipeline.extend([{'$project': {
                'fechaOrdenar': '$fechaEntrega',
                'fechaEntrega': {'$dateToString': {'format': '%d/%m/%Y', 'date': '$fechaEntrega'}},
                'regionNombre': '$sucursal.regionNombre',
                'zonaNombre': '$sucursal.zonaNombre',
                'tiendaNombre': '$sucursal.tiendaNombre',
                'estatus': '$estatus',
                'pedido': '$pedido',
                'consigna': '$consigna',
                'metodoEntrega': '$metodoEntrega',
                'timeslot_from': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_from'}},
                'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_to'}},
                }},
                {'$sort': {'fechaOrdenar': 1, 'regionNombre': 1, 'zonaNombre': 1, 'tiendaNombre': 1}}
            ])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
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
                        'estatus': dato['estatus'],
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
                    {'name': 'Estatus', 'selector':'estatus', 'formato':'texto', 'ancho': '200px'},
                    {'name': 'Timeslot From', 'selector':'timeslot_from', 'formato':'texto'},
                    {'name': 'Timeslot To', 'selector':'timeslot_to', 'formato':'texto'},
                    {'name': 'consigna', 'selector':'consigna', 'formato':'texto'},
                    {'name': 'Método Entrega', 'selector':'metodoEntrega', 'formato':'texto'},
                ]
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
        anioElegido = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year
        mesElegido = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month
        diaElegido = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day
        fechaElegida = self.filtros.fechas['fecha_fin'][:10]

        hoy = datetime.now()

        if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
            query_filtro_depto = f" and cd.idDepto = {self.filtros.depto} "
            campo_depto = 'subDeptoDescrip'
            titulo_nivel_producto = 'Sub Departamento'
        else:
            query_filtro_depto = ''
            campo_depto = 'deptoDescrip'
            titulo_nivel_producto = 'Departamento'
        pipeline = f"""select cd.{campo_depto} '{titulo_nivel_producto}',
            sum(case when anio={anioElegido-1} and dt.fecha < convert(date,DATEADD(yy,-1,(GETDATE()))) then ventaSinImpuestos else 0 end) AAnterior,
            sum(case when anio={anioElegido} then ventaSinImpuestos else 0 end) AActual,
            sum(case when anio={anioElegido} then objetivo else 0 end) objetivo,
            sum(case when anio=2022 and dt.fecha <= '{fechaElegida}' then objetivo else 0 end) objetivoDia
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

        # print(f'Query desde VentaSinImpuesto en tablas: {pipeline}')
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(pipeline)
        arreglo = crear_diccionario(cursor)

        if len(arreglo) > 0:
            hayResultados = "si"
            for i in range(len(arreglo)):
                if self.filtros.canal == '1':
                    objetivo = arreglo[i]['objetivo']
                    objetivoDia = arreglo[i]['objetivoDia']
                    # print(f'objetivoDia = {str(objetivoDia)}')
                    alcance = (arreglo[i]['AActual']/objetivo) - 1 if objetivo else '--'
                    alcanceDia = (arreglo[i]['AActual']/objetivoDia) - 1 if objetivoDia else '--'
                else:
                    alcance = '--'
                    objetivo = '--'
                    alcanceDia = '--'
                    objetivoDia = '--'
                vsaa = (arreglo[i]['AActual'] / arreglo[i]['AAnterior']) - 1 if arreglo[i]['AAnterior'] != 0 else '--'
                data.append({
                    'depto': arreglo[i][titulo_nivel_producto],
                    'objetivo': objetivo,
                    'venta': arreglo[i]['AActual'],
                    'alcance': alcance,
                    'venta_anterior': arreglo[i]['AAnterior'],
                    'vsaa': vsaa,
                    'objetivoDia': objetivoDia,
                    'alcanceDia': alcanceDia,
                })
            columns = [
                {'name': titulo_nivel_producto, 'selector':'depto', 'formato':'texto', 'ancho': '220px'},
                {'name': 'Objetivo '+mesTexto(mesElegido), 'selector':'objetivo', 'formato':'moneda'},
                {'name': 'Venta '+mesTexto(mesElegido)+' '+str(anioElegido), 'selector':'venta', 'formato':'moneda'},
                {'name': 'Alcance al Objetivo '+mesTexto(mesElegido), 'selector':'alcance', 'formato':'porcentaje'},
                {'name': 'Venta '+str(diaElegido)+' '+mesTexto(mesElegido)+' '+str(anioElegido - 1), 'selector':'venta_anterior', 'formato':'moneda'},
                {'name': 'Vs. '+str(anioElegido-1), 'selector':'vsaa', 'formato':'porcentaje'},
                {'name': 'Objetivo al '+str(diaElegido)+' de '+mesTexto(mesElegido)+' '+str(anioElegido), 'selector':'objetivoDia', 'formato':'moneda'},
                {'name': 'Alcance al Objetivo '+str(diaElegido)+' de '+mesTexto(mesElegido), 'selector':'alcanceDia', 'formato':'porcentaje'},
            ]
        else:
            hayResultados = 'no'
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
        else:
            print("No jaló, porque el agrupador es "+ self.filtros.agrupador)
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
        arreglo_tmp = await cursor.to_list(length=1000)
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
            arreglo_tmp = await cursor.to_list(length=1000)
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
            arreglo_resultados = await cursor.to_list(length=1000)
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
            arreglo_tmp = await cursor.to_list(length=1000)
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
            arreglo_resultados = await cursor.to_list(length=1000)
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

        if self.titulo == 'Justificados por Departamento':
            # Arreglo de departamentos:
            pipeline_departamentos = deepcopy(pipeline)
            pipeline_departamentos.extend([
                {'$group':{'_id': '$DescripDepto'}}
            ])
            cursor = collection.aggregate(pipeline_departamentos)
            arreglo_tmp = await cursor.to_list(length=1000)
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
            arreglo_resultados = await cursor.to_list(length=1000)
            if len(arreglo_resultados) <= 0:
                hayResultados = "no"
            
            else:
                hayResultados = "si"
                # Populamos con ceros el arreglo que tiene dos dimensiones: justificaciones x periodos
                # tabla = [[0]*len(arreglo_periodos)]*len(arreglo_justificaciones) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                tabla = zeros((len(arreglo_departamentos), len(arreglo_periodos) + 1)) # Esto no porque todos los apuntadores de la segunda dimensión apuntan al mismo arreglo
                # Para cada resultado del query principal, ponemos en nuestro arreglo-tabla los valores que sí tengamos:
                # print('len(arreglo_resultados) = '+str(len(arreglo_resultados)))
                for dato in arreglo_resultados:
                    x = arreglo_departamentos.index(dato['_id']['departamento'])
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
            # arreglo = await cursor.to_list(length=1000)
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
        pipeline = []
        data = []
        columns = []
        if self.titulo == '50 Tiendas con % Pedido Perfecto más bajo':
            if self.filtros.periodo != {}:
                collection = conexion_mongo('report').report_pedidoPerfecto
                if self.filtros.region != '' and self.filtros.region != "False":
                    # print('Sí hay región, y es: '+self.filtros.region)
                    filtro_lugar = True
                    if self.filtros.zona != '' and self.filtros.zona != "False":
                        if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
                # print(str(pipeline))
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=50)
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
                        'timeslot_from': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_from'}},
                        'timeslot_to': {'$dateToString': {'format': '%d/%m/%Y %H:%M', 'date': '$timeslot_to'}},
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
                # print(str(pipeline))
                # Ejecutamos el query:
                cursor = collection.aggregate(pipeline)
                arreglo = await cursor.to_list(length=50)
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
                        {'name': 'Evaluación', 'selector':'Evaluacion', 'formato':'texto', 'ancho': '240px'},
                        {'name': 'Cancelados', 'selector':'Cancelados', 'formato':'texto', 'ancho': '150px'},
                        {'name': 'Quejas', 'selector':'Quejas', 'formato':'texto'},
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
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                zona_query = '$zonaNombre'
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    tienda_query = '$tiendaNombre'
                    if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
            arreglo = await cursor.to_list(length=1000)
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
            if self.filtros.region != '' and self.filtros.region != "False":
                self.filtro_lugar = True
                zona_query = '$zonaNombre'
                if self.filtros.zona != '' and self.filtros.zona != "False":
                    tienda_query = '$tiendaNombre'
                    if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
            if self.filtros.tipoEntrega3 != '' and self.filtros.tipoEntrega3 != "False":
                pipeline.append(
                    {'$match': {'metodoEntrega': self.filtros.tipoEntrega3}}
                )
            if self.filtros.estatus != '' and self.filtros.estatus != "False":
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
            arreglo = await cursor.to_list(length=1000)
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
            else:
                hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def NPSDetalle(self):
        pipeline = []
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False":
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
                'FechaEnvio': {
                    '$gte': self.fecha_ini, 
                    '$lt': self.fecha_fin
                }
            }}
        ]
        if self.filtro_lugar:
            pipeline.append(
                {'$match': {'sucursal.'+nivel: self.lugar}}
            )
        # caminos = ['R1', 'R1A', 'R1B', 'R1C', 'R1D', 'R1E', 'R1F', 'R1G', 'R1H', 'R1I', 'R1J', 'R2', 'R2A', 'R2B', 'R2C', 'R2D', 'R2E', 'R2F', 'R2G', 'R2H', 'R2I', 'R3', 'R3A', 'R3B', 'R3C', 'R3D', 'R3E', 'R3F', 'R3G', 'R4', 'R4A', 'R4B', 'R4C', 'R4D', 'R4E', 'R4F', 'R5', 'R5A', 'R5B', 'R5C', 'R5D', 'R5E', 'R5F', 'R5G', 'R5H', 'R6', 'R6A', 'R6B', 'R6C', 'R6D', 'R6E', 'R6F', 'R6G', 'R7', 'R7A', 'R7B', 'R7C', 'R7D', 'R7E', 'R7F', 'R7G', 'R7H', 'R7I', 'R8', 'R8A', 'R8B', 'R8C', 'R8D', 'R8E', 'R8F', 'R8G', 'R8H', 'R8I', 'R9', 'R9A', 'R9B', 'R9C', 'R9D', 'R9E', 'R9F', 'R10']
        caminos = []
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
        for camino in caminos:
            pipeline[-1]['$project'][camino] = '$' + camino
        # print(str(pipeline))
        # Ejecutamos el query:
        collection = conexion_mongo('report').report_pedidoDetalleNPS
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=1000)
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
                {'name': 'Fecha Entrega', 'selector':'FechaEntrega', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Fecha Despacho', 'selector':'FechaDespacho', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Evaluación Entrega', 'selector':'EvaluacionEntrega', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Queja', 'selector':'Queja', 'formato':'texto'},
                {'name': 'Estatus', 'selector':'estatus', 'formato':'texto', 'ancho': '200px'},
                {'name': 'NPS', 'selector':'NPS', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Tipo Pedido', 'selector':'TipoPedido', 'formato':'texto', 'ancho': '200px'},
                {'name': 'No Imputable a Tienda', 'selector':'NoImputableTienda', 'formato':'texto', 'ancho': '200px'}
                # A esto falta agregarle los caminos
            ]
            for camino in caminos:
                columns.append({'name': camino, 'selector':camino, 'formato':'texto'})
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
                    data_i['camino'] = camino_tmp
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
        if self.filtros.region != '' and self.filtros.region != "False":
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
        if self.filtros.formato != '' and self.filtros.formato != "False":
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
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=1000)
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
        if self.filtros.region != '' and self.filtros.region != "False":
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
        filtro_sku = True if self.filtros.sku != '' and self.filtros.sku != "False" else False
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
        arreglo = await cursor.to_list(length=1000)
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
        if self.filtros.region != '' and self.filtros.region != "False":
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
        if self.filtros.depto != '' and self.filtros.depto != "False":
            filtro_producto = True
            if self.filtros.subDepto != '' and self.filtros.subDepto != "False":
                nivel_producto = 'subDepto'
                detalle_producto = int(self.filtros.subDepto)
            else:
                nivel_producto = 'depto'
                detalle_producto = int(self.filtros.depto)
        else:
            filtro_producto = False
        filtro_canal2 = True if self.filtros.canal2 != '' and self.filtros.canal2 != "False" else False
        filtro_e3 = True if self.filtros.e3 != '' and self.filtros.e3 != "False" else False
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
        arreglo = await cursor.to_list(length=1000)
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
        if self.filtros.region != '' and self.filtros.region != "False":
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(str(arreglo))
            if len(arreglo) >0:
                # print('Sí hay resultados: '+str(arreglo))
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
                    data.append({
                        'deptoNombre': deptos[i],
                        'frChedraui': frChedraui[i],
                        'frCornershop': frCornershop[i],
                        'dif': frChedraui[i] - frCornershop[i],
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
        pipeline = []
        data = []
        columns = []
        if self.titulo == 'Evaluación NPS por Día':
            data = []
            # self.fecha_ini = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ')
            # fecha_fin = datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ')
            self.fecha_ini = self.filtros.fechas['fecha_ini'][0:10]
            fecha_fin = self.filtros.fechas['fecha_fin'][0:10]
            if self.filtros.agrupador == 'dia':
                rango = "nmp.fecha"
            elif self.filtros.agrupador == "semana":
                rango = "n_sem_D_S"
            elif self.filtros.agrupador == "mes":
                rango = "abrev_mes"
            else:
                rango = "anio"
            pipeline = f"""SELECT COUNT(1) as cantidad, nd.calificacion, {rango} as rango
            from DWH.limesurvey.nps_mail_pedido nmp
            left join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nmp.nEncuesta=nd.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda"""
            if self.filtros.agrupador != "dia":
                pipeline += " left join DWH.dbo.dim_tiempo dt on nmp.fecha = dt.fecha "
            pipeline += f""" where nmp.fecha BETWEEN '{self.fecha_ini}' AND '{self.fecha_fin}' """
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                pipeline += f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                pipeline += f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                pipeline += f" and ct.region ='{self.filtros.region}' "
            pipeline += f" group by nd.calificacion, {rango} order by {rango}"

            # print("query desde tabla nps: "+pipeline)
            cnxn = conexion_sql('DWH')
            # print('Evaluación NPS por Día desde Tabla: '+str(pipeline))
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                # Crear nuevo arreglo de fechas y cambiar formato de fechas
                rangos = []
                for fila in arreglo:
                    if self.filtros.agrupador == "dia":
                        fila['rango'] = fila['rango'].strftime('%d/%m/%Y')
                    if fila['rango'] not in rangos:
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
            where ncp.tipo_respuesta = 'R2' and {agrupador_where} {lugar_where}
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
            left join DWH.dbo.dim_tiempo dt on npr.fecha=dt.fecha
            where ncp.tipo_respuesta = 'R2' and {agrupador_where} {lugar_where}
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

        if self.titulo == 'Las 30 Tiendas con NPS Más Bajo':
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

            pipeline = f"""select top 30 CONCAT(nmp.idtienda,' - ',nmp.descrip_tienda) tienda,nmp.region,nmp.zona,
            sum(case when nd.calificacion in (9,10) then 1 else 0 end) promotores,
            sum(case when nd.calificacion<=6 then 1 else 0 end) detractores,
            sum(case when nd.calificacion in (7,8) then 1 else 0 end) pasivos,
            case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end nps
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            left join DWH.dbo.dim_tiempo dt on nmp.fecha=dt.fecha
            where {agrupador_where} {lugar_where}
            group by CONCAT(nmp.idtienda,' - ',nmp.descrip_tienda),nmp.region,nmp.zona
            order by case when (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))=0 then 0 else
            (sum(case when nd.calificacion in (9,10) then 1 else 0 end)-sum(case when nd.calificacion<=6 then 1 else 0 end))*100/cast(count(1) as float) end"""

            # print("query desde tablas NPS: "+pipeline)
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

        if self.titulo == 'Comentarios y Calificación Encuesta NPS':
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
            b.timeslot_from,timeslot_to,MetodoEntrega,EstatusPedido, b.FechaEntrega,
            b.FechaDespacho,nmp.evaluacion as EvaluacionEntrega,b.Queja,nmp.estatus,
            b.NPS,b.Tipo,b.NoImputableTienda, nd.comentario,nmp.fecha as FechaEnvio,nd.fecha_encuesta as FechaEncuesta
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
            left join DWH.dbo.dim_tiempo dt on nmp.fecha=dt.fecha
            where nd.comentario is not null
            and {agrupador_where} {lugar_where}
            order by fecha_encuesta desc,calificacion"""

            # print("query desde tablas NPS: "+pipeline)
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
                    {'name': 'Fecha Encuesta', 'selector':'FechaEncuesta', 'formato':'texto', 'ancho': '200px'}
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
                        'FechaEnvio': row['FechaEnvio'],
                        'FechaEncuesta': row['FechaEncuesta'],
                    })
            else:
                hayResultados = 'no'
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

    async def ComparativoVentaXCanal(self):
        data = []
        columns = []
        if self.filtros.region != '' and self.filtros.region != "False":
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False":
                if self.filtros.tienda != '' and self.filtros.tienda != "False":
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
        arreglo_labels = await cursor.to_list(length=5)
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
        arreglo = await cursor.to_list(length=1000)
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
            arreglo = await cursor.to_list(length=1000)
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
        pipeline = f"""SELECT us.usuario, us.nombre, r.rol, us.estatus, ct.tiendasNombre
        from DJANGO.php.usuarios us
        left join DWH.artus.catTienda ct on us.idTienda = ct.tienda
        left join DJANGO.php.rol r on r.id = us.id_rol 
        where us.estatus is not null and us.estatus not in ('activo')"""
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
                data.append({
                    'Email': row['usuario'],
                    'Nombre': row['nombre'],
                    'Rol': row['rol'],
                    'Tienda': row['tiendasNombre'],
                    'Estatus': row['estatus'],
                    'Editar': 0
                })
            columns = [
                {'name': 'Email', 'selector':'Email', 'formato':'texto'},
                {'name': 'Nombre', 'selector':'Nombre', 'formato':'texto'},
                {'name': 'Rol', 'selector':'Rol', 'formato':'texto'},
                # {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho':'240px'},
                {'name': 'Estatus', 'selector':'Estatus', 'formato':'texto'},
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
            print(f"query desde tablas->Faltantes->PedidosPicker: {str(pipeline)}")
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
            print(f"query desde tablas->Faltantes->PedidosPicker: {str(pipeline)}")
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

        hayCanal = False if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == '' else True

        nMes = datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ').month
        nMes = '0'+ str(nMes) if nMes < 10 else f'{nMes}'

        if self.titulo == 'Detalle Departamentos':
            pipeline = f"""select DEPTO, DEPTO_NOMBRE,
                sum(DiaActual_AnioActual) DiaActual_AnioActual, sum(DiaActual_AnioAnterior) DiaActual_AnioAnterior, sum(DiaComparable_AnioAnterior) DiaComparable_AnioAnterior,(sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF)) porc_part_dia_actual, (sum(DiaComparable_AnioAnterior)/max(DiaComparable_AnioAnteriorTF)) DiaComparable_AnioAnteriorTF,
                (sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF))-(sum(DiaActual_AnioAnterior)/max(DiaActual_AnioAnteriorTF)) porcParDiff,
                avg(co.objetivo) objetivo,
                sum(DiaVencido_AnioActual) DiaVencidoAnioActual, sum(DiaVencido_AnioAnterior) DiaVencidoAnioAnterior,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF)) porc_part_dia_vencido,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF))-(sum(DiaVencido_AnioAnterior)/max(DiaVencido_AnioAnteriorTF)) porcParDiffVencido,
                max(hora) hora
                from DWH.artus.ventaHotSale vhs
                left join (select DISTINCT tipo,esOmnicanal
                from DWH.artus.catCanal ) cc on vhs.idTipo =cc.tipo
                left join DWH.artus.catObjetivo co{" on cc.esOmnicanal =co.idTipo and co.nMes=format(GETDATE(),'yyyyMM')" if not hayCanal else ' on vhs.idTipo =co.idTipo where vhs.idTipo = '+self.filtros.canal}
                and co.nMes = 2022{nMes}
                group by DEPTO, DEPTO_NOMBRE"""
            # print(f"query desde tablas->Temporada->Detalle Deptos: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                maxHora = 0
                totales = {'DiaActual_AnioActual': 0, 'DiaActual_AnioAnterior': 0, 'DiaComparable_AnioAnterior': 0, 'porc_part_dia_actual': 0, 'DiaComparable_AnioAnteriorTF': 0, 'porcParDiff': 0, 'DiaVencidoAnioActual': 0, 'DiaVencidoAnioAnterior': 0, 'porc_part_dia_vencido': 0, 'porcParDiffVencido': 0}
                for row in arreglo:
                    data.append({
                        'detalleDepto': '',
                        'IdDepto': row['DEPTO'],
                        'DeptoNombre': row['DEPTO_NOMBRE'],
                        'VentaHoy': row['DiaActual_AnioActual'],
                        'VentaHoyAA': row['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': row['DiaComparable_AnioAnterior'],
                        'PorcPartHoy': row['porc_part_dia_actual'],
                        'DiaComparable_AnioAnteriorTF': row['DiaComparable_AnioAnteriorTF'],
                        'PorcPartHoyVsAA': row['porcParDiff'],
                        'VentaAyer': row['DiaVencidoAnioActual'],
                        'VentaAyerAA': row['DiaVencidoAnioAnterior'],
                        'PorcPartAyer': row['porc_part_dia_vencido'],
                        'PorcPartAyerVsAA': row['porcParDiffVencido']
                    })
                    totales['DiaActual_AnioActual'] += float(row['DiaActual_AnioActual'])
                    totales['DiaActual_AnioAnterior'] += float(row['DiaActual_AnioAnterior'])
                    totales['DiaComparable_AnioAnterior'] += float(row['DiaComparable_AnioAnterior'])
                    totales['porc_part_dia_actual'] += float(row['porc_part_dia_actual'])
                    totales['DiaComparable_AnioAnteriorTF'] += float(row['DiaComparable_AnioAnteriorTF'])
                    totales['porcParDiff'] += float(row['porcParDiff'])
                    totales['DiaVencidoAnioActual'] += float(row['DiaVencidoAnioActual'])
                    totales['DiaVencidoAnioAnterior'] += float(row['DiaVencidoAnioAnterior'])
                    totales['porc_part_dia_vencido'] += float(row['porc_part_dia_vencido'])
                    totales['porcParDiffVencido'] += float(row['porcParDiffVencido'])
                    maxHora = int(row['hora']) if row['hora'] is not None and maxHora < int(row['hora']) else maxHora
                data.append({
                    'detalleDepto': '',
                    'IdDepto': '--',
                    'DeptoNombre': 'Total:',
                    'VentaHoy': totales['DiaActual_AnioActual'],
                    'VentaHoyAA': totales['DiaActual_AnioAnterior'],
                    'DiaComparable_AnioAnterior': totales['DiaComparable_AnioAnterior'],
                    'PorcPartHoy': totales['porc_part_dia_actual'],
                    'DiaComparable_AnioAnteriorTF': totales['DiaComparable_AnioAnteriorTF'],
                    'PorcPartHoyVsAA': totales['porcParDiff'],
                    'VentaAyer': totales['DiaVencidoAnioActual'],
                    'VentaAyerAA': totales['DiaVencidoAnioAnterior'],
                    'PorcPartAyer': totales['porc_part_dia_vencido'],
                    'PorcPartAyerVsAA': totales['porcParDiffVencido'],

                })
                columns = [
                    {'name': 'Ver Detalle', 'selector':'detalleDepto', 'formato':'detalleDepto'},
                    {'name': 'ID Depto', 'selector':'IdDepto', 'formato':'entero'},
                    {'name': 'Nombre Depto', 'selector':'DeptoNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Venta Hoy ('+str(maxHora)+':00)', 'selector':'VentaHoy', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Hoy AA', 'selector':'VentaHoyAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Día Comparable', 'selector':'DiaComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Hoy', 'selector':'PorcPartHoy', 'formato':'porcentaje'},
                    {'name': '% Part Comparable', 'selector':'DiaComparable_AnioAnteriorTF', 'formato':'porcentaje'},
                    {'name': '% Part Hoy Vs. AA', 'selector':'PorcPartHoyVsAA', 'formato':'porcentaje'},
                    {'name': 'Venta Ayer', 'selector':'VentaAyer', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer AA', 'selector':'VentaAyerAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Ayer', 'selector':'PorcPartAyer', 'formato':'porcentaje'},
                    {'name': '% Part Ayer Vs. AA', 'selector':'PorcPartAyerVsAA', 'formato':'porcentaje'}
                ]
            else:
                hayResultados = 'no'
                
        if self.titulo == 'Detalle Sub-Departamentos para Depto $depto':
            pipeline = f"""select SUBDEPTO, SUBDEPTO_NOMBRE,
                sum(DiaActual_AnioActual) DiaActual_AnioActual, sum(DiaActual_AnioAnterior) DiaActual_AnioAnterior, sum(DiaComparable_AnioAnterior) DiaComparable_AnioAnterior,(sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF)) porc_part_dia_actual, (sum(DiaComparable_AnioAnterior)/max(DiaComparable_AnioAnteriorTF)) DiaComparable_AnioAnteriorTF,
                (sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF))-(sum(DiaActual_AnioAnterior)/max(DiaActual_AnioAnteriorTF)) porcParDiff,
                avg(co.objetivo) objetivo,
                sum(DiaVencido_AnioActual) DiaVencidoAnioActual, sum(DiaVencido_AnioAnterior) DiaVencidoAnioAnterior,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF)) porc_part_dia_vencido,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF))-(sum(DiaVencido_AnioAnterior)/max(DiaVencido_AnioAnteriorTF)) porcParDiffVencido,
                max(hora) hora
                from DWH.artus.ventaHotSale vhs
                left join (select DISTINCT tipo,esOmnicanal
                from DWH.artus.catCanal ) cc on vhs.idTipo =cc.tipo
                left join DWH.artus.catObjetivo co{" on cc.esOmnicanal =co.idTipo and co.nMes=format(GETDATE(),'yyyyMM')" if not hayCanal else ' on vhs.idTipo =co.idTipo'}
                where DEPTO = {self.filtros.fromSibling}
                {'and vhs.idTipo = '+self.filtros.canal if hayCanal else ''}
                and co.nMes = 2022{nMes}
                group by SUBDEPTO, SUBDEPTO_NOMBRE"""

            # print(f"query desde tablas->Temporada->Detalle subDeptos: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                maxHora = 0
                for row in arreglo:
                    data.append({
                        'detalleSubDepto': '',
                        'IdSubDepto': row['SUBDEPTO'],
                        'SubDeptoNombre': row['SUBDEPTO_NOMBRE'],
                        'VentaHoy': row['DiaActual_AnioActual'],
                        'VentaHoyAA': row['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': row['DiaComparable_AnioAnterior'],
                        'PorcPartHoy': row['porc_part_dia_actual'],
                        'DiaComparable_AnioAnteriorTF': row['DiaComparable_AnioAnteriorTF'],
                        'PorcPartHoyVsAA': row['porcParDiff'],
                        'VentaAyer': row['DiaVencidoAnioActual'],
                        'VentaAyerAA': row['DiaVencidoAnioAnterior'],
                        'PorcPartAyer': row['porc_part_dia_vencido'],
                        'PorcPartAyerVsAA': row['porcParDiffVencido']
                    })
                    maxHora = int(row['hora']) if row['hora'] is not None and maxHora < int(row['hora']) else maxHora
                columns = [
                    {'name': 'Ver Detalle', 'selector':'detalleSubDepto', 'formato':'detalleSubDepto'},
                    {'name': 'ID SubDepto', 'selector':'IdSubDepto', 'formato':'entero'},
                    {'name': 'Nombre SubDepto', 'selector':'SubDeptoNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Venta Hoy ('+str(maxHora)+':00)', 'selector':'VentaHoy', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Hoy AA', 'selector':'VentaHoyAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Día Comparable', 'selector':'DiaComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Hoy', 'selector':'PorcPartHoy', 'formato':'porcentaje'},
                    {'name': '% Part Comparable', 'selector':'DiaComparable_AnioAnteriorTF', 'formato':'porcentaje'},
                    {'name': '% Part Hoy Vs. AA', 'selector':'PorcPartHoyVsAA', 'formato':'porcentaje'},
                    {'name': 'Venta Ayer', 'selector':'VentaAyer', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer AA', 'selector':'VentaAyerAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Ayer', 'selector':'PorcPartAyer', 'formato':'porcentaje'},
                    {'name': '% Part Ayer Vs. AA', 'selector':'PorcPartAyerVsAA', 'formato':'porcentaje'}
                ]
            else:
                hayResultados = 'no'
                
        if self.titulo == 'Detalle Clases para SubDepto $subDepto':
            pipeline = f"""select CLASE, CLASE_NOMBRE,
                sum(DiaActual_AnioActual) DiaActual_AnioActual, sum(DiaActual_AnioAnterior) DiaActual_AnioAnterior, sum(DiaComparable_AnioAnterior) DiaComparable_AnioAnterior,(sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF)) porc_part_dia_actual, (sum(DiaComparable_AnioAnterior)/max(DiaComparable_AnioAnteriorTF)) DiaComparable_AnioAnteriorTF,
                (sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF))-(sum(DiaActual_AnioAnterior)/max(DiaActual_AnioAnteriorTF)) porcParDiff,
                avg(co.objetivo) objetivo,
                sum(DiaVencido_AnioActual) DiaVencidoAnioActual, sum(DiaVencido_AnioAnterior) DiaVencidoAnioAnterior,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF)) porc_part_dia_vencido,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF))-(sum(DiaVencido_AnioAnterior)/max(DiaVencido_AnioAnteriorTF)) porcParDiffVencido,
                max(hora) hora
                from DWH.artus.ventaHotSale vhs
                left join (select DISTINCT tipo,esOmnicanal
                from DWH.artus.catCanal ) cc on vhs.idTipo =cc.tipo
                left join DWH.artus.catObjetivo co{" on cc.esOmnicanal =co.idTipo and co.nMes=format(GETDATE(),'yyyyMM')" if not hayCanal else ' on vhs.idTipo =co.idTipo'}
                where SUBDEPTO = {self.filtros.fromSibling}
                {'and vhs.idTipo = '+self.filtros.canal if hayCanal else ''}
                and co.nMes = 2022{nMes}
                group by CLASE, CLASE_NOMBRE"""

            # print(f"query desde tablas->Temporada->Detalle clases: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                maxHora = 0
                for row in arreglo:
                    data.append({
                        'detalleClase': '',
                        'IdClase': row['CLASE'],
                        'ClaseNombre': row['CLASE_NOMBRE'],
                        'VentaHoy': row['DiaActual_AnioActual'],
                        'VentaHoyAA': row['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': row['DiaComparable_AnioAnterior'],
                        'PorcPartHoy': row['porc_part_dia_actual'],
                        'DiaComparable_AnioAnteriorTF': row['DiaComparable_AnioAnteriorTF'],
                        'PorcPartHoyVsAA': row['porcParDiff'],
                        'VentaAyer': row['DiaVencidoAnioActual'],
                        'VentaAyerAA': row['DiaVencidoAnioAnterior'],
                        'PorcPartAyer': row['porc_part_dia_vencido'],
                        'PorcPartAyerVsAA': row['porcParDiffVencido']
                    })
                    maxHora = int(row['hora']) if row['hora'] is not None and maxHora < int(row['hora']) else maxHora
                columns = [
                    {'name': 'Ver Detalle', 'selector':'detalleClase', 'formato':'detalleClase'},
                    {'name': 'ID Clase', 'selector':'IdClase', 'formato':'entero'},
                    {'name': 'Nombre Clase', 'selector':'ClaseNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Venta Hoy ('+str(maxHora)+':00)', 'selector':'VentaHoy', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Hoy AA', 'selector':'VentaHoyAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Día Comparable', 'selector':'DiaComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Hoy', 'selector':'PorcPartHoy', 'formato':'porcentaje'},
                    {'name': '% Part Comparable', 'selector':'DiaComparable_AnioAnteriorTF', 'formato':'porcentaje'},
                    {'name': '% Part Hoy Vs. AA', 'selector':'PorcPartHoyVsAA', 'formato':'porcentaje'},
                    {'name': 'Venta Ayer', 'selector':'VentaAyer', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer AA', 'selector':'VentaAyerAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Ayer', 'selector':'PorcPartAyer', 'formato':'porcentaje'},
                    {'name': '% Part Ayer Vs. AA', 'selector':'PorcPartAyerVsAA', 'formato':'porcentaje'}
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Detalle Sub-Clases para Clase $clase':
            pipeline = f"""select SUBCLASE, SUBCLASE_NOMBRE,
                sum(DiaActual_AnioActual) DiaActual_AnioActual, sum(DiaActual_AnioAnterior) DiaActual_AnioAnterior, sum(DiaComparable_AnioAnterior) DiaComparable_AnioAnterior,(sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF)) porc_part_dia_actual, (sum(DiaComparable_AnioAnterior)/max(DiaComparable_AnioAnteriorTF)) DiaComparable_AnioAnteriorTF,
                (sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF))-(sum(DiaActual_AnioAnterior)/max(DiaActual_AnioAnteriorTF)) porcParDiff,
                avg(co.objetivo) objetivo,
                sum(DiaVencido_AnioActual) DiaVencidoAnioActual, sum(DiaVencido_AnioAnterior) DiaVencidoAnioAnterior,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF)) porc_part_dia_vencido,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF))-(sum(DiaVencido_AnioAnterior)/max(DiaVencido_AnioAnteriorTF)) porcParDiffVencido,
                max(hora) hora
                from DWH.artus.ventaHotSale vhs
                left join (select DISTINCT tipo,esOmnicanal
                from DWH.artus.catCanal ) cc on vhs.idTipo =cc.tipo
                left join DWH.artus.catObjetivo co{" on cc.esOmnicanal =co.idTipo and co.nMes=format(GETDATE(),'yyyyMM')" if not hayCanal else ' on vhs.idTipo =co.idTipo'}
                where CLASE = {self.filtros.fromSibling}
                {'and vhs.idTipo = '+self.filtros.canal if hayCanal else ''}
                and co.nMes = 2022{nMes}
                group by SUBCLASE, SUBCLASE_NOMBRE"""

            # print(f"query desde tablas->Temporada->Detalle subclases: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                maxHora = 0
                for row in arreglo:
                    data.append({
                        'detalleSubClase': '',
                        'IdSubClase': row['SUBCLASE'],
                        'SubClaseNombre': row['SUBCLASE_NOMBRE'],
                        'VentaHoy': row['DiaActual_AnioActual'],
                        'VentaHoyAA': row['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': row['DiaComparable_AnioAnterior'],
                        'PorcPartHoy': row['porc_part_dia_actual'],
                        'DiaComparable_AnioAnteriorTF': row['DiaComparable_AnioAnteriorTF'],
                        'PorcPartHoyVsAA': row['porcParDiff'],
                        'VentaAyer': row['DiaVencidoAnioActual'],
                        'VentaAyerAA': row['DiaVencidoAnioAnterior'],
                        'PorcPartAyer': row['porc_part_dia_vencido'],
                        'PorcPartAyerVsAA': row['porcParDiffVencido']
                    })
                    maxHora = int(row['hora']) if row['hora'] is not None and maxHora < int(row['hora']) else maxHora
                columns = [
                    {'name': 'Ver Detalle', 'selector':'detalleSubClase', 'formato':'detalleSubClase'},
                    {'name': 'ID SubClase', 'selector':'IdSubClase', 'formato':'entero'},
                    {'name': 'Nombre SubClase', 'selector':'SubClaseNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Venta Hoy ('+str(maxHora)+':00)', 'selector':'VentaHoy', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Hoy AA', 'selector':'VentaHoyAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Día Comparable', 'selector':'DiaComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Hoy', 'selector':'PorcPartHoy', 'formato':'porcentaje'},
                    {'name': '% Part Comparable', 'selector':'DiaComparable_AnioAnteriorTF', 'formato':'porcentaje'},
                    {'name': '% Part Hoy Vs. AA', 'selector':'PorcPartHoyVsAA', 'formato':'porcentaje'},
                    {'name': 'Venta Ayer', 'selector':'VentaAyer', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer AA', 'selector':'VentaAyerAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Ayer', 'selector':'PorcPartAyer', 'formato':'porcentaje'},
                    {'name': '% Part Ayer Vs. AA', 'selector':'PorcPartAyerVsAA', 'formato':'porcentaje'}
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Detalle Formatos para SubClase $subClase':
            pipeline = f"""select FORMATO_NOMBRE,
                sum(DiaActual_AnioActual) DiaActual_AnioActual, sum(DiaActual_AnioAnterior) DiaActual_AnioAnterior, sum(DiaComparable_AnioAnterior) DiaComparable_AnioAnterior,(sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF)) porc_part_dia_actual, (sum(DiaComparable_AnioAnterior)/max(DiaComparable_AnioAnteriorTF)) DiaComparable_AnioAnteriorTF,
                (sum(DiaActual_AnioActual)/max(DiaActual_AnioActualTF))-(sum(DiaActual_AnioAnterior)/max(DiaActual_AnioAnteriorTF)) porcParDiff,
                avg(co.objetivo) objetivo,
                sum(DiaVencido_AnioActual) DiaVencidoAnioActual, sum(DiaVencido_AnioAnterior) DiaVencidoAnioAnterior,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF)) porc_part_dia_vencido,
                (sum(DiaVencido_AnioActual)/max(DiaVencido_AnioActualTF))-(sum(DiaVencido_AnioAnterior)/max(DiaVencido_AnioAnteriorTF)) porcParDiffVencido,
                max(hora) hora
                from DWH.artus.ventaHotSale vhs
                left join (select DISTINCT tipo,esOmnicanal
                from DWH.artus.catCanal ) cc on vhs.idTipo =cc.tipo
                left join DWH.artus.catObjetivo co{" on cc.esOmnicanal =co.idTipo and co.nMes=format(GETDATE(),'yyyyMM')" if not hayCanal else ' on vhs.idTipo =co.idTipo'}
                where SUBCLASE = {self.filtros.fromSibling}
                {'and vhs.idTipo = '+self.filtros.canal if hayCanal else ''}
                and co.nMes = 2022{nMes}
                group by FORMATO_NOMBRE"""

            # print(f"query desde tablas->Temporada->Detalle formatos: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                maxHora = 0
                for row in arreglo:
                    data.append({
                        'FormatoNombre': row['FORMATO_NOMBRE'],
                        'VentaHoy': row['DiaActual_AnioActual'],
                        'VentaHoyAA': row['DiaActual_AnioAnterior'],
                        'DiaComparable_AnioAnterior': row['DiaComparable_AnioAnterior'],
                        'PorcPartHoy': row['porc_part_dia_actual'],
                        'DiaComparable_AnioAnteriorTF': row['DiaComparable_AnioAnteriorTF'],
                        'PorcPartHoyVsAA': row['porcParDiff'],
                        'VentaAyer': row['DiaVencidoAnioActual'],
                        'VentaAyerAA': row['DiaVencidoAnioAnterior'],
                        'PorcPartAyer': row['porc_part_dia_vencido'],
                        'PorcPartAyerVsAA': row['porcParDiffVencido']
                    })
                    maxHora = int(row['hora']) if row['hora'] is not None and maxHora < int(row['hora']) else maxHora
                columns = [
                    {'name': 'Formato', 'selector':'FormatoNombre', 'formato':'texto', 'ancho': '240px'},
                    {'name': 'Venta Hoy ('+str(maxHora)+':00)', 'selector':'VentaHoy', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Hoy AA', 'selector':'VentaHoyAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Día Comparable', 'selector':'DiaComparable_AnioAnterior', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Hoy', 'selector':'PorcPartHoy', 'formato':'porcentaje'},
                    {'name': '% Part Comparable', 'selector':'DiaComparable_AnioAnteriorTF', 'formato':'porcentaje'},
                    {'name': '% Part Hoy Vs. AA', 'selector':'PorcPartHoyVsAA', 'formato':'porcentaje'},
                    {'name': 'Venta Ayer', 'selector':'VentaAyer', 'formato':'moneda', 'ancho': '150px'},
                    {'name': 'Venta Ayer AA', 'selector':'VentaAyerAA', 'formato':'moneda', 'ancho': '150px'},
                    {'name': '% Part Ayer', 'selector':'PorcPartAyer', 'formato':'porcentaje'},
                    {'name': '% Part Ayer Vs. AA', 'selector':'PorcPartAyerVsAA', 'formato':'porcentaje'}
                ]
            else:
                hayResultados = 'no'
                
        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}
        # Return para debugging:
        # return {'hayResultados':'no', 'pipeline': [], 'columns':[], 'data':[]}

@router.post("/{seccion}")
async def tablas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = Tablas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso"}

