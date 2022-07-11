import { useState, useEffect } from 'react'
import { Row, Col } from 'reactstrap'
import fechas_srv from '../services/fechas_srv'
import Tabla from '../componentes/tablas/Tabla'
import Filtro from '../componentes/auxiliares/Filtro'
import UpdateUsuario from '../componentes/auxiliares/UpdateUsuario'
import UpdateUsuario2 from '../componentes/auxiliares/UpdateUsuario2'

const AltaUsuarios = () => {
    const [estatus, setEstatus] = useState({email: '', estatus: ''})
    const [usuario, setUsuario] = useState({email: '', estatus: ''})
    const [reloadTabla, setReloadTabla] = useState(0)

    const seccion = 'AltaUsuarios'

    useEffect(() => {
      console.log("Cambió estatus:")
      console.log(estatus)
    }, [estatus])

    useEffect(() => {
      console.log("Cambió usuario:")
      console.log(usuario)
    }, [usuario])

  return (
    <>
      <Row className='match-height'>
        <Col sm='12' lg={(estatus.email === '') ? 12 : 8}>
          <Tabla titulo='Usuarios en espera de validación' seccion={seccion} reload={reloadTabla} setEstatus={setEstatus} setUsuario={setUsuario} />
        </Col>
        {estatus.email !== '' && <Col sm='12' lg='4'>
            <UpdateUsuario usuario={estatus} setUsuario={setEstatus} reloadTabla={reloadTabla} setReloadTabla={setReloadTabla} />
        </Col>}
      </Row>
      <Row className='match-height'>
        {usuario.email !== '' && <Col sm='12'>
            <UpdateUsuario2 usuario={usuario} setUsuario={setUsuario} reloadTabla={reloadTabla} setReloadTabla={setReloadTabla} />
        </Col>}
      </Row>
    </>
  )
}
export default AltaUsuarios
