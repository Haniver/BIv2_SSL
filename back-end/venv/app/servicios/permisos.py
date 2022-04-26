from app.servicios.conectar_sql import conexion_sql, crear_diccionario

def tienePermiso(id_rol, seccion):
    # El ID de los componentes de React (idReact en la BD) es igual a la sección, pero con la primera letra en minúscula
    if seccion == "Home":
        return True
    idReact = seccion[0].lower() + seccion[1:]
    query = f"""select *
    from DJANGO.php.usuario_vista uv
    left join DJANGO.php.vistas v on uv.id_vista = v.id_vista
    where id_rol = {id_rol} and v.idReact = '{idReact}'"""
    cnxn = conexion_sql('DJANGO')
    cursor = cnxn.cursor().execute(query)
    resultados = crear_diccionario(cursor)
    # print(f"arreglo de resultados de permisos.py: {str(resultados)}")
    return True if len(resultados) > 0 else False

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
