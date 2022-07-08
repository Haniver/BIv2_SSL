from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.permisos import tienePermiso
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

            pipeline = f"""select nd.calificacion,count(1) reg, {agrupador_select}
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            left join DWH.dbo.dim_tiempo dt on nmp.fecha = dt.fecha 
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

            pipeline = f"""select nd.calificacion,count(1) reg, {agrupador_select}
            from DWH.limesurvey.nps_mail_pedido nmp
            inner join DWH.limesurvey.nps_detalle nd on nmp.id_encuesta =nd.id_encuesta and nd.nEncuesta=nmp.nEncuesta
            left join DWH.artus.catTienda ct on nmp.idTienda =ct.tienda
            left join DWH.dbo.dim_tiempo dt on nmp.fecha = dt.fecha 
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

@router.post("/{seccion}")
async def columnas_basicas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id, seccion):
        objeto = ColumnasBasicas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
