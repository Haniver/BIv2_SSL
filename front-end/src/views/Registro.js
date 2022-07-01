import React, { useEffect, useMemo, useState } from "react"
import { useSkin } from '@hooks/useSkin'
import { Link, Redirect } from 'react-router-dom'
import { Facebook, Twitter, Mail, GitHub } from 'react-feather'
import InputPasswordToggle from '@components/input-password-toggle'
import { Row, Col, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import Select from 'react-select'
import { selectThemeColors } from '@utils'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import AuthService from "@src/services/auth.service"
import UserService from '@src/services/user.service'
import cargarFiltros from "../services/cargarFiltros"
import Filtro from "../componentes/auxiliares/Filtro"
import { isStrongPassword, isAlpha, isEmail } from "validator"
import userService from "../services/user.service"

const Registro = () => {
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
    const yaExisteUsuario = await userService.yaExisteUsuario(valor)
    // Si ya está, mandar error
    if (yaExisteUsuario.data) {
        setMsgEmail({
            texto: `El usuario ${valor} ya está registrado`,
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
    } else if (!isStrongPassword(password1, {minLength: 10, minLowercase: 1, minUppercase: 1, minNumbers: 1, minSymbols: 0, minreturnScore: false})) {
      setMsgPassword1({
          texto: 'Tu contraseña debe tener por lo menos 10 caracteres que incluyan letras mayúsculas, minúsculas y números.',
          visible: true,
          color: 'danger'
      })
      setValidadoPassword(false)
    } else if (password1 !== password2) {
      setMsgPassword2({
          texto: 'Las contraseñas no coinciden',
          visible: true,
          color: 'danger'
      })
      setMsgPassword1({
        texto: `✔`,
        visible: true,
        color: 'success'
      })
      setValidadoPassword(false)
    } else {
      setMsgPassword2({
          texto: `✔`,
          visible: true,
          color: 'success'
      })
      setMsgPassword1({
        texto: `✔`,
        visible: true,
        color: 'success'
      })
      setValidadoPassword(true)
    }
  }, [password1, password2])
  
  // Validar nombre
  const [nombre, setNombre] = useState('')
  const [msgNombre, setMsgNombre] = useState({texto: '', visible: false, color: 'info'})
  const [validadoNombre, setValidadoNombre] = useState(false)
  const validarNombre = (valor) => {
    setMsgEnviar({
      visible: false
    })
    if (!isAlpha(valor, 'es-ES', ' ')) {
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
  
  // Validar apellido paterno
  const [apellidoP, setApellidoP] = useState('')
  const [msgApellidoP, setMsgApellidoP] = useState({texto: '', visible: false, color: 'info'})
  const [validadoApellidoP, setValidadoApellidoP] = useState(false)
  const validarApellidoP = (valor) => {
    setMsgEnviar({
      visible: false
    })
    if (!isAlpha(valor, 'es-ES', ' ')) {
        setMsgApellidoP({
            texto: 'Este no es un apellido válido en español',
            visible: true,
            color: 'danger'
        })
        setValidadoApellidoP(false)
    } else {
        setMsgApellidoP({
            texto: `✔`,
            visible: true,
            color: 'success'
        })
        setValidadoApellidoP(true)
    }
    setApellidoP(valor)
  }
  
  // Validar apellido materno
  const [apellidoM, setApellidoM] = useState('')
  const [msgApellidoM, setMsgApellidoM] = useState({texto: '', visible: false, color: 'info'})
  const [validadoApellidoM, setValidadoApellidoM] = useState(false)
  const validarApellidoM = (valor) => {
    if (!isAlpha(valor, 'es-ES', ' ')) {
        setMsgApellidoM({
            texto: 'Este no es un apellido válido en español',
            visible: true,
            color: 'danger'
        })
        setValidadoApellidoM(false)
    } else {
        setMsgApellidoM({
            texto: `✔`,
            visible: true,
            color: 'success'
        })
        setValidadoApellidoM(true)
    }
    setApellidoM(valor)
  }
  
  // Areas
  const [comboAreas, setComboAreas] = useState({label: '', value: ''})
  useEffect(async () => {
    const tmp = await userService.areas()
    // console.log('comboAreas:')
    // console.log(tmp.data)
    setComboAreas(tmp.data)
  }, [])
  const [area, setArea] = useState([])
  const [msgArea, setMsgArea] = useState({texto: '', visible: false, color: 'info'})
  const [validadoArea, setValidadoArea] = useState(false)
  const validarArea = (valor) => {
    console.log(`El valor que se va a insertar es: ${valor}`)
    setMsgEnviar({
      visible: false
    })
    if (valor !== '') {
      setMsgArea({
          texto: `✔`,
          visible: true,
          color: 'success'
      })
      setValidadoArea(true)
    } else {
      setValidadoArea(false)
    }
    setArea([...area, valor])
  }
  useEffect(() => {
    console.log("Áreas:")
    console.log(area)
  }, [area])
  
  // Tiendas
  // const [comboTiendas, setComboTiendas] = useState({label: '', value: ''})
  // useEffect(async () => {
  //   const tmp = await userService.todasLasTiendas()
  //   console.log('comboTiendas:')
  //   console.log(tmp.data)
  //   setComboTiendas(tmp.data)
  // }, [])
  // const [tienda, setTienda] = useState('')
  // const [msgTienda, setMsgTienda] = useState({texto: '', visible: false, color: 'info'})
  // const [validadoTienda, setValidadoTienda] = useState(false)
  // const validarTienda = (valor) => {
  //   setMsgEnviar({
  //     visible: false
  //   })
  //   if (valor !== '') {
  //     setMsgTienda({
  //         texto: `✔`,
  //         visible: true,
  //         color: 'success'
  //     })
  //     setValidadoTienda(true)
  //   } else {
  //     setValidadoTienda(false)
  //   }
  //   setTienda(valor)
  // }
  
  // Tienda
  const [region, setRegion] = useState('')
  const [zona, setZona] = useState('')
  const [tienda, setTienda] = useState('')
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
    // Preguntar a la API si el usuario ya está en la BD
    // if (tienda === '' || tienda === undefined) {
    //   setMensaje({
    //     texto: 'Por favor elige una tienda',
    //     visible: true,
    //     color: 'danger'
    //   })
    // }
    if (!(validadoApellidoM && validadoApellidoP && validadoEmail && validadoNombre && validadoPassword && validadoArea && validadoTienda)) {
        setMsgEnviar({
            texto: `Por favor llena todos los campos y verifica que no tengan errores`,
            visible: true,
            color: 'danger'
        })
    } else {
      // Enviar
      const resp_registro = await userService.registro(apellidoM, apellidoP, email, nombre, password1, area, tienda)
      const color_exito = (resp_registro.data.exito) ? 'success' : 'danger'
      setMsgEnviar({
        texto: resp_registro.data.mensaje,
        visible: true,
        color: color_exito
      })
    }
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
                    Nombre(s)
                </Label>
                </div>
                <Input id='nombre' onChange={e => validarNombre(e.target.value)} />
                {msgNombre.visible && <Alert color={msgNombre.color}>{msgNombre.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='apellidoP'>
                    Apellido Paterno
                </Label>
                </div>
                <Input id='apellidoP' onChange={e => validarApellidoP(e.target.value)} />
                {msgApellidoP.visible && <Alert color={msgApellidoP.color}>{msgApellidoP.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='apellidoM'>
                    Apellido Materno
                </Label>
                </div>
                <Input id='apellidoM' onChange={e => validarApellidoM(e.target.value)} />
                {msgApellidoM.visible && <Alert color={msgApellidoM.color}>{msgApellidoM.texto} </Alert>}
            </FormGroup>
            <FormGroup>
                <div className='d-flex justify-content-between'>
                <Label className='form-label' for='area'>
                    Área(s)
                </Label>
                </div>
                <Select
                  theme={selectThemeColors}
                  isMulti
                  className="basic-multi-select"
                  classNamePrefix="select"
                  name='area'
                  options={comboAreas}
                  isClearable={true}
                  onChange={e => {
                    validarArea(e.value)
                  }}
                />
                {msgArea.visible && <Alert color={msgArea.color}>{msgArea.texto} </Alert>}
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

export default Registro
