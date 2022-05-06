# job_dev_ventaDiaria
|Periodo de Ejecucion|Hora de Ejecucion|Dependencias|
|--|--|--|
|(periodo)|(hora)|(dependencias)|

# Job Steps:

![Vista_job_dev_ventaDiaria2.0.png](/docs/job_dev_ventaDiaria/Vista_job_dev_ventaDiaria2.0.png)

### 1.0  Extraccion de informacion de Tienda Online TRANS(dev_load_ventaDiariaTO)	
1.1 Extrae la informacion de la venta diaria de TO (ventaDiariaTO)
``` sql 
SELECT a.*,isnull(b.nTicket,0) nTicket
FROM 
(
	SELECT left(cast(fecha as varchar),6) anionmes,Fecha,Sucursal,a.Canal idCanal, 
	b.SubDepto,sum(VtaNetaSinImpSinDesc) Venta,0 devolucion,
	ROW_NUMBER() OVER(PARTITION BY a.fecha,a.sucursal,a.Canal 
	ORDER BY a.fecha,a.sucursal,a.Canal,b.SubDepto) id
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	where b.DEPTO <> 9 
	and Canal in (18,17,16)		
	--and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE()))) 
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(dd,-15,GETDATE()))
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-16,DATEADD(dd,-day(GETDATE()-1),GETDATE())))  
	--and convert(date,DATEADD(mm,-14,DATEADD(dd,-day(GETDATE()),GETDATE())))
	--and (a.fecha between 20210301 and 20210331 or a.fecha between 20210801 and 20210831)
	group by anionmes,Fecha,Sucursal,idCanal,b.SubDepto) A
left join 
(
	SELECT Fecha,Sucursal,a.Canal idCanal, COUNT(DISTINCT case when VtaNetaSinImpSinDesc > 0 then a.ticket else null end) nTicket
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	where b.DEPTO <> 9 
	and Canal in (18,17,16)
	--and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE()))) 
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-16,DATEADD(dd,-day(GETDATE()-1),GETDATE())))
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(dd,-15,GETDATE()))  
	--and convert(date,DATEADD(mm,-14,DATEADD(dd,-day(GETDATE()),GETDATE())))	
	--and (a.fecha between 20210301 and 20210331 or a.fecha between 20210801 and 20210831)
	group by Fecha,Sucursal,idCanal) B on A.fecha=B.fecha 
    and a.sucursal=b.sucursal and a.idCanal=b.idCanal and a.id=1
union
	select b.anionmes,b.Fecha,b.sucursal,a.Canal idCanal,b.subdepto,sum(b.venta) Venta,1 devolucion,0 id ,0 nTicket
	from (select LEFT(Pedido,9) nPedido,a.sucursal,a.canal 
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	where b.DEPTO <> 9 
	and Canal in (16,17,18)
	--and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-2,DATEADD(dd,-day(GETDATE()-1),GETDATE()))) 
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-17,DATEADD(dd,-day(GETDATE()-1),GETDATE())))
    and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(dd,-25,GETDATE()))  
	--and convert(date,DATEADD(mm,-13,DATEADD(dd,-day(GETDATE()),GETDATE())))
	--and (a.fecha between 20210201 and 20210331 or a.fecha between 20210701 and 20210831)
	group by nPedido,a.Sucursal,a.Canal) a
inner join
(
	select left(cast(fecha as varchar),6) anionmes,a.Fecha,a.Sucursal,LEFT(Pedido,9) nPedido,sum(a.VtaNetaSinImpSinDesc) Venta,b.SUBDEPTO 
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	where b.DEPTO <> 9 
	and Canal in (99)
	--and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE())))
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(dd,-15,GETDATE()))
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-16,DATEADD(dd,-day(GETDATE()-1),GETDATE())))  
	--and convert(date,DATEADD(mm,-14,DATEADD(dd,-day(GETDATE()),GETDATE())))
	--and (a.fecha between 20210301 and 20210331 or a.fecha between 20210801 and 20210831)
	group by anionmes,a.Fecha,a.sucursal,nPedido,b.SUBDEPTO ) b 
on a.nPedido=b.nPedido 
and a.sucursal=b.sucursal
group by b.anionmes,b.Fecha,b.sucursal,idCanal,b.subdepto
```   
1.2 Los datos se guardan en una tabla temporal (Table Output)(Temp_ventaDiariaTO)
``` sql 
temp.artus.ventaDiaria 
```   
### 2.0 Inserta los datos en la tabla de venta Diaria 
SCRIPT(update_insert_ventaDiariaTO)
``` sql 
update vd2
set vd2.ventaSinImpuestos=vd.ventaSinImpuestos,
vd2.id=vd.id,
vd2.nTicket=vd.nTicket 
from temp.artus.ventaDiaria vd 
inner join DWH.artus.ventaDiaria vd2 on vd.fecha =vd2.fecha 
	and vd.idTienda =vd2.idTienda 
	and vd.idCanal =vd2.idCanal 
	and vd.subdepto =vd2.subDepto 
	and vd.devolucion =vd2.devolucion;
insert into DWH.artus.ventaDiaria
select vd.fecha,vd.idTienda,vd.idCanal,vd.subdepto,vd.ventaSinImpuestos,0 objetivo,0 proyeccion,vd.devolucion,vd.anioMes,vd.id,vd.nTicket 
from temp.artus.ventaDiaria vd 
left join DWH.artus.ventaDiaria vd2 on vd.fecha =vd2.fecha 
	and vd.idTienda =vd2.idTienda 
	and vd.idCanal =vd2.idCanal 
    and vd.subdepto =vd2.subDepto 
	and vd.devolucion =vd2.devolucion 
where vd2.anioMes is null;
```
### 3.0  Extraccion de informacion de venta Diaria Terceros TRANS(dev_load_ventaDiariaTerceros)   (cornershop y rappi)
3.1 Extrae la informacion de la venta diaria de Terceros (ventaDiariaTerceros)
``` sql 
SELECT a.*,isnull(b.nTicket,0) nTicket
FROM 
(
	SELECT left(cast(fecha as varchar),6) anionmes, fecha,Sucursal,
	a.OrigenVenta idCanal, 
	b.SubDepto,sum(VtaNetaSinImpSinDesc) Venta,0 devolucion,
	ROW_NUMBER() OVER(PARTITION BY fecha,Sucursal,a.OrigenVenta 
    ORDER BY fecha,Sucursal,a.OrigenVenta,b.SubDepto) id	
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	--where a.Fecha BETWEEN 20211001 and 20211020
	where a.OrigenVenta in (35,36)	
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE()))) 
	--and a.Fecha BETWEEN 20210401 and 20211231
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-11,DATEADD(dd,-day(GETDATE()-1),GETDATE())))  
	--and convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()),GETDATE())))
	group by anionmes,fecha,Sucursal,idCanal,b.SubDepto) A
left join 
(
	SELECT left(cast(fecha as varchar),6) anionmes,fecha,Sucursal,a.OrigenVenta idCanal,
	count(DISTINCT case when VtaNetaSinImpSinDesc > 0 then a.ticket else null end) nTicket
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	--where a.Fecha BETWEEN 20211001 and 20211020
	where a.OrigenVenta in (35,36)	
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE())))
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-11,DATEADD(dd,-day(GETDATE()-1),GETDATE())))  
	--and convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()),GETDATE()))) 
	--and a.Fecha BETWEEN 20210401 and 20211231
	group by anionmes,fecha,Sucursal,idCanal) B on A.fecha=B.fecha
    and a.sucursal=b.sucursal 
    and A.idCanal=B.idCanal 
    and a.id=1
```     
3.2 Los datos se guardan en una tabla temporal (Table Output) (temp_ventaDiariaTerceros)
``` sql 
temp.artus.ventaDiaria 
```
### 4.0 Inserta los datos en la tabla de venta Diaria  SCRIPT(update_insert_ventaDiariaTerceros)
``` sql 
update vd2
set vd2.ventaSinImpuestos=vd.ventaSinImpuestos,
vd2.id=vd.id,
vd2.nTicket=vd.nTicket 
from temp.artus.ventaDiaria vd 
	inner join DWH.artus.ventaDiaria vd2 on vd.fecha =vd2.fecha 
    and vd.idTienda =vd2.idTienda 
    and vd.idCanal =vd2.idCanal 
    and vd.subdepto =vd2.subDepto;
insert into DWH.artus.ventaDiaria
select vd.fecha,vd.idTienda,vd.idCanal,vd.subdepto,vd.ventaSinImpuestos,0 objetivo,0 proyeccion,vd.devolucion,vd.anioMes,vd.id,vd.nTicket 
from temp.artus.ventaDiaria vd 
	left join DWH.artus.ventaDiaria vd2 on vd.fecha =vd2.fecha
    and vd.idTienda =vd2.idTienda 
    and vd.idCanal =vd2.idCanal 
    and vd.subdepto =vd2.subDepto 
where vd2.anioMes is null;
```    
### 5.0  Extraccion de informacion de Venta Diaria Tienda Fisica TRANS(dev_load_ventaDiariaTF)   
5.1 Extrae la informacion de la venta diaria  (ventaDiaria)
``` sql 
SELECT left(cast(fecha as varchar),6) anionmes, max(fecha) maxFcha,Sucursal,0 idCanal, b.SubDepto,sum(VtaNetaSinImpSinDesc) Venta,0 devolucion,0 id,0 nTicket	
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where b.DEPTO <> 9 
	and Canal in (0,1)
	--and Canal in (0)
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE())))
	--and year(CONVERT(date, convert(varchar(10), a.fecha)))=2021  
	--and MONTH (CONVERT(date, convert(varchar(10), a.fecha)))=8
	--and a.fecha between 20210301 and 20211030
group by anionmes,Sucursal,b.SubDepto	
```
5.2 Los datos se guardan en una tabla temporal (Table Output)(temp_VentaDiaria)
``` sql 
temp.artus.ventaDiaria 
```
5.3 Extrae la informacion de la venta diaria  (ventaxDiaTF)
``` sql 
SELECT fecha,sucursal,0 idCanal,sum(VtaNetaSinImpSinDesc) Venta
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where b.DEPTO <> 9 
	and Canal in (0,1)	
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,GETDATE()-15)
group by fecha,sucursal 
```
5.4 Los datos se guardan en una tabla temporal (Table Output2)(temp_vemtaxdiaTF)
``` sql 
temp.artus.ventaxdia
```

