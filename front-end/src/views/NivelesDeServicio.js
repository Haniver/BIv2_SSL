import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import Pie from '../componentes/graficos/Pie'
import Tabla from '../componentes/tablas/Tabla'
// import userService from '../services/user.service'

const NivelesDeServicio = () => {
  const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
  const [region, setRegion] = useState(false)
  const [zona, setZona] = useState(false)
  const [tienda, setTienda] = useState(false)
  const [categoria, setCategoria] = useState(false)
  const [tipoEntrega, setTipoEntrega] = useState(false)

  const seccion = 'NivelesDeServicio'

  // useEffect(() => {
  //   console.log(`categoria: ${categoria}`)
  //   console.log(`tipoEntrega: ${tipoEntrega}`)
  // }, [fechas, region, zona, tienda, categoria, tipoEntrega])

  return (
    <Fragment>
      {/* {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>} */}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setCategoria={setCategoria} setTipoEntrega={setTipoEntrega} />
        </Col>
      </Row>
      {(tienda === '' || tienda === false || tienda === undefined) && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus de Entrega y No Entrega por Área' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Pedidos Cancelados por Área' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      {(tienda === '' || tienda === false || tienda === undefined) && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Estatus de Entrega y No Entrega por Área' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      {tienda !== '' && tienda !== false && tienda !== undefined && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <Pie titulo='Estatus de Entrega y No Entrega por Área' formato='entero' seccion={seccion} yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
        <Col xl='6' sm='12'>
          <Pie titulo='Pedidos Cancelados por Área' formato='entero' seccion={seccion} yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <ColumnasApiladas titulo='Estatus de Entrega y No Entrega por Día' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} categoria={categoria} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>
    </Fragment>
  )
}
export default NivelesDeServicio
