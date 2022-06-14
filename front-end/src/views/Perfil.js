import React, { useState, useEffect } from "react"
import { useSkin } from '@hooks/useSkin'
import { Link, Redirect } from 'react-router-dom'
import { Facebook, Twitter, Mail, GitHub } from 'react-feather'
import InputPasswordToggle from '@components/input-password-toggle'

import { Row, Col, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import AuthService from "@src/services/auth.service"
import cargarFiltros from "../services/cargarFiltros"
import Filtro from "../componentes/auxiliares/Filtro"
import UserService from '@src/services/user.service'
import { isStrongPassword } from "validator"

const Perfil = () => {
  const [skin, setSkin] = useSkin()
  const [cambiandoTienda, setCambiandoTienda] = useState(false)
  const [tiendaActualNombre, setTiendaActualNombre] = useState(false)
  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
  const [cambiandoPassword, setCambiandoPassword] = useState(false)
  const userData = localStorage.getItem('userData')
  const tiendaActual = JSON.parse(userData).tienda
  const [mensaje, setMensaje] = useState({texto: '', visible: false, color: 'info'})
  const [paginaActiva, setPaginaActiva] = useState(false)
  const [passwordVieja, setPasswordVieja] = useState('')
  const [password1, setPassword1] = useState('')
  const [password2, setPassword2] = useState('')
  // const firstRender = useRef(true)
  
  // here we run any validation, returning true/false
  const handleSave = (event) => {
    event.preventDefault()
    if (cambiandoPassword && !isStrongPassword(password1, {minLength: 10, minLowercase: 1, minUppercase: 1, minNumbers: 1, minSymbols: 0, minreturnScore: false})) {
        // console.log(`La contaseña es ${password1}`)
        setMensaje({
            texto: 'Tu contraseña debe tener por lo menos 10 caracteres que incluyan letras mayúsculas, minúsculas y números.',
            visible: true,
            color: 'danger'
        })
    } else if (cambiandoPassword && password1 !== password2) {
          setMensaje({
              texto: 'Las contraseñas no coinciden',
              visible: true,
              color: 'danger'
          })
    } else if (cambiandoTienda && (tienda === '' || tienda === undefined)) {
      setMensaje({
        texto: 'Por favor elige una tienda',
        visible: true,
        color: 'danger'
      })
    } else {
      setMensaje({
          texto: 'Validando...',
          visible: true,
          color: 'info'
      })
      UserService.cambiarPerfil(passwordVieja, password1, tienda)
      .then(respuesta => {
          setMensaje({
              texto: respuesta.data.mensaje,
              visible: true,
              color: 'info'
          })
      })
    }
  }

  useEffect(async () => {
    // console.log("¿Está aquí el loop infinito?")
    if (tiendaActual !== null) {
      const tiendaActualNombre_tmp = await cargarFiltros.nombreTienda(tiendaActual)
      // console.log('tiendaActualNombre_tmp:')
      // console.log(tiendaActualNombre_tmp)
      setTiendaActualNombre(tiendaActualNombre_tmp.data.nombreTienda)
      // setComboTienda({label: tiendaActualNombre, value: tiendaActual})
    }
  }, [])

  // const illustration = skin === 'dark' ? 'login-v2-dark.svg' : 'login-v2.svg',
  const illustration = 'home_paleta.svg',
    source = require(`@src/assets/images/pages/${illustration}`).default

//   const handleLogin = (e) => {
//     e.preventDefault()

//     setErrorVisible(false)
//     console.log(username, password)
//     AuthService.login(username, password).then(
//       () => {
//         // window.location.reload()
//         window.location.assign('/')
//       },
//       error => {
//         setErrorVisible(true)
//       }
//     )
//   }
  
  return (
    <div className='auth-wrapper auth-v2'>
      <Row className='auth-inner m-0'>
        {/* <Col className='d-none d-lg-flex align-items-center p-5' lg='8' sm='12'>
          <div className='w-100 d-lg-flex align-items-center justify-content-center px-5'>
            <img className='img-fluid' src={source} alt='Login V2' />
          </div>
        </Col> */}
        <Col className='d-flex align-items-center auth-bg px-2 p-lg-5' sm='12'>
          <Col className='px-xl-2 mx-auto' sm='8' md='6' lg='12'>
            <CardTitle tag='h2' className='font-weight-bold mb-1'>
              Cambiar Tienda o Contraseña
            </CardTitle>
            {/* <CardText className='mb-2'>Por favor accede con tu correo y contraseña.</CardText> */}
            {/* <Form className='auth-login-form mt-2' onSubmit={handleLogin}> */}
            <Form className='auth-login-form mt-2' onSubmit={handleSave}>
              <FormGroup>
                <Label className='form-label' for='login-email'>
                  <b>Tienda Actual</b>: {tiendaActualNombre}
                </Label>
                <Button.Ripple color='dark' onClick={() => {
                    if (cambiandoTienda) {
                      setCambiandoTienda(false)
                      setRegion('')
                      setZona('')
                      setTienda('')
                    } else {
                      setCambiandoTienda(true)
                    }
                  }} block>
                  {(cambiandoTienda) ? 'Cancelar' : 'Cambiar Tienda'}
                </Button.Ripple>
                {cambiandoTienda && <Row className='match-height'>
                  <Col sm='12'>
                    <Filtro region={region} zona={zona} tienda={tienda} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
                  </Col>
                </Row>}
              </FormGroup>
              <FormGroup>
                <div className='d-flex justify-content-between'>
                  <Button.Ripple color='dark' onClick={() => {
                      if (cambiandoPassword) {
                        setCambiandoPassword(false)
                        setPasswordVieja('')
                        setPassword1('')
                        setPassword2('')
                      } else {
                        setCambiandoPassword(true)
                      }
                    }} block>
                    {(cambiandoPassword) ? 'Cancelar' : 'Cambiar Contraseña'}
                  </Button.Ripple>
                  </div>
                  {cambiandoPassword && <Row className='match-height'>
                  <Col sm='12'>
                    <FormGroup>
                      <div className='d-flex justify-content-between'>
                      <Label className='form-label' for='login-password1'>
                          Contraseña Anterior
                      </Label>
                      </div>
                      <InputPasswordToggle className='input-group-merge' id='passwordVieja' onChange={e => setPasswordVieja(e.target.value)} />
                    </FormGroup>
                    <FormGroup>
                      <div className='d-flex justify-content-between'>
                      <Label className='form-label' for='login-password1'>
                          Nueva Contraseña
                      </Label>
                      </div>
                      <InputPasswordToggle className='input-group-merge' id='password1' onChange={e => setPassword1(e.target.value)} />
                    </FormGroup>
                    <FormGroup>
                      <div className='d-flex justify-content-between'>
                      <Label className='form-label' for='login-password2'>
                          Repetir Nueva Contraseña
                      </Label>
                      </div>
                      <InputPasswordToggle className='input-group-merge' id='password2' onChange={e => setPassword2(e.target.value)} />
                    </FormGroup>
                    </Col>
                  </Row>}
              </FormGroup>
            {(cambiandoPassword || cambiandoTienda) && <Button.Ripple color='primary' type='submit' block>
              Realizar cambios
            </Button.Ripple>}
            {mensaje.visible && <Alert color={mensaje.color}>
              {mensaje.texto} </Alert>}
            </Form>
          </Col>
        </Col>
      </Row>
    </div>
  )
}

export default Perfil