### 6.0  Inserta los datos en la tabla de Venta Diaria  SCRIPT(update_insert_ventaDiariaTF)
``` sql   
update vd2
set vd2.ventaSinImpuestos=vd.ventaSinImpuestos,vd2.id=vd.id,vd2.fecha=vd.fecha
from temp.artus.ventaDiaria vd 
	inner join DWH.artus.ventaDiaria vd2 on vd.idTienda =vd2.idTienda 
    and vd.idCanal =vd2.idCanal
    and vd.subdepto =vd2.subDepto 
    and vd.anioMes =vd2.anioMes;
insert into DWH.artus.ventaDiaria
select vd.fecha,vd.idTienda,vd.idCanal,vd.subdepto,vd.ventaSinImpuestos,0 objetivo,0 proyeccion,vd.devolucion,vd.anioMes,vd.id,vd.nTicket 
from temp.artus.ventaDiaria vd 
	left join DWH.artus.ventaDiaria vd2 on vd.idTienda =vd2.idTienda 
    and vd.idCanal =vd2.idCanal 
    and vd.subdepto =vd2.subDepto  
    and vd.anioMes =vd2.anioMes
where vd2.anioMes is null;

update vxd2
set vxd2.ventaSinImpuestos=vxd.ventaSinImpuestos
from temp.artus.ventaxdia vxd 
	inner join DWH.artus.ventaxdia vxd2 on vxd.idTienda =vxd2.idTienda
    and vxd.idCanal =vxd2.idCanal 
    and vxd.fecha = vxd2.fecha;
insert into DWH.artus.ventaxdia
select vxd.* 
from temp.artus.ventaxdia vxd 
	left join DWH.artus.ventaxdia vxd2 on vxd.idTienda =vxd2.idTienda 
    and vxd.idCanal =vxd2.idCanal 
    and vxd.fecha = vxd2.fecha
where vxd2.fecha is null;
```    
### 7.0  Extraccion de informacion de Venta Diaria Call Center TRANS(dev_load_ventaDiariaCallCenter)   
7.1 Extrae la informacion de la venta diaria Call Center (ventaDiaria)
``` sql 
SELECT a.*,isnull(b.nTicket,0) nTicket
FROM 
(
	SELECT left(cast(fecha as varchar),6) anionmes, fecha,Sucursal,2 idCanal,b.SubDepto,
    sum(VtaNetaSinImpSinDesc) Venta,0 devolucion,ROW_NUMBER() OVER(PARTITION BYfecha,Sucursal 
    ORDER BY fecha,Sucursal,b.SubDepto) id 
    from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	--where a.Fecha BETWEEN 20211001 and 20211020
	where 
	CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE()))) 
	--and CONVERT(date, convert(varchar(10), a.fecha)) between convert(date,DATEADD(mm,-11,DATEADD(dd,-day(GETDATE()-1),GETDATE())))  
	--and convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()),GETDATE())))
	--a.Fecha BETWEEN 20210901 and 20211231
	and b.depto = 9 --Depto Miscelaneos (Cobro de Servicios)
	and b.sku = 2448 --Descripcion del servicio (Deposito Vta a Dom)
	group by anionmes,fecha,Sucursal,b.SubDepto) A
left join 
(
	SELECT left(cast(fecha as varchar),6) anionmes,fecha,Sucursal,	 
2 idCanal,
	count(DISTINCT case when VtaNetaSinImpSinDesc > 0 then a.ticket else null end) nTicket
	from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
	--where a.Fecha BETWEEN 20211001 and 20211020
	where 
	CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()-1),GETDATE())))
	--and CONVERT(date, convert(varchar(10), a.fecha)) between 	convert(date,DATEADD(mm,-11,DATEADD(dd,-day(GETDATE()-1),GETDATE())))  
	--and convert(date,DATEADD(mm,-1,DATEADD(dd,-day(GETDATE()),GETDATE()))) 
	--a.fecha between 20210901 and 20211231
	and b.depto = 9 --Depto Miscelaneos (Cobro de Servicios)
	and b.sku = 2448 --Descripcion del servicio (Deposito Vta a Dom)
	group by anionmes,fecha,Sucursal) B on A.fecha=B.fecha 
	and a.sucursal=b.sucursal 
	and A.idCanal=B.idCanal 
	and a.id=1 
```
7.2 Los datos se guardan en una tabla temporal (Table Output)(temp_ventaDiariaCC)
``` sql 
temp.artus.ventaDiaria 
```	
### 8.0  Inserta los datos en la tabla de Venta Diaria  SCRIPT(update_insert_ventaDiariaCallCenter)
``` sql  
update vd2
set vd2.ventaSinImpuestos=vd.ventaSinImpuestos,vd2.id=vd.id,vd2.nTicket=vd.nTicket 
from temp.artus.ventaDiaria vd 
	inner join DWH.artus.ventaDiaria vd2 on vd.fecha =vd2.fecha 
    and vd.idTienda =vd2.idTienda 
    and vd.idCanal =vd2.idCanal a
    nd vd.subdepto =vd2.subDepto;
insert into DWH.artus.ventaDiaria
select vd.fecha,vd.idTienda,vd.idCanal,vd.subdepto,vd.ventaSinImpuestos,0 objetivo,0 proyeccion,vd.devolucion,vd.anioMes,vd.id,vd.nTicket 
from temp.artus.ventaDiaria vd 
	left join DWH.artus.ventaDiaria vd2 on vd.fecha =vd2.fecha
    and vd.idTienda =vd2.idTienda 
    and vd.idCanal =vd2.idCanal 
    and vd.subdepto =vd2.subDepto 
where vd2.anioMes is null;
```
### 9.0  Envio de informacion de Venta por Objetivo JOB(job_dev_envio_ventaXObjetivo)    
9.1 Extrae la informacion de la Venta por Objetivo y la transforma en una archivo xml para despues enviarlo por correo a usuarios en especifico (dev_file_ventaxObjetivo)
9.1.1 Extrae la informacion de Detalle por Mes  y la transforma en un archivo (detallexMes)
``` sql 
select dt.descrip_mes,
	sum(case when idCanal in (16,17,18,2) then ventaSinImpuestos else 0 end) TOnline,
	sum(case when idCanal in (0) then ventaSinImpuestos else 0 end) TFisica
from DWH.artus.ventaDiaria vd
	left join DWH.dbo.dim_tiempo dt on vd.fecha =dt.id_fecha 
where dt.anio = year(GETDATE()-1)
	and idCanal in (0,16,17,18)
	and ventaSinImpuestos is not null
group by  dt.descrip_mes,dt.num_mes 
order by dt.num_mes 
```
9.1.2 Extrae la informacion de Detalle por Departamento  y la transforma en un archivo (detallexDepartamento)
``` sql 
select dt.descrip_mes,cm.DEPTO_NOMBRE, 
sum(case when dt.anio = year(GETDATE()-1) then ventaSinImpuestos else 0 end) VentaActual,
sum(case when dt.anio = year(DATEADD(yy,-1,GETDATE()-1)) then ventaSinImpuestos else 0 end) VentaAnterior
from DWH.artus.ventaDiaria vd
	left join DWH.dbo.dim_tiempo dt on vd.fecha =dt.id_fecha
	left join (select DISTINCT DEPTO_NOMBRE,SUBDEPTO 
	from DWH.artus.catMARA) cm on vd.subDepto =cm.SUBDEPTO 
where dt.anio >= year(DATEADD(yy,-1,GETDATE()-1))
	and idCanal in (16,17,18)
	and ventaSinImpuestos is not null
group by  dt.descrip_mes,cm.DEPTO_NOMBRE,dt.num_mes 
order by dt.num_mes 
```
9.1.3 Extrae la informacion de Detalle por Terceros por Día y la transforma en un archivo (detallexTercerosxdia)
``` sql 
select dt.fecha,
sum(case when idCanal = 35 then ventaSinImpuestos else 0 end) Cornershop,
sum(case when idCanal = 36 then ventaSinImpuestos else 0 end) rappi
from DWH.artus.ventaDiaria vd
	left join DWH.dbo.dim_tiempo dt on vd.fecha =dt.id_fecha 
where idCanal in (35,36)
	and dt.anio = year(GETDATE()-1)
	and dt.fecha < convert(date,getdate())
group by dt.fecha
order by dt.fecha
```
9.1.4 Extrae la informacion de Detalle por Terceros  y la transforma en un archivo (detallexTerceros)
``` sql 
select dt.descrip_mes,cc.descripTipo Terceros, 
sum(ventaSinImpuestos) VentaActual
from DWH.artus.ventaDiaria vd
	left join DWH.dbo.dim_tiempo dt on vd.fecha =dt.id_fecha
	left join DWH.artus.catCanal cc on vd.idCanal =cc.idCanal 
where dt.anio = year(GETDATE()-1)
	and vd.idCanal in (35,36)
	and dt.fecha < convert(date,getdate())
group by  dt.descrip_mes,dt.num_mes, cc.descripTipo
order by dt.num_mes 
``` 
9.2 Los datos se envian por correo (dev_mail_ventaxObjetivo)

