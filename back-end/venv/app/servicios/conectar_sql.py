# Módulo para conectarse a una base de datos de MS SQL Server
import pyodbc
import servicios.credenciales as credenciales

def conexion_sql(bd='DJANGO'):
    cadena_conexion = cadena_conexion = f"DRIVER={{{credenciales.sql()['driver']}}};IntegratedSecurity=true;SERVER={credenciales.sql()['servidor']};DATABASE={bd};UID={credenciales.sql()['usuario']};PWD={credenciales.sql()['password']}"
    # print(f"cadena_conexion: {cadena_conexion}")
    cnxn = pyodbc.connect(cadena_conexion)
    return cnxn


def crear_diccionario(cursor):
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results