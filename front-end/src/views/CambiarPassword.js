import React, { useState, useEffect, useRef } from "react"
import { Link, useParams } from 'react-router-dom'
import { Row, Col, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import InputPasswordToggle from '@components/input-password-toggle'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import UserService from "@src/services/user.service"
import { isStrongPassword } from "validator"

const CambiarPassword = () => {
  
  const [mensaje, setMensaje] = useState({texto: '', visible: false, color: 'info'})
  const [paginaActiva, setPaginaActiva] = useState(false)
  const [password1, setPassword1] = useState('')
  const [password2, setPassword2] = useState('')
  const { token } = useParams()
  const firstRender = useRef(true)
  
  useEffect(() => {
  
    // No mostrar página si el token no está activo
    if (firstRender.current) {
        UserService.cambiarPasswordActivo(token)
        .then(respuesta => {
            if (respuesta.data.mensaje === 'Activo') {
                setPaginaActiva(true)
            } else if (respuesta.data.mensaje === 'Inactivo') {
                setPaginaActiva(false)
                setMensaje({
                    texto: 'El token ha expirado',
                    visible: true,
                    color: 'danger'
                })
            } else {
                setPaginaActiva(false)
                setMensaje({
                    texto: respuesta.data.mensaje,
                    visible: true,
                    color: 'warning'
                })
            }
        })
    }
    firstRender.current = false
  }, [])


  // here we run any validation, returning true/false
  const handleSave = (event) => {
    event.preventDefault()
    if (!isStrongPassword(password1, {minLength: 10, minLowercase: 1, minUppercase: 1, minNumbers: 1, minSymbols: 0, minreturnScore: false})) {
        // console.log(`La contaseña es ${password1}`)
        setMensaje({
            texto: 'Tu contraseña debe tener por lo menos 10 caracteres que incluyan letras mayúsculas, minúsculas y números.',
            visible: true,
            color: 'danger'
        })
    } else if (password1 !== password2) {
        setMensaje({
            texto: 'Las contraseñas no coinciden',
            visible: true,
            color: 'danger'
        })
    } else {
        setMensaje({
            texto: 'Validando...',
            visible: true,
            color: 'info'
        })
        UserService.cambiarPassword(password1, token)
        .then(respuesta => {
            setMensaje({
                texto: respuesta.data.mensaje,
                visible: true,
                color: 'info'
            })
        })
    }
  }

  // const illustration = skin === 'dark' ? 'login-v2-dark.svg' : 'login-v2.svg',
  const illustration = 'login.svg',
    source = require(`@src/assets/images/pages/${illustration}`).default

  return (
    <div className='auth-wrapper auth-v2'>
      <Row className='auth-inner m-0'>
        <Link className='brand-logo' to='/'>
          <img src={Logo}/>
          <h2 className='brand-text text-primary ml-1'>BI Omnicanal</h2>
        </Link>
        <Col className='d-none d-lg-flex align-items-center p-5' lg='8' sm='12'>
          <div className='w-100 d-lg-flex align-items-center justify-content-center px-5'>
            <img className='img-fluid' src={source} alt='Login V2' />
          </div>
        </Col>
        <Col className='d-flex align-items-center auth-bg px-2 p-lg-5' lg='4' sm='12'>
          <Col className='px-xl-2 mx-auto' sm='8' md='6' lg='12'>
            <CardTitle tag='h2' className='font-weight-bold mb-1'>
                Cambiar contraseña
            </CardTitle>
            {paginaActiva && <>
            <CardText className='mb-2'>Tu contraseña debe tener por lo menos 10 caracteres que incluyan letras mayúsculas, minúsculas y números.</CardText>
            <Form className='auth-login-form mt-2' onSubmit={handleSave}>
                <FormGroup>
                    <div className='d-flex justify-content-between'>
                    <Label className='form-label' for='login-password1'>
                        Contraseña
                    </Label>
                    </div>
                    <InputPasswordToggle className='input-group-merge' id='password1' onChange={e => setPassword1(e.target.value)} />
                </FormGroup>
                <FormGroup>
                    <div className='d-flex justify-content-between'>
                    <Label className='form-label' for='login-password2'>
                        Contraseña de nuevo
                    </Label>
                    </div>
                    <InputPasswordToggle className='input-group-merge' id='password2' onChange={e => setPassword2(e.target.value)} />
                </FormGroup>
                <Button.Ripple color='primary' type='submit' block>
                    Cambiar Contraseña
                </Button.Ripple>
            </Form> </>}
            {mensaje.visible && <Alert color={mensaje.color}>
                    {mensaje.texto} </Alert>}
            {/* <p className='text-center mt-2'>
              <span className='mr-25'>New on our platform?</span>
              <Link to='/'>
                <span>Create an account</span>
              </Link>
            </p>
            <div className='divider my-2'>
              <div className='divider-text'>or</div>
            </div>
            <div className='auth-footer-btn d-flex justify-content-center'>
              <Button.Ripple color='facebook'>
                <Facebook size={14} />
              </Button.Ripple>
              <Button.Ripple color='twitter'>
                <Twitter size={14} />
              </Button.Ripple>
              <Button.Ripple color='google'>
                <Mail size={14} />
              </Button.Ripple>
              <Button.Ripple className='mr-0' color='github'>
                <GitHub size={14} />
              </Button.Ripple>
            </div> */}
          </Col>
        </Col>
      </Row>
    </div>
  )
}

export default CambiarPassword
