from datetime import datetime, timedelta, date
from email.mime import base
from typing import Optional
from app.servicios import conectar_sql

from fastapi import Header, Depends, FastAPI, HTTPException, status, Body, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import FileResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import json

router = APIRouter()
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "f2a0dc035f4a8d2cf4d6a0b2f9d25cda2f70bd7bc83b6ed81499c0bfa5355dd7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    usuario: Optional[str] = None

class User(BaseModel):
    usuario: str
    # id_rol: Optional[int] = None
    nombre: Optional[str] = None
    rol: Optional[str] # Esto es para fines de ajustarse a utils.js de Vuexy. Debería ser el rol real, o usar el id_rol
    id: Optional[int] = None
    vistas: Optional[str]
    documentos: Optional[str]
    # vistas: Optional[list] = []
    # documentos: Optional[list] = []
    tienda: Optional[int]
    apellidoP: Optional[str]
    apellidoM: Optional[str]
    menu: Optional[str]
    nivel: Optional[int]
    region: Optional[int]
    zona: Optional[int]

class UserInDB(User):
    password: str

class claseCambiarPassword(BaseModel):
    password: Optional[str]
    token: Optional[str]
    passwordVieja: Optional[str]
    tienda: Optional[str]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def buscar_usuario_en_bd(usuario):
    respuesta = []
    cnxn = conectar_sql.conexion_sql('DJANGO')
    cursor = cnxn.cursor()
    cursor.execute(f"""select u.id, u.usuario, u.nivel, u.password, u.nombre, u.idTienda, ct.region, ct.zona
    from DJANGO.php.usuarios u
    left join DWH.artus.catTienda ct on  u.idTienda =ct.tienda
    where usuario = '{usuario}'""")
    resultados = conectar_sql.crear_diccionario(cursor)
    usuario = resultados[0]['usuario']
    # id_rol = resultados[0]['id_rol']
    password = resultados[0]['password']
    nombre = resultados[0]['nombre']
    # rol = resultados[0]['rol']
    nivel = resultados[0]['nivel']
    id = resultados[0]['id']
    tienda = resultados[0]['idTienda']
    region = resultados[0]['region']
    zona = resultados[0]['zona']

    # Obtener Vistas a las que tiene acceso el usuario
    cursor.execute(f"""select distinct v.id_vista, v.categoria, v.idReact, v.title, v.icon 
    from DJANGO.php.usuarios us 
    left join DJANGO.php.usuariosAreas ua on ua.id_usuario = us.id
    left join DJANGO.php.permisosVistas pv on pv.area = ua.area
    left join DJANGO.php.vistas v on v.id_vista = pv.vista
    where us.id = {id}
    and v.activado = 1
    and v.idReact is not NULL 
    and v.idReact != ''""")
    resultados = conectar_sql.crear_diccionario(cursor)
    vistas = []
    for row in resultados:
        vistas.append({
            "id_vista": int(row['id_vista']),
            "categoria": row['categoria'],
            "idReact": row['idReact'],
            "title": row['title'],
            "icon": row['icon']
        })
    # Obtener Documentos a los que tiene acceso el usuario
    # query = f"""select vd.title, vd.categoria, vd.icon, vd.nombre_archivo, vd.id_vista 
    # from DJANGO.php.vistas_documentos vd 
    # left join DJANGO.php.usuario_vista uv on uv.id_vista = vd.id_vista 
    # left join DJANGO.php.usuarios u on uv.id_rol = u.id_rol 
    # where u.usuario = '{usuario}'
    # and vd.activado = 1
    # order by vd.lugar"""
    # # print(f"Query para el diccionario de documentos desde auth.py: {str(query)}")
    # cursor.execute(query)
    # resultados = conectar_sql.crear_diccionario(cursor)
    # # print(f"Diccionario de documentos desde auth.py: {str(resultados)}")
    documentos = []
    # for row in resultados:
    #     documentos.append({
    #         "nombre_archivo": row['nombre_archivo'],
    #         "categoria": row['categoria'],
    #         "id_vista": int(row['id_vista']),
    #         "title": row['title'],
    #         "icon": row['icon']
    #     })
    rol = f'Usuario Nivel {str(nivel)}'
    respuesta = {usuario: {'usuario': usuario, 'password': password, 'nombre': nombre, 'nivel': nivel, 'rol': rol, 'id': id, 'vistas': json.dumps(vistas), 'documentos': json.dumps(documentos), 'tienda': tienda, 'region': region, 'zona': zona}}
    # print(f"Respuesta desde auth.py: {str(respuesta)}")
    return respuesta

def get_user(db, usuario: str):
    if usuario in db:
        user_dict = db[usuario]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, usuario: str, password: str):
    user = get_user(fake_db, usuario)
    if not user:
        return False
    if password != user.password:
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else: # Si no se define una expiración, por default es hoy a la media noche
        dt = datetime.date.today() + datetime.timedelta(days=1) # Mañana
        expire = datetime.combine(dt, datetime.min.time()) # Mañana a las 0:00
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No pudieron validarse las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario: str = payload.get("sub")
        if usuario is None:
            raise credentials_exception
        token_data = TokenData(usuario=usuario)
    except JWTError:
        raise credentials_exception
    user = get_user(buscar_usuario_en_bd(usuario=token_data.usuario), usuario=token_data.usuario)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user
