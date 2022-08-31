from asyncio.windows_events import NULL
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
    prefix="/tablasExpandibles",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class TablasExpandibles():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo

        if self.filtros.fechas != None:
            self.fecha_ini = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) - timedelta(seconds=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
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

    async def CostoPorPedido(self):
        anio = self.filtros.anio
        mes = self.filtros.mes
        data = []
        series = []
        hayResultados = 'no'
        queryMetodoEnvio = f"and cf.TiendaEnLinea = '{self.filtros.metodoEnvio}'" if self.filtros.metodoEnvio != '' and self.filtros.metodoEnvio != "False" and self.filtros.metodoEnvio != None else ''
        queryAnio = f"and cf.Anio = {self.filtros.anio}" if self.filtros.anio != 0 and self.filtros.anio != None else ''
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    queryLugar = f""" and ct.tienda = {self.filtros.tienda} """
                else:
                    queryLugar = f""" and ct.zona = {self.filtros.zona} """
            else:
                queryLugar = f""" and ct.region = {self.filtros.region} """
        else:
            queryLugar = ''
        queryMes = f"and cf.Mes = {self.filtros.mes}" if self.filtros.mes != 0 and self.filtros.mes != None else ''
        if self.titulo == 'Tabla General':
            pipeline = f"""select * from dwh.report.consolidadoFinanzas cf 
                left join DWH.artus.catTienda ct on cf.Cebe = ct.tienda 
                left join DWH.dbo.dim_tiempo dt on dt.id_fecha = cf.Anio * 10000 + cf.Mes * 100 + 1
                where Mes <= 12
                {queryMetodoEnvio}
                {queryAnio}
                {queryMes}
                {queryLugar}
                order by cf.Mes, cf.Cebe
                """
        # print(f"query desde tablas->CostoPorPedido->{self.titulo}: {str(pipeline)}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(pipeline)
        arreglo = crear_diccionario(cursor)
        if len(arreglo) > 0:
            hayResultados = "si"
            totRH = totEnvio = totCombustible = totPPickedUp = totPEnviados = totPZubale = totEstimadoZubale  = totConsumosInternos = totGND = totMattoTransp = totTotalGasto = totPedidos = 0
            data = [{}]
            # n=1
            for row in arreglo:
                dataSub = []
                query = f"""select * from DWH.report.consolidadoFinanzasPicker
                where Año={str(int(row['Anio']))} and Mes={str(int(row['Mes']))} and CeBe={row['Cebe']}"""
                cursor = cnxn.cursor().execute(query)
                arregloSub = crear_diccionario(cursor)
                columnsSub = [
                    {'name': 'Puesto', 'selector':'Puesto', 'formato':'texto'},
                    {'name': 'Autorizados', 'selector':'Autorizada', 'formato':'entero'},
                    {'name': 'Ocupados', 'selector':'Ocupada', 'formato':'entero'},
                    {'name': 'Vacantes', 'selector':'Vacante', 'formato':'entero'}
                ]
                for rowSub in arregloSub:
                # Wawa dataSub queda vacío y subTabla no se envía
                    dataSub.append({
                        'Puesto': rowSub['Puesto'],
                        'Autorizada': rowSub['Autorizada'],
                        'Ocupada': rowSub['Ocupada'],
                        'Vacante': rowSub['Vacante']
                    })
                # print(f"DataSub: {str(dataSub)}")
                if row['TiendaEnLinea'] == "No es Zubale":
                    metodoEnvio = 'Recursos Propios'
                elif row['TiendaEnLinea'] == "Logística":
                    metodoEnvio = 'Rec. Propios/Logística'
                else:
                    metodoEnvio = 'Zubale'
                # print(f"subTabla debería ser {json.dumps({'columns': columnsSub, 'data': dataSub})}")
                datum = {
                    'Region': row['regionNombre'],
                    'Zona': row['zonaNombre'],
                    'Tienda': row['tiendaNombre'],
                    'Anio': str(int(row['Anio'])),
                    'Mes': row['descrip_mes'],
                    'MetodoEnvio': metodoEnvio,
                    'RH': row['RH'],
                    'Envio': row['Envio'],
                    'Combustible': row['Combustible'],
                    'Pedidos': row['pRH'],
                    'pPickedUp': row['pPickedUp'],
                    'pEnviados': row['pEnviados'],
                    'pZubale': row['pZubale'],
                    'EstimadoZubale': float(row['pZubale']) * 113.3,
                    'ConsumosInternos': row['ConsumosInternos'],
                    'GND': row['GND'],
                    'MattoTransp': row['MattoTransp'],
                    'TotalGasto': row['TotalGasto'],
                    'TotalGtosXPedido': row['TotalGtosXPedido'],
                    'subTabla': json.dumps({'columns': columnsSub, 'data': dataSub})
                }
                # print(f"datum: {str(datum)}")
                data.append(datum)
                totRH += float(row['RH'])
                totEnvio += float(row['Envio'])
                totCombustible += float(row['Combustible'])
                totPedidos += float(row['pRH'])
                totPPickedUp += float(row['pPickedUp'])
                totPEnviados += float(row['pEnviados'])
                totPZubale += float(row['pZubale'])
                totEstimadoZubale += float(float(row['pZubale']) * 113.3)
                totConsumosInternos += float(row['ConsumosInternos'])
                totGND += float(row['GND'])
                totMattoTransp += float(row['MattoTransp'])
                totTotalGasto += float(row['TotalGasto'])
            data[0] = {
                'Region': '',
                'Zona': '',
                'Tienda': '',
                'Anio': '',
                'Mes': '',
                'MetodoEnvio': 'Total:',
                'RH': totRH,
                'Envio': totEnvio,
                'Combustible': totCombustible,
                'Pedidos': totPedidos,
                'pPickedUp': totPPickedUp,
                'pEnviados': totPEnviados,
                'pZubale': totPZubale,
                'EstimadoZubale': totEstimadoZubale,
                'ConsumosInternos': totConsumosInternos,
                'GND': totGND,
                'MattoTransp': totMattoTransp,
                'TotalGasto': totTotalGasto,
                'esTotal': True
            }
            columns = [
                {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '400px'},
                {'name': 'Año', 'selector':'Anio', 'formato':'texto'},
                {'name': 'Mes', 'selector':'Mes', 'formato':'texto'},
                {'name': 'Método de Envío', 'selector':'MetodoEnvio', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Cto Recursos Humanos', 'selector':'RH', 'formato':'moneda'},
                {'name': 'Cto Envío', 'selector':'Envio', 'formato':'moneda'},
                {'name': 'Combustible', 'selector':'Combustible', 'formato':'moneda'},
                {'name': 'Pedidos', 'selector':'Pedidos', 'formato':'entero'},
                {'name': 'Pedidos Recogidos en Tienda', 'selector':'pPickedUp', 'formato':'entero'},
                {'name': 'Pedidos Enviados', 'selector':'pEnviados', 'formato':'entero'},
                {'name': 'Pedidos Zubale', 'selector':'pZubale', 'formato':'entero'},
                {'name': 'Estimado Zubale', 'selector':'EstimadoZubale', 'formato':'moneda'},
                {'name': 'Consumos Internos', 'selector':'ConsumosInternos', 'formato':'moneda'},
                {'name': 'GND', 'selector':'GND', 'formato':'moneda'},
                {'name': 'Mantenimiento Transporte', 'selector':'MattoTransp', 'formato':'moneda'},
                {'name': 'Gastos Totales', 'selector':'TotalGasto', 'formato':'moneda'},
                {'name': 'Gasto Total por Pedido', 'selector':'TotalGtosXPedido', 'formato':'moneda'}
            ]

        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}

@router.post("/{seccion}")
async def tablas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id, seccion):
        objeto = TablasExpandibles(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso"}

