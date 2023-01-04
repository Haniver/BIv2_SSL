from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_active_user
from app.servicios.conectar_sql import conexion_sql, crear_diccionario

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, date
from app.servicios.permisos import tienePermiso
from app.servicios.logs import loguearConsulta, loguearError, logUpdateFaltantes
import traceback
from inspect import stack

class Producto(BaseModel):
    sku: Optional[int]
    motivo: Optional[int]
    fecha: Optional[str]
    tienda: Optional[int]

class UsuarioParaActualizar(BaseModel):
    email: Optional[str]
    estatus: Optional[str]

router = APIRouter(
    # prefix="/",
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.get("/cargarMotivosFaltantes")
async def cargar_motivos_faltantes():
    query = """select mfp.id_pregunta,mfp.pregunta,mfr.id_respuesta,mfr.respuesta
        from DJANGO.php.motivo_faltante_pregunta mfp
        left join DJANGO.php.motivo_faltante_respuesta mfr on mfp.id_pregunta =mfr.id_pregunta
        where mfp.estatus = 1 and mfr.estatus = 1"""
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor().execute(query)
    arreglo = crear_diccionario(cursor)
    res = []
    if len(arreglo) > 0:
        for row in arreglo:
            res.append({'label': row['respuesta'], 'value': row['id_respuesta']})
    return res

@router.post("/updateMotivosFaltantes")
async def update_motivos_faltantes(producto: Producto, request: Request, user: dict = Depends(get_current_active_user)):
    query = f"""update fs set fs.id_respuesta={str(producto.motivo)} from DWH.report.faltante_sku fs where fecha='{producto.fecha}' and store_num = {str(producto.tienda)} and sku={str(producto.sku)}"""
    query2 = f"""SELECT respuesta from DJANGO.php.motivo_faltante_respuesta where id_respuesta = {str(producto.motivo)}"""
    cnxn = conexion_sql('DWH')
    try:
        cnxn.cursor().execute(query)
        cnxn.commit()
    except Exception:
        return {'exito': False}
    cursor = cnxn.cursor().execute(query2)
    arreglo = crear_diccionario(cursor)
    motivoTxt = arreglo[0]['respuesta']
    print(f"MotivoTxt: {motivoTxt}")
    logUpdateFaltantes(request.client.host, user.usuario, producto.fecha, producto.tienda, producto.sku, motivoTxt)
    return {'exito': True}

@router.post("/updateEstatusUsuario")
async def update_motivos_faltantes(usuarioParaActualizar: UsuarioParaActualizar, user: dict = Depends(get_current_active_user)):
    loguearConsulta(stack()[0][3], user.usuario, seccion, titulo, filtros, request.client.host)
    if tienePermiso(user.id, 'AltaUsuarios'):
        query = f"""update us set us.estatus='{str(usuarioParaActualizar.estatus)}' from DJANGO.php.usuarios us where usuario='{usuarioParaActualizar.email}'"""
        # print("Query desde updateEstatusUsuario: " + query)
        cnxn = conexion_sql('DJANGO')
        # print(f"Query desde updateEstatusUsuario en cargarMotivosFaltantes: {query}")
        try:
            cnxn.cursor().execute(query)
            cnxn.commit()
        except Exception:
            return {'exito': False}
        return {'exito': True}
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}  