### 10.0  Envio de informacion de Venta por SKU por Proveedor JOB(job_dev_venta_departamento) 
10.1 Extrae la informacion de Venta por Subclase por Proveedor TRANS(prod_cargaDetalleVentaxSKUxProveedor)
10.1.1 Extrae la informacion de la Venta x Subclase por Proveedor (Table input)(cargaDetalleVentaxSubclasexProveedor)
``` sql 
select fecha, b.SUBCLASE,b.PROVEEDOR,
sum(case when Canal in (18,17,16,99) then VtaNetaSinImpSinDesc else 0 end) ventaTO,
sum(case when Canal in (18,17,16,99) then Unidades else 0 end) cantTO,
sum(case when Canal in (0,1) then VtaNetaSinImpSinDesc else 0 end) ventaTF,
sum(case when Canal in (0,1) then Unidades else 0 end) cantTF
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where b.DEPTO <> 9
	--and Canal in (18,17,16,0)
	and Canal in (0,1,18,17,16,99)
	and CONVERT(date, convert(varchar(10), a.fecha)) BETWEEN convert(date,GETDATE()-5)  
    and convert(date,GETDATE()-1)
group by fecha,b.SUBCLASE,b.PROVEEDOR   
```
10.1.2 Los datos se guardan en la tabla temporal (Table input)(temp_cargaDetalleVentaxSubclasexProveedor)
``` sql 
artus.ventaxsubClasexproveedor
```

