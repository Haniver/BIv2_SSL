import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import Tabla from '../componentes/tablas/Tabla'
import userService from '../services/user.service'
// import userService from '../services/user.service'

const FoundRateCornershop = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [region, setRegion] = useState(userService.getRegionPorNivel())
    const [zona, setZona] = useState(userService.getZonaPorNivel())
    const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
    const [botonEnviar, setBotonEnviar] = useState(0)

    const seccion = 'FoundRateCornershop'

  return (
    <>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Found Rate Cornershop Vs. Chedraui' fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>
        {(tienda === '' || tienda === false || tienda === undefined) && <Col sm='12' lg='6'>
          <EjesMultiples titulo='Found Rate Cornershop Vs. Chedraui Por Lugar' fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>}
      </Row>
      {(tienda === '' || tienda === false || tienda === undefined) && <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Tabla titulo='Top 10 Tiendas con mejor Found Rate Chedraui' quitarBusqueda quitarPaginacion quitarExportar fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          <Tabla titulo='Top 10 Tiendas con mejor Found Rate Cornershop' quitarBusqueda quitarPaginacion quitarExportar fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Tabla titulo='Detalle Found Rate por Departamento' quitarBusqueda quitarPaginacion quitarExportar fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
          <EjesMultiples titulo='Found Rate Cornershop Vs. Chedraui Por Día' fechas={fechas} region={region} zona={zona} tienda={tienda} seccion={seccion} />
        </Col>
      </Row>
    </>
  )
}
export default FoundRateCornershop
