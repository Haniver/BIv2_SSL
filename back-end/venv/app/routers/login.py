from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user, authenticate_user, buscar_usuario_en_bd, create_access_token, TokenData, claseCambiarPassword, User, Token, UserInDB
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.enviarEmail import enviarEmail
from app.servicios import urls
from datetime import datetime, timedelta, date, time
from dateutil.relativedelta import relativedelta
import random
import string
import pyodbc

from fastapi import Depends, FastAPI, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import FileResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
# from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware

router = APIRouter()

################### Endpoints Públicos ######################

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(buscar_usuario_en_bd(form_data.username), form_data.username, form_data.password)
    # Si no hay usuario (o sea las credenciales son incorrectas), regresar error.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    hoy = date.today()
    ahorita = datetime.now()
    haceUnMes = ahorita - relativedelta(months=1)
    haceUnMes = haceUnMes.strftime('%Y-%m-%d %H:%M:%S')
    # Bloquear al usuario si no se ha logueado en un mes.
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor()
    query = f"""UPDATE DJANGO.php.usuarios
    SET estatus='expirado' 
    WHERE usuario='{user.usuario}'
    AND fecha_ultimo_login is not null
    AND fecha_ultimo_login < '{haceUnMes}'"""
    cursor.execute(query)
    cnxn.commit()
    # Mandar error si el usuario no está activo
    query = f"""SELECT estatus
    from DJANGO.php.usuarios
    WHERE usuario='{user.usuario}'"""
    cursor.execute(query)
    arreglo = crear_diccionario(cursor)
    # print(f"El estatus del usuario (desde login.py) es: {arreglo[0]['estatus']}")
    if arreglo[0]['estatus'] != 'activo':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Registrar este login como el último
    ahorita_sql = ahorita.strftime('%Y-%m-%d %H:%M:%S')
    query = f"""UPDATE DJANGO.php.usuarios
    SET fecha_ultimo_login='{ahorita_sql}' 
    WHERE usuario='{user.usuario}'"""
    cursor.execute(query)
    cnxn.commit()
    # Crear token
    medianoche = datetime.combine(hoy, time.max)
    diferencia = medianoche - ahorita
    access_token_expires = timedelta(seconds=diferencia.seconds)
    # access_token_expires = timedelta(seconds=20) # Para fines de debugging, lo vamos a poner de 30 segundos
    access_token = create_access_token(
        data={"sub": user.usuario}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/roles")
async def roles():
    respuesta = []
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor()
    cursor.execute("select * from DJANGO.php.rol r")
    rows = cursor.fetchall()
    for row in rows:
        respuesta.append({'value': row.id, 'label': row.rol})
    # print(f'Respuesta desde roles en login.py: {str(respuesta)}')
    return respuesta

@router.post("/recuperarPassword")
async def recuperarPassword(tokenData: TokenData):
    cnxn = conexion_sql()
    cursor = cnxn.cursor()
    cursor.execute("select nombre from DJANGO.php.usuarios where usuario = '"+tokenData.usuario+"'")
    row = cursor.fetchone()
    if row == None: # Si no se encontró el email en la BD
        cuerpo = "<html><head></head><body><p>Alguien solicitó el envío de un enlace para recuperar tu contraseña de Chedraui BI con el correo "+tokenData.usuario+", pero este correo no está en nuestra base de datos. Por favor reintenta con el correo correcto, o regístrate.</p><p><span style='color:#1A2976;'>Saludos,<br />BI Omnicanal<br />Grupo Comercial Chedraui <img src='https://i.ibb.co/qyc21cy/logo-Email.png'></span></p></body></html>"
        receivers = [tokenData.usuario]
        titulo = "BI Omnicanal - Recuperación contraseña"
        return enviarEmail(titulo, receivers, cuerpo)
    else: # Si el email sí está en la BD
        token_resetear_password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(25))
        expiracion = datetime.now() + timedelta(hours=6)
        expiracion = expiracion.strftime("%Y-%m-%d %H:%M:%S")
        cnxn = conexion_sql()
        cursor = cnxn.cursor()
        query = "UPDATE DJANGO.php.usuarios SET token_resetear_password = '"+token_resetear_password+"', expiracion_trp='"+expiracion+"' WHERE usuario = '"+tokenData.usuario+"'"
        try:
            cursor.execute(query)
            cnxn.commit()
        except pyodbc.Error as e:
            return {'mensaje':'Error al intentar actualizar base de datos: '+str(e)}
        # return {'mensaje':query}
        cuerpo = "<html><head></head><body><p>Hola "+ row.nombre + ", buen día.</p><p>Da clic <a href='" + urls.frontendUrlHttp() + '/cambiarPassword/' + token_resetear_password + "'> aquí </a> para generar tu nueva contraseña.</p><p><span style='color:#1A2976;'>Saludos,<br />BI Omnicanal<br />Grupo Comercial Chedraui <img src='https://i.ibb.co/qyc21cy/logo-Email.png'></span></p></body></html>"
        receivers = [tokenData.usuario]
        titulo = "BI Omnicanal - Recuperación contraseña"
        return enviarEmail(titulo, receivers, cuerpo)

