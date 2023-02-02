# Se envía un diccionario "res" que contiene:
#     - Un arreglo 'series_outer' que contiene varios diccionarios con:
#         * Un string 'name' con el título de cada fragmento de barra N1
#         * Un arreglo 'data' (ej. lista_regiones) con diccionarios que corresponden a cada contienen:
#             * Un string 'name' con el título de la barra de primer nivel1
#             * Un número 'y' con el valor de esa barra del primer nivel1
#             * Un número 'drilldown' que tiene el id de esa barra de primer nivel1
#     - Un arreglo 'drilldown_series' que contiene diccionarios con:
#         * Un string 'name' con el título de la barra de primer nivel1 (otra vez), pero en esta ocasión para que sirva como título del eje x del segundo nivel1 del gráfico
#         * Un número 'id' con el id de la barra de primer nivel1 (otra vez), para identificar el gráfico de 2o. nivel1.
#         * Un arreglo 'data' (ej. region_data) que contiene, sin índices:
#             * El nombre de la barra de segundo nivel1
#             * El valor o monto para esa barra

from copy import deepcopy
from time import strftime
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import fechaAbrevEspanol
from app.servicios.formatoFechas import mesTexto
from datetime import datetime, date, timedelta, time
from calendar import monthrange
import json
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack

