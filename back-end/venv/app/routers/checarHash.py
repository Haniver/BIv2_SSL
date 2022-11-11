from asyncio.windows_events import NULL
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.Filtro import Filtro
from app.servicios.formatoFechas import ddmmyyyy
from datetime import datetime, timedelta
from calendar import monthrange
from app.servicios.formatoFechas import mesTexto
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from copy import deepcopy
from numpy import zeros
from app.servicios.permisos import tienePermiso
from argon2 import PasswordHasher

router = APIRouter(
    prefix="/checarHash",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def set_hash (password: str, email: str):
    # query = f"""SELECT hash from DJANGO.php.usuarios WHERE usuario = '{email}'"""
    # cnxn = conexion_sql('DJANGO')
    # cursor = cnxn.cursor().execute(query)
    # arreglo = crear_diccionario(cursor)
    # passEnBD = arreglo[0]['hash']
    ph = PasswordHasher()
    hash = ph.hash(password)
    query = f"""UPDATE DJANGO.php.usuarios
        SET hash = '{hash}'
        WHERE usuario = '{email}'"""
    cnxn = conexion_sql('DJANGO')
    cnxn.cursor().execute(query)
    cnxn.commit()
    return {'respuesta': 'Parece que ya se hizo. Chécale en la BD'}

async def set_hash (password: str, email: str):
    verificado = ph.verify(hash, password)

    if verificado:
        resultado = 'Passwords sí coinciden'
    else:
        resultado = 'Passwords no coinciden'
    res = {'resultado': verificado, 'enviada': password}
    print(str(res))
    return res

