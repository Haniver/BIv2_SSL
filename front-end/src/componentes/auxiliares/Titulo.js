// ** Third Party Components
// import PropTypes from 'prop-types'
import { Card, CardBody, CardTitle } from 'reactstrap'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import { useState, useEffect, useReducer } from 'react'
import CustomUrls from '../../services/customUrls'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'

const Titulo = ({titulo, subtitulo}) => {
  const [hayError, setHayError] = useState(false)

  return (
    <>
        <h3 className='titulo'>{titulo.toUpperCase()}</h3>
        <p className='subtitulo'>{subtitulo}</p>
        <hr className='hrTitulo' />
    </>
  )
}

export default Titulo