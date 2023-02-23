import React, { useEffect, useMemo, useState } from "react"
import { useSkin } from '@hooks/useSkin'
import { Link, Redirect } from 'react-router-dom'
import InputPasswordToggle from '@components/input-password-toggle'
import { Row, Col, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import Select from 'react-select'
import { selectThemeColors } from '@utils'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import Filtro from "../componentes/auxiliares/Filtro"
import { isStrongPassword, isEmail } from "validator"
import userService from "../services/user.service"
import axios from "axios"
import CustomUrls from "../services/customUrls"

const ChecarHash = () => {
  const [skin, setSkin] = useSkin()
  const [verOlvidePassword, setVerOlvidePassword] = useState(false)
  const [msgEnviar, setMsgEnviar] = useState({texto: '', visible: false, color: 'info'})

  // const illustration = skin === 'dark' ? 'login-v2-dark.svg' : 'login-v2.svg',
  const illustration = 'login.svg',
    source = require(`@src/assets/images/pages/${illustration}`).default

  // Validar email
  const [email, setEmail] = useState('')
  const [msgEmail, setMsgEmail] = useState({texto: '', visible: false, color: 'info'})
  const [validadoEmail, setValidadoEmail] = useState(false)
  const validarEmail = async (valor) => {
    setMsgEnviar({
      visible: false
    })
    const verificarUsuario = await userService.verificarUsuario(valor)
    if (verificarUsuario.data === "Dominio no válido") {
      setMsgEmail({
          texto: `El dominio de este correo no es válido`,
          visible: true,
          color: 'danger'
      })
      setVerOlvidePassword(true)
      setValidadoEmail(false)
    } else if (!isEmail(valor)) {
      setMsgEmail({
        texto: `Este no es un email válido`,
        visible: true,
        color: 'danger'
      })
      setVerOlvidePassword(true)
      setValidadoEmail(false)
    } else {
        setMsgEmail({
            texto: `✔`,
            visible: true,
            color: 'success'
        })
        setVerOlvidePassword(false)
        setValidadoEmail(true)
    }
    setEmail(valor)
  }
  
  // Validar passwords
  const [password1, setPassword1] = useState('')
  const [msgPassword1, setMsgPassword1] = useState({texto: '', visible: false, color: 'info'})
  const [password2, setPassword2] = useState('')
  const [msgPassword2, setMsgPassword2] = useState({texto: '', visible: false, color: 'info'})
  const [validadoPassword, setValidadoPassword] = useState(false)
  const [arrancando, setArrancando] = useState(true)
  useEffect(() => {
    // console.log(`password1 = '${password1}'`)
    setMsgEnviar({
      visible: false
    })
    if (arrancando) {
      setArrancando(false)
    }
    setValidadoPassword(true)
  }, [password1])
  
  // Validar nombre
  const [nombre, setNombre] = useState('')
  const [msgNombre, setMsgNombre] = useState({texto: '', visible: false, color: 'info'})
  const [validadoNombre, setValidadoNombre] = useState(false)
  const validarNombre = (valor) => {
    setMsgEnviar({
      visible: false
    })
    // if (!isAlpha(valor, {allow_spaces: true, extra_characters: ','})) {
    if (!/^([a-zA-Z," "À-ÿ\u00f1\u00d1]*)$/.test(valor)) {
        setMsgNombre({
            texto: 'Este no es un nombre válido en español',
            visible: true,
            color: 'danger'
        })
        setValidadoNombre(false)
    } else {
        setMsgNombre({
            texto: `✔`,
            visible: true,
            color: 'success'
        })
        setValidadoNombre(true)
    }
    setNombre(valor)
  }
  
  // Nivel
  const comboNivel = [
    {label: 'Tienda', value: 1},
    {label: 'Zona', value: 2},
    {label: 'Región', value: 3},
    {label: 'Nacional', value: 4}
  ]
  const [nivel, setNivel] = useState(0)
  const [msgNivel, setMsgNivel] = useState({texto: '', visible: false, color: 'info'})
  const [validadoNivel, setValidadoNivel] = useState(false)
  const validarNivel = (valor) => {
    // console.log(`El valor que se va a insertar es: ${valor}`)
    setMsgEnviar({
      visible: false
    })
    if (valor > 0) {
      setMsgNivel({
          texto: `✔`,
          visible: true,
          color: 'success'
      })
      setValidadoNivel(true)
    } else {
      setMsgNivel({
        texto: `Por favor elige un nivel`,
        visible: true,
        color: 'danger'
      })
    setValidadoNivel(false)
    }
    setNivel(valor)
  }
  
  // Tienda
  const [region, setRegion] = useState(userService.getRegionPorNivel())
  const [zona, setZona] = useState(userService.getZonaPorNivel())
  const [tienda, setTienda] = useState(userService.getTiendaPorNivel())
  const [msgTienda, setMsgTienda] = useState({texto: '', visible: false, color: 'info'})
  const [validadoTienda, setValidadoTienda] = useState(false)
  useEffect(() => {
    setMsgEnviar({
      visible: false
    })
    if (tienda !== '') {
      setMsgTienda({
          texto: `✔`,
          visible: true,
          color: 'success'
      })
      setValidadoTienda(true)
    } else {
      setValidadoTienda(false)
    }
  }, [tienda])
  
  // Validar formulario completo
  const handleRegistro = async (e) => {
    e.preventDefault()
    setMsgPassword1(password1)
    // Enviar
    axios({
      method: 'post',
      url: `${CustomUrls.ApiUrl()}checarHash`,
      headers: {
        accept:'application/json',
        'Content-Type':'application/json'
      },
      data: {
        password: password1,
        email
      }
    })
  }
  return (
    <div className='auth-wrapper auth-v2'>
      <Row className='auth-inner m-0'>
        <Link className='brand-logo' to='/'>
          <img src={Logo}/>
          <h2 className='brand-text text-primary ml-1'>BI Omnicanal</h2>
        </Link>
        <Col className='d-none d-lg-flex align-items-center p-5' lg='4' sm='12'>
          <div className='w-100 d-lg-flex align-items-center justify-content-center'>
            <img className='img-fluid' src={source} alt='Login V2' />
          </div>
        </Col>
        <Col className='d-flex align-items-center auth-bg px-2 p-lg-5' lg='8' sm='12'>
          <Col className='px-xl-2 mx-auto' sm='8' md='6' lg='12'>
            <CardTitle tag='h2' className='font-weight-bold mb-1'>
              Registro
            </CardTitle>
            <CardText className='mb-2'>Por favor llena los campos para tu registro.</CardText>
            <Form className='auth-login-form mt-2' onSubmit={handleRegistro}>
              <FormGroup>
                <Label className='form-label' for='registro-email'>
                  Correo
                </Label>
                <Input type='email' id='registro-email' placeholder='tunombre@chedraui.com.mx' autoFocus onChange={e => validarEmail(e.target.value)} />
                {msgEmail.visible && <Alert color={msgEmail.color}>{msgEmail.texto} </Alert>}
                {verOlvidePassword && <Link to='/recuperar'>
                    <small>¿Olvidaste tu contraseña?</small>
                  </Link>}
              </FormGroup>
              <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='password1'>
                    Contraseña
                </Label>
                </div>
                <InputPasswordToggle className='input-group-merge' id='password1' onChange={e => setPassword1(e.target.value)} />
                {msgPassword1.visible && <Alert color={msgPassword1.color}>{msgPassword1.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='password2'>
                    Repetir Contraseña
                </Label>
                </div>
                <InputPasswordToggle className='input-group-merge' id='password2' onChange={e => setPassword2(e.target.value)} />
                {msgPassword2.visible && <Alert color={msgPassword2.color}>{msgPassword2.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='nombre'>
                    Nombre Completo
                </Label>
                </div>
                <Input id='nombre' onChange={e => validarNombre(e.target.value)} />
                {msgNombre.visible && <Alert color={msgNombre.color}>{msgNombre.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='nivel'>
                    Nivel
                </Label>
                </div>
                <Select
                  theme={selectThemeColors}
                  className="basic-multi-select"
                  classNamePrefix="select"
                  name='nivel'
                  options={comboNivel}
                  isClearable={true}
                  onChange={e => {
                    validarNivel(e.value)
                  }}
                />
                {msgNivel.visible && <Alert color={msgNivel.color}>{msgNivel.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <Label className='form-label' for='login-email'>
                  Tienda por Defecto
                </Label>
                <Filtro region={region} zona={zona} tienda={tienda} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
              </FormGroup>
              <Button.Ripple color='primary' type='submit' block>
                Solicitar Registro
              </Button.Ripple>
              {msgEnviar.visible && <Alert color={msgEnviar.color}>{msgEnviar.texto} </Alert>}
            </Form>
          </Col>
        </Col>
      </Row>
    </div>
  )
}

export default ChecarHash