router = APIRouter(
    prefix="/columnasApiladasDrilldown",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class ColumnasApiladasDrilldown():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def PedidosPendientes(self):
        print("Entró a PedidosPendientes")
        hayResultados = "no"
        categorias = []
        pipeline = []
        series = []
        serie1 = []
        serie2 = []
        serie3 = []
        serie4 = []
        serie5 = []

        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel1 = 'idTienda'
                    nivel2 = 'tiendaNombre'
                    nivel3 = 'tiendaNombre'
                    lugar = int(self.filtros.tienda)
                else:
                    nivel1 = 'zona'
                    nivel2 = 'tiendaNombre'
                    nivel3 = 'tiendaNombre'
                    lugar = int(self.filtros.zona)
            else:
                nivel1 = 'region'
                nivel2 = 'zonaNombre'
                nivel3 = 'tiendaNombre'
                lugar = int(self.filtros.region)
        else:
            filtro_lugar = False
            nivel2 = 'regionNombre'
            nivel3 = 'zonaNombre'
            lugar = ''

        filtroHoy = {
            '$match': {
                'prioridad': {
                    '$ne': 'Futuro'
                }
            }
        }
        collection = conexion_mongo('report').report_pedidoPendientes
        pipeline.extend([{'$unwind': '$sucursal'}, filtroHoy])
        if filtro_lugar:
            pipeline.append({'$match': {'sucursal.'+ nivel1: lugar}})
        if self.filtros.tipoEntrega != None and self.filtros.tipoEntrega != "False" and self.filtros.tipoEntrega != "":
                pipeline.append({'$match': {'metodoEntrega': self.filtros.tipoEntrega}})
        if self.filtros.origen != None and self.filtros.origen != "False" and self.filtros.origen != "":
                pipeline.append({'$match': {'origen': self.filtros.origen}})

        if self.titulo == 'Pedidos Por Región':
            pipeline.append({'$match': {'estatus': 'pendientes'}})
            pipeline.append({'$project': {'nivel2': '$sucursal.'+nivel2, 'nivel3': '$sucursal.'+nivel3, '2_DIAS': {'$cond': [{'$eq':['$prioridad', '2 DIAS']}, 1, 0]}, 'HOY_ATRASADO': {'$cond': [{'$eq':['$prioridad', 'HOY ATRASADO']}, 1, 0]}, '1_DIA': {'$cond': [{'$eq':['$prioridad', '1 DIA']}, 1, 0]}, 'HOY_A_TIEMPO': {'$cond': [{'$eq':['$prioridad', 'HOY A TIEMPO']}, 1, 0]}, 'ANTERIORES': {'$cond': [{'$eq':['$prioridad', 'ANTERIORES']}, 1, 0]}}})
            pipeline.append({'$group':{'_id':{'nivel2': '$nivel2', 'nivel3': '$nivel3'}, '2_DIAS':{'$sum':'$2_DIAS'}, 'HOY_ATRASADO':{'$sum':'$HOY_ATRASADO'}, '1_DIA':{'$sum':'$1_DIA'}, 'HOY_A_TIEMPO':{'$sum':'$HOY_A_TIEMPO'}, 'ANTERIORES':{'$sum':'$ANTERIORES'}}})
            pipeline.append({'$sort': {'_id': 1}})
            cursor = collection.aggregate(pipeline)
            # print(f"Pipeline desde ColumnasApiladas -> PedidosPendientes -> Estatus Pedidos por Área: {str(pipeline)}")
            arreglo = await cursor.to_list(length=1000)
            # Esta sección viene pegada de columnasDrilldown
            class Nodo:
                def __init__(self):
                    self.codigo = None
                    self.nombre = ""
                    self.monto = 0
                    self.hijos = []
                def addHijo(self, hijo):
                    self.hijos.append(hijo)

            def buscar_region(arbol, codigo):
                for nodo in arbol:
                    if nodo.codigo == codigo:
                        return nodo
                return "No encontrado"

            arbol = []

            for registro in arreglo:
                codigo = registro['_id']['nivel2']
                region_existente = buscar_region(arbol, codigo)
                if region_existente != "No encontrado":
                    nodo_region = region_existente
                    nodo_region.monto += float(registro['monto'])
                else:
                    nodo_region = Nodo()
                    nodo_region.codigo = codigo
                    nodo_region.nombre = registro['_id']['nivel2']
                    nodo_region.monto = int(registro['monto'])
                    arbol.append(nodo_region)
                nodo_zona = Nodo()
                nodo_zona.nombre = registro['_id']['nivel3']
                nodo_zona.monto = registro['monto']
                nodo_region.addHijo(nodo_zona)

            drilldown_series = []
            lista_regiones = []
            for region in arbol:
                region_data = []
                for zona in region.hijos:
                    arr_zona = []
                    arr_zona.append(zona.nombre)
                    arr_zona.append(round(float(zona.monto), 2))
                    region_data.append(arr_zona)
                drilldown_series.append({
                    'name': region.nombre,
                    'id': region.codigo,
                    'data': region_data
                })
                lista_regiones.append({
                    'name': region.nombre,
                    'y': round(float(region.monto), 2),
                    'drilldown': region.codigo   
                })
            series_outer = [{
                'name': 'Departamentos',
                'data': lista_regiones
            }]

            # A partir de aquí es lo que se tenía originalmente en columnasApiladas
            if len(arreglo) >0:
                hayResultados = "si"
                for row in arreglo:
                    categorias.append(row['_id'])
                    serie1.append(row['HOY_A_TIEMPO'])
                    serie2.append(row['HOY_ATRASADO'])
                    serie3.append(row['1_DIA'])
                    serie4.append(row['2_DIAS'])
                    serie5.append(row['ANTERIORES'])
                series.extend([
                    {'name': 'Hoy a tiempo', 'data':serie1, 'color': 'secondary'},
                    {'name': 'Hoy atrasado', 'data':serie2, 'color': 'danger'},
                    {'name': '1 día', 'data':serie3, 'color': 'warning'},
                    {'name': '2 días', 'data':serie4, 'color': 'primary'},
                    {'name': 'Anteriores', 'data':serie5, 'color': '#FF3D51'}
                ])
            else:
                hayResultados = "no"

        if self.titulo == 'Ejemplo':
            print("Entró a ejemplo")
            hayResultados = 'si'
            pipeline = []
            categorias = ['Izquierda', 'Centro', 'Derecha']
            tituloApiladas = ['Arriba', 'Enmedio', 'Abajo']
            colores = ['#00FFFF', '#0000FF', '#808000'] # Color para las columnas que se apilan en cada punto del eje horizontal: arriba, enmedio y abajo, respectivamente
            subCategorias = [ # Cada subarreglo corresponde a una categoría (p. ej., una región), y tiene las subcategorías de esa categoría (p. ej., zonas).
                ['Izquierda1', 'Izquierda2', 'Izquierda3', 'Izquierda4'],
                ['Centro1', 'Centro2', 'Centro3'],
                ['Abajo1', 'Abajo2', 'Abajo3']
            ]
            dataArribaN1 = [1, 2, 3]
            dataEnmedioN1 = [4, 5, 6]
            dataAbajoN1 = [7, 8, 9]
            DataIzquierdaArriba = [10, 11, 12, 4] # Fíjate cómo en este arreglo (y en los siguientes dos) hay 4 valores porque la categoría 'Izquierda' tiene 4 subcategorías
            DataIzquierdaEnmedio = [13, 14, 15, 4]
            DataIzquierdaAbajo = [16, 17, 18, 4]
            DataCentroArriba = [19, 20, 21]
            DataCentroEnmedio = [22, 23, 24]
            DataCentroAbajo = [25, 26, 27]
            DataDerechaArriba = [28, 29, 30]
            DataDerechaEnmedio = [31, 32, 33]
            DataDerechaAbajo = [34, 35, 36]

            dataN1 = [dataArribaN1, dataEnmedioN1, dataAbajoN1]
            dataN2 = [
                [
                    DataIzquierdaArriba, DataIzquierdaEnmedio, DataIzquierdaAbajo
                ], [
                    DataCentroArriba, DataCentroEnmedio, DataCentroAbajo
                ], [
                    DataDerechaArriba, DataDerechaEnmedio, DataDerechaAbajo
                ]
            ]
            # Entonces para acceder a un dato de dataN2, tienes que hacer dataN2[índice categoría][índice de barra][índice de subcategoría]

        return {'hayResultados':hayResultados, 'categorias':categorias, 'subCategorias':subCategorias, 'tituloApiladas': tituloApiladas, 'colores': colores, 'dataN1': dataN1, 'dataN2': dataN2, 'pipeline': pipeline}

@router.post("/{seccion}")
async def columnas_apiladas_drilldown (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = ColumnasApiladasDrilldown(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}
