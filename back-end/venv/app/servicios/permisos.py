from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.urls import rutaLogs
from datetime import datetime

def tienePermiso(idUsuario, seccion):
    # El ID de los componentes de React (idReact en la BD) es igual a la sección, pero con la primera letra en minúscula
    cnxn = conexion_sql('DJANGO')
    if seccion == "Home":
        cursor = cnxn.cursor().execute(f"select usuario from DJANGO.php.usuarios u where id = {idUsuario}")
        resultados = crear_diccionario(cursor)
        # print(f"resultados[0]['usuario'][-15:] desde permisos.py = {resultados[0]['usuario'][-15:]}")
        return resultados[0]['usuario'][-15:] == 'chedraui.com.mx'
    idReact = seccion[0].lower() + seccion[1:]
    query = f"""select * from DJANGO.php.permisosVistas pv 
    left join DJANGO.php.usuariosAreas ua on pv.area = ua.area 
    left join DJANGO.php.vistas v on v.id_vista = pv.vista 
    where ua.id_usuario  = {idUsuario}
    and v.idReact='{idReact}'"""
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    # print(f"arreglo de resultados de permisos.py: {str(resultados)}")
    return len(resultados) > 0

def permisoMarkdown(id_rol, nombre_archivo):
    query = f"""
    select * 
    from DJANGO.php.vistas_documentos vd 
    left join DJANGO.php.usuario_vista uv on vd.id_vista = uv.id_vista 
    where vd.nombre_archivo = '{nombre_archivo}'
    and uv.id_rol = {id_rol}
    """
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    # print(f"arreglo de resultados de permisos.py: {str(resultados)}")
    return True if len(resultados) > 0 else False