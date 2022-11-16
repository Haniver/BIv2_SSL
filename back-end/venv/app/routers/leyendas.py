from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import date, datetime, timedelta
from calendar import monthrange
from app.servicios.permisos import tienePermiso

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
            print(f"Query desde leyendas -> PedidoPerfecto: {query}")
            cnxn = conexion_sql('DWH')
            cursor = cnxn.cursor().execute(query)
            arreglo = crear_diccionario(cursor)
            # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
            if len(arreglo) > 0:
                hayResultados = "si"
                res = arreglo[0]['ultima_actualizacion'].strftime("%d/%m/%Y %H:%M")
        else:
            print(f"No entró a nada porque el título es: '{self.titulo}'")
        return {'hayResultados':hayResultados, 'res': res, 'pipeline': query}

@router.get("/{seccion}")
async def leyendas (titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    # print("El usuario desde tarjetas .py es: {str(user)}")
    if tienePermiso(user.id, seccion):
        objeto = Leyendas(titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}        

