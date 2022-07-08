import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import Pie from '../componentes/graficos/Pie'


const Faltantes = () => {
    
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [agrupador, setAgrupador] = useState('semana')
    
    const seccion = 'Faltantes'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setAgrupador={setAgrupador} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Pie titulo='Tasa de justificados' formato='entero' fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          <Tabla titulo='Justificaciones' seccion={seccion} quitarBusqueda={true} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} />
        </Col>
      </Row>
      <Row className='match-height'>
        {(zona === '' || zona === false || zona === undefined) && <Col sm='12' lg='6'>
          <Tabla titulo='Justificados por Lugar' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} />
        </Col>}
        <Col sm='12' lg={(zona === '' || zona === false || zona === undefined) ? '6' : '12'}>
          <Tabla titulo='Justificados por Tienda' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Justificados por Departamento' seccion={seccion} quitarBusqueda={true} fechas={fechas} region={region} zona={zona} tienda={tienda} agrupador={agrupador} />
        </Col>
      </Row>
    </>
  )
}
export default Faltantes
