import React, { useState } from "react"
import { Link, Redirect } from 'react-router-dom'
import { Row, Col, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import UserService from "@src/services/user.service"
import { isEmail } from "validator"

const Recuperar = () => {
  
  const [mensaje, setMensaje] = useState({texto: '', visible: false, color: 'info'})
  const [email, setEmail] = useState('')

  // here we run any validation, returning true/false
  const handleSave = (event) => {
    event.preventDefault()
    if (!isEmail(email)) {
        setMensaje({
            texto: 'Este no es un email válido',
            visible: true,
            color: 'danger'
        })
    } else {
    setMensaje({
        texto: 'Validando...',
        visible: true,
        color: 'info'
    })
    UserService.recuperarPassword(email)
    .then(respuesta => {
        const color = (respuesta.data.mensaje === 'Email enviado con éxito') ? 'success' : 'warning'
        setMensaje({
            texto: respuesta.data.mensaje,
            visible: true,
            color
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
                Recuperar contraseña
            </CardTitle>
            <CardText className='mb-2'>Ingresa tu correo y te haremos llegar el link para el restablecimiento de tu contraseña</CardText>
            <Form className='auth-login-form mt-2' onSubmit={handleSave}>
              <FormGroup>
                <Label className='form-label' for='login-email'>
                  Correo
                </Label>
                <Input type='email' id='login-email' placeholder='tunombre@chedraui.com.mx' autoFocus onChange={e => setEmail(e.target.value)} />
              </FormGroup>
              <Button.Ripple color='primary' type='submit' block>
                Enviar enlace
              </Button.Ripple>
              {mensaje.visible && <Alert color={mensaje.color}>
                {mensaje.texto}
              </Alert>}
            </Form>
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

export default Recuperar
