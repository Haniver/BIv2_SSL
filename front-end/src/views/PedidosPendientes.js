import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import Pie from '../componentes/graficos/Pie'
import Leyenda from '../componentes/auxiliares/Leyenda'
import Titulo from '../componentes/auxiliares/Titulo'

const PedidosPendientes = () => {
  const [tipoEntrega, setTipoEntrega] = useState('')
  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [origen, setOrigen] = useState('Vtex')
  const [botonEnviar, setBotonEnviar] = useState(0)

  const seccion = 'PedidosPendientes'

  return (
    <Fragment>
      <Row className='match-height'>
        <Col sm='12'>
          <Titulo titulo='Pedidos Pendientes' subtitulo='Información de pedidos pendientes de entrega a cliente' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} origen={origen} setTipoEntrega={setTipoEntrega} setRegion={setRegion} setZona={setZona} setTienda={setTienda} setOrigen={setOrigen} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Leyenda seccion={seccion} titulo='Última actualización:' />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col xl={tipoEntrega ? '12' : '6'} sm='12'>
          <Pie extenderDerecha titulo='Estatus Pedidos No Entregados' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} coloresPedidosPendientes />
        </Col>
        {!tipoEntrega && <Col xl='6' sm='12'>
          <Pie titulo='Pedidos Por Tipo de Entrega' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>}
      </Row>
      <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Área' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Pedidos del Día' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Fecha' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>
        {(tienda === '' || tienda === undefined || tienda === false) && <Col xl='6' sm='12'>
          <Tabla titulo='Tiendas con Pedidos Atrasados Mayores a 1 Día' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} />
        </Col>}
        {(tienda !== '' && tienda !== undefined && tienda !== false) && <Col xl='6' sm='12'>
          <Tabla titulo={`Detalle de pedidos tienda ${tienda}`} tituloAPI= 'Detalle de pedidos tienda $tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} />
        </Col>}
      </Row>
      <Row className='match-height'>
      {(tienda === '' || tienda === undefined || tienda === false) && <Col sm='12'>
          <Tabla titulo='Pedidos No Entregados o No Cancelados' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} opcionesPaginacion={[20, 40, 60, 80, 100]} />
        </Col>}
      {(tienda !== '' && tienda !== undefined && tienda !== false) && <Col sm='12'>
          <Tabla titulo={`Pedidos No Entregados o No Cancelados Tienda ${tienda}`} tituloAPI='Pedidos No Entregados o No Cancelados Tienda $tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} opcionesPaginacion={[5, 10, 20, 50, 100]} />
        </Col>}
      </Row>
    </Fragment>
  )
}
export default PedidosPendientes
