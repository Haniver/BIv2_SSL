from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_active_user
from app.servicios.conectar_mongo import conexion_mongo
from app.servicios.conectar_sql import conexion_sql, crear_diccionario
from app.servicios.Filtro import Filtro
from datetime import date, datetime, timedelta
from calendar import monthrange
from app.servicios.permisos import tienePermiso

router = APIRouter(
    prefix="/tarjetasEnFila",
    # dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

class TarjetasEnFila():
    def __init__(self, filtros: Filtro, titulo: str):
        self.filtros = filtros
        self.titulo = titulo
        if self.filtros.fechas != None:
            self.fecha_ini_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_ini'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) if self.filtros.fechas['fecha_ini'] != None and self.filtros.fechas['fecha_ini'] != '' else None
            self.fecha_fin_a12 = datetime.combine(datetime.strptime(self.filtros.fechas['fecha_fin'], '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.min.time()) + timedelta(days=1) if self.filtros.fechas['fecha_fin'] != None and self.filtros.fechas['fecha_fin'] != '' else None
        if self.filtros.region != '' and self.filtros.region != "False" and self.filtros.region != None:
            self.filtro_lugar = True
            if self.filtros.zona != '' and self.filtros.zona != "False" and self.filtros.zona != None:
                if self.filtros.tienda != '' and self.filtros.tienda != "False" and self.filtros.tienda != None:
                    self.nivel_lugar = 'tienda'
                    self.lugar = int(self.filtros.tienda)
                else:
                    self.nivel_lugar = 'zona'
                    self.lugar = int(self.filtros.zona)
            else:
                self.nivel_lugar = 'region'
                self.lugar = int(self.filtros.region)
        else:
            self.filtro_lugar = False

    async def Temporada(self):
        res = []
        hoyStr = datetime.today().strftime('%Y-%m-%d')
        hoyInt = int(hoyStr[0:4]) * 10000 + int(hoyStr[5:7]) * 100 + int(hoyStr[8:10])
        hayResultados = 'no'
        query = ''
        hayCanal = False if self.filtros.canal == False or self.filtros.canal == 'False' or self.filtros.canal == None or self.filtros.canal == '' else True
        # print(f"Canal desde TarjetasEnFila -> Temporada: {str(self.filtros.canal)}")
        query = f"""select hora, sum(ventaConImp) venta
            from DWH.report.pedido_hora ph
            where fechaCreacion = '{hoyStr}'
            and hora in (
                select max(hora)
                from DWH.report.pedido_hora 
                where fechaCreacion = '{hoyStr}'
            )
            group by hora
        """
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
        res.append({
            'valor': arreglo[0]['venta'],
            'titulo': f"Venta Última Hora (0{arreglo[0]['hora']}:00)" if int(arreglo[0]['hora']) < 10 else f"Venta Última Hora ({arreglo[0]['hora']}:00)",
            'icon': 'DollarSign',
            'formato': 'moneda'
        })

        query = f"""select hora, sum(pedidos) pedidos
            from DWH.report.pedido_hora ph
            where fechaCreacion = '{hoyStr}'
            and hora in (
                select max(hora)
                from DWH.report.pedido_hora 
                where fechaCreacion = '{hoyStr}'
            )
            group by hora
            """
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
        res.append({
            'valor': arreglo[0]['pedidos'],
            'titulo': f"Pedidos Última Hora (0{arreglo[0]['hora']}:00)" if int(arreglo[0]['hora']) < 10 else f"Pedidos Última Hora ({arreglo[0]['hora']}:00)",
            'icon': 'Package',
            'formato': 'entero'
        })

        query = f"""select sum(ventaSinImpuestos) venta
            from DWH.artus.ventaDiariaHora vdh 
            where fecha = {hoyInt}
            and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
            """
        print(f"query desde tarjetas.py -> Temporada -> Venta Hoy: {str(query)}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
        res.append({
            'valor': arreglo[0]['venta'],
            'titulo': 'Venta Hoy',
            'icon': 'DollarSign',
            'formato': 'moneda'
        })

        query = f"""select sum(ventaSinImpuestos)/(
                select sum(ventaSinImpuestos)
                from DWH.artus.ventaDiariaHora vdh 
                where fecha = {hoyInt}
                and idCanal in (0)
            ) porc_part
            from DWH.artus.ventaDiariaHora vdh 
            where fecha = {hoyInt}
            and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
            """
        # print(f"query desde tarjetas.py -> Temporada -> % Participación Venta Hoy: {str(query)}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
        res.append({
            'valor': arreglo[0]['porc_part'],
            'titulo': '% Participación Venta Hoy',
            'icon': 'Percent',
            'formato': 'porcentaje'
        })

        query = f"""select sum(nTicket) pedidos, sum(ventaSinImpuestos) venta
        from DWH.artus.ventaDiariaHora vdh
        where fecha = {hoyInt}
        and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
        """
        # print(f"query desde tarjetas.py -> Temporada -> % Participación Venta Hoy: {str(query)}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        print(f"arreglo desde tarjetasEnFila: {str(arreglo)}")
        res.append({
            'titulo': 'Ticket Promedio (sin imp)',
            'valor': float(arreglo[0]['venta']/arreglo[0]['pedidos']),
            'icon': 'FileText',
            'formato': 'moneda'
        })

        query = f"""select SUM(item) / SUM(nTicket) artPromedio from DWH.artus.ventaDiariaHora vdh
        where fecha = {hoyInt}
        and idCanal {'not in (0' if not hayCanal else 'in ('+str(self.filtros.canal)})
        """
        print(f"query desde tarjetas.py -> Temporada -> Artículos Promedio: {str(query)}")
        cnxn = conexion_sql('DWH')
        cursor = cnxn.cursor().execute(query)
        arreglo = crear_diccionario(cursor)
        # print(f"arreglo desde ejesMultiplesApilados: {str(arreglo)}")
        res.append({
            'titulo': 'Artículos Promedio',
            'valor': float(arreglo[0]['artPromedio']),
            'icon': 'Box',
            'formato': 'entero'
        })

        return {'hayResultados':hayResultados, 'res': res, 'pipeline': query}

@router.post("/{seccion}")
async def tarjetasEnFila (filtros: Filtro, titulo: str, seccion: str, user: dict = Depends(get_current_active_user)):
    # print("El usuario desde tarjetas .py es: {str(user)}")
    if tienePermiso(user.id, seccion):
        objeto = TarjetasEnFila(filtros, titulo)
        funcion = getattr(objeto, seccion)
        diccionario = await funcion()
        return diccionario
    else:
        return {"message": "No tienes permiso para acceder a este recurso."}        