10.1.3 Extrae la informacion de la Venta por SKU(Table input)(cargaDetalleVentaxSKU)
``` sql 
select fecha,b.SKU,
sum(VtaNetaSinImpSinDesc) ventaTO,
sum(Unidades) cantTO
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where b.DEPTO <> 9
	--and Canal in (18,17,16,0)
	and Canal in (18,17,16,99)
	and CONVERT(date, convert(varchar(10), a.fecha)) BETWEEN convert(date,GETDATE()-5)  
    and convert(date,GETDATE()-1)
group by fecha,b.sku
```
10.1.4Los datos se guardan en la tabla temporal (Table input)(temp_cargaDetalleVentaxSKU)
``` sql 
artus.ventaxdiaxsku
```
10.2 Inserta los datos en la tabla de ventaxsubClasexproveedor  SCRIPT(query_insertUpdate_ventaxSKUClaseProveedor)
``` sql 
update b
set b.ventaTO =a.ventaTO, b.cantTO =a.cantTO, b.ventaTF=a.ventaTF, b.cantTF =a.cantTF 
from temp.artus.ventaxsubClasexproveedor a 
	inner join DWH.artus.ventaxsubClasexproveedor b on a.fecha =b.fecha
    and a.subClase=b.subClase 
    and a.proveedor =b.proveedor;
insert into DWH.artus.ventaxsubClasexproveedor
select a.*
from temp.artus.ventaxsubClasexproveedor a 
	left join DWH.artus.ventaxsubClasexproveedor b on a.fecha =b.fecha 
    and a.subClase=b.subClase 
    and a.proveedor =b.proveedor
where b.ventaTO is null;

update b
set b.ventaTO =a.ventaTO, b.cantTO =a.cantTO 
from temp.artus.ventaxdiaxsku a 
	inner join DWH.artus.ventaxdiaxsku b on a.fecha =b.fecha 
    and a.sku =b.sku;
insert into DWH.artus.ventaxdiaxsku
select a.*
from temp.artus.ventaxdiaxsku a 
	left join DWH.artus.ventaxdiaxsku b on a.fecha =b.fecha 
    and a.sku=b.sku 
where b.sku is null;
```
10.3 Extrae la informacion de Venta por Subclase por Proveedor TRANS(prod_fileDetalleVentaxSKUxProveedor)
10.3.1 Extrae la informacion de la Venta x Subclase por Proveedor (input_detalleVentaSubClaseProveedor)
``` sql 
select dt.num_mes nMes,cm.DEPTO_NOMBRE,cm.SUBDEPTO_NOMBRE,
cm.CLASE_NOMBRE,cm.SUBCLASE_NOMBRE,cm.PROVEEDOR_NOMBRE, 
sum(vc.ventaTO) ventaTO,sum(vc.cantTO) cantTO,sum(vc.ventaTF) ventaTF,sum(vc.cantTF) cantTF
from DWH.artus.ventaxsubClasexproveedor vc
	left join DWH.dbo.dim_tiempo dt on vc.fecha =dt.id_fecha 
	left join DWH.artus.catMARA cm on vc.subClase =cm.SUBCLASE 
    and vc.proveedor =cm.PROVEEDOR 
where dt.num_mes = month(GETDATE()-1) 
	and dt.anio = year(GETDATE()-1)
group by dt.num_mes,cm.DEPTO_NOMBRE,cm.SUBDEPTO_NOMBRE,
cm.CLASE_NOMBRE,cm.SUBCLASE_NOMBRE,cm.PROVEEDOR_NOMBRE
```
10.3.2 La informacion de la Venta x Subclase por Proveedor la guarda en un documento de Excel (Microsoft Excel writer)
*F:\file_temp\reportes\out\detalleVentaxSKUxProveedorxsubClase*
Sheet Name: *detalleProveedor*

