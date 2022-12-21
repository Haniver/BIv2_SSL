import React, { useState } from "react"
import { useSkin } from '@hooks/useSkin'
import { Link, Redirect } from 'react-router-dom'
import { Facebook, Twitter, Mail, GitHub } from 'react-feather'
import InputPasswordToggle from '@components/input-password-toggle'
import { Row, Col, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import AuthService from "@src/services/auth.service"

const Login = () => {
  const [skin, setSkin] = useSkin()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorVisible, setErrorVisible] = useState(false)

  // const illustration = skin === 'dark' ? 'login-v2-dark.svg' : 'login-v2.svg',
  const illustration = 'login.svg',
    source = require(`@src/assets/images/pages/${illustration}`).default

  const handleLogin = (e) => {
    e.preventDefault()

    setErrorVisible(false)
    // console.log(username, password)
    AuthService.login(username, password).then(
      () => {
        window.location.assign('/')
      },
      error => {
        setErrorVisible(true)
      }
    )
  }
  
  return (
    <div className='auth-wrapper auth-v2'>
      <Row className='auth-inner m-0'>
        {/* <Link className='brand-logo' to='/'>
          <img src={Logo}/>
          <h2 className='brand-text text-primary ml-1'>BI Omnicanal</h2>
        </Link> */}
        <Col className='d-none d-lg-flex align-items-center p-5 fondo-negro' lg='8' sm='12'>
          <div className='w-100 d-lg-flex align-items-center justify-content-center px-5'>
            <img className='img-fluid' src={source} alt='Login V2' />
          </div>
        </Col>
        <Col className='d-flex align-items-center auth-bg px-2 p-lg-5' lg='4' sm='12'>
          <Col className='px-xl-2 mx-auto' sm='8' md='6' lg='12'>
            <CardTitle tag='h2' className='font-weight-bold mb-1'>
              Acceso
            </CardTitle>
            <CardText className='mb-2'>Por favor accede con tu correo y contraseña.</CardText>
            <Form className='auth-login-form mt-2' onSubmit={handleLogin}>
              <FormGroup>
                <Label className='form-label' for='login-email'>
                  Correo
                </Label>
                <Input type='email' id='login-email' placeholder='tunombre@chedraui.com.mx' autoFocus onChange={e => setUsername(e.target.value)} />
              </FormGroup>
              <FormGroup>
                <div className='d-flex justify-content-between'>
                  <Label className='form-label' for='login-password'>
                    Contraseña
                  </Label>
                  <Link to='/recuperar'>
                    <small>Olvidé mi contraseña</small>
                  </Link>
                </div>
                <InputPasswordToggle className='input-group-merge' id='login-password' onChange={e => setPassword(e.target.value)} />
              </FormGroup>
              {/* <FormGroup>
                <CustomInput type='checkbox' className='custom-control-Primary' id='remember-me' label='Remember Me' />
              </FormGroup> */}
              {/* Aquí tienes que meter la llamada a la función, que también tienes que definir, que autentique al usuario. Todo sácalo de auth-for-reference. Cuando se loguee, mándalo a Home  */}
              <Button.Ripple color='primary' type='submit' block>
                Acceder
              </Button.Ripple>
              {errorVisible && <Alert color="danger">
                Acceso fallido. Si el problema persiste, contacta al administrador.
              </Alert>}
            </Form>
            <Link to='/registro'>
              <small>¿No tienes cuenta? Regístrate</small>
            </Link>
          </Col>
        </Col>
      </Row>
    </div>
  )
}

export default Login
