import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import Barras from '../componentes/graficos/Barras'
import ColumnasBasicas from '../componentes/graficos/ColumnasBasicas'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
// import userService from '../services/user.service'
import tarjetasCombinadas from '../services/tarjetasCombinadas'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import Pie from '../componentes/graficos/Pie'
import userService from '../services/user.service'

import {
  LogIn,
  LogOut,
  Percent,
  Search,
  Maximize
} from 'react-feather'

const FoundRate = () => {
  const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
  const [region, setRegion] = useState(userService.getRegionPorNivel())
  const [zona, setZona] = useState(userService.getZonaPorNivel())
  const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
  const [tarjetasOriginalYFinal, setTarjetasOriginalYFinal] = useState({res: {'Monto Original': '', 'Monto Final': '', '% Variación': ''}})
  const [tarjetasFoundYFulfillment, setTarjetasFoundYFulfillment] = useState({res: {'Found Rate': '', 'Fulfillment Rate': ''}})
  const [botonEnviar, setBotonEnviar] = useState(0)

  const seccion = 'FoundRate'
  
  useEffect(async () => {
    const res1 = await tarjetasCombinadas(seccion, 'OriginalYFinal', {
        fechas, 
        region, 
        zona, 
        tienda
    })
    setTarjetasOriginalYFinal(res1)
    const res2 = await tarjetasCombinadas(seccion, 'FoundYFulfillment', {
        fechas, 
        region, 
        zona, 
        tienda
    })
    setTarjetasFoundYFulfillment(res2)
  }, [fechas, region, zona, tienda])

    return (
    <Fragment>
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
        <Col sm='4'>
          <Tarjeta formato='moneda' icono={<LogIn size={21} />} titulo='Monto Original' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasOriginalYFinal}  />
        </Col>
        <Col sm='4'>
          <Tarjeta formato='moneda' icono={<LogOut size={21} />} titulo='Monto Final' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasOriginalYFinal}  />
        </Col>
        <Col sm='4'>
          <Tarjeta formato='porcentaje' icono={<Percent size={21} />} titulo='% Variación' colorPositivo fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasOriginalYFinal}  />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
      <Col sm='12'>
          <Barras titulo='Monto Original Vs. Final' seccion={seccion} formato='moneda' yLabel='' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Lugar' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <Pie titulo='Estatus de pedidos (Totales)' formato='entero' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      {tienda !== false && tienda !== '' && <Row className='match-height'>
        <Col sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Día' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col xl='6' sm='12'>
          <Tarjeta formato='porcentaje' icono={<Search size={21} />} titulo='Found Rate' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasFoundYFulfillment}  />
        </Col>
        <Col xl='6' sm='12'>
          <Tarjeta formato='porcentaje' icono={<Maximize size={21} />} titulo='Fulfillment Rate' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasFoundYFulfillment}  />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasBasicas titulo='Found Rate Vs. Fulfillment Rate' seccion={seccion} formato='porcentaje' yLabel='Porcentaje' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <Tabla titulo='Detalle Porcentaje Estatus por Lugar' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      {tienda !== false && tienda !== '' && <Row className='match-height'>
        <Col sm='12'>
          <Pie titulo='Detalle Porcentaje Estatus por Lugar' formato='entero' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Fulfillment Rate, Found Rate y Pedidos por Día' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Estatus por Tienda' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        {/* <Col xl='6' sm='12'>
          <Tabla titulo='Tiendas Top 20 Estatus Incompleto' quitarPaginacion seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col> */}
      </Row>}
      {tienda !== false && tienda !== '' && <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Detalle de Pedidos Tienda' seccion={seccion} fechas={fechas} tienda={tienda} />
        </Col>
      </Row>}
    </Fragment>
  )
}
export default FoundRate
