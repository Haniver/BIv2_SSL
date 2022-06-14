import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import CargarFiltros from '../services/cargarFiltros'
import Pie from '../componentes/graficos/Pie'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import fechas_srv from '../services/fechas_srv'

const Home = () => {
  const illustration = 'home_paleta.svg',
    source = require(`@src/assets/images/pages/${illustration}`).default
  const seccion = 'Home'
  const userData = localStorage.getItem('userData')
  const tienda = JSON.parse(userData).tienda
  const [tiendaNombre, setTiendaNombre] = useState('')
  useEffect(async () => {
    if (tienda !== null) {
        const tiendaNombre_tmp = await CargarFiltros.nombreTienda(tienda)
        setTiendaNombre(tiendaNombre_tmp.data.nombreTienda)
      }
    }, [])
  const hoy = new Date()
  const fechas_dia = {fecha_ini: hoy, fecha_fin: hoy}
  const fechas_mes = {fecha_ini: fechas_srv.primeroDelMesSinVencer(), fecha_fin: hoy}
  const agrupador = 'dia'
  console.log(`Hoy es:`)
  console.log(hoy)

  return (
    <Fragment>
      {tienda !== null && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{tiendaNombre}</h2>
        </Col>
      </Row>}
      {tienda !== null && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Pedidos del Día' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas_dia} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <Pie titulo='Estatus de Entrega y No Entrega por Área' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas_dia} tienda={tienda} />
        </Col>
      </Row>}
      {tienda !== null && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Fulfillment Rate y Found Rate' seccion={seccion} fechas={fechas_mes} tienda={tienda} />
        </Col>
      </Row>}
      {tienda !== null && <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Pedidos Perfectos' fechas={fechas_mes} tienda={tienda} agrupador={agrupador} seccion={seccion} />
        </Col>
      </Row>}
      {tienda === null && <Row className='match-height'>
        <Col className='d-none d-lg-flex align-items-center p-5' sm='12'>
          <div className='w-100 d-lg-flex align-items-center justify-content-center px-5'>
            <img className='img-fluid' src={source} alt='Login V2' />
          </div>
        </Col>
      </Row>}
    </Fragment>
  )
}
export default Home
