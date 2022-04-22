from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import datetime, date, timedelta
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/sankey",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class Sankey():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if filtros.fechas['fecha_ini'] != None and filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if filtros.fechas['fecha_fin'] != None and filtros.fechas['fecha_fin'] != '' else None

    async def CatalogoArticulos(self):
        if self.filtros.periodo == {}:
            return {'hayResultados':'no','data':[], 'colors': ['#000']}
        data = []
        elegidos = {}
        colores = ['#FFA785'] # El primer color corresponde a "ERP", y ya después cada nodo tiene su color asignado
        estructura = {
            'Producto Omnicanal': {
                'data': ['', 'Producto Omnicanal', 0],
                'color': '#74CFDE',
                'orden': 1
            },
            'Bandera Incorrecta': {
                'data': ['', 'Bandera Incorrecta', 0],
                'color': '#ff3d51',
                'orden': 2
            },
            'Aptos para la venta': {
                'data': ['Producto Omnicanal', 'Aptos para la venta', 0],
                'color': '#85DB8A',
                'orden': 3
            },
            'Baja': {
                'data': ['Producto Omnicanal', 'Baja', 0],
                'color': '#74CFDE',
                'orden': 4
            },
            'Aprobados Para TL': {
                'data': ['Aptos para la venta', 'Aprobados Para TL', 0],
                'color': '#85DB8A',
                'orden': 5
            },
            'No Aprobados': {
                'data': ['Aptos para la venta', 'No Aprobados', 0],
                'color': '#85DB8A',
                'orden': 6
            }#,
            # 'CDB': {
            #     'data': ['Aprobados Para TL', 'CDB', 0],
            #     'color': '#FF9642',
            #     'orden': 7
            # }
        }
        # print(f"self.filtros.agrupador desde sankey: {self.filtros.agrupador}")
        # print(f"self.filtros.periodo desde sankey: {self.filtros.periodo}")
        if self.filtros.agrupador == 'semana':
            filtroAgrupador = f" where idSemDS = {self.filtros.periodo['semana']} "
        else:
            filtroAgrupador = f" where idSemDS is not null "
        if self.filtros.grupoDeptos != '' and self.filtros.grupoDeptos != 'False':
            if self.filtros.deptoAgrupado != '' and self.filtros.deptoAgrupado != 'False':
                if self.filtros.subDeptoAgrupado != '' and self.filtros.subDeptoAgrupado != 'False':
                    filtroLugar = f" and Subdepartamento='{self.filtros.subDeptoAgrupado}' "
                else:
                    filtroLugar = f" and departamento='{self.filtros.deptoAgrupado}' "
            else:
                filtroLugar = f" and grupo='{self.filtros.grupoDeptos}' "
        else:
            filtroLugar = ''
        query = f"""
        select * from DWH.report.catalogoUXConsolidado
        {filtroAgrupador}
        {filtroLugar}
        """
        print(f"query desde sankey: {query}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        resultados = crear_diccionario(cursor)
        # print(f"resultados desde sankey: {str(resultados)}")
        if len(resultados) > 0:
            hayResultados = "si"
            for row in resultados:
                # print(f"int(row['productoOmnicanal']) = {int(row['productoOmnicanal'])}")
                estructura['Producto Omnicanal']['data'][2] += int(row['productoOmnicanal'])
                estructura['Bandera Incorrecta']['data'][2] += int(row['banderaIncorrecta'])
                estructura['Aptos para la venta']['data'][2] += int(row['aptosVenta'])
                estructura['Baja']['data'][2] += int(row['baja'])
                estructura['Aprobados Para TL']['data'][2] += int(row['VisibleTL'])
                estructura['No Aprobados']['data'][2] += int(row['noVisible'])
                # estructura['CDB']['data'][2] += int(row['articulosCDB'])
                # print(f"estructura['Producto Omnicanal']['data'][2] = {estructura['Producto Omnicanal']['data'][2]}")
            for item in estructura.items():
                if item[1]['data'][2] > 0:
                    elegidos[item[0]] = item[1]
            elegidos = {k: v for k, v in sorted(elegidos.items(), key=lambda item: item[1]['orden'])} # https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
            # print(f"elegidos: {str(elegidos)}")
            for item in elegidos.items():
                colores.append(item[1]['color'])
                data.append(item[1]['data'])
            # print(f"data: {str(data)}")
        else:
            hayResultados = "no"
        return {'hayResultados':hayResultados,'data':data, 'colors': colores}

@router.post("/{seccion}")
async def sankey (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    if tienePermiso(user.id_rol, seccion):
        objeto = Sankey(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}