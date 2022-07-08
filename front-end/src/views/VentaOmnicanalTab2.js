import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import fechas_srv from '../services/fechas_srv'
import Pie from '../componentes/graficos/Pie'
import ColumnasDrilldown from '../componentes/graficos/ColumnasDrilldown'
import Tabla from '../componentes/tablas/Tabla'
import {
  ShoppingCart,
  FileText,
  Search,
  Maximize
} from 'react-feather'

const VentaOmnicanalTab2 = () => {
  const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
  const [proveedor, setProveedor] = useState(0)

  const seccion = 'VentaOmnicanal'
    // Para debugging
//   useEffect(() => {
//     console.log(`fecha_ini: ${fecha_ini}`)
//     console.log(`fecha_fin: ${fecha_fin}`)
//     console.log(`proveedor: ${proveedor}`)
//   }, [fechas, proveedor])

  return (
    <Fragment>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro fechas={fechas} proveedor={proveedor} setFechas={setFechas} setProveedor={setProveedor} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Tabla titulo='Venta Top 200 Proveedores' seccion={seccion} fechas={fechas} proveedor={proveedor} />
        </Col>
        <Col sm='12' lg='6'>
          <ColumnasDrilldown titulo='Monto de Venta por Departamento' labelOrdenadas='Monto de Venta' seccion={seccion} formato='moneda' fechas={fechas} proveedor={proveedor} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Top 1,000 SKU' seccion={seccion} fechas={fechas} proveedor={proveedor} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Tabla titulo='Venta por día' seccion={seccion} fechas={fechas} proveedor={proveedor} />
        </Col>
      </Row>
    </Fragment>
  )
}
export default VentaOmnicanalTab2
