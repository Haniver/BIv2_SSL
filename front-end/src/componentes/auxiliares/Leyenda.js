// ** Third Party Components
// import PropTypes from 'prop-types'
import { Card, CardBody } from 'reactstrap'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import { useState, useEffect, useReducer } from 'react'
import CustomUrls from '../../services/customUrls'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'

const Leyenda = ({seccion, titulo}) => {
  const [hayError, setHayError] = useState(false)
  const [leyenda, setLeyenda] = useState('')
      const [estadoLoader, dispatchLoader] = useReducer((estadoLoader, accion) => {
        switch (accion.tipo) {
          case 'llamarAPI':
            return { contador: estadoLoader.contador + 1 }
          case 'recibirDeAPI':
            return { contador: estadoLoader.contador - 1 }
          default:
            throw new Error()
        }
      }, {contador: 0})

  useEffect(async() => {
    let leyenda_tmp = 3.1416
    let hayResultados = 'no'
    dispatchLoader({tipo: 'llamarAPI'})
    const res = await axios({
      method: 'get',
      url: `${CustomUrls.ApiUrl()}leyendas/${seccion}?titulo=${titulo}`,
      headers: authHeader()
    })
    if (res.data.hayResultados === 'si') {
      setHayError(false)
      leyenda_tmp = res.data.res
      hayResultados = res.data.hayResultados
      dispatchLoader({tipo: 'recibirDeAPI'})
      setLeyenda(leyenda_tmp)
    } else {
      setHayError(true)
    }
  }, [])

  return (
    <Card className='text-center'>
      <CardBody className='leyenda'>
        {hayError && <p></p>}
        {!hayError && estadoLoader.contador === 0 && <>
          <p className='leyenda'>{titulo} {leyenda}</p>
        </>}
        {!hayError && estadoLoader.contador !== 0 && <LoadingGif mini />}
      </CardBody>
    </Card>
  )
}

export default Leyenda