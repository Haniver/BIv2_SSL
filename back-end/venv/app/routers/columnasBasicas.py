from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta, time
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack
from app.servicios.formatoFechas import mesTexto

router = APIRouter(
    prefix="/columnasBasicas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class ColumnasBasicas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def FoundRate(self):
        categorias = []
        series = []

        if self.titulo == 'Found Rate Vs. Fulfillment Rate':
            serie1 = []
            serie2 = []

            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                filtro_lugar = True
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
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
                    serie1.append(round(row['fulfillment_rate'], 4))
                    serie2.append(round(row['found_rate'], 4))
                series.extend([
                    {'name': 'Fulfillment Rate', 'data':serie1, 'color': 'primary'},                                
                    {'name': 'Found Rate', 'data':serie2, 'color': 'secondary'}
                ])
            else:
                hayResultados = "no"
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'categoria':self.filtros.categoria}
        # Para debugging
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': []}

    async def Nps(self):
        categorias = []
        series = []

        if self.titulo == 'Distribución de clientes por calificación':
            serie1 = []
            serie2 = []

            if self.filtros.agrupador == 'dia':
                agrupador_select = "dt.fecha"
                mes = int(self.filtros.periodo['mes'])
                mes = str(mes) if mes >= 10 else '0'+str(mes)
                dia = int(self.filtros.periodo['dia'])
                dia = str(dia) if dia >= 10 else '0'+str(dia)
                agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
            elif self.filtros.agrupador == "semana":
                agrupador_select = "dt.anio, dt.num_semana"
                semana_completa = str(self.filtros.periodo['semana'])
                num_semana = str(int(semana_completa[4:]))
                anio = semana_completa[0:4]
                agrupador_where = f" dt.anio={anio} and dt.num_semana='W{num_semana}'"
            elif self.filtros.agrupador == "mes":
                agrupador_select = "dt.anio, dt.num_mes"
                agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"

            # Rawa
            # pipeline = f"""select nd.calificacion,count(1) reg, {agrupador_select}
            # from DWH.limesurvey.nps_mail_pedido nmp
            # inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            # left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            # left join DWH.dbo.dim_tiempo dt on nmp.fecha = dt.fecha 
            # where {agrupador_where} """
            pipeline = f"""select nd.calificacion,count(1) reg, {agrupador_select}
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on ho.creation_date = dt.fecha 
            where {agrupador_where} """
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                pipeline += f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                pipeline += f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                pipeline += f" and ct.region ='{self.filtros.region}' "
            pipeline += f" group by nd.calificacion, {agrupador_select} order by calificacion"

            # print("query desde columnas básicas nps ahorita: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                for i in range(len(arreglo)):
                    categorias = []
                    serie1.append(arreglo[i]['reg'])

                series = [
                    {
                        'name': 'Distribución',
                        'data': serie1, 
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color':'primary'
                    }
                ]
            else:
                hayResultados = 'no'

        if self.titulo == 'Distribución de clientes por calificación 2':
            serie1 = []
            serie2 = []

            if self.filtros.agrupador == 'dia':
                agrupador_select = "dt.fecha"
                mes = int(self.filtros.periodo['mes'])
                mes = str(mes) if mes >= 10 else '0'+str(mes)
                dia = int(self.filtros.periodo['dia'])
                dia = str(dia) if dia >= 10 else '0'+str(dia)
                agrupador_where = f" dt.fecha='{self.filtros.periodo['anio']}-{mes}-{dia}'"
            elif self.filtros.agrupador == "semana":
                agrupador_select = "dt.anio, dt.num_semana"
                semana_completa = str(self.filtros.periodo['semana'])
                num_semana = str(int(semana_completa[4:]))
                anio = semana_completa[0:4]
                agrupador_where = f" dt.anio={anio} and dt.num_semana='W{num_semana}'"
            elif self.filtros.agrupador == "mes":
                agrupador_select = "dt.anio, dt.num_mes"
                agrupador_where = f" dt.num_mes={self.filtros.periodo['mes']} and dt.anio={self.filtros.periodo['anio']}"
            # Rawa
            # pipeline = f"""select nd.calificacion,count(1) reg, {agrupador_select}
            # from DWH.limesurvey.nps_mail_pedido nmp
            # inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            # left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            # left join DWH.dbo.dim_tiempo dt on nmp.fecha = dt.fecha 
            # where {agrupador_where} """
            pipeline = f"""select nd.calificacion,count(1) reg, {agrupador_select}
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            LEFT JOIN DWH.dbo.hecho_order ho ON ho.order_number =nmp.pedido
            left join DWH.dbo.dim_tiempo dt on ho.creation_date = dt.fecha 
            where {agrupador_where} """
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                pipeline += f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                pipeline += f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                pipeline += f" and ct.region ='{self.filtros.region}' "
            pipeline += f" group by nd.calificacion, {agrupador_select} order by calificacion"

            # print("query desde columnas básicas nps ahorita: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                categorias = ['']
                for i in range(len(arreglo)):
                    name = int(arreglo[i]['calificacion'])
                    y = [arreglo[i]['reg']]
                    if name <=6:
                        color = 'danger'
                    elif name <= 8:
                        color = 'warning'
                    else:
                        color = 'success'
                    series.append( {
                        'name': name,
                        'y': y,
                        'type': 'column',
                        'formato_tooltip':'entero', 
                        'color': color
                    })
            else:
                hayResultados = 'no'

        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': pipeline, 'categoria':self.filtros.categoria}
        # Para debugging
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': []}

    async def CostoPorPedido(self):
        categorias = []
        series = []
        subSubTitulo = ''
        queryMetodoEnvio = f"and cf.TiendaEnLinea = '{self.filtros.metodoEnvio}'" if self.filtros.metodoEnvio != '' and self.filtros.metodoEnvio != "False" and self.filtros.metodoEnvio != None else ''
        if self.filtros.anio != 0 and self.filtros.anio != None:
            query1Anio = f"and cf.Anio = {self.filtros.anio}"
            query2Anio = f"and Anio = {self.filtros.anio}"
        else:
            query1Anio = query2Anio = ''
        if self.filtros.mes != 0 and self.filtros.mes != None:
            query1Mes = f"and cf.Mes = {self.filtros.mes}"
            query2Mes = f"and Mes = {self.filtros.mes}"
        else:
            query1Mes = query2Mes = ''
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    queryLugar = f""" and ct.tienda = {self.filtros.tienda} """
                    lugar = f"tiendaNombre"
                else:
                    queryLugar = f""" and ct.zona = {self.filtros.zona} """
                    lugar = f"tiendaNombre"
            else:
                queryLugar = f""" and ct.region = {self.filtros.region} """
                lugar = f"zonaNombre"
        else:
            queryLugar = ''
            lugar = f"regionNombre"

        if self.titulo == 'Pedidos por Picker':
            series = []
            data = []
            query = f"""select * from  DWH.artus.catCostos"""
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            costosReferencia_tmp = crear_diccionario(cursor)
            costosReferencia = {}
            for row in costosReferencia_tmp:
                costosReferencia[row['descripCosto']] = row['Costo']
            pipeline = f"""select {lugar} as lugar, sum(cf.pRH) pedidos from dwh.report.consolidadoFinanzas cf 
                left join DWH.artus.catTienda ct on cf.Cebe = ct.tienda 
                left join DWH.dbo.dim_tiempo dt on dt.id_fecha = cf.Anio * 10000 + cf.Mes * 100 + 1
                where Mes <= 12
                {queryMetodoEnvio}
                {query1Anio}
                {query1Mes}
                {queryLugar}
                group by {lugar}
                """
            # print(f"query desde ColumnasBasicas->PedidosPorPicker->{self.titulo}->General: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    query = f"""select SUM(Ocupada) as pickers from DWH.report.consolidadoFinanzasPicker cfp
                    left join DWH.artus.catTienda ct on cfp.Cebe = ct.tienda 
                    where Puesto like '%surtidor%'
                    and ct.{lugar} = '{row['lugar']}'
                    {query2Anio} 
                    {query2Mes} 
                    {queryLugar}"""
                    # print(f"query desde columnasBasicas->PedidosPorPicker->{self.titulo}->Picker: {str(query)}")
                    cursor = cnxn.cursor().execute(query)
                    arregloSub = crear_diccionario(cursor)
                    pedidos = float(row['pedidos'])
                    pickers = float(arregloSub[0]['pickers']) if arregloSub[0]['pickers'] is not None else 0
                    # print(f"DataSub: {str(dataSub)}")
                    pedidosPorPicker = pedidos / pickers if pickers != 0 else 0
                    data.append((pedidosPorPicker, row['lugar'])) 
                # Lo ordenas según https://stackoverflow.com/questions/31942169/python-sort-array-of-arrays-by-multiple-conditions
                data = sorted(data)
                # Extraes los datos para las series y las categories
                for tupla in data:
                    series.append(tupla[0])
                    categorias.append(tupla[1])
                series = [
                    {
                        'name': 'Pedidos por Picker',
                        'data': series,
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'primary'
                    }
                ]
            else:
                hayResultados = 'no'
                series = []

        if self.titulo == 'Costo de RH por pedido':
            series = []
            data = []
            query = f"""select * from  DWH.artus.catCostos"""
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            costosReferencia_tmp = crear_diccionario(cursor)
            costosReferencia = {}
            for row in costosReferencia_tmp:
                costosReferencia[row['descripCosto']] = row['Costo']
            pipeline = f"""select {lugar} as lugar, sum(cf.pRH) pedidos, sum(cf.RH) RH, SUM(cf.Envio) Envio, SUM(cf.Combustible) Combustible from dwh.report.consolidadoFinanzas cf 
                left join DWH.artus.catTienda ct on cf.Cebe = ct.tienda 
                left join DWH.dbo.dim_tiempo dt on dt.id_fecha = cf.Anio * 10000 + cf.Mes * 100 + 1
                where Mes <= 12
                {queryMetodoEnvio}
                {query1Anio}
                {query1Mes}
                {queryLugar}
                group by {lugar}
                """
            # print(f"query desde tablas->CostoPorPedido->{self.titulo}->General: {str(pipeline)}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)
            if len(arreglo) > 0:
                hayResultados = "si"
                for row in arreglo:
                    pedidos = float(row['pedidos'])
                    RH = float(row['RH']) if row['RH'] is not None else 0
                    Envio = float(row['Envio']) if row['Envio'] is not None else 0
                    Combustible = float(row['Combustible']) if row['Combustible'] is not None else 0
                    # print(f"DataSub: {str(dataSub)}")
                    RHxPedido = ((RH + Envio + Combustible) / pedidos) if pedidos != 0 else 0
                    data.append((RHxPedido, row['lugar'])) 
                # Lo ordenas según https://stackoverflow.com/questions/31942169/python-sort-array-of-arrays-by-multiple-conditions
                data = sorted(data)
                # Extraes los datos para las series y las categories
                for tupla in data:
                    series.append(
                    {
                        'name': tupla[1],
                        'y': tupla[0],
                        'type': 'column',
                        'formato_tooltip':'moneda', 
                        'color':'secondary'
                    }
                    )
            else:
                hayResultados = 'no'
                series = []

        if self.titulo == 'Prueba':
            hayResultados = 'si'
            pipeline = []
            categorias = ['mexicanos', 'al', 'grito', 'de', 'guerra', 'acero']
            series = []
            #     {
            #         'name': 'Costo de RH por Pedido',
            #         'data': [5,3,7,9,4,5],
            #         'type': 'column',
            #         'formato_tooltip':'moneda', 
            #         'color':'secondary'
            #     }
            # ]
            data = [300,500,100, 900,600,300]
            for i in range(6):
                if i % 3 == 0:
                    color = 'success'
                elif i % 3 == 1:
                    color = '#FFFFFF'
                else:
                    color = 'danger'
                series.append( {
                    'y': data[i],
                    'type': 'column',
                    'formato_tooltip':'entero', 
                    'color': color
                })
            subSubTitulo = f'Actualizado al {datetime.now().strftime("%d/%m/%Y a las %H:%M")}'
        return {'hayResultados':hayResultados, 'series':series, 'categorias': categorias, 'subSubTitulo': subSubTitulo, 'pipeline': pipeline}

    async def PedidosPendientes(self):
        pipeline = []
        data = []
        categorias = []
        subSubTitulo = ''
        series = []
        filtroHoy = {
            '$match': {
                'fechaEntrega': {
                    '$lte': datetime.combine(date.today(), time(hour=23, minute=59, second=59))
                }
            }
        }
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel = 'idTienda'
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

        collection = conexion_mongo('report').report_pedidoPendientes
        pipeline.extend([
            {'$unwind': '$sucursal'}, 
            filtroHoy
            ])
        if filtro_lugar:
            pipeline.append({'$match': {'sucursal.'+ nivel: lugar}})
        if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
            pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
        if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
            pipeline.append({'$match': {'origen': self.filtros.origen}})

        if self.titulo == 'Pedidos pendientes de entrega':
            # pipeline.append({'$project': {'2_DIAS': {'$cond': [{'$eq':['$prioridad', '2 DIAS']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, '1_DIA': {'$cond': [{'$eq':['$prioridad', '1 DIA']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}, 'ANTERIORES': {'$cond': [{'$eq':['$prioridad', 'ANTERIORES']}, 1, 0]}}})
            # pipeline.append({'$group':{'_id':0, '2_DIAS':{'$sum':'$2_DIAS'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, '1_DIA':{'$sum':'$1_DIA'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}, 'ANTERIORES':{'$sum':'$ANTERIORES'}}})
            pipeline.append({
                '$group': {
                    '_id':'$prioridad', 
                    'pedidos':{'$sum':1},
                    'actualizacion': {'$max': '$fechaUpdate'}
                }
            })
            # print(f"Pipeline desde columnasBasicas -> Pedidos Pendientes: {str(pipeline)}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            print(str(arreglo))
            if len(arreglo) <= 0:
                # print("No hubo resultados")
                hayResultados = "no"
            else:
                hayResultados = "si"
                estatus = ['ANTERIORES', '2 DIAS', '1 DIA', 'HOY ATRASADO', 'HOY A TIEMPO']
                categorias = [elemento.title() for elemento in estatus]
                valores = [next((item.get("pedidos", 0) for item in arreglo if item["_id"] == key),0) for key in estatus]
                # print(f"Valores = {valores}")
                for i in range(len(estatus)):
                    if i == 0:
                        color = 'danger'
                    elif i == 4:
                        color = 'secondary'
                    else:
                        color = 'light'
                    # res[indice]['y'] = resultado['pedidos']
                    series.append({
                        'y': valores[i],
                        'type': 'column',
                        'formato_tooltip':'entero',
                        'color': color
                    })
                actualizacion = arreglo[0]['actualizacion'] - timedelta(hours=6)
                actualizacion = actualizacion.strftime("%d/%m/%Y a las %H:%M:%S")
                subSubTitulo = f"Actualizado al {actualizacion} hrs."

        return {'hayResultados':hayResultados, 'series':series, 'categorias': categorias, 'subSubTitulo': subSubTitulo, 'pipeline': pipeline}

@router.post("/{seccion}")
async def columnas_basicas (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = ColumnasBasicas(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
