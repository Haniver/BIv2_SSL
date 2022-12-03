from fastapi import APIRouter, Depends, HTTPException, Request, Request

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import date, datetime, timedelta
from calendar import monthrange
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError
import traceback
from inspect import stack

router = APIRouter(
    prefix="/leyendas",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Leyendas():
    def __init__(self, titulo: str):
        self.titulo = titulo

    async def PedidoPerfecto(self):
        hayResultados = 'no'
        res = []
        query = []
        if self.titulo == 'Última actualización:':
            query = f"""select max(ultimo_cambio) as ultima_actualizacion from DWH.dbo.hecho_order"""
            # print(f"Query desde leyendas -> PedidoPerfecto: {query}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                res = arreglo[0]['ultima_actualizacion'].strftime("%d/%m/%Y %H:%M")
        return {'hayResultados':hayResultados, 'res': res, 'pipeline': query}

    async def PedidosPendientes(self):
        hayResultados = 'no'
        res = []
        query = []
        if self.titulo == 'Última actualización:':
            collection = conexion_mongo('report').report_pedidoPendientes
            pipeline = [
                {'$sort': {'fechaUpdate': -1}},
                {'$group': {'_id': None, 'ultima_actualizacion': {'$first': "$fechaUpdate"}}}
            ]
            # print(f"Query desde leyendas -> PedidosPendientes: {pipeline}")
            cursor = collection.aggregate(pipeline)
            arreglo = await cursor.to_list(length=1000)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                menos_dos = arreglo[0]['ultima_actualizacion'] - timedelta(hours=6)
                res = menos_dos.strftime("%d/%m/%Y %H:%M")
        return {'hayResultados':hayResultados, 'res': res, 'pipeline': query}

@router.get("/{seccion}")
async def leyendas (titulo: str, seccion: str, request: Request, user: dict = Depends(get_current_active_user)):
    # print("El usuario desde tarjetas .py es: {str(user)}")
    # print(f"Filtros desde leyendas: {str(filtros)}")
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, ip=request.client.host)
    if tienePermiso(user.id, seccion):
        try:
            objeto = Leyendas(titulo)
            funcion = getattr(objeto, seccion)
            diccionario = await funcion()
        except:
            error = traceback.format_exc()
            loguearError(stack()[0][3], user.usuario, seccion, titulo, error, ip=request.client.host)
            return {'hayResultados':'error'}
        return diccionario

    else:
        return {"message": "No tienes permiso para acceder a este recurso."}        

