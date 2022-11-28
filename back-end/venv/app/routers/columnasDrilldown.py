from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack

router = APIRouter(
    prefix="/columnasDrilldown",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class ColumnasDrilldown():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def VentaOmnicanal(self):
        nivel_lugar = ''
        filtro_lugar = False
        lugar = ''
        pipeline = []
        res = 'No se entró a ninguna opción'
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel_lugar = 'tienda'
                    lugar = int(self.filtros.tienda)
                else:
                    nivel_lugar = 'zona'
                    lugar = int(self.filtros.zona)
            else:
                nivel_lugar = 'region'
                lugar = int(self.filtros.region)
        else:
            filtro_lugar = False
        if self.filtros.proveedor != '' and self.filtros.proveedor != 0 and self.filtros.proveedor != True and self.filtros.proveedor != 'True' and self.filtros.proveedor != None:
            filtro_proveedor = True
            proveedor = self.filtros.proveedor
        else:
            filtro_proveedor = False

        if filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ nivel_lugar: lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}, {'$unwind': '$articulo'}])

        if self.titulo == 'Monto de Venta por Departamento':
            collection = conexion_mongo('report').report_mktArtusDiarioDepto
            pipeline.extend([{'$group': {'_id': {'subLabel': '$articulo.subDeptoNombre', 'codigo': '$articulo.depto', 'label': '$articulo.deptoNombre'}, 'monto': {'$sum': {'$add': ['$ventaWeb','$ventaAppMovil','$ventaCallCenter']}}}}])
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                # res = arreglo
       
        # Para que esto jale, cada nodo debe tener un ['_id']['codigo'], ['_id']['label'], ['_id']['subLabel'] y ['_id']['monto']. Espero que todos los casos de barras drilldown puedan cumplir con este formato. No te preocupes si el dashboard no es de Deptos y SubDeptos; el principio es el mismo y jala igual.
        class Nodo:
            def __init__(self):
                self.codigo = None
                self.nombre = ""
                self.monto = 0
                self.hijos = []
            def addHijo(self, hijo):
                self.hijos.append(hijo)

        def buscar_depto(arbol, codigo):
            for nodo in arbol:
                if nodo.codigo == codigo:
                    return nodo
            return "No encontrado"

        arbol = []

        for registro in arreglo:
            codigo = registro['_id']['codigo']
            depto_existente = buscar_depto(arbol, codigo)
            if depto_existente != "No encontrado":
                nodo_depto = depto_existente
                nodo_depto.monto += float(registro['monto'])
            else:
                nodo_depto = Nodo()
                nodo_depto.codigo = codigo
                nodo_depto.nombre = registro['_id']['label']
                nodo_depto.monto = int(registro['monto'])
                arbol.append(nodo_depto)
            nodo_subdepto = Nodo()
            nodo_subdepto.nombre = registro['_id']['subLabel']
            nodo_subdepto.monto = registro['monto']
            nodo_depto.addHijo(nodo_subdepto)

        drilldown_series = []
        lista_deptos = []
        for depto in arbol:
            depto_data = []
            for subDepto in depto.hijos:
                arr_subdepto = []
                arr_subdepto.append(subDepto.nombre)
                arr_subdepto.append(round((float(subDepto.monto)), 2))
                depto_data.append(arr_subdepto)
            drilldown_series.append({
                'name': depto.nombre,
                'id': depto.codigo,
                'data': depto_data
            })
            lista_deptos.append({
                'name': depto.nombre,
                'y': round(float(depto.monto), 2),
                'drilldown': depto.codigo   
            })
        series_outer = [{
            'name': 'Departamentos',
            'data': lista_deptos
        }]

        res = {'series_outer': series_outer, 'drilldown_series': drilldown_series}

        return {'hayResultados':hayResultados, 'res': res}

    async def VentaOmnicanal2(self):
        nivel_lugar = ''
        filtro_lugar = False
        lugar = ''
        pipeline = []
        res = 'No se entró a ninguna opción'
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    nivel_lugar = 'tienda'
                    lugar = int(self.filtros.tienda)
                else:
                    nivel_lugar = 'zona'
                    lugar = int(self.filtros.zona)
            else:
                nivel_lugar = 'region'
                lugar = int(self.filtros.region)
        else:
            filtro_lugar = False
        if self.filtros.proveedor != '' and self.filtros.proveedor != 0 and self.filtros.proveedor != True and self.filtros.proveedor != 'True' and self.filtros.proveedor != None:
            filtro_proveedor = True
            proveedor = self.filtros.proveedor
        else:
            filtro_proveedor = False

        if filtro_lugar:
            pipeline.extend([{'$unwind': '$sucursal'}, {'$match': {'sucursal.'+ nivel_lugar: lugar}}])
        pipeline.extend([{'$match': {'fecha': {'$gte': self.fecha_ini_a12, '$lt': self.fecha_fin_a12}}}, {'$unwind': '$articulo'}])

        if self.titulo == 'Monto de Venta por Departamento':
            collection = conexion_mongo('report').report_mktProveedores
            if filtro_proveedor:
                pipeline.append({'$match': {'articulo.proveedor': proveedor}})
            pipeline.append({'$group': {'_id': {'subLabel': '$articulo.subdeptoNombre', 'codigo': '$articulo.depto', 'label': '$articulo.deptoNombre'}, 'monto': {'$sum': '$vtaSinImp'}}})
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            if len(arreglo) <= 0:
                hayResultados = "no"
                res = pipeline
            else:
                hayResultados = "si"
                # res = arreglo

        # Para que esto jale, cada nodo debe tener un ['_id']['codigo'], ['_id']['label'], ['_id']['subLabel'] y ['_id']['monto']. Espero que todos los casos de barras drilldown puedan cumplir con este formato. No te preocupes si el dashboard no es de Deptos y SubDeptos; el principio es el mismo y jala igual.
        class Nodo:
            def __init__(self):
                self.codigo = None
                self.nombre = ""
                self.monto = 0
                self.hijos = []
            def addHijo(self, hijo):
                self.hijos.append(hijo)

        def buscar_depto(arbol, codigo):
            for nodo in arbol:
                if nodo.codigo == codigo:
                    return nodo
            return "No encontrado"

        arbol = []

        for registro in arreglo:
            codigo = registro['_id']['codigo']
            depto_existente = buscar_depto(arbol, codigo)
            if depto_existente != "No encontrado":
                nodo_depto = depto_existente
                nodo_depto.monto += float(registro['monto'])
            else:
                nodo_depto = Nodo()
                nodo_depto.codigo = codigo
                nodo_depto.nombre = registro['_id']['label']
                nodo_depto.monto = int(registro['monto'])
                arbol.append(nodo_depto)
            nodo_subdepto = Nodo()
            nodo_subdepto.nombre = registro['_id']['subLabel']
            nodo_subdepto.monto = registro['monto']
            nodo_depto.addHijo(nodo_subdepto)

        drilldown_series = []
        lista_deptos = []
        for depto in arbol:
            depto_data = []
            for subDepto in depto.hijos:
                arr_subdepto = []
                arr_subdepto.append(subDepto.nombre)
                arr_subdepto.append(round(float(subDepto.monto), 2))
                depto_data.append(arr_subdepto)
            drilldown_series.append({
                'name': depto.nombre,
                'id': depto.codigo,
                'data': depto_data
            })
            lista_deptos.append({
                'name': depto.nombre,
                'y': round(float(depto.monto), 2),
                'drilldown': depto.codigo   
            })
        series_outer = [{
            'name': 'Departamentos',
            'data': lista_deptos
        }]

        res = {'series_outer': series_outer, 'drilldown_series': drilldown_series}

        return {'hayResultados':hayResultados, 'res': res}

@router.post("/{seccion}")
async def columnas_drilldown (filtros: Filtro, titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = ColumnasDrilldown(filtros, titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, filtros, request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}

