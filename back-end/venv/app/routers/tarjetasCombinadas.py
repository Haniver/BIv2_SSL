from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import date, datetime, timedelta
from calendar import monthrange
from app.servicios.formatoFechas import mesTexto
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/tarjetasCombinadas",
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class TarjetasCombinadas():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if filtros.canal != '' and filtros.canal != "False" and filtros.canal != None:
            self.canal = filtros.canal
        else:
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute("select distinct tipo from DWH.artus.catCanal where descripTipo not in ('Tienda Fisica')")
            arreglo = crear_diccionario(cursor)
            self.canal = ",".join([str(elemento['tipo']) for elemento in arreglo])
        self.anioElegido = datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').year
        self.mesElegido = datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').month
        self.diaElegido = datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ').day
        self.mesTexto = mesTexto(self.mesElegido)

        self.anioElegido_inicio = datetime(self.anioElegido, 1, 1).strftime('%Y%m%d')
        self.anioElegido_fin = datetime(self.anioElegido, self.mesElegido, self.diaElegido).strftime('%Y%m%d')
        self.anioAnterior_inicio = datetime(self.anioElegido - 1, 1, 1).strftime('%Y%m%d')
        self.anioAnterior_fin = datetime(self.anioElegido - 1, self.mesElegido, self.diaElegido).strftime('%Y%m%d')
        self.mesElegido_inicio = datetime(self.anioElegido, self.mesElegido, 1).strftime('%Y%m%d')
        self.mesElegido_fin = datetime(self.anioElegido, self.mesElegido, self.diaElegido).strftime('%Y%m%d')
        self.mesAnterior_inicio = datetime(self.anioElegido - 1, self.mesElegido, 1).strftime('%Y%m%d')
        self.mesAnterior_fin = datetime(self.anioElegido - 1, self.mesElegido, self.diaElegido).strftime('%Y%m%d')


    async def VentaSinImpuesto(self):

        if self.titulo == 'Mes':
            query_filtro_fechas = f""" and dt.anio in ({self.anioElegido},{self.anioElegido - 1})
            and dt.abrev_mes='{self.mesTexto}' """
        elif self.titulo == 'Anio':
            query_filtro_fechas = f""" and (dt.id_fecha BETWEEN {self.anioElegido_inicio} and {self.anioElegido_fin} or dt.id_fecha BETWEEN {self.anioAnterior_inicio} and {self.anioAnterior_fin}) """
        elif self.titulo == 'MesAlDia':
            query_filtro_fechas = f"""and dt.anio in ({self.anioElegido}, {self.anioElegido - 1}) and dt.num_mes = {self.mesElegido}"""
        if self.titulo == 'MesAlDia':
            query = f"""select dt.anio, sum(ventaSinImpuestos) venta, sum(objetivo) objetivo,
            sum(case when anio={self.anioElegido} and dt.fecha <= '{self.anioElegido}-{self.mesElegido}-{self.diaElegido}' then objetivo else 0 end) objetivoDia,
            sum(case when DAY(dt.fecha) <= {self.diaElegido} then ventaSinImpuestos else 0 end) ventaDia
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

        print(f"Query para {self.titulo}:\n{query}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        # if self.titulo == 'MesAlDia':
            # print(f'Query MesAlDia en TarjetasCombinadas: {str(query)}')
        # print(str(arreglo))

        if len(arreglo) <= 0:
            hayResultados = "no"
            res = '--'
        else:
            hayResultados = "si"
            if len(arreglo) >= 2:
                venta_pasado = arreglo[0]['venta']
                venta_actual = arreglo[1]['venta']
                objetivo = arreglo[1]['objetivo']
            elif len(arreglo) == 1:
                venta_pasado = 0
                venta_actual = arreglo[0]['venta']
                objetivo = arreglo[0]['objetivo']
            dias_en_mes = monthrange(self.anioElegido, self.mesElegido)[1]
            proyeccion_actual = dias_en_mes*venta_actual/self.diaElegido
            avance_actual = venta_actual/objetivo if objetivo != 0 else '--'
            alcance_actual = proyeccion_actual/objetivo - 1 if objetivo != 0 else '--'
            res = {}
            if self.titulo == 'Anio':
                res['Venta $anio'] = venta_actual
                res['Venta $anioPasado al $dia de $mes'] = venta_pasado
                res['Objetivo $anioActual al $dia de $mes'] = objetivo
                res['Variación $anioActual vs. $anioAnterior'] = (venta_actual/venta_pasado) - 1 if venta_pasado != 0 else '--'
                res['Variación Objetivo $anioActual'] = (venta_actual / objetivo) - 1 if objetivo != 0 else '--'
            elif self.titulo == 'Mes':
                res['Venta $mes $anio'] = venta_actual
                res['Objetivo $mes $anio'] = objetivo
                res['Proyección $mes $anio'] = proyeccion_actual
                res['Avance $mes $anio'] = avance_actual
                res['Alcance $mes $anio'] = alcance_actual
            elif self.titulo == 'MesAlDia':
                if len(arreglo) >= 2:
                    objetivoDia = arreglo[1]['objetivoDia']
                    ventaDiaActual = arreglo[1]['ventaDia']
                    ventaDiaAnterior = arreglo[0]['ventaDia']
                else:
                    objetivoDia = arreglo[0]['objetivoDia']
                    ventaDiaActual = arreglo[0]['ventaDia']
                    ventaDiaAnterior = 0
                res['Venta 1 al $dia $mes $anioActual'] = ventaDiaActual
                res['Objetivo 1 al $dia $mes $anio'] = objetivoDia
                res['Objetivo Vs. Venta al $dia $mes $anio'] = float(ventaDiaActual)/float(objetivoDia) - 1 if objetivoDia != 0 else '--'
                res['Venta 1 al $dia $mes $anioAnterior'] = ventaDiaAnterior
                res['Venta $anioAnterior Vs. $anioActual al $dia $mes'] = (ventaDiaActual/ventaDiaAnterior) - 1 if ventaDiaAnterior != 0 else '--'

        # print(f'Respuesta desde TarjetasCombinadas: {res}')
        return {'hayResultados':hayResultados, 'pipeline':query, 'res':res}

    async def FoundRate(self):
        self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
        self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
        collection = conexion_mongo('report').report_foundRate
        pipeline = [{'$unwind': '$sucursal'}]
        pipeline.append({'$match': {'sucursal.tienda': int(self.filtros.tienda)}})
        pipeline.append({'$match': {'fechaUltimoCambio': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}})
        pipeline.append({'$group':{'_id':'$sucursal.tienda', 'monto_ini': {'$sum': '$monto_ini'}, 'monto_fin': {'$sum': '$monto_fin'}}})
        cursor = collection.aggregate(pipeline)
        arreglo = await cursor.to_list(length=1000)
        res = {}
        if len(arreglo) >0:
            hayResultados = "si"
            for row in arreglo:
                monto_ini = float(row['monto_ini'])
                monto_fin = float(row['monto_fin'])
                res['Monto Original'] = monto_ini
                res['Monto Final'] = monto_fin
                res['% Variación'] = (monto_fin/monto_ini)-1
        else:
            hayResultados = 'no'

        # print(f'Respuesta desde TarjetasCombinadas: {res}')
        return {'hayResultados':hayResultados, 'pipeline':pipeline, 'res':res}
        return {'hayResultados':'no', 'pipeline':'', 'res':''}

@router.post("/{seccion}")
async def tarjetas_combinadas (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id, seccion):
        objeto = TarjetasCombinadas(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}  