10.4 Extrae la informacion de Venta por SKU TRANS(prod_fileDetalleVentaxSKU)
10.4.1 Extrae la informacion de la Venta x SKU (input_detalleVentaxSKU)
``` sql 
select dt.num_mes nMes,cm.DEPTO_NOMBRE,cm.SUBDEPTO_NOMBRE,cm.CLASE_NOMBRE,cm.SUBCLASE_NOMBRE,cm.SKU,cm.SKU_NOMBRE, cm.PROVEEDOR_NOMBRE, 
sum(vc.ventaTO) ventaTO,sum(vc.cantTO) cantTO
from DWH.artus.ventaxdiaxsku vc
	left join DWH.dbo.dim_tiempo dt on vc.fecha =dt.id_fecha 
	left join DWH.artus.catMARA cm on vc.sku =cm.SKU  
where dt.num_mes = month(GETDATE()-1) 
	and dt.anio = year(GETDATE()-1)
group by dt.num_mes,cm.DEPTO_NOMBRE,cm.SUBDEPTO_NOMBRE,
cm.CLASE_NOMBRE,cm.SUBCLASE_NOMBRE,cm.SKU,cm.SKU_NOMBRE, 
cm.PROVEEDOR_NOMBRE 
```

10.4.2 La informacion de la Venta x SKU la guarda en un documento de Excel (Microsoft Excel writer)
*F:\file_temp\reportes\out\detalleVentaxSKUxProveedorxsubClase*
Sheet Name: *detalleSKU*


