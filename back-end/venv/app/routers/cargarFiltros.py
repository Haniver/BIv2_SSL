from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.formatoFechas import mesTexto
from app.servicios.Filtro import Filtro

router = APIRouter(
    prefix="/filtros",
    responses={404: {"description": "Not found"}},
)

@router.get("/cargarRegion")
async def cargar_region():
    collection = conexion_mongo('report').catTienda
    pipeline = [
        {'$match': {'REGION_NOMBRE': {'$ne': 'N/A'}}},
        {'$match': {'REGION': {'$ne': 100}}},
        {'$match': {'REGION': {'$ne': 99}}},
        {'$match': {'REGION': {'$ne': 90}}},
        {'$group': {'_id': {'label': '$REGION_NOMBRE', 'value': '$REGION'}}},
        {'$project': {'_id': 0,'label':'$_id.label', 'value':'$_id.value'}},
        {'$sort': {'label': 1}}
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

@router.get("/cargarZona")
async def cargar_zona(region: int):
    collection = conexion_mongo('report').catTienda
    pipeline = [
        {'$match': {'REGION': {'$eq': region}}},
        {'$match': {'ZONA_NOMBRE': {'$ne': 'N/A'}}},
        {'$group': {'_id': {'label': '$ZONA_NOMBRE', 'value': '$ZONA'}}},
        {'$project': {'_id': 0, 'label':'$_id.label', 'value':'$_id.value'}},
        {'$sort': {'label': 1}}
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

@router.get("/cargarTienda")
async def cargar_tienda(region: int, zona: int):
    collection = conexion_mongo('report').catTienda
    if region > 0:
        if zona > 0:
            pipeline =[{'$match': {'ZONA': {'$eq': zona}}}]
        else:
            pipeline =[{'$match': {'REGION': {'$eq': region}}}]
    else:
        pipeline =[]
    pipeline.extend([
        {'$match': {'TIENDA_NOMBRE': {'$ne': 'N/A'}}},
        {'$group': {'_id': {'label': '$TIENDA_NOMBRE', 'value': '$TIENDA'}}},
        {'$project': {'_id': 0, 'label':'$_id.label', 'value':'$_id.value'}},
        {'$sort': {'label': 1}}
    ])
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

@router.get("/cargarDepto")
async def cargar_depto(user: dict = Depends(get_current_active_user)):
    collection = conexion_mongo('report').catArticulos
    pipeline = [
        {'$match': {'DEPTO_NOMBRE': {'$ne': 'N/A'}}},
        {'$group': {'_id': {'label': '$DEPTO_NOMBRE', 'value': '$DEPTO'}}},
        {'$project': {'_id': 0,'label':'$_id.label', 'value':'$_id.value'}},
        {'$sort': {'label': 1}}
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

@router.get("/cargarSubDepto")
async def cargar_subdepto(depto: int, user: dict = Depends(get_current_active_user)):
    collection = conexion_mongo('report').catArticulos
    pipeline = [
        {'$match': {'DEPTO': {'$eq': depto}}},
        {'$match': {'SUBDEPTO_NOMBRE': {'$ne': 'N/A'}}},
        {'$group': {'_id': {'label': '$SUBDEPTO_NOMBRE', 'value': '$SUBDEPTO'}}},
        {'$project': {'_id': 0, 'label':'$_id.label', 'value':'$_id.value'}},
        {'$sort': {'label': 1}}
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

@router.get("/cargarProveedor")
async def cargar_proveedor(user: dict = Depends(get_current_active_user)):
    collection = conexion_mongo('report').catArticulos
    pipeline = [
        {'$group': {'_id': {'id': '$PROVEEDOR', 'nombre': '$PROVEEDOR_NOMBRE'}}},
        {'$project': {'_id':0, 'value':'$_id.id', 'label':'$_id.nombre'}},
        {'$sort': {'label': 1}}
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

@router.post("/cargarPeriodo")
async def cargar_periodo(filtros: Filtro, user: dict = Depends(get_current_active_user)):
    pipeline = [
        {'$match': {'fecha': {'$gte': datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), '$lte': datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ')}}},
        {'$group': {'_id': {}}},
        {'$sort': {}}
    ]
    group = pipeline[1]['$group']['_id']
    sort = pipeline[2]['$sort']
    if filtros.agrupador == 'mes' or filtros.agrupador == 'dia':
        group['anio'] = {'$year': '$fecha'}
        group['mes'] = {'$month': '$fecha'}
        sort['_id.anio'] = 1
        sort['_id.mes'] = 1
        if filtros.agrupador == 'dia':
            group['dia'] = {'$dayOfMonth': '$fecha'}
            sort['_id.dia'] = 1
    elif filtros.agrupador == 'semana':
        group['semana'] = '$idSemDS'
        group['semana_descrip'] = '$nSemDS'
        sort['_id.semana'] = 1
    # print(pipeline)
    collection = conexion_mongo('report').catTiempo
    cursor = collection.aggregate(pipeline)
    arreglo = await cursor.to_list(length=1000)
    # print(f'arreglo desde CargarPeriodo en CargarFiltros.py: {arreglo}')
    res = []
    for registro in arreglo:
        if registro['_id'] != {}:
            if filtros.agrupador == 'mes' or filtros.agrupador == 'dia':
                anio = registro['_id']['anio']
                mes = registro['_id']['mes']
                label = mesTexto(mes) + ' ' + str(anio)
                value = {
                    'anio': anio,
                    'mes': mes
                }
                if filtros.agrupador == 'dia':
                    dia = registro['_id']['dia']
                    label = str(dia) + ' ' + label
                    value['dia'] = dia
            elif filtros.agrupador == 'semana':
                label = registro['_id']['semana_descrip']
                value = {'semana': registro['_id']['semana']}
            objeto = {
                'label': label,
                'value': value
            }
            res.append(objeto)
    # print(f'periodos desde cargarPeriodo.py: {str(res)}')
    # print(f"Lo que se regresa desde CargarFiltros -> CargarPeriodo es: {str(res)}")
    return res

@router.get("/cargarFormato")
async def cargar_formato(user: dict = Depends(get_current_active_user)):
    collection = conexion_mongo('report').catTienda
    pipeline = [
        {'$match': {
            'FORMATO_NOMBRE': {
                '$ne': 'N/A'
            }
        }},
        {'$group': {
            '_id': {
                'label': '$FORMATO_NOMBRE',
                'value': '$FORMATO'
            }
        }},
        {'$sort': {
            '_id.label': 1
        }}
    ]
    cursor = collection.aggregate(pipeline)
    arreglo = await cursor.to_list(length=None)
    res = []
    for row in arreglo:
        res.append({
            'label': row['_id']['label'],
            'value': row['_id']['value']
        })
    return res

@router.get("/cargarNps")
async def cargar_nps(user: dict = Depends(get_current_active_user)):
    query = """select descripcion, orden
    from DWH.limesurvey.nps_cat_preguntas 
    where tipo_respuesta = 'R1'
    and flujo = 'F1'
    order by orden"""
    cnxn = conexion_sql('DWH')
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    res = []
    for row in resultados:
        res.append({
            'label': row['descripcion'],
            'value': row['descripcion']
        })
    return res

@router.get("/nombreTienda")
async def nombre_tienda(tienda: int, user: dict = Depends(get_current_active_user)):
    collection = conexion_mongo('report').catTienda
    pipeline = [
        {'$match': {
            'TIENDA': tienda
        }}
    ]
    cursor = collection.aggregate(pipeline)
    arreglo = await cursor.to_list(length=None)
    # print(str(arreglo))
    res = {'nombreTienda': arreglo[0]['Tiendas_nombre']}
    return res

@router.get("/numeroTienda")
async def numero_tienda(nombreTienda: str, user: dict = Depends(get_current_active_user)):
    collection = conexion_mongo('report').catTienda
    pipeline = [
        {'$match': {
            'Tiendas_nombre': nombreTienda
        }}
    ]
    # print(f"pipeline desde CargarFiltros -> numeroTienda: {pipeline}")
    cursor = collection.aggregate(pipeline)
    arreglo = await cursor.to_list(length=None)
    # print(str(arreglo))
    res = {'numeroTienda': arreglo[0]['TIENDA']}
    return res

@router.get("/getRegionYZona")
async def get_region_y_zona(idTienda: int):
    # print("Se entró a get_region_y_zona")
    collection = conexion_mongo('report').catTienda
    pipeline = [
        {'$match': {
            'TIENDA': idTienda
        }}
    ]
    # print(f"pipeline desde CargarFiltros -> getRegionYZona: {pipeline}")
    cursor = collection.aggregate(pipeline)
    arreglo = await cursor.to_list(length=None)
    # print(str(arreglo))
    res = {'region': {'value': arreglo[0]['REGION'], 'label': arreglo[0]['REGION_NOMBRE']}, 'zona': {'value': arreglo[0]['ZONA'], 'label': arreglo[0]['ZONA_NOMBRE']}}
    # print("Se va a mandar respuesta desde get_region_y_zona")
    return res

@router.get("/cargarDeptoAgrupado")
async def cargar_depto_agrupado(grupoDeptos: str, user: dict = Depends(get_current_active_user)):
    query = f"""select distinct departamento 
    from DWH.report.catalogoUXConsolidado 
    where grupo='{grupoDeptos}'"""
    cnxn = conexion_sql('DWH')
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    res = []
    for row in resultados:
        res.append({
            'label': row['departamento'],
            'value': row['departamento']
        })
    return res

@router.get("/cargarSubDeptoAgrupado")
async def cargar_subdepto_agrupado(deptoAgrupado: str, user: dict = Depends(get_current_active_user)):
    query = f"""select distinct Subdepartamento 
    from DWH.report.catalogoUXConsolidado 
    where departamento='{deptoAgrupado}'"""
    cnxn = conexion_sql('DWH')
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    res = []
    for row in resultados:
        res.append({
            'label': row['Subdepartamento'],
            'value': row['Subdepartamento']
        })
    return res

@router.get("/cargarCanal")
async def cargar_subdepto_agrupado(user: dict = Depends(get_current_active_user)):
    query = f"""select distinct descripTipo, tipo 
    from DWH.artus.catCanal
    where descripTipo not in ('Tienda Fisica')
    order by descripTipo"""
    cnxn = conexion_sql('DWH')
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    res = []
    for row in resultados:
        res.append({
            'label': row['descripTipo'],
            'value': row['tipo']
        })
    return res
