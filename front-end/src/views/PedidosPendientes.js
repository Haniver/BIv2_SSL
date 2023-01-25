import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import Pie from '../componentes/graficos/Pie'
import Titulo from '../componentes/auxiliares/Titulo'
import ColumnasBasicas from '../componentes/graficos/ColumnasBasicas'
import EjesMultiples from '../componentes/graficos/EjesMultiples'

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
          <Filtro region={region} zona={zona} tienda={tienda} tipoEntrega={tipoEntrega} setTipoEntrega={setTipoEntrega} setRegion={setRegion} setZona={setZona} setTienda={setTienda} botonEnviar={botonEnviar} setBotonEnviar={setBotonEnviar} />
        </Col>
      </Row>
      <Row className='match-height'>
        {/* <Col sm='12'>
          <ErrorBoundary 
            FallbackComponent={ErrorHandling.ErrorFallback} 
            // onError={ErrorHandling.myErrorHandler} 
            // onReset={() => {
            //   // reset the state of the app
            // }}
          >
            <Leyenda seccion={seccion} titulo='Última actualización:' />
          </ErrorBoundary>
        </Col> */}
      </Row>
      <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasBasicas extenderDerecha subtitulo = 'Pedidos Pendientes de Entrega Hoy' titulo='Pedidos pendientes de entrega' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} coloresPedidosPendientes />
        </Col>
        <Col xl='6' sm='12'>
          <ColumnasApiladas extenderIzquierda titulo='Entrega de pedidos por ventana de tiempo' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>
      </Row>
      <Row className='match-height'>
        {!tipoEntrega && <Col xl='6' sm='12'>
          <Pie titulo='Pedidos Por Tipo de Entrega' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>}
        <Col xl={tipoEntrega ? '12' : '6'} sm='12'>
          <ColumnasApiladas titulo='Pedidos Por Región' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col xl='12' sm='12'>
          <ColumnasApiladas titulo='Entrega de pedidos por fecha' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col>
        {/* <Col xl='6' sm='12'>
          <EjesMultiples titulo='Pedidos Programados para Siguientes Días' seccion={seccion} formato='entero' yLabel='Pedidos' tipoEntrega={tipoEntrega} region={region} zona={zona} tienda={tienda} origen={origen} />
        </Col> */}
      </Row>
      {(tienda === '' || tienda === undefined || tienda === false) && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Tiendas con Pedidos Atrasados Mayores a 1 Día' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      {(tienda !== '' && tienda !== undefined && tienda !== false) && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Detalle de pedidos tienda ${tienda}`} tituloAPI= 'Detalle de pedidos tienda $tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      {(tienda === '' || tienda === undefined || tienda === false) && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Detalle Pedidos Pendientes por Tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
      {(tienda !== '' && tienda !== undefined && tienda !== false) && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo={`Pedidos No Entregados o No Cancelados Tienda ${tienda}`} tituloAPI='Pedidos No Entregados o No Cancelados Tienda $tienda' seccion={seccion} region={region} zona={zona} tienda={tienda} origen={origen} tipoEntrega={tipoEntrega} />
        </Col>
      </Row>}
    </Fragment>
  )
}
export default PedidosPendientes
