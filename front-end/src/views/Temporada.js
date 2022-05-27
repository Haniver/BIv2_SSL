import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import EjesMultiplesApilados from '../componentes/graficos/EjesMultiplesApilados'
import Tabla from '../componentes/tablas/Tabla'
import {
    DollarSign,
    Box,
    Calendar,
    Percent
  } from 'react-feather'
  

const Temporada = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.noUTC(new Date())})
    const [canal, setCanal] = useState(false)
    const [depto, setDepto] = useState('')
    const [subDepto, setSubDepto] = useState('')
    const [clase, setClase] = useState('')
    const [subClase, setSubClase] = useState('')
    // console.log(`Fecha y hora actual: ${new Date()}`)

    useEffect(() => {
      setSubDepto('')
    }, [depto])

    useEffect(() => {
      setClase('')
    }, [subDepto])

    useEffect(() => {
      setSubClase('')
    }, [clase])

    // useEffect(() => {
    //   console.log(fechas)
    // }, [fechas])

    const seccion = 'Temporada'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro mismoMes fechas={fechas} canal={canal} setFechas={setFechas} setCanal={setCanal} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col>
            <Tarjeta icono={<DollarSign size={21} />} seccion={seccion} formato='moneda' titulo='Venta Última Hora' />
        </Col>
        <Col>
            <Tarjeta icono={<Box size={21} />} seccion={seccion} formato='entero' titulo='Pedidos Última Hora' />
        </Col>
         <Col>
            <Tarjeta icono={<DollarSign size={21} />} seccion={seccion} formato='moneda' titulo='Venta Hoy' canal={canal} />
        </Col>
        <Col>
            <Tarjeta icono={<Percent size={21} />} seccion={seccion} formato='porcentaje' titulo='% Participación Venta Hoy' canal={canal} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos Levantados Hoy (con impuesto)' fechas={fechas} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos Pagados Hoy (sin impuesto)' canal={canal} fechas={fechas} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos por Día' fechas={fechas} canal={canal} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados splineLabelsEnabled seccion={seccion} titulo='Venta por Región' fechas={fechas} canal={canal} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados splineLabelsEnabled seccion={seccion} titulo='Venta por Departamento' fechas={fechas} canal={canal} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados splineLabelsEnabled seccion={seccion} titulo='Venta por Formato' fechas={fechas} canal={canal} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
            <Tabla quitarPaginacion seccion={seccion} titulo='Detalle Departamentos' fechas={fechas} canal={canal} setSibling={setDepto} />
        </Col>
      </Row>
      {depto !== '' && depto !== undefined && <Row className='match-height'>
        <Col sm='12'>
            <Tabla quitarPaginacion seccion={seccion} titulo={`Detalle Sub-Departamentos para Depto ${depto}`} tituloAPI='Detalle Sub-Departamentos para Depto $depto' fechas={fechas} canal={canal} fromSibling={depto} setSibling={setSubDepto} />
        </Col>
      </Row>}
      {subDepto !== '' && subDepto !== undefined && <Row className='match-height'>
        <Col sm='12'>
            <Tabla quitarPaginacion seccion={seccion} titulo={`Detalle Clases para SubDepto ${subDepto}`} tituloAPI='Detalle Clases para SubDepto $subDepto' fechas={fechas} canal={canal} fromSibling={subDepto} setSibling={setClase} />
        </Col>
      </Row>}
      {clase !== '' && clase !== undefined && <Row className='match-height'>
        <Col sm='12'>
            <Tabla quitarPaginacion seccion={seccion} titulo={`Detalle Sub-Clases para Clase ${clase}`} tituloAPI='Detalle Sub-Clases para Clase $clase' fechas={fechas} canal={canal} fromSibling={clase} setSibling={setSubClase} />
        </Col>
      </Row>}
      {subClase !== '' && subClase !== undefined && <Row className='match-height'>
        <Col sm='12'>
            <Tabla quitarPaginacion seccion={seccion} titulo={`Detalle Formatos para SubClase ${subClase}`} tituloAPI='Detalle Formatos para SubClase $subClase' fechas={fechas} canal={canal} fromSibling={subClase} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Card>
              <CardBody>
              <iframe src="https://datastudio.google.com/embed/reporting/f39d3f71-6d94-4827-8a79-77f470d3ce67/page/K02eC" allowFullScreen frameBorder={0} width='100%' height='500px'></iframe>
              </CardBody>
          </Card>
        </Col>
      </Row>
    </>
  )
}
export default Temporada