### 11.0  Envio de informacion de Venta por Objetivo JOB(job_dev_venta_departamento)   
11.1 Extrae la informacion de la Venta por Objetivo (dev_file_ventaxObjetivo)
11.1.1 Extrae la informacion de la Venta Diaria por Departamento (Table input)(ventaDiariaxDepto)
``` sql 
select a.fecha,Sucursal,Terminal,Transaccion,hora,cast(left(Pedido,9) as int) pedido_n,SUM(VtaNetaSinImpSinDesc) VtaNetaSinImpSinDesc,
case when SUM(VtaConImpConDesc) < 0 then 1 else 0 end devolucion,count(1) item,
sum(case when b.DEPTO = 1 then a.VtaNetaSinImpSinDesc else 0 end) pgcComestible,
sum(case when b.DEPTO = 1 then 1 else 0 end) itemPgcComestible,
sum(case when b.DEPTO = 2 then a.VtaNetaSinImpSinDesc else 0 end) transAlimentos,
sum(case when b.DEPTO = 2 then 1 else 0 end) itemTransAlimentos,
sum(case when b.DEPTO = 4 then a.VtaNetaSinImpSinDesc else 0 end) ropaZapateria,
sum(case when b.DEPTO = 4 then 1 else 0 end) itemRopaZapateria,
sum(case when b.DEPTO = 6 then a.VtaNetaSinImpSinDesc else 0 end) electroMuebles,
sum(case when b.DEPTO = 6 then 1 else 0 end) itemElectroMuebles,
sum(case when b.DEPTO = 7 then a.VtaNetaSinImpSinDesc else 0 end) variedades,
sum(case when b.DEPTO = 7 then 1 else 0 end) itemVariedades,
sum(case when b.DEPTO = 90 then a.VtaNetaSinImpSinDesc else 0 end) pgcNoComestible,
sum(case when b.DEPTO = 90 then 1 else 0 end) itemPgcNoComestible,
sum(case when b.DEPTO = 91 then a.VtaNetaSinImpSinDesc else 0 end) perecederosNoTrans,
sum(case when b.DEPTO = 91 then 1 else 0 end) itemPerecederosNoTrans,
sum(VtaConImpConDesc) VtaConImp
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where b.DEPTO <> 9
	and CONVERT(date, convert(varchar(10), a.fecha)) >= convert(date,GETDATE()-10)
	--and a.fecha between 20210101 and 20210830 
	and a.Canal in (18,17,16,99)
	and len(a.Pedido) > 1
group by a.fecha,Sucursal,Terminal,Transaccion,hora,pedido_n
```
11.1.2  Los datos se guardan en una tabla temporal (Table Output)(temp_ventaDiariaxDepto)
``` sql 
temp.artus.pedidoVtaSinImp
```
11.2 Inserta los datos en la tabla de pedidoVtaSinImp (insert_update_pedidoVtaSinImp_hecho_order)
``` sql 
update a
set a.VtaNetaSinImpSinDesc=b.VtaNetaSinImpSinDesc,
a.item=b.item,
a.pgcComestible=b.pgcComestible,
a.itemPgcComestible=b.itemPgcComestible,
a.transAlimentos=b.transAlimentos,
a.itemTransAlimentos=b.itemTransAlimentos,
a.ropaZapateria=b.ropaZapateria,
a.itemRopaZapateria=b.itemRopaZapateria,
a.electroMuebles=b.electroMuebles,
a.itemElectroMuebles=b.itemElectroMuebles,
a.variedades=b.variedades,
a.itemVariedades=b.itemVariedades,
a.pgcNoComestible=b.pgcNoComestible,
a.itemPgcNoComestible=b.itemPgcNoComestible,
a.perecederosNoTrans=b.perecederosNoTrans,
a.itemPerecederosNoTrans=b.itemPerecederosNoTrans,
a.devolucion=case when b.VtaNetaSinImpSinDesc < 0 then 1 else 0 end,
a.dateUpdate=format(GETDATE(),'yyyyMMddHHmmss'),
a.VtaConImp=b.VtaConImp 
FROM DWH.artus.pedidoVtaSinImp a
	inner join TEMP.artus.pedidoVtaSinImp b on b.fecha =a.fecha
    and b.idTienda =a.idTienda 
    and b.pedido = a.pedido 
	and b.terminal =a.terminal 
    and b.transaccion =a.transaccion 
    and b.hora =a.hora;
insert into DWH.artus.pedidoVtaSinImp
SELECT b.*,case when b.VtaNetaSinImpSinDesc < 0 then 1 else 0 end devolucion,format(GETDATE(),'yyyyMMddHHmmss') dateUpdate
FROM TEMP.artus.pedidoVtaSinImp b
	left join DWH.artus.pedidoVtaSinImp a on b.fecha =a.fecha 
    and b.idTienda =a.idTienda
    and b.pedido = a.pedido 
	and b.terminal =a.terminal 
    and b.transaccion =a.transaccion 
    and b.hora =a.hora
where a.pedido is null;

update ho
set 
ho.vtaSinImp=pvsi.VtaNetaSinImpSinDesc,
ho.vtaConImp=pvsi.VtaConImp 
from DWH.dbo.hecho_order ho 
inner join (
select pedido,idTienda,sum(VtaNetaSinImpSinDesc) VtaNetaSinImpSinDesc,sum(VtaConImp) VtaConImp 
from DWH.artus.pedidoVtaSinImp pvsi
where CONVERT(date, convert(varchar(10), pvsi.fecha)) >= convert(date,GETDATE()-35)
and pvsi.VtaNetaSinImpSinDesc > 0
and pvsi.devolucion=0
group by pedido,idTienda) 
pvsi on ho.order_number =pvsi.pedido and ho.store_num =pvsi.idTienda;
update ho
set ho.montoDevolucion=pvsi.VtaNetaSinImpSinDesc 
from DWH.dbo.hecho_order ho 
	inner join (
	select pedido,idTienda,sum(VtaNetaSinImpSinDesc) VtaNetaSinImpSinDesc
	from DWH.artus.pedidoVtaSinImp pvsi
	where CONVERT(date, convert(varchar(10), pvsi.fecha)) >= convert(date,GETDATE()-35)
	and pvsi.devolucion=1
	group by pedido,idTienda) pvsi on ho.order_number =pvsi.pedido 
    and ho.store_num =pvsi.idTienda;
```
11.3 Vacia la tabla temporal pedidoVtaSinImp (truncate_table_pedidoVtaSinImp)
``` sql 
truncate table TEMP.artus.pedidoVtaSinImp;
```
### 12.0  Extraccion de informacion de Venta TOP SKU Tienda Fisica TRANS(dev_load_venta_topSKU_TF)  

