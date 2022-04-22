import { Fragment, useState, useEffect } from 'react'
import { Row, Col, Card, CardBody } from 'reactstrap'
import Filtro from '../componentes/auxiliares/Filtro'
import fechas_srv from '../services/fechas_srv'
import Tarjeta from '../componentes/auxiliares/Tarjeta'
import ColumnasSuperpuestas from '../componentes/graficos/ColumnasSuperpuestas'
import Burbuja3D from '../componentes/graficos/Burbuja3D'
import AreaBasica from '../componentes/graficos/AreaBasica'
import Tabla from '../componentes/tablas/Tabla'
import {
    Users,
    UserPlus,
    UserCheck,
    FileText
  } from 'react-feather'
import EjesMultiples from '../componentes/graficos/EjesMultiples'
// import Distribucion3D from '../componentes/graficos/Distribucion3D'
import Distribucion3D from '../componentes/graficos/Distribucion3D'
  
const ResultadoRFM = () => {
    
    const [fechas, setFechas] = useState({fecha_ini: fechas_srv.primeroDelMesVencido(), fecha_fin: fechas_srv.actualVencida()})
    const [anioRFM, setAnioRFM] = useState(fechas_srv.anioActual())
    const [mesRFM, setMesRFM] = useState(fechas_srv.mesActual() + 1)

    const seccion = 'ResultadoRFM'

    // useEffect(() => {
    //   console.log(`Región = ${region}`)
    //   console.log(`Zona = ${zona}`)
    //   console.log(`Tienda = ${tienda}`)
    // }, [region, zona, tienda])
    

  return (
    <>
      <Row className='match-height'>
        <Col sm='12'>
          <h2 className='centrado'>RFM {fechas_srv.tresMesesMenos(anioRFM, mesRFM)} - {fechas_srv.mesTexto(mesRFM)} {anioRFM}</h2>
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12'>
          <Filtro anioRFM={anioRFM} mesRFM={mesRFM} setAnioRFM={setAnioRFM} setMesRFM={setMesRFM} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='6' lg='3'>
          <Tarjeta icono={<Users size={21} />} seccion={seccion} formato='entero' titulo='Clientes' anioRFM={anioRFM} mesRFM={mesRFM} />
        </Col>
        <Col sm='6' lg='3'>
          <Tarjeta icono={<UserPlus size={21} />} seccion={seccion} formato='porcentaje' titulo='% Clientes Nuevos' anioRFM={anioRFM} mesRFM={mesRFM} />
        </Col>
        <Col sm='6' lg='3'>
          <Tarjeta icono={<UserCheck size={21} />} seccion={seccion} formato='porcentaje' titulo='% Clientes Recurrentes' anioRFM={anioRFM} mesRFM={mesRFM} />
        </Col>
        <Col sm='6' lg='3'>
          <Tarjeta icono={<FileText size={21} />} seccion={seccion} formato='moneda' titulo='Ticket Promedio' anioRFM={anioRFM} mesRFM={mesRFM} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
            <ColumnasSuperpuestas titulo='Antigüedad del Cliente Vs. Venta' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
            <ColumnasSuperpuestas titulo='Estatus de Cuenta del Cliente Vs. Venta' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='4'>
            <Burbuja3D titulo='Frecuencia por Monto' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='4'>
            <Burbuja3D titulo='Frecuencia por Recencia' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='4'>
            <Burbuja3D titulo='Recencia por Monto' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='4'>
            <AreaBasica titulo='Usuarios por Frecuencia' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='4'>
            <AreaBasica titulo='Usuarios por Monto' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='4'>
            <AreaBasica titulo='Usuarios por Recencia' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
            <Distribucion3D titulo='1000 Usuarios con Mayor Monto, vs. Frecuencia y Recencia' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
            <Distribucion3D titulo='1000 Usuarios con Menor Monto, vs. Frecuencia y Recencia' anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
            <Tabla titulo='Clientes por Segmento' quitarPaginacion anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
            <Row className='match-height'>
                <Col sm='12'>
                    <EjesMultiples titulo='Quejas por Segmento' quitarPaginacion anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
                </Col>
            </Row>
            <Row className='match-height'>
                <Col sm='12'>
                    <EjesMultiples titulo='Fuera de Tiempo por Segmento' quitarPaginacion anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
                </Col>
            </Row>
        </Col>
      </Row>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
            <EjesMultiples titulo='Cantidad de Clientes por Segmento y Calificación NPS' quitarPaginacion anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
        <Col sm='12' lg='6'>
            <EjesMultiples titulo='Cantidad de Quejas por Segmento de clientes y Calificación NPS' quitarPaginacion anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col>
      </Row>
      <Row className='match-height'>
        {/* <Col sm='12' lg='6'>
            <EjesMultiples titulo='Cantidad de Quejas por Segmento de clientes y Calificación NPS' quitarPaginacion anioRFM={anioRFM} mesRFM={mesRFM} seccion={seccion} />
        </Col> */}
      </Row>
    </>
  )
}
export default ResultadoRFM
