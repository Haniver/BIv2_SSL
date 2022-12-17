import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import TarjetaEnFila from '../componentes/auxiliares/TarjetaEnFila'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import EjesMultiplesApilados from '../componentes/graficos/EjesMultiplesApilados'
import Tabla from '../componentes/tablas/Tabla'
import Leyenda from '../componentes/auxiliares/Leyenda'
import {
    DollarSign,
    Box,
    Calendar,
    Percent,
    FileText,
    Package
  } from 'react-feather'
  

const Temporada = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesSinVencer(), fecha_fin: fechas_srv.noUTC(new Date())})
    const [canal, setCanal] = useState(1)
    const [depto, setDepto] = useState('')
    const [subDepto, setSubDepto] = useState('')
    const [clase, setClase] = useState('')
    const [subClase, setSubClase] = useState('')
    const [fuenteDataStudio, setFuenteDataStudio] = useState('')
    const hora = new Date().getHours()
    const [botonEnviar, setBotonEnviar] = useState(0)

    // useEffect(() => {
    //   console.log(`canal=${canal}`)
    // }, [canal])
    useEffect(() => {
      setSubDepto('')
    }, [depto])

    useEffect(() => {
      setClase('')
    }, [subDepto])

    useEffect(() => {
      setSubClase('')
    }, [clase])

    useEffect(() => {
      if ((fechas.fecha_fin.getMonth() <= 4 && fechas.fecha_fin.getFullYear() === 2022) || fechas.fecha_fin.getFullYear() < 2022) {
        setFuenteDataStudio("https://datastudio.google.com/embed/reporting/f39d3f71-6d94-4827-8a79-77f470d3ce67/page/K02eC")
      } else {
        setFuenteDataStudio("https://datastudio.google.com/embed/reporting/ccd588c9-6f90-4f72-b878-8f6c7233cde3/page/K02eC")
      }
    }, [fechas])

    const seccion = 'Temporada'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Leyenda seccion={seccion} titulo='Última actualización:' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro mismoMes fechas={fechas} canal={canal} setFechas={setFechas} setCanal={setCanal} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      {hora >= 8 && <Row className='match-height'>
        <Col sm='12'>
          <TarjetaEnFila seccion={seccion} formato='moneda' titulo='Indicadores' cols={{ xl: '4', sm: '6' }}/>
        </Col>
      </Row>}
      {hora >= 8 && <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos Levantados Hoy (con impuesto - todos los canales)' fechas={fechas} />
        </Col>
      </Row>}
      {hora >= 8 && <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos Pagados Hoy (sin impuesto)' canal={canal} fechas={fechas} />
        </Col>
      </Row>}
      {hora >= 8 && <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados seccion={seccion} titulo='Pedidos por Día' fechas={fechas} canal={canal} />
        </Col>
      </Row>}
      {hora >= 8 && <Row className='match-height'>
        <Col sm='12'>
            <EjesMultiplesApilados splineLabelsEnabled seccion={seccion} titulo='Venta por Región' fechas={fechas} canal={canal} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
            <Tabla seccion={seccion} titulo='Venta por Tienda' fechas={fechas} canal={canal} />
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
              <iframe src={fuenteDataStudio} allowFullScreen frameBorder={0} width='100%' height='500px'></iframe>
              </CardBody>
          </Card>
        </Col>
      </Row>
    </>
  )
}
export default Temporada
