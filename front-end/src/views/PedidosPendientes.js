import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'

const PedidosPendientes = () => {
  const [tipoEntrega, setTipoEntrega] = useState(false)
  const [region, setRegion] = useState(false)
  const [zona, setZona] = useState(false)
  const [tienda, setTienda] = useState(false)

  const seccion = 'PedidosPendientes'

  return (
    <Fragment>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} setTipoEntrega={setTipoEntrega} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Área' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Pedidos del Día' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Fecha' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} />
        </Col>
        {(tienda === '' || tienda === undefined || tienda === false) && <Col xl='6' sm='12'>
          <Tabla titulo='Tiendas con Pedidos Atrasados Mayores a 1 Día' seccion={seccion} region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} />
        </Col>}
        {(tienda !== '' && tienda !== undefined && tienda !== false) && <Col xl='6' sm='12'>
          <Tabla titulo={`Detalle de pedidos tienda ${tienda}`} tituloAPI= 'Detalle de pedidos tienda $tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} />
        </Col>}
      </Row>
      <Row className='match-height'>
      {(tienda === '' || tienda === undefined || tienda === false) && <Col xl='6' sm='12'>
          <Tabla titulo='Pedidos No Entregados o No Cancelados' seccion={seccion} region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} opcionesPaginacion={[5, 10, 20, 50, 100]} />
        </Col>}
      {(tienda !== '' && tienda !== undefined && tienda !== false) && <Col xl='6' sm='12'>
          <Tabla titulo={`Pedidos No Entregados o No Cancelados ${tienda}`} tituloAPI='Pedidos No Entregados o No Cancelados $tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} opcionesPaginacion={[5, 10, 20, 50, 100]} />
        </Col>}
      </Row>
    </Fragment>
  )
}
export default PedidosPendientes
