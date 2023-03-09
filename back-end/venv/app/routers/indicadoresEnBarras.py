# Regresa un arreglo de diccionarios con:
# titulo: el título de la sección
# formatoBarras: El formato del valor de las barras (moneda, entero, etc.)
# data: Un arreglo que contiene diccionarios con cada uno de los indicadores en la sección, ya sean barras o los indicadores que aparecen a un lado de las barras. Cada diccionario contiene:
  # titulo: La etiqueta de la barra
  # valor: El valor numérico del indicador
  # posicion: 'barra' o 'lado', dependiendo de cómo se muestre el indicador
  # color: El color de la barra o texto (en el caso de que el indicador esté a un lado)
  # formato: Solo para indicadores a un lado, indica el formato (moneda, porcentaje, entero, etc.)

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import date, datetime, timedelta, time
from calendar import monthrange
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack
from app.servicios.formatoFechas import mesTexto, ultimoDiaVencidoDelMesReal

router = APIRouter(
    prefix="/indicadoresEnBarras",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class IndicadoresEnBarras():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    self.nivel_lugar = 'tienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    self.nivel_lugar = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                self.nivel_lugar = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False
        ###############
        if filtros.canal != '' and filtros.canal != "False" and filtros.canal != None:
            self.canal = filtros.canal
        else:
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute("select distinct tipo from DWH.artus.catCanal where descripTipo not in ('Tienda Fisica')")
            arreglo = crear_diccionario(cursor)
            self.canal = ",".join([str(elemento['tipo']) for elemento in arreglo])
    
    async def VentaSinImpuesto(self):
        anioElegido = self.filtros.anio
        mesElegido = self.filtros.mes + 1
        # print(f"Mes elegido: {mesElegido}")
        ayer = date.today() - timedelta(days=1)
        if mesElegido == ayer.month and anioElegido == ayer.year:
            diaElegido = diaElegido = ayer.day
        else:
            last_day = date(anioElegido, mesElegido, 1).replace(
            month=mesElegido % 12 + 1, day=1) - timedelta(days=1)
            diaElegido = last_day.day
        mesEnTexto = mesTexto(mesElegido)

        anioElegido_inicio = datetime(anioElegido, 1, 1).strftime('%Y%m%d')
        # Get the last day of the given month
        last_day = date(int(anioElegido), int(mesElegido), 1).replace(month=mesElegido % 12 + 1, day=1) - timedelta(days=1)

        # Get the last second of the last minute of the last hour of the last day
        mesElegido_fin = datetime.combine(
            last_day, time.max).replace(
            hour=23, minute=59, second=59)

        self.ayer = datetime(anioElegido, mesElegido, diaElegido).strftime('%Y%m%d')
        anioElegido_fin = datetime(anioElegido, 12, 31).strftime('%Y%m%d')
        self.anioAnterior_inicio = datetime(anioElegido - 1, 1, 1).strftime('%Y%m%d')
        self.anioAnterior_fin = datetime(anioElegido - 1, mesElegido, diaElegido).strftime('%Y%m%d')
        mesElegido_inicio = datetime(anioElegido, mesElegido, 1).strftime('%Y%m%d')
        mesElegido_fin = datetime(anioElegido, mesElegido, diaElegido).strftime('%Y%m%d')
        self.mesAnterior_inicio = datetime(anioElegido - 1, mesElegido, 1).strftime('%Y%m%d')
        self.mesAnterior_fin = datetime(anioElegido - 1, mesElegido, diaElegido).strftime('%Y%m%d')
        res = []
        res_tmp = {}
        for variante in ['Mes', 'Anio', 'MesAlDia']:
            if variante == 'Mes':
                query_filtro_fechas = f""" and dt.anio in ({anioElegido},{anioElegido - 1})
                and dt.abrev_mes='{mesEnTexto}' """
            elif variante == 'Anio':
                query_filtro_fechas = f""" and (dt.id_fecha BETWEEN {anioElegido_inicio} and {self.ayer} or dt.id_fecha BETWEEN {self.anioAnterior_inicio} and {self.anioAnterior_fin}) """
            elif variante == 'MesAlDia':
                query_filtro_fechas = f"""and dt.anio in ({anioElegido}, {anioElegido - 1}) and dt.num_mes = {mesElegido}"""
            if variante == 'MesAlDia':
                query = f"""select dt.anio, sum(ventaSinImpuestos) venta, sum(objetivo) objetivo,
                sum(case when anio={anioElegido} and dt.fecha <= '{anioElegido}-{mesElegido}-{diaElegido}' then objetivo else 0 end) objetivoDia,
                sum(case when DAY(dt.fecha) <= {diaElegido} then isnull (ventaSinImpuestos, 0) else 0 end) ventaDia
                from DWH.artus.ventaDiaria vd
                left join DWH.dbo.dim_tiempo dt on vd.fecha =dt.id_fecha
                left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
                left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
                left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
                where cc.tipo in ({self.canal}) {query_filtro_fechas}
                """
            else:
                query = f"""select dt.anio, sum(ventaSinImpuestos) venta, sum(objetivo) objetivo
                from DWH.artus.ventaDiaria vd
                left join DWH.dbo.dim_tiempo dt on vd.fecha =dt.id_fecha
                left join DWH.artus.catTienda ct on vd.idTienda =ct.tienda
                left join DWH.artus.cat_departamento cd on vd.subDepto = cd.idSubDepto
                left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal
                where cc.tipo in ({self.canal}) {query_filtro_fechas} """
            if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
                if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                    if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                        query += f""" and ct.tienda = {self.filtros.tienda} """
                    else:
                        query += f""" and ct.zona = {self.filtros.zona} """
                else:
                    query += f""" and ct.region = {self.filtros.region} """
            if self.filtros.depto != '' and self.filtros.depto != "False" and self.filtros.depto != None:
                if self.filtros.subDepto != '' and self.filtros.subDepto != "False" and self.filtros.subDepto != None:
                    query += f""" and cd.idSubDepto = {self.filtros.subDepto} """
                else:
                    query += f""" and cd.idDepto = {self.filtros.depto} """
            query += " group by dt.anio order by dt.anio "

            # print(f"-- Query para {variante} en IndicadoresEnBarra:\n{query}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # if variante == 'MesAlDia':
                # print(f'Query MesAlDia en TarjetasCombinadas: {str(query)}')
            # print(str(arreglo))

            if len(arreglo) >= 2:
                venta_pasado = arreglo[0]['venta'] if arreglo[0]['venta'] is not None else 0
                venta_actual = arreglo[1]['venta'] if arreglo[1]['venta'] is not None else 0
                objetivo = arreglo[1]['objetivo'] if arreglo[1]['objetivo'] is not None else 0
            elif len(arreglo) == 1:
                venta_pasado = 0
                venta_actual = arreglo[0]['venta'] if arreglo[0]['venta'] is not None else 0
                objetivo = arreglo[0]['objetivo'] if arreglo[0]['objetivo'] is not None else 0
            else:
                venta_pasado = 0
                venta_actual = 0
                objetivo = 0
            dias_en_mes = monthrange(anioElegido, mesElegido)[1]
            # print(f"****** dias_en_mes: {dias_en_mes}. venta_actual: {venta_actual}. diaElegido: {diaElegido}******")
            proyeccion_actual = dias_en_mes*venta_actual/diaElegido
            avance_actual = venta_actual/objetivo if objetivo != 0 else '--'
            alcance_actual = proyeccion_actual/objetivo - 1 if objetivo != 0 else '--'
            if variante == 'Anio':
                res_tmp['Venta $anio'] = venta_actual
                res_tmp['Venta $anioPasado al $dia de $mes'] = venta_pasado
                res_tmp['Objetivo $anioActual al $dia de $mes'] = objetivo
                res_tmp['Variación $anioActual vs. $anioAnterior'] = (venta_actual/venta_pasado) - 1 if venta_pasado != 0 else '--'
                res_tmp['Variación Objetivo $anioActual'] = (venta_actual / objetivo) - 1 if objetivo != 0 else '--'
            elif variante == 'Mes':
                res_tmp['Venta $mes $anio'] = venta_actual
                res_tmp['Objetivo $mes $anio'] = objetivo
                res_tmp['Proyección $mes $anio'] = proyeccion_actual
                res_tmp['Avance $mes $anio'] = avance_actual
                res_tmp['Alcance $mes $anio'] = alcance_actual
            elif variante == 'MesAlDia':
                if len(arreglo) >= 2:
                    objetivoDia = arreglo[1]['objetivoDia'] if arreglo[1]['objetivoDia'] is not None else 0
                    ventaDiaActual = arreglo[1]['ventaDia'] if arreglo[1]['ventaDia'] is not None else 0
                    ventaDiaAnterior = arreglo[0]['ventaDia'] if arreglo[0]['ventaDia'] is not None else 0
                elif len(arreglo) == 1:
                    objetivoDia = arreglo[0]['objetivoDia'] if arreglo[0]['objetivoDia'] is not None else 0
                    ventaDiaActual = arreglo[0]['ventaDia'] if arreglo[0]['ventaDia'] is not None else 0
                    ventaDiaAnterior = 0
                else:
                    objetivoDia = 0
                    ventaDiaActual = 0
                    ventaDiaAnterior = 0
                res_tmp['Venta 1 al $dia $mes $anioActual'] = ventaDiaActual #Check
                res_tmp['Objetivo 1 al $dia $mes $anio'] = objetivoDia #Check
                res_tmp['Objetivo Vs. Venta al $dia $mes $anio'] = float (ventaDiaActual)/float(objetivoDia) - 1 if objetivoDia != 0 else '--' #Check
                res_tmp['Venta 1 al $dia $mes $anioAnterior'] = ventaDiaAnterior #Check
                res_tmp['Venta $anioAnterior Vs. $anioActual al $dia $mes'] = (ventaDiaActual/ventaDiaAnterior) - 1 if ventaDiaAnterior != 0 else '--'
        # print(f'Respuesta desde TarjetasCombinadas que realmente son tarjetasEnFila: {res_tmp}')
        res = [
            {
                'titulo': f"<b>Anual</b>: {str(anioElegido)} al {str(diaElegido)} de {mesEnTexto}",
                'formatoBarras': 'moneda',
                'barras': [
                    {
                        # 'titulo': f'Venta {anioElegido}',
                        # (1)
                        'titulo': "Canal Propio",
                        'valor': res_tmp['Venta $anio'],
                        'color': 'secondary'
                    },
                    {
                        # 'titulo': f'Objetivo {anioElegido} al {diaVencido} de {mesEnTexto}',
                        # (2)
                        'titulo': "Objetivo (a la fecha)",
                        'valor': res_tmp['Objetivo $anioActual al $dia de $mes'],
                        'color': 'light'
                    },
                    {
                        # 'titulo': f'Venta {anioElegido - 1} al {diaVencido} de {mesEnTexto}',
                        # (3)
                        'titulo': "Año Anterior (a la fecha)",
                        'valor': res_tmp['Venta $anioPasado al $dia de $mes'],
                        'color': 'dark'
                    }
                ],
                'laterales': [
                    {
                        # Parece que esto es Variación vs. Objetivo Anual (el que va solo)
                        # 'titulo': f'Variación Objetivo {anioElegido}',
                        # (4)
                        'titulo': "Variación vs. Objetivo Anual",
                        'valor': res_tmp['Variación Objetivo $anioActual'],
                        'formato': 'porcentaje'
                    },
                    {
                        # 'titulo': f'Variación {anioElegido} vs. {anioElegido - 1}',
                        # (9)
                        'titulo': f'Variación vs. {anioElegido - 1}',
                        'valor': res_tmp['Variación $anioActual vs. $anioAnterior'],
                        'formato': 'porcentaje'
                    },
                ]
            }, {
                'titulo': f"<b>Mensual</b>: {mesEnTexto} {str(anioElegido)}",
                'formatoBarras': 'moneda',
                'barras': [
                    {
                        # 'titulo': f'Venta {mesEnTexto} {anioElegido}',
                        # (5)
                        'titulo': "Canal Propio",
                        'valor': res_tmp['Venta $mes $anio'],
                        'color': 'secondary'
                    },
                    {
                        # 'titulo': f'Objetivo {mesEnTexto} {anioElegido}',
                        # (6)
                        'titulo': f'Objetivo mensual',
                        'valor': res_tmp['Objetivo $mes $anio'],
                        'color': 'light'
                    },
                    {
                        # 'titulo': f'Venta 1 al {diaVencido} {mesEnTexto} {anioElegido - 1}',
                        # (7)
                        'titulo': f'Año Anterior (a la fecha)',
                        'valor': res_tmp['Venta 1 al $dia $mes $anioAnterior'],
                        'color': 'dark'
                    }
                ],
                'laterales': [
                    {
                        # 'titulo': f'Objetivo Vs. Venta al {diaVencido} {mesEnTexto} {anioElegido}',
                        # (8)
                        'titulo': f'Variación vs. Objetivo Mensual',
                        'valor': res_tmp['Objetivo Vs. Venta al $dia $mes $anio'],
                        'formato': 'porcentaje'
                    },
                    {
                        # 'titulo': f'Venta {anioElegido - 1} Vs. {anioElegido} al {diaVencido} {mesEnTexto}',
                        # (10)
                        'titulo': f'Variación vs. {str(anioElegido - 1)}',
                        'valor': res_tmp['Venta $anioAnterior Vs. $anioActual al $dia $mes'],
                        'formato': 'porcentaje'
                    }
                ]
            }
        ]
        return {'res': res, 'pipeline': query}

@router.post("/{seccion}")
async def indicadoresEnBarras (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    # print("El usuario desde tarjetas .py es: {str(user)}")
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = IndicadoresEnBarras(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}        

