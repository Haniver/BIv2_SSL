import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import CargarFiltros from '../services/cargarFiltros'
import Pie from '../componentes/graficos/Pie'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import fechas_srv from '../services/fechas_srv'
import userService from '../services/user.service'

const Home = () => {
  const illustration = 'home_paleta.svg',
    source = require(`@src/assets/images/pages/${illustration}`).default
  const seccion = 'Home'
  const userData = localStorage.getItem('userData')
  const tienda_tmp = JSON.parse(userData).tienda
  // console.log(`tienda_tmp = ${tienda_tmp}`)
  const [tiendaNombre, setTiendaNombre] = useState('')
  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const email = userService.getEmail()
  useEffect(async () => {
    if (tienda_tmp !== null) {
        const tiendaNombre_tmp = await CargarFiltros.nombreTienda(tienda_tmp)
        setTiendaNombre(tiendaNombre_tmp.data.nombreTienda)
        if (userService === 3) {
          setRegion(userService.getRegion())
        } else if (userService === 2) {
          setRegion(userService.getRegion())
          setZona(userService.getZona())
        } else if (userService === 1) {
          setRegion(userService.getRegion())
          setZona(userService.getZona())
          setTienda(tienda_tmp)
        }
      }
    }, [])
  const hoy = new Date()
  const fechas_dia = {fecha_ini: hoy, fecha_fin: hoy}
  const fechas_mes = {fecha_ini: fechas_srv.primeroDelMesSinVencer(), fecha_fin: hoy}
  const agrupador = 'dia'
  // console.log(`Hoy es:`)
  // console.log(hoy)

  if (tienda_tmp !== null) {
    return (
      <Fragment>
        <Row className='match-height'>
          <Col xl='6' sm='12'>
            <ColumnasApiladas titulo='Pedidos del Día' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas_dia} region={region} zona={zona} tienda={tienda} />
          </Col>
          <Col xl='6' sm='12'>
            <Pie titulo='Estatus de Entrega y No Entrega' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas_dia} region={region} zona={zona} tienda={tienda} />
          </Col>
        </Row>
        <Row className='match-height'>
          <Col sm='12'>
            <EjesMultiples titulo='Fulfillment Rate y Found Rate' seccion={seccion} fechas={fechas_mes} region={region} zona={zona} tienda={tienda} />
          </Col>
        </Row>
        <Row className='match-height'>
          <Col sm='12'>
            <EjesMultiples titulo='Pedidos Perfectos' fechas={fechas_mes} region={region} zona={zona} tienda={tienda} agrupador={agrupador} seccion={seccion} />
          </Col>
        </Row>
      </Fragment>
    )
  } else {
    return (
      <Fragment>
        <div className='w-100 d-lg-flex align-items-center justify-content-center px-5'>
          <img className='img-fluid' src={source} />
        </div>
      </Fragment>
    )
  }
}
export default Home
