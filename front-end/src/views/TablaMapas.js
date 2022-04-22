import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'

const TablaMapas = () => {
    
    const seccion = 'TablaMapas'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12' lg='6'>
          <Tabla titulo='Tabla de Mapas' seccion={seccion} />
        </Col>
      </Row>
    </>
  )
}
export default TablaMapas
