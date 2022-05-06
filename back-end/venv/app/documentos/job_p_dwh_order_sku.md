# job_p_dwh_order_sku
|Periodo de Ejecucion|Hora de Ejecucion|Dependencias|
|--|--|--|
|(periodo)|(hora)|(dependencias)|     
# Job Steps:
![Vista_job_p_dwh_order_sku.png](/docs/job_p_dwh_order_sku/Vista_job_p_dwh_order_sku.png)

### 1.0   JOB(job_stage_input_dwh_sku)
#### 1.1 Extraccion del nombre de archivo a trabajar TRANS(dev_fecha_ant_order_report)
1.1.1 Concatena el nombre del archivo con la fecha (Table input)
```sql
select CONCAT('order-report-',CAST(DATEADD(DAY,-1,GETDATE()) AS DATE),'.*\.csv') as Fecha
```
1.1.2 Se agrega como una variable el tecto concatenado (set variables)
#### 1.2 Se obtiene un Archivo por medio de SFTP y se coloca un una nueva ruta para poder usarlo (Get a file with SFTP - Orders (Hybris))
Remote Directory: /opt/chedraui/trcan/Order_Report
Target Directory: F:\file_temp\order_report\input
#### 1.3 Se edita el archivo para utilizar solo los datos requeridos y se agregan otros faltantes. El resultado de guarda en una tabla TRANS(dev_load_csv_order_repor)
#### 1.4 Inserta los datos en la tabla dim_estatus_sku SCRIPT(SQL)
```sql
insert into DWH.dbo.dim_estatus_sku (consignment_status,sku_status,delivery_mode)
SELECT dx.CONSIGNMENT_STATUS,dx.SKU_STATUS,dx.DELIVERY_MODE
FROM (
	select DISTINCT isnull(OR2.CONSIGNMENT_STATUS,'S/D') CONSIGNMENT_STATUS,isnull(or2.SKU_STATUS,'S/D') SKU_STATUS,isnull(or2.DELIVERY_MODE,'S/D') DELIVERY_MODE
	from TEMP.stg.order_report or2) dx
	left join DWH.dbo.dim_estatus_sku des on dx.CONSIGNMENT_STATUS=des.consignment_status 
    and dx.SKU_STATUS=des.sku_status 
    and dx.DELIVERY_MODE=des.delivery_mode
where des.id_estatus_sku is null;
```
#### 1.5 Actualiza e Inserta los datos en la tabla hecho_sku SCRIPT(SQL2)
```sql
update hs
set hs.fecha_creacion=dx.F_CREACION,
hs.fecha_redendcion=dx.F_REDENDCION,
hs.fecha_delivery=dx.F_DELIVERY,
hs.id_estatus_sku=dx.id_estatus_sku,
hs.items_ori=dx.ITEMS_ORI,
hs.items_fin=dx.ITEMS_FIN,
hs.items_found=dx.ITEMS_FOUND,
hs.items_agregados=dx.ITEMS_AGREGADOS,
hs.fecha_ult_mod=dx.F_ULT_MOD,
hs.pedido_tienda=dx.PEDIDO_TIENDA,
hs.entry_ori_amount=dx.ENTRY_ORI_AMOUNT,
hs.entry_fin_amount=dx.ENTRY_FIN_AMOUNT,
hs.consignment_ori_amount=dx.CONSIGNMENT_ORI_AMOUNT,
hs.consignment_fin_amount=dx.CONSIGNMENT_FIN_AMOUNT 
from dwh.dbo.hecho_sku hs
inner join
	(select ORDER_NUMBER,STORE_NUMBER,isnull(CONSIGNMENT_NUMBER,'S/D') CONSIGNMENT_NUMBER,F_CREACION ,F_REDENDCION,F_DELIVERY,SKU,des.id_estatus_sku, 
	ITEMS_ORI,ITEMS_FIN ,ITEMS_FOUND,ITEMS_AGREGADOS ,F_ULT_MOD ,PEDIDO_TIENDA,ENTRY_ORI_AMOUNT,ENTRY_FIN_AMOUNT,CONSIGNMENT_ORI_AMOUNT,CONSIGNMENT_FIN_AMOUNT 
	from TEMP.stg.order_report or2
		LEFT JOIN DWH.dbo.dim_estatus_sku des on isnull(OR2.CONSIGNMENT_STATUS,'S/D')=des.consignment_status 
    	and isnull(or2.SKU_STATUS,'S/D')=des.sku_status 
    	and isnull(or2.DELIVERY_MODE,'S/D')=des.delivery_mode) dx on hs.order_number = dx.order_number 
    and hs.store_number =dx.STORE_NUMBER 
    and hs.consignment_number =dx.CONSIGNMENT_NUMBER 
    and hs.sku =dx.sku; 
    
insert into dwh.dbo.hecho_sku
select dx.*,null fecha_completo
from 
	(select ORDER_NUMBER,STORE_NUMBER,isnull(CONSIGNMENT_NUMBER,'S/D') CONSIGNMENT_NUMBER,F_CREACION ,F_REDENDCION,F_DELIVERY,SKU,des.id_estatus_sku, 
	ITEMS_ORI,ITEMS_FIN ,ITEMS_FOUND,ITEMS_AGREGADOS ,F_ULT_MOD ,PEDIDO_TIENDA,ENTRY_ORI_AMOUNT,ENTRY_FIN_AMOUNT,CONSIGNMENT_ORI_AMOUNT,CONSIGNMENT_FIN_AMOUNT 
	from TEMP.stg.order_report or2
		LEFT JOIN DWH.dbo.dim_estatus_sku des on isnull(OR2.CONSIGNMENT_STATUS,'S/D')=des.consignment_status 
   		and isnull(or2.SKU_STATUS,'S/D')=des.sku_status 
   		and isnull(or2.DELIVERY_MODE,'S/D')=des.delivery_mode) dx
	LEFT JOIN dwh.dbo.hecho_sku hs on hs.order_number =dx.order_number 
    and hs.store_number =dx.STORE_NUMBER 
    and hs.consignment_number =dx.CONSIGNMENT_NUMBER 
    and hs.sku =dx.sku
where hs.order_number is null;
```
#### 1.6 Inserta el archivo en otra ruta para su futuro uso (Move files)
File/Folder Source: F:\file_temp\order_report\input
File/Folder Destination: F:\file_temp\order_report\input\process
### 2.0 Actualiza los estatus de los pedidos SCRIPT(update_estatus_pedido_montos)
``` sql 
update ho
set ho.tmp_n_estatus='INCOMPLETO'
from DWH.dbo.hecho_order ho
	inner join 
	(SELECT DISTINCT hs.store_number,hs.order_number 
	FROM DWH.dbo.hecho_sku hs
		inner join 
		(select DISTINCT order_number,store_num 
		from DWH.dbo.hecho_order ho
			inner join DWH.dbo.dim_estatus de on ho.id_estatus = de.id_estatus 
			where de.descrip_consignment_status in ('Delivery Completed','Picked Up')
			and convert(date,ho.ultimo_cambio) BETWEEN convert(date,getdate()-20)
       	 and convert(date,getdate()-1)
			and ho.tmp_n_estatus is null ) dx on hs.store_number =dx.store_num
        and hs.ORDER_NUMBER =dx.order_number
		inner join DWH.dbo.dim_estatus_sku des on  hs.id_estatus_sku =des.id_estatus_sku 
        and des.sku_status = 'INCOMPLETO' 
where hs.items_fin = 0) dx on ho.store_num =dx.store_number 
	and ho.order_number =dx.order_number;

update ho
set ho.tmp_n_estatus='INC_SUSTITUTOS'
from DWH.dbo.hecho_order ho
	inner join 
	(SELECT DISTINCT hs.store_number,hs.order_number 
	FROM DWH.dbo.hecho_sku hs
		inner join 
		(select DISTINCT order_number,store_num 
		from DWH.dbo.hecho_order ho
			inner join DWH.dbo.dim_estatus de on ho.id_estatus = de.id_estatus 
		where de.descrip_consignment_status in ('Delivery Completed','Picked Up')
        	and convert(date,ho.ultimo_cambio) BETWEEN convert(date,getdate()-20) 
        	and convert(date,getdate()-1)
			and ho.tmp_n_estatus is null ) dx on hs.store_number =dx.store_num 
			and hs.ORDER_NUMBER =dx.order_number
		inner join DWH.dbo.dim_estatus_sku des on  hs.id_estatus_sku =des.id_estatus_sku 
        	and des.sku_status in ('INC_SUBSTITUTO_REMOVED','INC_SUBSTITUTO_ADIC') 
		where hs.items_fin > 0) dx on ho.store_num =dx.store_number 
        	and ho.order_number =dx.order_number;
            
update ho
set ho.tmp_n_estatus='COMPLETO'
from DWH.dbo.hecho_order ho
	inner join 
	(SELECT DISTINCT hs.store_number,hs.order_number 
	FROM DWH.dbo.hecho_sku hs
		inner join 
			(select DISTINCT order_number,store_num 
			from DWH.dbo.hecho_order ho
			inner join DWH.dbo.dim_estatus de on ho.id_estatus = de.id_estatus 
			where de.descrip_consignment_status in ('Delivery Completed','Picked Up')
			and convert(date,ho.ultimo_cambio) BETWEEN convert(date,getdate()-20) 
            and convert(date,getdate()-1)
			and ho.tmp_n_estatus is null ) dx on hs.store_number =dx.store_num 
            and hs.ORDER_NUMBER =dx.order_number
			inner join DWH.dbo.dim_estatus_sku des on  hs.id_estatus_sku =des.id_estatus_sku 
            and des.sku_status not in ('INC_SUBSTITUTO_REMOVED','INC_SUBSTITUTO_ADIC','INCOMPLETO')
			where hs.items_fin > 0) dx on ho.store_num =dx.store_number 
            and ho.order_number =dx.order_number;
            
update ho
set ho.tmp_n_estatus='COMPLETO'
FROM DWH.dbo.hecho_order ho
	inner join DWH.dbo.dim_estatus de on ho.id_estatus = de.id_estatus
where de.descrip_consignment_status in ('Delivery Completed','Picked Up')
	and ho.tmp_n_estatus is null
	and convert(date,ho.ultimo_cambio) BETWEEN convert(date,getdate()-20)
    and convert(date,getdate()-2);
    
update ho
set ho.items_ini=dx.items_ini,
ho.items_fin=dx.items_fin,
ho.items_found=dx.items_found,
ho.monto_ini=dx.monto_ini,
ho.monto_fin=dx.monto_fin
from DWH.dbo.hecho_order ho
	inner join DWH.dbo.dim_estatus de on ho.id_estatus = de.id_estatus
	inner join (
	select or2.ORDER_NUMBER,or2.STORE_NUMBER,
	sum(case when or2.items_ori > 0 then 1 else 0 end) items_ini,max(case when or2.items_ori > 0 then or2.CONSIGNMENT_ORI_AMOUNT else 0 end) monto_ini,
	sum(case when or2.items_fin > 0 then 1 else 0 end) items_fin,max(case when or2.items_ori > 0 then or2.CONSIGNMENT_FIN_AMOUNT else 0 end) monto_fin,
	sum(case when or2.items_ori > 0 and or2.items_fin > 0 then 1 else 0 end) items_found
	from temp.stg.order_report or2
	group by or2.ORDER_NUMBER,or2.STORE_NUMBER ) dx on ho.order_number = dx.order_number 
    and ho.store_num =dx.store_number
where de.descrip_consignment_status in ('Delivery Completed','Picked Up')
	and convert(date,ho.ultimo_cambio) BETWEEN convert(date,getdate()-20) 
    and convert(date,getdate()-1);
```
### 3.0 Actualiza las fechas del ultimo cambio SCRIPT(update_fecha_ultimo_cambio)
``` sql 
update hs
set hs.fecha_completo=convert(date,ho.ultimo_cambio)
from DWH.dbo.hecho_sku hs 
	inner join DWH.dbo.hecho_order ho on hs.store_number =ho.store_num 
    and hs.order_number =ho.order_number 
	left join DWH.dbo.dim_estatus de on ho.id_estatus =de.id_estatus 
where de.descrip_consignment_status in ('Delivery Completed','Picked Up')
	and convert(date,ho.ultimo_cambio)=convert(DATE,GETDATE()-1) 
	and hs.fecha_completo is null;
```
### 4.0 Inserta los datos en la tabla report.foundrate_sku_canal SCRIPT(insert_report.foundrate_sku_canal_7_dias)
```sql 
delete (insert_report.foundrate_sku_canal_7_dias)
from DWH.report.foundrate_sku_canal
where fecha >= convert(date,GETDATE()-7); 
insert into DWH.report.foundrate_sku_canal
select dx.ultimo_cambio,store_num,sku,sum(dx.item_ori) item_ori,sum(dx.item_fin) item_fin,dx.canal,ds.descrip_tienda tienda,ds.region,ds.zona,
m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha 
from (
	select convert(date,ho.ultimo_cambio) ultimo_cambio,ho.store_num,hs.sku,
	case when hs.items_ori > 0 then 1 end item_ori,
	case when hs.items_ori > 0 and hs.items_fin > 0 then 1 else 0 end item_fin,'Chedraui' canal
	from DWH.dbo.hecho_sku hs,  DWH.dbo.hecho_order ho
	where convert(date,ho.ultimo_cambio)>= convert(date,GETDATE()-7) 
	and hs.order_number = ho.order_number
	and hs.store_number =ho.store_num
	and ho.tmp_n_estatus is not null
	and hs.items_ori > 0) dx
	left join DWH.dbo.dim_store ds on dx.store_num=ds.idtienda
	left join TEMP.stg.mara m on dx.sku=m.Articulo
	left join DWH.dbo.dim_tiempo dt on dx.ultimo_cambio=dt.fecha
group by dx.ultimo_cambio,store_num,sku,dx.canal,ds.descrip_tienda,ds.region,ds.zona,m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha
UNION 
select c.[Day],c.branch_id,c.sku,
sum(times_ordered) item_ini , sum(found_rate *times_ordered) item_fin,'Cornershop' Canal,ds.descrip_tienda tienda,ds.region,ds.zona,m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha 
from TEMP.stg.cornershop c
	left join DWH.dbo.dim_store ds on c.branch_id=ds.idtienda
	left join TEMP.stg.mara m on c.sku=m.Articulo
	left join DWH.dbo.dim_tiempo dt on c.[Day] =dt.fecha 
where len(c.SKU)=7
	and c.[Day] >= CONVERT(date,GETDATE()-7)
group by c.[Day],c.Branch_ID,c.SKU,ds.descrip_tienda,ds.region,ds.zona,
m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha;
```
### 5.0 Inserta los datos en la tabla report.foundrate_sku SCRIPT(insert_report.foundrate_sku_7_dias)
```sql 
delete
from DWH.report.foundrate_sku
where fecha >= CONVERT (date,GETDATE()-7);
insert into DWH.report.foundrate_sku
select dx.ultimo_cambio,store_num,sku,sum(dx.item_ori) item_ori,sum(dx.item_fin) item_fin,dx.canal,ds.descrip_tienda tienda,ds.region,ds.zona,
m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha 
from (
	select convert(date,ho.ultimo_cambio) ultimo_cambio,ho.store_num,hs.sku,
	case when hs.items_ori > 0 then 1 end item_ori,
	case when hs.items_ori > 0 and hs.items_fin > 0 then 1 else 0 end item_fin,'Chedraui' canal
	from DWH.dbo.hecho_sku hs,  DWH.dbo.hecho_order ho
	where convert(date,ho.ultimo_cambio)>= convert(date,GETDATE()-7) 
	and hs.order_number = ho.order_number
	and hs.store_number =ho.store_num
	and ho.tmp_n_estatus is not null
	and hs.items_ori > 0) dx
	left join DWH.dbo.dim_store ds on dx.store_num=ds.idtienda
	left join TEMP.stg.mara m on dx.sku=m.Articulo
	left join DWH.dbo.dim_tiempo dt on dx.ultimo_cambio=dt.fecha
group by dx.ultimo_cambio,store_num,sku,dx.canal,ds.descrip_tienda,ds.region,ds.zona,m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha
HAVING sum(dx.item_fin)*100/cast(sum(dx.item_ori) as float) < 100
UNION 
select c.[Day],c.branch_id,c.sku,
sum(times_ordered) item_ini , sum(found_rate *times_ordered) item_fin,'Cornershop' Canal,
ds.descrip_tienda tienda,ds.region,ds.zona,
m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha 
from TEMP.stg.cornershop c
	left join DWH.dbo.dim_store ds on c.branch_id=ds.idtienda
	left join TEMP.stg.mara m on c.sku=m.Articulo
	left join DWH.dbo.dim_tiempo dt on c.[Day] =dt.fecha 
where len(c.SKU)=7
	and c.[Day] >= CONVERT(date,GETDATE()-7)
group by c.[Day],c.Branch_ID,c.SKU,ds.descrip_tienda,ds.region,ds.zona,m.Descripcion,m.Depto,m.DescripDepto,m.SubDepto,m.DescripSubdepto,m.E3,dt.descrip_fecha
HAVING sum(found_rate *times_ordered)*100/cast(sum(times_ordered) as float) < 100;
```
### 6.0 Inserta los datos en la tabla report.faltante_sku SCRIPT(insert_report_faltante_sku)
```sql 
insert into DWH.report.faltante_sku
select dy.*
from 
(
	select dx.fecha,dx.store_num,ds.region,ds.zona,ds.descrip_tienda, 
	dx.sku,m.Descripcion,m.DescripDepto,m.DescripSubdepto,m.DescripClase, 
	dx.pedido_completo,dx.pedido_incompleto,(dx.pedido_completo + dx.pedido_incompleto) total_pedido,
	round(case when ma.MEINS='KG' then (dx.items_ori/1000.00) else dx.items_ori end,2) items_ori,
	round(case when ma.MEINS='KG' then (dx.items_fin/1000.00) else dx.items_fin end,2) items_fin,
	case when ma.MEINS='KG' and dx.items_ori-dx.items_fin <= 50 then 1 else round(dx.items_fin/cast(dx.items_ori as float),2) end as FillRate_online,
	null items_ori_cornershop,null items_fin_cornershop,--round(dy.items_ori_cornershop,2) items_ori_cornershop,round(dy.items_fin_cornershop,2) items_fin_cornershop,
	null FillRate_cornershop,--round(dy.items_fin_cornershop/cast(dy.items_ori_cornershop as float),2) FillRate_cornershop,	
	null vtapzs_tienda,
	null vtapzs_total,
	null InvFinUni,
	null pzaDif,
	null InvAnterior, 
	null id_respuesta 	
	from 
	(
	select 
	convert(date,ho.ultimo_cambio) fecha,ho.store_num,hs.sku,
	isnull(sum(case when isnull(ma.MEINS,'S/D') not in ('KG') and hs.items_fin >= hs.items_ori  then 1
	when isnull(ma.MEINS,'S/D') in ('KG') and hs.items_fin>0 and hs.items_ori > 0 then 1 else 0 end),0) pedido_completo,
	isnull(sum(case when isnull(ma.MEINS,'S/D') not in ('KG') and hs.items_fin >= hs.items_ori  then 0
	when isnull(ma.MEINS,'S/D') in ('KG') and hs.items_fin>0 and hs.items_ori > 0 then 0 else 1 end),0) pedido_incompleto,
	isnull(sum(case when isnull(ma.MEINS,'S/D') not in ('KG') and hs.items_fin >= hs.items_ori  then 0
	when isnull(ma.MEINS,'S/D') in ('KG') and hs.items_fin>0 and hs.items_ori > 0 then 0 else hs.items_ori end),0) items_ori,
	isnull(sum(case when isnull(ma.MEINS,'S/D') not in ('KG') and hs.items_fin >= hs.items_ori  then 0
	when isnull(ma.MEINS,'S/D') in ('KG') and hs.items_fin>0 and hs.items_ori > 0 then 0 else hs.items_fin end),0) items_fin
	from DWH.dbo.hecho_sku hs
	inner join DWH.dbo.hecho_order ho on hs.order_number = ho.order_number and hs.store_number =ho.store_num and convert(date,ho.ultimo_cambio)=hs.fecha_completo 
	left join DWH.artus.mara ma on ma.MATNR =hs.sku
	where hs.fecha_completo >= convert(date,GETDATE()-1)
	and ho.tmp_n_estatus is not null
	and hs.items_ori > 0
	and case when isnull(ma.MEINS,'S/D') not in ('KG') and hs.items_fin >= hs.items_ori  then 0
	when isnull(ma.MEINS,'S/D') in ('KG') and hs.items_fin>0 and hs.items_ori > 0 then 0 else 1 end > 0
	group by convert(date,ho.ultimo_cambio),ho.store_num,hs.sku ) dx
--left join
--(
--select 
--c.[Day] fecha,c.branch_id store_num,c.sku,
--sum(times_ordered) items_ori_cornershop , sum(found_rate *times_ordered) items_fin_cornershop
--from TEMP.stg.cornershop c 
--where len(c.SKU)=7
--and c.[Day] >= @fecha
--group by c.[Day],c.Branch_ID,c.SKU
-- ) dy 
-- on dx.fecha=dy.fecha and dx.store_num=dy.store_num and dx.sku=dy.sku
--left join DWH.artus.venta_sku vs on dx.fecha=concat('2021-',SUBSTRING(cast(vs.dia as varchar(10)),4,2),'-',RIGHT(vs.dia,2)) and dx.store_num=vs.tienda and dx.sku=vs.sku
--left join TEMP.stg.inventario_2021 i on dx.fecha=convert(date,i.FechaInven) and dx.sku=i.SKU and dx.store_num=i.Tienda
--left join TEMP.stg.inventario_2021 ii on dx.fecha=DATEADD(DAY,-1,convert(date,ii.FechaInven)) and dx.sku=ii.SKU and dx.store_num=ii.Tienda
	left join TEMP.stg.mara m on dx.sku=m.Articulo
	left join DWH.dbo.dim_store ds on dx.store_num=ds.idtienda
	left join DWH.artus.mara ma on ma.MATNR =dx.sku ) dy 	
	left join DWH.report.faltante_sku fs on fs.fecha=dy.fecha 
    and fs.store_num=dy.store_num 
    and fs.sku=dy.sku
where fs.sku is null;

update fs
set Descripcion=REPLACE(Descripcion,'''','')
FROM DWH.report.faltante_sku fs
WHERE fs.fecha = convert(date,GETDATE()-1);

update fs
set Descripcion=REPLACE(Descripcion,'#','')
FROM DWH.report.faltante_sku fs
WHERE fs.fecha = convert(date,GETDATE()-1);
```
### 7.0 Extraccion de informacion report.faltante_sku TRANS(dev_load_inventarioFaltante)
7.1 Extrae la informacion de report.faltante_sku (Table input)(input_reporte.faltante_sku)
```sql 
select fecha,store_num,sku 
from DWH.report.faltante_sku fs
where fecha = convert(date,GETDATE()-1)
```
7.2 Los datos se guardan en una tabla temporal (Table Output)(output_Temp_ventaDiariaTO)
``` sql 
temp.dbo.Omincal_data_Artus
```
### 8.0 Elimina los Registros temporales de Inventario SCRIPT(elimina_registros_inventario)
``` sql 
delete
from TEMP.stg.inventario_2021 
where FechaInven < convert(date,GETDATE()-10);
```     
### 9.0 Actualiza los datos de UP Sells SCRIPT(update_upSells)
``` sql 
update ho
set ho.upSells=1
from DWH.dbo.hecho_order ho
	inner join DWH.dbo.hecho_sku hs on ho.order_number =hs.order_number 
    and ho.store_num=hs.store_number
	inner join DWH.dbo.dim_estatus_sku des on hs.id_estatus_sku =des.id_estatus_sku 
where convert(date,data_update) > convert(date,GETDATE()-20)
	and ho.tmp_n_estatus = 'COMPLETO'
	and des.sku_status in ('COMPLETO_ADIC');
``` 

