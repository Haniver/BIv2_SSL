from asyncio.windows_events import NULL
from fastapi import APIRouter, Depends, HTTPException, Request

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
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack
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
            pipeline = f"""select *, ct.tienda as NumSucursal from dwh.report.consolidadoFinanzas cf 
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
            totRH = totEnvio = totCombustible = totPPickedUp = totPEnviados = totPZubale = totConsumosInternos = totGND = totMattoTransp = totTotalGasto = totPedidos = totCostoEnvioRH = totCostoRHPorPedido = totReclutamiento = totPagoPorDistancia = totReclutamientoPorApoyo = totpZub45 = totpTotal = totCtoXpZubale = totDifCtoReclut = totTelefonia = totServImpresión = totEmpaqEnvolturas = totEquipoMenor = totEtiquetas = totPapArtEscritorio = totUniformes = totGtosUSOTDA = totGNDSinRequisitos = totGNDMultas = totGNDViaticos = totTotalGtosXPedido = totTotalGtosXPedido = 0
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
                    'Anio': row['Anio'] if row['Anio'] is not None else '--',
                    'Mes': row['descrip_mes'] if row['descrip_mes'] is not None else '--',
                    'MetodoEnvio': metodoEnvio,
                    'FechaInicioProyecto': row['FechaIniProye'] if row['FechaIniProye'] is not None else '--',
                    'Region': row['regionNombre'] if row['regionNombre'] is not None else '--',
                    'Zona': row['zonaNombre'] if row['zonaNombre'] is not None else '--',
                    'Tienda': row['tiendaNombre'] if row['tiendaNombre'] is not None else '--',
                    'NumSucursal': row['NumSucursal'] if row['NumSucursal'] is not None else '--',
                    'RH': row['RH'] if row['RH'] is not None else '--',
                    'Envio': row['Envio'] if row['Envio'] is not None else '--',
                    'Combustible': row['Combustible'] if row['Combustible'] is not None else '--',
                    'Pedidos': row['pRH'] if row['pRH'] is not None else '--',
                    'pPickedUp': row['pPickedUp'] if row['pPickedUp'] is not None else '--',
                    'pEnviados': row['pEnviados'] if row['pEnviados'] is not None else '--',
                    'CostoEnvioRH': row['CtoEnvioRH'] if row['CtoEnvioRH'] is not None else '--',
                    'CostoRHPorPedido': row['CtoRHXPedido'] if row['CtoRHXPedido'] is not None else '--',
                    'Reclutamiento': row['Reclutamiento'] if row['Reclutamiento'] is not None else '--',
                    'PagoPorDistancia': row['PagoXDistancia'] if row['PagoXDistancia'] is not None else '--',
                    'ReclutamientoPorApoyo': row['ReclutaXApoyo'] if row['ReclutaXApoyo'] is not None else '--',
                    'PedidosZubale': row['pZubale'] if row['pZubale'] is not None else '--',
                    'PedidosZubale45': row['pZub45'] if row['pZub45'] is not None else '--',
                    'PedidosTotales': row['pTotal'] if row['pTotal'] is not None else '--',
                    'CostoPorPedidoZubale': row['CtoXpZubale'] if row['CtoXpZubale'] is not None else '--',
                    'DiferenciaCostoReclutamiento': row['DifCtoReclut'] if row['DifCtoReclut'] is not None else '--',
                    'Telefonía': row['Telefonia'] if row['Telefonia'] is not None else '--',
                    'ServiciosDeImpresion': row['ServImpresión'] if row['ServImpresión'] is not None else '--',
                    'EmpaquesDeEnvolturas': row['EmpaqEnvolturas'] if row['EmpaqEnvolturas'] is not None else '--',
                    'EquipoMenor': row['EquipoMenor'] if row['EquipoMenor'] is not None else '--',
                    'Etiquetas': row['Etiquetas'] if row['Etiquetas'] is not None else '--',
                    'PapeleriaYArticulosDeEscritorio': row['PapArtEscritorio'] if row['PapArtEscritorio'] is not None else '--',
                    'Uniformes': row['Uniformes'] if row['Uniformes'] is not None else '--',
                    'GastosUSOTDA': row['GtosUSOTDA'] if row['GtosUSOTDA'] is not None else '--',
                    'ConsumosInternos': row['ConsumosInternos'] if row['ConsumosInternos'] is not None else '--',
                    'GNDSinRequisitos': row['GNDSinRequisitos'] if row['GNDSinRequisitos'] is not None else '--',
                    'GNDMultas': row['GNDMultas'] if row['GNDMultas'] is not None else '--',
                    'GNDViaticos': row['GNDViaticos'] if row['GNDViaticos'] is not None else '--',
                    'GND': row['GND'] if row['GND'] is not None else '--',
                    'MattoTransp': row['MattoTransp'] if row['MattoTransp'] is not None else '--',
                    'TotalGasto': row['TotalGasto'] if row['TotalGasto'] is not None else '--',
                    'TotalGtosXPedido': row['TotalGtosXPedido'] if row['TotalGtosXPedido'] is not None else '--',
                    'subTabla': json.dumps({'columns': columnsSub, 'data': dataSub})
                }
                # print(f"datum: {str(datum)}")
                data.append(datum)
                totRH += float(row['RH']) if row['RH'] is not None else 0
                totEnvio += float(row['Envio']) if row['Envio'] is not None else 0
                totCombustible += float(row['Combustible']) if row['Combustible'] is not None else 0
                totPedidos += float(row['pRH']) if row['pRH'] is not None else 0
                totPPickedUp += float(row['pPickedUp']) if row['pPickedUp'] is not None else 0
                totPEnviados += float(row['pEnviados']) if row['pEnviados'] is not None else 0
                totPZubale += float(row['pZubale']) if row['pZubale'] is not None else 0
                totConsumosInternos += float(row['ConsumosInternos']) if row['ConsumosInternos'] is not None else 0
                totGND += float(row['GND']) if row['GND'] is not None else 0
                totMattoTransp += float(row['MattoTransp']) if row['MattoTransp'] is not None else 0
                totTotalGasto += float(row['TotalGasto']) if row['TotalGasto'] is not None else 0
                totCostoEnvioRH += float(row['CtoEnvioRH']) if row['CtoEnvioRH'] is not None else 0
                totCostoRHPorPedido += float(row['CtoRHXPedido']) if row['CtoRHXPedido'] is not None else 0
                totReclutamiento += float(row['Reclutamiento']) if row['Reclutamiento'] is not None else 0
                totPagoPorDistancia += float(row['PagoXDistancia']) if row['PagoXDistancia'] is not None else 0
                totReclutamientoPorApoyo += float(row['ReclutaXApoyo']) if row['ReclutaXApoyo'] is not None else 0
                totpZub45 = float(row['pZub45']) if row['pZub45'] is not None else 0
                totpTotal = float(row['pTotal']) if row['pTotal'] is not None else 0
                totCtoXpZubale = float(row['CtoXpZubale']) if row['CtoXpZubale'] is not None else 0
                totDifCtoReclut = float(row['DifCtoReclut']) if row['DifCtoReclut'] is not None else 0
                totTelefonia = float(row['Telefonia']) if row['Telefonia'] is not None else 0
                totServImpresión = float(row['ServImpresión']) if row['ServImpresión'] is not None else 0
                totEmpaqEnvolturas = float(row['EmpaqEnvolturas']) if row['EmpaqEnvolturas'] is not None else 0
                totEquipoMenor = float(row['EquipoMenor']) if row['EquipoMenor'] is not None else 0
                totEtiquetas = float(row['Etiquetas']) if row['Etiquetas'] is not None else 0
                totPapArtEscritorio = float(row['PapArtEscritorio']) if row['PapArtEscritorio'] is not None else 0
                totUniformes = float(row['Uniformes']) if row['Uniformes'] is not None else 0
                totGtosUSOTDA = float(row['GtosUSOTDA']) if row['GtosUSOTDA'] is not None else 0
                totGNDSinRequisitos = float(row['GNDSinRequisitos']) if row['GNDSinRequisitos'] is not None else 0
                totGNDMultas = float(row['GNDMultas']) if row['GNDMultas'] is not None else 0
                totGNDViaticos = float(row['GNDViaticos']) if row['GNDViaticos'] is not None else 0
                totTotalGtosXPedido = float(row['TotalGtosXPedido']) if row['TotalGtosXPedido'] is not None else 0
            data[0] = {
                'Anio': '',
                'Mes': '',
                'MetodoEnvio': '',
                'FechaInicioProyecto': '',
                'Region': '',
                'Zona': '',
                'Tienda': '',
                'NumSucursal': '--',
                'RH': totRH,
                'Envio': totEnvio,
                'Combustible': totCombustible,
                'Pedidos': totPedidos,
                'pPickedUp': totPPickedUp,
                'pEnviados': totPEnviados,
                'CostoEnvioRH': totCostoEnvioRH,
                'CostoRHPorPedido': totCostoRHPorPedido,
                'Reclutamiento': totReclutamiento,
                'PagoPorDistancia': totPagoPorDistancia,
                'ReclutamientoPorApoyo': totReclutamientoPorApoyo,
                'pZubale': totPZubale,
                'PedidosZubale45': totpZub45,
                'PedidosTotales': totpTotal,
                'CostoPorPedidoZubale': totCtoXpZubale,
                'DiferenciaCostoReclutamiento': totDifCtoReclut,
                'Telefonía': totTelefonia,
                'ServiciosDeImpresion': totServImpresión,
                'EmpaquesDeEnvolturas': totEmpaqEnvolturas,
                'EquipoMenor': totEquipoMenor,
                'Etiquetas': totEtiquetas,
                'PapeleriaYArticulosDeEscritorio': totPapArtEscritorio,
                'Uniformes': totUniformes,
                'GastosUSOTDA': totGtosUSOTDA,
                'ConsumosInternos': totConsumosInternos,
                'GNDSinRequisitos': totGNDSinRequisitos,
                'GNDMultas': totGNDMultas,
                'GNDViaticos': totGNDViaticos,
                'GND': totGND,
                'MattoTransp': totMattoTransp,
                'TotalGasto': totTotalGasto,
                'TotalGtosXPedido': totTotalGtosXPedido,
                'esTotal': True
            }
            columns = [
                {'name': 'Año', 'selector':'Anio', 'formato':'texto'},
                {'name': 'Mes', 'selector':'Mes', 'formato':'texto'},
                {'name': 'Método de Envío', 'selector':'MetodoEnvio', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Región', 'selector':'Region', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Zona', 'selector':'Zona', 'formato':'texto', 'ancho': '200px'},
                {'name': 'Tienda', 'selector':'Tienda', 'formato':'texto', 'ancho': '400px'},
                {'name': 'Sucursal', 'selector':'NumSucursal', 'formato':'entero', 'ancho': '400px'},
                {'name': 'Cto Recursos Humanos', 'selector':'RH', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Cto Envío', 'selector':'Envio', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'Combustible', 'selector':'Combustible', 'formato':'moneda'},
                {'name': 'Pedidos', 'selector':'Pedidos', 'formato':'entero'},
                {'name': 'Pedidos Recogidos en Tienda', 'selector':'pPickedUp', 'formato':'entero', 'ancho': '220px'},
                {'name': 'Pedidos Enviados', 'selector':'pEnviados', 'formato':'entero', 'ancho': '220px'},
                {'name': 'Costo de Envío RH', 'selector':'CostoEnvioRH', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Costo RH Por Pedido', 'selector':'CostoRHPorPedido', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Reclutamiento', 'selector':'Reclutamiento', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'Pago Por Distancia', 'selector':'PagoPorDistancia', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Reclutamiento Por Apoyo', 'selector':'ReclutamientoPorApoyo', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Pedidos Zubale', 'selector':'pZubale', 'formato':'moneda', 'ancho': '200px'},
                {'name': 'PedidosZubale45', 'selector':'PedidosZubale45', 'formato':'moneda', 'ancho': '200px'},
                {'name': 'Pedidos Totales', 'selector':'PedidosTotales', 'formato':'moneda', 'ancho': '200px'},
                {'name': 'Costo Por PedidoZubale', 'selector':'CostoPorPedidoZubale', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Diferencia Costo Reclutamiento', 'selector':'DiferenciaCostoReclutamiento', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Telefonía', 'selector':'Telefonía', 'formato':'moneda'},
                {'name': 'Servicios De Impresion', 'selector':'ServiciosDeImpresion', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Empaques De Envolturas', 'selector':'EmpaquesDeEnvolturas', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Equipo Menor', 'selector':'EquipoMenor', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'Etiquetas', 'selector':'Etiquetas', 'formato':'moneda'},
                {'name': 'Papeleria Y Articulos De Escritorio', 'selector':'PapeleriaYArticulosDeEscritorio', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Uniformes', 'selector':'Uniformes', 'formato':'moneda'},
                {'name': 'Gastos USOTDA', 'selector':'GastosUSOTDA', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'Consumos Internos', 'selector':'ConsumosInternos', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'GND Sin Requisitos', 'selector':'GNDSinRequisitos', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'GND Multas', 'selector':'GNDMultas', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'GND Viáticos', 'selector':'GNDViaticos', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'GND', 'selector':'GND', 'formato':'moneda'},
                {'name': 'Mantenimiento Transporte', 'selector':'MattoTransp', 'formato':'moneda', 'ancho': '220px'},
                {'name': 'Gastos Totales', 'selector':'TotalGasto', 'formato':'moneda', 'ancho': '180px'},
                {'name': 'Gasto Total por Pedido', 'selector':'TotalGtosXPedido', 'formato':'moneda', 'ancho': '200px'}
            ]

        return {'hayResultados':hayResultados, 'pipeline': pipeline, 'columns':columns, 'data':data}

@router.post("/{seccion}")
async def tablas (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = TablasExpandibles(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso"}

