from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import date, datetime
from calendar import monthrange
from copy import deepcopy

router = APIRouter(
    prefix="/dashboards/VentaSinImpuesto",
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def venta_sin_impuestos (filtros: Filtro, seccion: str):

    anio_actual = datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year
    anio_anterior = anio_actual - 1
    if filtros.canal != '' and filtros.canal != "False" and filtros.canal != None:
        canal = filtros.canal
    else:
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute("select distinct tipo from DWH.artus.catCanal where descripTipo not in ('Tienda Fisica')")
        arreglo = crear_diccionario(cursor)
        canal = ",".join([str(elemento['tipo']) for elemento in arreglo])
    meses_txt = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    mes_actual = datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month

    cnxn = conexion_sql('DWH')
    cursor = cnxn.cursor()
    
    query = f"select cd.deptoDescrip, sum(case when anio={anio_anterior} and dt.fecha < convert(date,DATEADD(yy,-1,(GETDATE()))) then isnull (ventaSinImpuestos, 0) else 0 end) AAnterior, sum(case when anio={anio_actual} then isnull (ventaSinImpuestos, 0) else 0 end) AActual, sum(case when anio={anio_actual} then objetivo else 0 end) Objetivo from DWH.artus.ventaDiaria vd left join DWH.dbo.dim_tiempo dt on vd.fecha=dt.id_fecha left join DWH.artus.cat_departamento cd on vd.subDepto=cd.idSubDepto left join DWH.dbo.dim_store st on st.idtienda = vd.idTienda left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal where dt.anio in ({anio_anterior},{anio_actual}) and cc.tipo in ({canal}) and dt.num_mes in({mes_actual}) "
    query += " and st.region = '{}' ".format(filtros.region) if filtros.region != '' and filtros.region != "False" and filtros.region != None else ''
    query += " and st.zona = '{}' ".format(filtros.zona) if filtros.zona != '' and filtros.zona != "False" and filtros.zona != None else ''
    query += " and st.descrip_tienda = '{}' ".format(filtros.tienda) if filtros.tienda != '' and filtros.tienda != "False" and filtros.tienda != None else ''
    query += " group by cd.deptoDescrip "

    cursor.execute(query)
    # rows = cursor.fetchall()
    # for row in rows:

    pipeline = []
    canales = []
    res = {}
    # Crear un arreglo con los canales seleccionados o disponibles
    pipelineB = [{'$match':{'nombreColumna': {'$nin': [None]}}}, {'$match':{'tipo': {'$nin': [0]}}}] # Excluimos la tienda física o los registros que no tengan canal
    if filtros.canal != '' and filtros.canal != "False" and filtros.canal != None:
        pipelineB.append({'$match':{'tipo':int(filtros.canal)}})
    pipelineB.append({'$group':{'_id':'$nombreColumna'}})
    # print(pipelineB)
    collectionB = conexion_mongo('report').catCanal
    cursorB = collectionB.aggregate(pipelineB)
    arregloB = await cursorB.to_list(length=100)
    for fila in arregloB:
        canales.append(fila['_id'])
    pipeline = []
    if filtro_lugar:
        pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ nivel_lugar: lugar}}])
    if filtros.depto != '' and filtros.depto != "False" and filtros.depto != None:
        pipeline.append({'$unwind':'$producto'})
        if filtros.subDepto != '' and filtros.subDepto != "False" and filtros.subDepto != None:
            pipeline.append({'$match':{'producto.subDepto': filtros.subDepto}})
        else:
            pipeline.append({'$match':{'producto.idDepto': filtros.depto}})
    pipeline.append({'$unwind': '$kpi'})

    # El pipeline va a terminar con un facet que tiene la respuesta para cada tarjeta:
    facet = {'$facet':{'anio actual': [], 'anio pasado':[], 'mes actual': [], 'mes pasado': []}}

    # Cada elemento del facet va a tener un filtro de fecha
    fecha_actual = datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ')
    anio_pasado_al_dia_actual = datetime(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
    inicio_anio_pasado = datetime(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, 1, 1)
    inicio_anio_actual = datetime(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, 1, 1)
    inicio_mes_actual = datetime(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year, datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
    inicio_mes_pasado = datetime(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, 1)
    mes_pasado_al_dia_actual = datetime(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year - 1, datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month, datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day)
    match_anio_actual = {'$match': {'fecha': {'$gte': 0, '$lte': 0}}} # Inicializar fechas a 0
    match_anio_pasado = deepcopy(match_anio_actual) # Crear copia
    match_mes_actual = deepcopy(match_anio_actual) # Crear copia
    match_mes_pasado = deepcopy(match_anio_actual) # Crear copia
    match_anio_actual['$match']['fecha']['$gte'] = inicio_anio_actual
    match_anio_actual['$match']['fecha']['$lte'] = fecha_actual
    match_anio_pasado['$match']['fecha']['$gte'] = inicio_anio_pasado
    match_anio_pasado['$match']['fecha']['$lte'] = anio_pasado_al_dia_actual
    match_mes_actual['$match']['fecha']['$gte'] = inicio_mes_actual
    match_mes_actual['$match']['fecha']['$lte'] = fecha_actual
    match_mes_pasado['$match']['fecha']['$gte'] = inicio_mes_pasado
    match_mes_pasado['$match']['fecha']['$lte'] = mes_pasado_al_dia_actual
    facet['$facet']['anio actual'].append(match_anio_actual)
    facet['$facet']['anio pasado'].append(match_anio_pasado)
    facet['$facet']['mes actual'].append(match_mes_actual)
    facet['$facet']['mes pasado'].append(match_mes_pasado)

    # Después del filtro de fecha de arriba, a cada facet se le agrega la suma de cada canal y el objetivo.
    # Aquí dividimos en más facets, porque para las tarjetas el _id es 0, mientras que para las gráficas es variable.
    group_sin_canales = {'_id':0, 'objetivo': {'$sum': '$kpi.objetivoTO'}}
    for canal in canales:
        group_sin_canales[canal] = {'$sum': '$kpi.'+canal}
    group_cero = {'$group': group_sin_canales}
    group_mes = deepcopy(group_cero)
    group_dia = deepcopy(group_cero)
    group_zona = deepcopy(group_cero)
    group_mes['$group']['_id'] = {'$month':'$fecha'}
    group_dia['$group']['_id'] = {'$dayOfMonth':'$fecha'}
    group_zona['$group']['_id'] = {'$sucursal.'+nombre_lugar}
    facet['$facet']['anio actual'].append({'$facet':{'cero':[group_cero], 'mes':[group_mes], 'zona':[group_zona]}})
    facet['$facet']['anio pasado'].append({'$facet':{'cero':[group_cero], 'mes':[group_mes], 'zona':[group_zona]}})
    facet['$facet']['mes actual'].append({'$facet':{'cero':[group_cero], 'dia':[group_dia], 'zona':[group_zona]}})
    facet['$facet']['mes pasado'].append({'$facet':{'cero':[group_cero], 'dia':[group_dia], 'zona':[group_zona]}})

    # Esa suma de cada canal la condensamos en la suma total de todos los canales ($add suma varios campos en uno):
    canales = ['$'+canal for canal in canales]
    project_suma_canales = {'$project': {'venta':{'$add': canales}, 'objetivo': '$objetivo'}}
    facet['$facet']['anio actual'][1]['$facet']['cero'].append(project_suma_canales)
    facet['$facet']['anio pasado'][1]['$facet']['cero'].append(project_suma_canales)
    facet['$facet']['mes actual'][1]['$facet']['cero'].append(project_suma_canales)
    facet['$facet']['mes pasado'][1]['$facet']['cero'].append(project_suma_canales)
    facet['$facet']['anio actual'][1]['$facet']['zona'].append(project_suma_canales)
    facet['$facet']['anio pasado'][1]['$facet']['zona'].append(project_suma_canales)
    facet['$facet']['mes actual'][1]['$facet']['zona'].append(project_suma_canales)
    facet['$facet']['mes pasado'][1]['$facet']['zona'].append(project_suma_canales)
    facet['$facet']['anio actual'][1]['$facet']['mes'].append(project_suma_canales)
    facet['$facet']['anio pasado'][1]['$facet']['mes'].append(project_suma_canales)
    facet['$facet']['mes actual'][1]['$facet']['dia'].append(project_suma_canales)
    facet['$facet']['mes pasado'][1]['$facet']['dia'].append(project_suma_canales)

    # Y finalmente ponemos en el pipeline un facet con todas sus ramificaciones:
    pipeline.append(facet)

    # Para debuggear
    # print(pipeline)

    # Ejecución del query
    # collection = conexion_mongo('report').report_ventaDiaria
    # cursor = collection.aggregate(pipeline)
    # arreglo = await cursor.to_list(length=5000)
    # print("Creó el arreglo")

    # if len(arreglo) > 0:
    #     hayResultados = "si"
    #     venta_anio_actual = arreglo[0]['anio actual'][0]['venta']
    #     venta_anio_pasado = arreglo[0]['anio pasado'][0]['venta']
    #     objetivo_anio_actual = arreglo[0]['anio actual'][0]['objetivo']
    #     objetivo_anio_pasado = arreglo[0]['anio pasado'][0]['objetivo']
    #     venta_mes_actual = arreglo[0]['mes actual'][0]['venta']
    #     objetivo_mes_actual = arreglo[0]['mes actual'][0]['objetivo']
    #     dias_en_mes = monthrange(fecha_actual.year, fecha_actual.month)[1]
    #     dia_del_mes = fecha_actual.day
    #     proyeccion_mes_actual = dias_en_mes*venta_mes_actual/dia_del_mes
    #     avance_mes_actual = venta_mes_actual/objetivo_mes_actual if objetivo_mes_actual != 0 else '--'
    #     alcance_mes_actual = proyeccion_mes_actual/objetivo_mes_actual - 1 if objetivo_mes_actual != 0 else '--'

    #     res['Venta $anio'] = venta_anio_actual
    #     res['Venta $anioPasado al $dia de $mes'] = venta_anio_pasado
    #     res['Objetivo $anioActual al $dia de $mes'] = objetivo_anio_actual
    #     res['Variación $anioActual vs. $anioAnterior'] = (venta_anio_actual/venta_anio_pasado) - 1 if venta_anio_pasado != 0 else '--'
    #     res['Variación Objetivo $anioActual'] = (objetivo_anio_actual / objetivo_anio_pasado) - 1 if objetivo_anio_pasado != 0 else '--'
    #     res['Venta $mes $anio'] = venta_mes_actual
    #     res['Objetivo $mes $anio'] = objetivo_mes_actual
    #     res['Proyección $mes $anio'] = proyeccion_mes_actual
    #     res['Avance $mes $anio'] = avance_mes_actual
    #     res['Alcance $mes $anio'] = alcance_mes_actual
    # else:
    #     hayResultados = "no"
    #     res = '--'
    # hayResultados = 'si'

    # respuesta para producción
    # return {'hayResultados':hayResultados, 'pipeline':pipeline, 'res':res}

    # Respuesta para debuggear
    return {'hayResultados':'no', 'pipeline':pipeline, 'res':[]}