from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.permisos import tienePermiso, crearLog
from inspect import stack

router = APIRouter(
    prefix="/spiderweb",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Spiderweb():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def Nps(self):
        categories = []
        series = []

        fecha_fin = self.filtros.fechas['fecha_fin'][:10]
        clauseCatProveedor = " AND cp.proveedor is not null "
        if len(self.filtros.provLogist) > 0:
            clauseCatProveedor = " AND ("
            contador = 0
            for prov in self.filtros.provLogist:
                clauseCatProveedor += f" cp.proveedor = '{prov}' "
                if contador < len(self.filtros.provLogist) - 1:
                    clauseCatProveedor += f" OR "
                else:
                    clauseCatProveedor += f") "
                contador += 1
        clauseCatProveedor += f" AND ((cp.fecha_from = '2022-11-23' AND (cp.fecha_to is null OR cp.fecha_to <= '{fecha_fin}') OR (cp.fecha_from <= '{fecha_fin}' AND cp.fecha_to is null)))"

        if self.titulo == 'Respuestas por responsable':
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

            pipeline = f"""select ncp.responsable,sum(case when ncp.flujo='F1' then npr.cant else 0 end) RF1,
            sum(case when ncp.flujo='F2' then npr.cant else 0 end) RF2, {agrupador_select}
            from DWH.limesurvey.nps_pregunta_respuesta npr
            inner join DWH.limesurvey.nps_cat_preguntas ncp on npr.id_pregunta =ncp.id_pregunta
            inner join DWH.dbo.dim_tiempo dt on npr.fecha=dt.fecha
            left join DWH.artus.catTienda ct on npr.idTienda =ct.tienda
            left join DWH.artus.catProveedores cp on cp.idTienda = npr.idTienda 
            where ncp.tipo_respuesta = 'R2'
            and {agrupador_where} {clauseCatProveedor} """
            if self.filtros.tienda != '' and self.filtros.tienda != None and self.filtros.tienda != 'False':
                pipeline += f""" and ct.tienda ='{self.filtros.tienda}' """
            elif self.filtros.zona != '' and self.filtros.zona != None and self.filtros.zona != 'False':
                pipeline += f" and ct.zona='{self.filtros.zona}' "
            elif self.filtros.region != '' and self.filtros.region != None and self.filtros.region != 'False':
                pipeline += f" and ct.region ='{self.filtros.region}' "
            pipeline += f""" group by ncp.responsable, {agrupador_select}"""

            # print("query desde spiderweb: "+pipeline)
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(pipeline)
            arreglo = crear_diccionario(cursor)

            if len(arreglo) > 0:
                hayResultados = "si"
                # Obtener las sumas para después sacar promedio:
                sum_rf1 = sum_rf2 = 0
                for row in arreglo:
                    sum_rf1 += int(row['RF1'])
                    sum_rf2 += int(row['RF2'])
                rf1_porcent = []
                rf2_porcent = []
                for row in arreglo:
                    categories.append(row['responsable'])
                    rf1_valor = 100 * float(row['RF1'])/sum_rf1 if sum_rf1 != 0 else '--'
                    rf2_valor = 100 * float(row['RF2'])/sum_rf2 if sum_rf2 != 0 else '--'
                    rf1_porcent.append(round(rf1_valor, 2))
                    rf2_porcent.append(round(rf2_valor, 2))
                series.extend([
                    {
                        'name': 'Promotores',
                        'data': rf2_porcent,
                        'color': 'success',
                        'pointPlacement': 'on'
                    },
                    {
                        'name': 'Pasivos y Detractores',
                        'data': rf1_porcent,
                        'color': 'danger',
                        'pointPlacement': 'on'
                    },
                ])
            else:
                hayResultados = 'no'

        return {'hayResultados':hayResultados,'categories':categories, 'series':series, 'pipeline': pipeline, 'categoria':self.filtros.categoria}
        # Para debugging
        # return {'hayResultados':'no','categories':[], 'series':[], 'pipeline': []}

@router.post("/{seccion}")
async def spiderweb (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    crearLog(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        objeto = Spiderweb(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
