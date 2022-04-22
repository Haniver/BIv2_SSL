import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import UpdateUsuario from '../componentes/auxiliares/UpdateUsuario'

const AltaUsuarios = () => {
    const [usuario, setUsuario] = useState({email: '', estatus: ''})
    const [reloadTabla, setReloadTabla] = useState(0)

    const seccion = 'AltaUsuarios'

  return (
    <>
      <Row className='match-height'>
        <Col sm='12' lg={(usuario.email === '') ? 12 : 8}>
          <Tabla titulo='Usuarios en espera de validación' seccion={seccion} reload={reloadTabla} setUsuario={setUsuario} />
        </Col>
        {usuario.email !== '' && <Col sm='12' lg='4'>
            <UpdateUsuario usuario={usuario} setUsuario={setUsuario} reloadTabla={reloadTabla} setReloadTabla={setReloadTabla} />
        </Col>}
      </Row>
    </>
  )
}
export default AltaUsuarios
