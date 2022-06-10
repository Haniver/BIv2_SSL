import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import ColumnasApiladas from '../componentes/graficos/ColumnasApiladas'
import Barras from '../componentes/graficos/Barras'
import ColumnasBasicas from '../componentes/graficos/ColumnasBasicas'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
import userService from '../services/user.service'
import tarjetasCombinadas from '../services/tarjetasCombinadas'
import Tarjeta from '../componentes/auxiliares/Tarjeta'

import {
  LogIn,
  LogOut,
  Percent
} from 'react-feather'

const FoundRate = () => {
  const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
  const [region, setRegion] = useState(false)
  const [zona, setZona] = useState(false)
  const [tienda, setTienda] = useState(false)
  const [tarjetasCombinadasTienda, setTarjetasCombinadasTienda] = useState({res: {'Monto Original': '', 'Monto Final': '', '% Variación': ''}})
  
  const seccion = 'FoundRate'
  
  useEffect(async () => {
    if (tienda !== false && tienda !== undefined && tienda !== '') {
      // setTarjetasCombinadasTienda('cargando')
      const res = await tarjetasCombinadas(seccion, 'Anio', {
          fechas, 
          region, 
          zona, 
          tienda
      })
      setTarjetasCombinadasTienda(res)
    }
  }, [fechas, region, zona, tienda])

    return (
    <Fragment>
      {userService.getNivel() <= 3 && <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>{userService.getLugarNombre()}</h2>
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} region={region} zona={zona} tienda={tienda} setFechas={setFechas} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Lugar' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <Barras titulo='Monto Original Vs. Final' seccion={seccion} formato='moneda' yLabel='' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      {tienda !== false && tienda !== '' && <Row className='match-height'>
        <Col sm='12'>
          <ColumnasApiladas titulo='Estatus Pedidos por Día' seccion={seccion} formato='entero' yLabel='Pedidos' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      {tienda !== false && tienda !== '' && <Row className='match-height'>
        <Col sm='4'>
          <Tarjeta formato='moneda' icono={<LogIn size={21} />} titulo='Monto Original' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasCombinadasTienda}  />
        </Col>
        <Col sm='4'>
          <Tarjeta formato='moneda' icono={<LogOut size={21} />} titulo='Monto Final' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasCombinadasTienda}  />
        </Col>
        <Col sm='4'>
          <Tarjeta formato='porcentaje' icono={<Percent size={21} />} titulo='% Variación' fechas={fechas} region={region} zona={zona} tienda={tienda} resAPI={tarjetasCombinadasTienda}  />
        </Col>
      </Row>}
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <ColumnasBasicas titulo='Found Rate Vs. Fulfillment Rate' seccion={seccion} formato='porcentaje' yLabel='Porcentaje' fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <Tabla titulo='Detalle Porcentaje Estatus por Lugar' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>}
      <Row className='match-height'>
        <Col sm='12'>
          <EjesMultiples titulo='Fulfillment Rate, Found Rate y Pedidos por Día' seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
      </Row>
      {(tienda === false || tienda === '') && <Row className='match-height'>
        <Col xl='6' sm='12'>
          <Tabla titulo='Tiendas Top 20 Estatus Completo' quitarPaginacion seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
        <Col xl='6' sm='12'>
          <Tabla titulo='Tiendas Top 20 Estatus Incompleto' quitarPaginacion seccion={seccion} fechas={fechas} region={region} zona={zona} tienda={tienda} />
        </Col>
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