12.1 Extrae la informacion de la venta top SKU (venta_topSKU)
``` sql 
SELECT top 1000 a.fecha,a.sku,sum(a.unidades) cant,sum(a.vtanetasinImpSinDesc) Venta,'TF' Tipo
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where 
	--a.fecha between 20211010 and 20211010 
	CONVERT(date, convert(varchar(10), a.fecha)) = convert(date,GETDATE()-1)
	and a.canal in (0)
	and b.DEPTO <> 9
	and a.origenVenta not in (35,36)
group by a.fecha,a.sku
order by sum(a.unidades) desc
```
12.2 Los datos se guardan en una tabla temporal (Table Output)(temp_venta_topSKU)
``` sql 
temp.artus.detalleTopSKU
```
### 13.0  Extraccion de informacion de Venta TOP SKU Tienda Online  TRANS(dev_load_venta_topSKU_TO)
13.1 Extrae la informacion de la venta top SKU (venta_topSKU_TO
``` sql 
SELECT top 100 a.fecha,a.sku,
sum(a.unidades) cant,
sum(a.vtanetasinImpSinDesc) Venta,'TO' Tipo
from sapds.ventas_tickets_detalle a
	inner join sapds.V_T_M_ARTICULOSYSERVICIOS b on a.sku = b.sku
	inner join sapds.T_M_Tiendas c on a.sucursal = c.tienda
where 
	--a.fecha between 20211010 and 20211010 
	CONVERT(date, convert(varchar(10), a.fecha)) = convert(date,GETDATE()-1)
	and a.canal in (16,17,18,99)
	and b.DEPTO <> 9
group by a.fecha,a.sku
order by sum(a.unidades) desc
```
13.2 Los datos se guardan en una tabla temporal (Table Output)(temp_venta_topSKU_TO)
``` sql 
temp.artus.detalleTopSKU
```
### 14.0  Extraccion de informacion de Venta TOP SKU Tienda Online  SCRIPT(delete_detalleTopSKU_ultimos10dias)
Borra los datos de los ultimos 10 días.
``` sql 
delete
from temp.artus.detalleTopSKU
where CONVERT(date, convert(varchar(10), fecha)) < convert(date,GETDATE()-10);
update ho
set ho.tmp_n_estatus=case when DATEDIFF(hh, isnull(ho.timeslot_to,ho.creation_date + 3),cast(concat(dt.fecha,' ',
case when len(hora)=1 then concat('00:0',hora,':00') 
when len(hora)=2 then concat('00:',hora,':00')
when len(hora)=3 then concat('0',SUBSTRING(cast(hora as varchar),1,1),':',SUBSTRING(cast(hora as varchar),2,2),':00')
when len(hora)=4 then concat(SUBSTRING(cast(hora as varchar),1,2),':',SUBSTRING(cast(hora as varchar),3,2),':00')
else null end) as datetime))<48 then 'DEV_COMPLETA_FUERATIEMPO' ELSE 'DEV_COMPLETA_ATIEMPO' END 
/*SELECT ho.order_number,ho.timeslot_to,dt.fecha,DATEDIFF(d, ho.timeslot_to,dt.fecha) dia,tmp_n_estatus, 
case when len(hora)=1 then concat('00:0',hora,':00') 
when len(hora)=2 then concat('00:',hora,':00')
when len(hora)=3 then concat('0',SUBSTRING(cast(hora as varchar),1,1),':',SUBSTRING(cast(hora as varchar),2,2),':00')
when len(hora)=4 then concat(SUBSTRING(cast(hora as varchar),1,2),':',SUBSTRING(cast(hora as varchar),3,2),':00')
else null end hora,
cast(concat(dt.fecha,' ',
case when len(hora)=1 then concat('00:0',hora,':00') 
when len(hora)=2 then concat('00:',hora,':00')
when len(hora)=3 then concat('0',SUBSTRING(cast(hora as varchar),1,1),':',SUBSTRING(cast(hora as varchar),2,2),':00')
when len(hora)=4 then concat(SUBSTRING(cast(hora as varchar),1,2),':',SUBSTRING(cast(hora as varchar),3,2),':00')
else null end
) as datetime) fechaCompleta,
DATEDIFF(hh, isnull(ho.timeslot_to,ho.creation_date + 3),cast(concat(dt.fecha,' ',
case when len(hora)=1 then concat('00:0',hora,':00') 
when len(hora)=2 then concat('00:',hora,':00')
when len(hora)=3 then concat('0',SUBSTRING(cast(hora as varchar),1,1),':',SUBSTRING(cast(hora as varchar),2,2),':00')
when len(hora)=4 then concat(SUBSTRING(cast(hora as varchar),1,2),':',SUBSTRING(cast(hora as varchar),3,2),':00')
else null end
) as datetime)) difHora,
case when DATEDIFF(hh, isnull(ho.timeslot_to,ho.creation_date + 3),cast(concat(dt.fecha,' ',
case when len(hora)=1 then concat('00:0',hora,':00') 
when len(hora)=2 then concat('00:',hora,':00')
when len(hora)=3 then concat('0',SUBSTRING(cast(hora as varchar),1,1),':',SUBSTRING(cast(hora as varchar),2,2),':00')
when len(hora)=4 then concat(SUBSTRING(cast(hora as varchar),1,2),':',SUBSTRING(cast(hora as varchar),3,2),':00')
else null end
) as datetime))<48 then 'DE_COMPLETA_FUERATIEMPO' ELSE 'DE_COMPLETA_ATIEMPO' END estatus*/
from DWH.dbo.hecho_order ho 
	left join DWH.dbo.dim_estatus de on ho.id_estatus =de.id_estatus
	left join (select min(fecha) fecha,min(hora) hora,idTienda,pedido
		from DWH.artus.pedidoVtaSinImp pvsi
        where devolucion = 1
		group by idTienda,pedido) a on ho.store_num =a.idTienda 
	and ho.order_number =a.pedido
	left join DWH.dbo.dim_tiempo dt on a.fecha=dt.id_fecha 			
where case when convert(date,ho.creation_date) >= '2022-01-01' and (ho.montoDevolucion * -1) > (vtaSinImp * .85) then 1 else 0 end = 1
	and convert(date,ho.creation_date) >= convert(date,GETDATE()-30)
	and de.descrip_consignment_status not like '%Cancel%'
	and ISNULL(ho.tmp_n_estatus,'OTRO') IN ('COMPLETO','DEV_COMPLETA','DE_COMPLETA_FUERATIEMPO','DE_COMPLETA_ATIEMPO','DEV_COMPLETA_FUERATIEMPO','DEV_COMPLETA_ATIEMPO');
```

