from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.permisos import tienePermiso, crearLog
from inspect import stack

router = APIRouter(
    prefix="/columnasAgrupadasYApiladas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class ColumnasAgrupadasYApiladas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def CatalogoArticulos(self):
        if self.filtros.periodo == {}:
            return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': ""}
        categorias = []
        series = []
        nSemDS = []
        idSemDS = []
        kpis = {
            'productoOmnicanal': {
                'nombreLargo': 'Producto Omnicanal',
                'periodoAct': [],
                'periodoAnt': [],
                'colorAct': '#bf6745',
                'colorAnt': '#FFA785'
            },
            'banderaIncorrecta': {
                'nombreLargo': 'Bandera Incorrecta',
                'periodoAct': [],
                'periodoAnt': [],
                'colorAct': '#bf0011',
                'colorAnt': '#ff3d51'
            },
            'aptosVenta': {
                'nombreLargo': 'Aptos Para la Venta',
                'periodoAct': [],
                'periodoAnt': [],
                'colorAct': '#348f9e',
                'colorAnt': '#74CFDE'
            },
            'baja': {
                'nombreLargo': 'Baja',
                'periodoAct': [],
                'periodoAnt': [],
                'colorAct': '#bf0011',
                'colorAnt': '#ff3d51'
            },
            'aprobadosTL': {
                'nombreLargo': 'Aprobados en TL',
                'periodoAct': [],
                'periodoAnt': [],
                'colorAct': '#459b4a',
                'colorAnt': '#85DB8A'
            },
            'noAprobados': {
                'nombreLargo': 'No aprobados',
                'periodoAct': [],
                'periodoAnt': [],
                'colorAct': '#242424',
                'colorAnt': '#646464'
            },
        }

        if self.filtros.agrupador == 'semana':
            select_periodo = 'nSemDS'
            filtroAgrupador = f" where idSemDS = {self.filtros.periodo['semana']} or idSemDS = {int(self.filtros.periodo['semana']) - 1}"
        else:
            # Si no está agrupado por semana, de plano no voy a regresar nada porque actualmente no tengo ni el nombre del campo por mes
            return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': ""}

        if self.filtros.grupoDeptos != '' and self.filtros.grupoDeptos != 'False':
            if self.filtros.deptoAgrupado != '' and self.filtros.deptoAgrupado != 'False':
                select_departamento = 'grupo, departamento, Subdepartamento'
                where_departamento = f"and grupo = '{self.filtros.grupoDeptos}' and departamento = '{self.filtros.deptoAgrupado}'"
            else:
                select_departamento = 'grupo, departamento'
                where_departamento = f"and grupo = '{self.filtros.grupoDeptos}'"
        else:
            select_departamento = 'grupo'
            where_departamento = ''
        # Obtener los periodos elegido y anterior y 
        query = f"""select DISTINCT idSemDS, nSemDS 
        from DWH.report.catalogoUXConsolidado cu
        where idSemDS in (
        select DISTINCT idSemDS
        from DWH.dbo.dim_tiempo dt
        where fecha in (
        select DATEADD(d,-1,min(fecha)) fechaFin
        from DWH.dbo.dim_tiempo dt
        where idSemDS = {self.filtros.periodo['semana']})
        OR idSemDS = {self.filtros.periodo['semana']})
        order by idSemDS
        """
        # print(f"query 1 desde columnasAgrupadasYApiladas: {query}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        resultados = crear_diccionario(cursor)
        if len(resultados) == 2:
            for row in resultados:
                nSemDS.append(row['nSemDS'])
                idSemDS.append(row['idSemDS'])
            query = f"""select nSemDS, {select_departamento} as categoria, sum(productoOmnicanal) as productoOmnicanal, sum(banderaIncorrecta) as banderaIncorrecta, sum(aptosVenta) as aptosVenta, sum(baja) as baja, sum(VisibleTL) as aprobadosTL, sum(noVisible) as noAprobados
            from DWH.report.catalogoUXConsolidado cu
            where idSemDS in ({','.join([str(i) for i in idSemDS])}) {where_departamento}
            group by nSemDS, {select_departamento}"""

            # print(f"query 2 desde columnasAgrupadasYApiladas: {query}")

            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            resultados = crear_diccionario(cursor)
            # Necesitas tener en un arreglo los periodos
            if len(resultados) > 0:
                hayResultados = "si"
                for row in resultados:
                    if row['categoria'] not in categorias:
                        categorias.append(row['categoria'])
                    periodoAAgregar = 'periodoAnt' if nSemDS[0] == row['nSemDS'] else 'periodoAct'
                    for kpi in kpis:
                        kpis[kpi][periodoAAgregar].append(row[kpi])
                for kpi in kpis:
                    series.extend([
                        {
                            'name': f"{kpis[kpi]['nombreLargo']} - {nSemDS[0]}",
                            'stack': kpi,
                            'data': kpis[kpi]['periodoAnt'],
                            'color': kpis[kpi]['colorAnt']
                        },
                        {
                            'name': f"{kpis[kpi]['nombreLargo']} - {nSemDS[1]}",
                            'stack': kpi,
                            'data': kpis[kpi]['periodoAct'],
                            'color': kpis[kpi]['colorAct']
                        }
                    ])
        # series = [
        #     {
        #         'name': 'ERP sem 13',
        #         'stack': 'ERP',
        #         'data': [1049, 4936, 6798, 43015, 18837, 19083],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'ERP sem 14',
        #         'stack': 'ERP',
        #         'data': [1049, 5039, 6803, 43126, 19334, 19408],
        #         'color': 'primary'
        #     }, {
        #         'name': 'Bandera Incorrecta sem 13',
        #         'stack': 'Bandera Incorrecta',
        #         'data': [0, 1, 0, 0, 0, 2],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'Bandera Incorrecta sem 14',
        #         'stack': 'Bandera Incorrecta',
        #         'data': [0, 1, 0, 0, 0, 2],
        #         'color': 'primary'
        #     }, {
        #         'name': 'Producto Omnicanal sem 13',
        #         'stack': 'Producto Omnicanal',
        #         'data': [1049, 4935, 6798, 43015, 18837, 19081],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'Producto Omnicanal sem 14',
        #         'stack': 'Producto Omnicanal',
        #         'data': [1049, 5038, 6803, 43126, 19334, 19406],
        #         'color': 'primary'
        #     }, {
        #         'name': 'Baja sem 13',
        #         'stack': 'Baja',
        #         'data': [0, 1840, 0, 0, 12513, 336],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'Baja sem 14',
        #         'stack': 'Baja',
        #         'data': [0, 1840, 0, 0, 12513, 336],
        #         'color': 'primary'
        #     }, {
        #         'name': 'Aptos Venta sem 13',
        #         'stack': 'Aptos Venta',
        #         'data': [1049, 3096, 6798, 43015, 6324, 18747],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'Aptos Venta sem 14',
        #         'stack': 'Aptos Venta',
        #         'data': [1049, 3199, 6803, 43126, 6821, 19072],
        #         'color': 'primary'
        #     }, {
        #         'name': 'No Visible sem 13',
        #         'stack': 'No Visible',
        #         'data': [80, 764, 486, 8647, 14242, 7063],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'No Visible sem 14',
        #         'stack': 'No Visible',
        #         'data': [78, 838, 476, 8757, 14635, 7366],
        #         'color': 'primary'
        #     }, {
        #         'name': 'Visible sem 13',
        #         'stack': 'Visible',
        #         'data': [969, 4172, 6312, 34368, 4595, 12020],
        #         'color': 'secondary'
        #     }, {
        #         'name': 'Visible sem 14',
        #         'stack': 'Visible',
        #         'data': [971, 4201, 6327, 34369, 4699, 12042],
        #         'color': 'primary'
        #     }
        # ]
        
            else:
                hayResultados = "no"
        else:
            hayResultados = "no"
            # print(f"len(resultados) no es 2, sino {len(resultados)}: {str(resultados)}")

        # print('Lo que se devuelve desde columnasApiladas es: ' + str({'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': query}))
        return {'hayResultados':hayResultados,'categorias':categorias, 'series':series, 'pipeline': query}
        # Return para debugging:
        # return {'hayResultados':'no','categorias':[], 'series':[], 'pipeline': pipeline}

@router.post("/{seccion}")
async def columnas_agrupadas_y_apiladas (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    crearLog(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        objeto = ColumnasAgrupadasYApiladas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
