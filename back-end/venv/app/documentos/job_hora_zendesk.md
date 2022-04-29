# job_hora_zendesk
|Periodo de Ejecucion|Hora de Ejecucion|Dependencias|
|--|--|--|
|(periodo)|(hora)|(dependencias)|   

# Job Steps:
![Vista_job_p_dwh_order_sku.png](/docs/job_hora_zendesk/Vista_job_hora_zendesk.png)

### 1.0  Api que extrae la informacion del portar de Zendesk TRANS(dev_load_API_Zendesk)

### 2.0  Actualiza e Inserta la informacion en la tabla hecho_ticket_zendesk  SCRIPT(insert_updat_hecho_ticket_zendesk)
``` sql 
update htz
set htz.priority=tz.priority,
htz.status=tz.status,
htz.order_number=tz.order_number,
htz.fecha_creacion=tz.fecha_creacion,
htz.fecha_update=tz.fecha_update,
htz.campo=tz.campo,
htz.id_user=tz.id_user
from DWH.dbo.hecho_ticket_zendesk htz
inner join TEMP.stg.ticket_zendesk tz on htz.id = tz.id and htz.id_formulario = tz.id_formulario and htz.id_campo = tz.id_campo;

insert into DWH.dbo.hecho_ticket_zendesk
select tz.*
from TEMP.stg.ticket_zendesk tz 
left join DWH.dbo.hecho_ticket_zendesk htz on htz.id = tz.id and htz.id_formulario = tz.id_formulario and htz.id_campo = tz.id_campo
where htz.id is null;

delete
from DWH.dbo.hecho_ticket_zendesk 
where id in (679496,675829,679402,675629,674780,689266,686683,689924,689278,689653,691697,678128,692207,693327,694388,692605,695618,698402,
700137,726655,727365,738439,739727,673840,740035,738490,739596,746895,748784,752688,752684,745536,751214,751228,762915,766409,765990,765031,
768444,770805,780441,782236,784444,789250,788503,791856,805268,804650,811782,833920,843734,862603,869211,892544,870943,871914,876752,887126,
877426,914046,933839,927422,914794,914658,916951,920968,925184,939496,1035873,1038192,1037958,1039705,1039445,1042424) and formulario = 'Incidencia';
```

### 3.0  Actualiza e Inserta la informacion en la tabla hecho_ticket_zendesk  SCRIPT(update_quejas_hecho_order)
``` sql 
update ho
set ho.id_ticket_zendesk_queja=dx.id,
ho.data_update=getdate()
from DWH.dbo.hecho_order ho 
inner join (

    select htz.id,htz.priority,htz.status,htz.order_number,(htz.fecha_creacion - 0.25) fecha_creacion,htz.fecha_update,htz.formulario,
    max(case when htz.id_campo = 360028982073 then htz.campo end) Tipo_incidencia,  
    max(case when htz.id_campo = 360030010334 then htz.campo end) Consigna,
    max(ds.idtienda) idtienda, max(ds.region) region,max(ds.zona) zona,max(ds.descrip_tienda) descrip_tienda
    --dtz.id_campo,dtz.titulo_campo,htz.campo,ds.descrip_zendesk 
    from DWH.dbo.hecho_ticket_zendesk htz
    left join DWH.dbo.dim_store ds on htz.campo = ds.etiqueta_zendesk and id_campo = 360028995534
    left join DWH.dbo.dim_ticket_zendesk dtz on htz.id_campo = dtz.id_campo
    WHERE CONVERT(date,htz.fecha_creacion - 0.25) between convert(date,getdate()-7) and convert(date,getdate()-1) 
    group by htz.id,htz.priority,htz.status,htz.order_number,(htz.fecha_creacion - 0.25),htz.fecha_update,htz.formulario        
) dx on cast(ho.order_number as varchar) = dx.order_number  and ho.store_num=dx.idtienda
    where dx.Tipo_incidencia in ('incidencia_devolucion_producto','entrega_en_falso_','entrega_incompleta_de_pedido','pedido_retrasado_')
    and dx.formulario='Incidencia'
    and dx.idtienda is not null
    and dx.consigna is null;

update ho
set ho.id_ticket_zendesk_queja=dx.id,
ho.data_update=getdate()
from DWH.dbo.hecho_order ho 
inner join (

    select htz.id,htz.priority,htz.status,htz.order_number,(htz.fecha_creacion - 0.25) fecha_creacion,htz.fecha_update,htz.formulario,
    max(case when htz.id_campo = 360028982073 then htz.campo end) Tipo_incidencia,  
    max(case when htz.id_campo = 360030010334 then htz.campo end) Consigna,
    max(ds.idtienda) idtienda, max(ds.region) region,max(ds.zona) zona,max(ds.descrip_tienda) descrip_tienda
    --dtz.id_campo,dtz.titulo_campo,htz.campo,ds.descrip_zendesk 
    from DWH.dbo.hecho_ticket_zendesk htz
    left join DWH.dbo.dim_store ds on htz.campo = ds.etiqueta_zendesk and id_campo = 360028995534
    left join DWH.dbo.dim_ticket_zendesk dtz on htz.id_campo = dtz.id_campo
    WHERE CONVERT(date,htz.fecha_creacion - 0.25) between convert(date,getdate()-7) and convert(date,getdate()-1)      
    group by htz.id,htz.priority,htz.status,htz.order_number,(htz.fecha_creacion - 0.25),htz.fecha_update,htz.formulario        
) dx on ho.consignment_number = dx.consigna
    where dx.Tipo_incidencia in ('incidencia_devolucion_producto','entrega_en_falso_','entrega_incompleta_de_pedido','pedido_retrasado_')
    and dx.formulario='Incidencia'
    and dx.idtienda is not null
    and dx.consigna is not null;  
```