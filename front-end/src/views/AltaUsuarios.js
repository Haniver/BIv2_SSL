import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import UpdateUsuario from '../componentes/auxiliares/UpdateUsuario'

const AltaUsuarios = () => {
    const [estatus, setEstatus] = useState({email: '', estatus: ''})
    const [reloadTabla, setReloadTabla] = useState(0)

    const seccion = 'AltaUsuarios'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12' lg={(estatus.email === '') ? 12 : 8}>
          <Tabla titulo='Usuarios en espera de validación' seccion={seccion} reload={reloadTabla} setEstatus={setEstatus} />
        </Col>
        {estatus.email !== '' && <Col sm='12' lg='4'>
            <UpdateUsuario usuario={estatus} setUsuario={setEstatus} reloadTabla={reloadTabla} setReloadTabla={setReloadTabla} />
        </Col>}
      </Row>
    </>
  )
}
export default AltaUsuarios