# Verifica si el token para cambiar la contraseña esá activo
@router.get("/cambiarPasswordActivo/{token_resetear_password}")
async def cambiarPasswordActivo(token_resetear_password: str):
    ahora = datetime.now()
    cnxn = conexion_sql()
    cursor = cnxn.cursor()
    try:
        cursor.execute("select expiracion_trp from DJANGO.php.usuarios where token_resetear_password = '"+token_resetear_password+"'")
        row = cursor.fetchone()
    except pyodbc.Error as e:
        return {'mensaje':'Error al buscar en la base de datos: '+str(e)}
    if row == None or ahora > row.expiracion_trp: # Si no se encontró el token en la BD o ya expiró
        return {'mensaje':'Inactivo'}
    else:
        return {'mensaje':'Activo'}

#Cambia la password en la BD
@router.post("/cambiarPassword")
async def cambiarPassword(objetoCambiarPassword: claseCambiarPassword):
    ahora = datetime.now()
    ahora = ahora.strftime("%Y-%m-%d %H:%M:%S")
    cnxn = conexion_sql()
    cursor = cnxn.cursor()
    query = "UPDATE DJANGO.php.usuarios SET password = '"+objetoCambiarPassword.password+"' WHERE token_resetear_password = '"+objetoCambiarPassword.token+"' and expiracion_trp > '"+ahora+"'"
    try:
        cursor.execute(query)
        cnxn.commit()
    except pyodbc.Error as e:
        return {'mensaje':'Error al intentar actualizar base de datos: '+str(e)}
    return {'mensaje':'Contraseña actualizada correctamente, ya puedes acceder a tu cuenta.'}

@router.post("/verificarUsuario")
async def verificar_usuario(input: TokenData):
    cnxn = conexion_sql()
    cursor = cnxn.cursor()
    query = f"SELECT usuario from DJANGO.php.usuarios WHERE usuario = '{input.usuario}'"
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor().execute(query)
    arreglo = crear_diccionario(cursor)
    # print(f'arreglo desde verificarUsuario en login.py: {str(arreglo)}')
    return True if len(arreglo) > 0 else False

############# Endpoints Restringidos #############
@router.get("/comprobarToken")
async def comprobar_token(current_user: User = Depends(get_current_active_user)):
    return {'estatus':'logueado'}

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.usuario}]

@router.post("/cambiarPerfil")
async def cambiarPerfil(objetoCambiarPassword: claseCambiarPassword, user: dict = Depends(get_current_active_user)):
    # print('Entrando a cambiarPerfil')
    ahora = datetime.now()
    ahora = ahora.strftime("%Y-%m-%d %H:%M:%S")
    # mensaje = f'Usuario es {str(user)}, password vieja es {objetoCambiarPassword.passwordVieja} y password nueva es {objetoCambiarPassword.password}'
    # print(mensaje)
    if (objetoCambiarPassword.password != ''):
        if (user.password == objetoCambiarPassword.passwordVieja):
            cnxn = conexion_sql('DJANGO')
            cursor = cnxn.cursor()
            query = f"UPDATE DJANGO.php.usuarios SET password = '{objetoCambiarPassword.password}' WHERE usuario = '{user.usuario}'"
            try:
                cursor.execute(query)
                cnxn.commit()
            except pyodbc.Error as e:
                return {'mensaje':'Error al intentar actualizar base de datos: '+str(e)}
        else:
            return {'mensaje': 'La password anterior es incorrecta'}
    if (objetoCambiarPassword.tienda != ''):
        cnxn = conexion_sql('DJANGO')
        cursor = cnxn.cursor()
        query = f"UPDATE DJANGO.php.usuarios SET idTienda = '{int(objetoCambiarPassword.tienda)}' WHERE usuario = '{user.usuario}'"
        try:
            cursor.execute(query)
            cnxn.commit()
        except pyodbc.Error as e:
            return {'mensaje':'Error al intentar actualizar base de datos: '+str(e)}
    return {'mensaje':f'Datos actualizados correctamente.'}
    # return {'mensaje': mensaje}

@router.post("/registro")
async def registro(input_usuario: UserInDB):
    # print('Entrando a registro')
    ahora = datetime.now()
    ahora = ahora.strftime("%Y-%m-%d %H:%M:%S")
    # mensaje = f'Usuario es {str(user)}, password vieja es {objetoCambiarPassword.passwordVieja} y password nueva es {objetoCambiarPassword.password}'
    # print(mensaje)
    nombre_completo = input_usuario.nombre + ' ' + input_usuario.apellidoP + ' ' + input_usuario.apellidoM
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor()
    # Los valores posibles para estatus son revisión, bloqueado y activo
    query = f"""INSERT INTO DJANGO.php.usuarios (nombre, password, usuario, id_rol, idTienda, estatus)
        VALUES ('{nombre_completo}', '{input_usuario.password}', '{input_usuario.usuario}', {input_usuario.id_rol}, {input_usuario.tienda}, 'revisión')"""
    try:
        # print(f'query desde registro en login.py: {query}')
        cursor.execute(query)
        cnxn.commit()
    except pyodbc.Error as e:
        return {'mensaje':'Error al intentar actualizar base de datos: '+str(e), 'exito': False}
    return {'mensaje':f'Su solicitud de creación de usuario ha sido enviada. En breve recibirá respuesta al correo que registró.', 'exito': True}
    # return {'mensaje': mensaje}
