import { selectThemeColors } from '@utils'
import { useEffect, useState } from 'react'
import axios from 'axios'
import authHeader from '@src/services/auth.header'
import CustomUrls from "../../services/customUrls"
import { Row, Col, Card, CardHeader, CardBody, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import Select from 'react-select'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import Filtro from './Filtro'
import { isStrongPassword, isAlpha, isEmail } from "validator"
import userService from '../../services/user.service'
import cargarFiltros from '../../services/cargarFiltros'

const UpdateUsuario2 = ({usuario, setUsuario, reloadTabla, setReloadTabla}) => {

    console.log("Usuario:")
    console.log(usuario)
    const [errorVisible, setErrorVisible] = useState(false)
    
    // Estatus
    const comboEstatus = [
        {label: 'revisión', value: 'revisión'},
        {label: 'activo', value: 'activo'},
        {label: 'bloqueado', value: 'bloqueado'},
        {label: 'rechazado', value: 'rechazado'}
    ]
    const [estatusValue, setEstatusValue] = useState({label: usuario.estatus, value: usuario.estatus})

    const [msgEnviar, setMsgEnviar] = useState({texto: '', visible: false, color: 'info'})
    // Validar email
    const [email, setEmail] = useState(usuario.email)
    const [msgEmail, setMsgEmail] = useState({texto: '', visible: false, color: 'info'})
    const [validadoEmail, setValidadoEmail] = useState(false)
    const validarEmail = async (valor) => {
        setMsgEnviar({
        visible: false
        })
        const verificarUsuario = await userService.verificarUsuario(valor)
        // Si ya está, mandar error
        if (verificarUsuario.data === "Usuario ya estaba") {
        setMsgEmail({
            texto: `El usuario ${valor} ya está registrado`,
            visible: true,
            color: 'danger'
        })
        setVerOlvidePassword(true)
        setValidadoEmail(false)
        } else if (verificarUsuario.data === "Dominio no válido") {
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

    // Validar nombre
    const [nombre, setNombre] = useState(usuario.nombre)
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

    // Areas
    const [comboAreas, setComboAreas] = useState({label: '', value: ''})
    const [areas, setAreas] = useState([])
    useEffect(async () => {
        const tmp = await userService.areas()
        // console.log('comboAreas:')
        // console.log(tmp.data)
        setComboAreas(tmp.data)
        const arr_areas_txt = usuario.areas.split(", ")
        console.log("arr_areas_txt:")
        console.log(arr_areas_txt)
        const arr_areas_obj = []
        arr_areas_txt.forEach((area_txt) => {
        const value = tmp.data.findIndex(object => {
            return object.label === area_txt
            }).value
        arr_areas_obj.push({
            value,
            label: area_txt
        })
        })
        setAreas(arr_areas_obj)
    }, [])
    const [msgArea, setMsgArea] = useState({texto: '', visible: false, color: 'info'})
    const [validadoArea, setValidadoArea] = useState(false)
    const validarArea = (evento) => {
        // console.log(`El valor que se va a insertar es: ${valor}`)
        const areas_tmp = []
        evento.forEach(elemento => {
        areas_tmp.push(elemento.value)
        })
        setMsgEnviar({
        visible: false
        })
        if (areas_tmp.length > 0) {
        setMsgArea({
            texto: `✔`,
            visible: true,
            color: 'success'
        })
        setValidadoArea(true)
        } else {
        setMsgArea({
            texto: `Elige por lo menos un área`,
            visible: true,
            color: 'danger'
        })
        setValidadoArea(false)
        }
        setAreas(areas_tmp)
    }
    
    // Nivel
    const comboNivel = [
        {label: 'Tienda', value: 1},
        {label: 'Zona', value: 2},
        {label: 'Región', value: 3},
        {label: 'Nacional', value: 4},
        {label: 'Administrador de sistema', value: 5}
    ]
    const [nivel, setNivel] = useState(comboNivel[usuario.nivel + 1])
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
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState(cargarFiltros.numeroTienda(usuario.tienda))
    const [msgTienda, setMsgTienda] = useState({texto: '', visible: false, color: 'info'})
    const [validadoTienda, setValidadoTienda] = useState(false)
    // const indice = .findIndex(object => {
    //     return object.label === usuario.tienda
    //     }).value
    // setTienda({
    //     value,
    //     label: usuario.tienda
    // })
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
        if (!(validadoEmail && validadoNombre && validadoArea && validadoTienda && validadoNivel)) {
            setMsgEnviar({
                texto: `Por favor llena todos los campos y verifica que no tengan errores`,
                visible: true,
                color: 'danger'
            })
        } else {
        // Enviar
        const resp_registro = await userService.registro('', '', email, nombre, '', areas, tienda, nivel, estatusValue)
        /* Wawa aquí tienes que cambiar:
         * El registro de UserService para que pepene estatusValue (con default = '')
         * El back end de ese registro para que maneje correctamente apellidos en blanco, password en blanco y estatus (lleno y en blanco)
        */
        const color_exito = (resp_registro.data.exito) ? 'success' : 'danger'
        setMsgEnviar({
            texto: resp_registro.data.mensaje,
            visible: true,
            color: color_exito
        })
        }
    }
    
    
    return (
        <Card>
            <CardHeader>
                <CardTitle tag='h2' className='font-weight-bold mb-1'>
                Registro
                </CardTitle>
                </CardHeader>
            <CardBody>
                <Row>
                <Col>
                <Form className='auth-login-form mt-2' onSubmit={handleRegistro}>
                <FormGroup>
                    <Label className='form-label' for='registro-email'>
                    Correo
                    </Label>
                    <Input 
                        type='email' 
                        id='registro-email' 
                        placeholder='tunombre@chedraui.com.mx' 
                        autoFocus 
                        value={email}
                        onChange={e => validarEmail(e.target.value)} 
                        />
                    {msgEmail.visible && <Alert color={msgEmail.color}>{msgEmail.texto} </Alert>}
                </FormGroup>
                <FormGroup>
                    <div className='d-flex justify-content-between'>
                    <Label className='form-label' for='nombre'>
                        Nombre Completo
                    </Label>
                    </div>
                    <Input id='nombre' onChange={e => validarNombre(e.target.value)} value={nombre} />
                    {msgNombre.visible && <Alert color={msgNombre.color}>{msgNombre.texto} </Alert>}
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
                    value={areas}
                    onChange={e => {
                        validarArea(e)
                    }}
                    />
                    {msgArea.visible && <Alert color={msgArea.color}>{msgArea.texto} </Alert>}
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
                <FormGroup>
                <Label>Cambiar estatus</Label>
                <Select
                theme={selectThemeColors}
                value={estatusValue}
                className='react-select'
                classNamePrefix='select'
                name='estatus'
                options={comboEstatus}
                onChange={(e) => setEstatusValue(e)}
                // isClearable={true}
                />
                <br />
                {errorVisible && <Alert color="danger">
                    Ocurrió un error al actualizar la base de datos
                </Alert>}
                <Button.Ripple color='primary' type='submit' block>
                    Modificar Datos
                </Button.Ripple>
                {msgEnviar.visible && <Alert color={msgEnviar.color}>{msgEnviar.texto} </Alert>}
                </FormGroup>
                </Form>
                </Col>
                </Row>
            </CardBody>
        </Card>
    )
}

export default UpdateUsuario2