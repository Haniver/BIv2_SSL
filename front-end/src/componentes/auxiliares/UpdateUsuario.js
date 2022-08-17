import { selectThemeColors } from '@utils'
import { useEffect, useState } from 'react'
import axios from 'axios'
import authHeader from '@src/services/auth.header'
import CustomUrls from "../../services/customUrls"
import { Row, Col, Card, CardHeader, CardBody, CardTitle, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import Select from 'react-select'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import { isStrongPassword, isAlpha, isEmail, isByteLength } from "validator"
import userService from '../../services/user.service'
import cargarFiltros from '../../services/cargarFiltros'
import Filtro from './Filtro'

const UpdateUsuario = ({usuario, setUsuario, reloadTabla, setReloadTabla}) => {

    // console.log("Usuario:")
    // console.log(usuario)
    const [errorVisible, setErrorVisible] = useState(false)
    
    // ID
    const [id, setId] = useState(0)

    // Estatus
    const comboEstatus = [
        {label: 'revisión', value: 'revisión'},
        {label: 'activo', value: 'activo'},
        {label: 'bloqueado', value: 'bloqueado'},
        {label: 'rechazado', value: 'rechazado'}
    ]
    const [estatusValue, setEstatusValue] = useState({})

    const [msgEnviar, setMsgEnviar] = useState({texto: '', visible: false, color: 'info'})
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
        setValidadoEmail(false)
        } else if (!isEmail(valor)) {
        setMsgEmail({
            texto: `Este no es un email válido`,
            visible: true,
            color: 'danger'
        })
        setValidadoEmail(false)
        } else {
            setMsgEmail({
                texto: `✔`,
                visible: true,
                color: 'success'
            })
            setValidadoEmail(true)
        }
        setEmail(valor)
    }

    // Validar nombre
    const [nombre, setNombre] = useState('')
    const [msgNombre, setMsgNombre] = useState({texto: '', visible: false, color: 'info'})
    const [validadoNombre, setValidadoNombre] = useState(false)
    const validarNombre = (valor) => {
        setMsgEnviar({
        visible: false
        })
        if (!isAlpha(valor, 'es-ES', {ignore: '\s'})) {
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
    const [areasOpcion, setAreasOpcion] = useState([])
    const [msgArea, setMsgArea] = useState({texto: '', visible: false, color: 'info'})
    const [validadoArea, setValidadoArea] = useState(false)
    const validarArea = (evento) => {
        // console.log(`El valor que se va a insertar es: ${valor}`)
        // console.log("El evento de validarArea es:")
        // console.log(evento)
        const areasOpcion_tmp = []
        const areas_tmp = []
        evento.forEach(elemento => {
            areas_tmp.push(elemento.value)
            areasOpcion_tmp.push({value: elemento.value, label: elemento.label})
        })
        setMsgEnviar({
        visible: false
        })
        if (areasOpcion_tmp.length > 0) {
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
        // console.log("Áreas:")
        // console.log(areas)
        setAreasOpcion(areasOpcion_tmp)
        setAreas(areas_tmp)
    }
    useEffect(async () => {
        const tmp = await userService.areas()
        // console.log('comboAreas:')
        // console.log(tmp.data)
        setComboAreas(tmp.data)
        const arr_areas_txt = usuario.areas.split(", ")
        // console.log("arr_areas_txt:")
        // console.log(arr_areas_txt)
        const arr_areas_obj = []
        arr_areas_txt.forEach((area_txt) => {
            const indice_area = tmp.data.findIndex(object => {
                return object.label === area_txt
                })
            const value = tmp.data[indice_area].value
            arr_areas_obj.push({
                value,
                label: area_txt
            })
        })
        // console.log("Inicialmente áreas es:")
        // console.log(arr_areas_obj)
        setAreas(arr_areas_obj)
        validarArea(arr_areas_obj)
    }, [usuario])
    
    // Nivel
    const comboNivel = [
        {label: 'Tienda', value: 1},
        {label: 'Zona', value: 2},
        {label: 'Región', value: 3},
        {label: 'Nacional', value: 4},
        {label: 'Admin', value: 5}
    ]
    const [nivel, setNivel] = useState({})
    const [opcionNivel, setOpcionNivel] = useState({})
    const [msgNivel, setMsgNivel] = useState({texto: '', visible: false, color: 'info'})
    const [validadoNivel, setValidadoNivel] = useState(false)
    const validarNivel = (e) => {
        // console.log(`El valor que se va a insertar es: ${valor}`)
        setMsgEnviar({
        visible: false
        })
        if (e.value > 0) {
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
        setNivel(e.value)
        setOpcionNivel({value: e.value, label: e.label})
    }
    
    // Tienda
    const [region, setRegion] = useState('')
    const [zona, setZona] = useState('')
    const [tienda, setTienda] = useState('')
    const [tiendaVisible, setTiendaVisible] = useState(false)
    // Cargar la tienda, que se obtiene de forma asíncrona a partir de los props
    useEffect(async () => {
        if (usuario.tienda) {
            const idTienda = await cargarFiltros.numeroTienda(usuario.tienda)
            const regionYZona = await cargarFiltros.getRegionYZona(idTienda.data.numeroTienda)
            setRegion(regionYZona.data.region.value)
            setZona(regionYZona.data.zona.value)
            setTienda(idTienda.data.numeroTienda)
        }
        setTiendaVisible(true)
    }, [usuario])
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
    
    // Razón del Rechazo
    const [razonRechazo, setRazonRechazo] = useState('')
    const [validadoRazonRechazo, setValidadoRazonRechazo] = useState(false)
    const [visibleRazonRechazo, setVisibleRazonRechazo] = useState(false)
    const [msgRazonRechazo, setMsgRazonRechazo] = useState({texto: '', visible: false, color: 'info'})
    useEffect(() => {
        if (estatusValue.value === 'rechazado') {
            setVisibleRazonRechazo(true)
            setValidadoRazonRechazo(false)
        } else {
            setVisibleRazonRechazo(false)
            setRazonRechazo('')
            setValidadoRazonRechazo(true)
        }
    }, [estatusValue])
    const validarRazonRechazo = (valor) => {
        if (visibleRazonRechazo) {
            if (!isByteLength(valor, {min:10, max: undefined})) {
                setMsgRazonRechazo({
                    texto: `Por favor redacta una razón más larga`,
                    visible: true,
                    color: 'danger'
                })
                setValidadoRazonRechazo(false)
            } else {
                setMsgRazonRechazo({
                    texto: `✔`,
                    visible: true,
                    color: 'success'
                })
                setValidadoRazonRechazo(true)
            }
            setRazonRechazo(valor)
        } else {
            setValidadoRazonRechazo(true)
            setRazonRechazo('')
        }
    }

    // Validar formulario completo
    const handleRegistro = async (e) => {
        e.preventDefault()
        if (!(validadoEmail && validadoNombre && validadoArea && validadoTienda && validadoNivel && validadoArea && validadoRazonRechazo)) {
            setMsgEnviar({
                texto: `Por favor llena todos los campos y verifica que no tengan errores`,
                visible: true,
                color: 'danger'
            })
        } else {
        // Enviar
        const resp_registro = await userService.updateUsuario(email, nombre, areas, tienda, nivel, estatusValue.value, razonRechazo, id)
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
        setReloadTabla(reloadTabla + 1)
        }
    }

    // Cargar todo de nuevo cuando cambia el usuario
    useEffect(async () => {
        setEstatusValue({label: usuario.estatus, value: usuario.estatus})
        setEmail(usuario.email)
        setNombre(usuario.nombre)
        const indiceNivel = comboNivel.findIndex(object => {
            return object.label === usuario.nivel
        })
        setNivel(comboNivel[indiceNivel].value)
        setOpcionNivel(comboNivel[indiceNivel])
        validarNivel(comboNivel[indiceNivel])
        validarEmail(usuario.email)
        validarNombre(usuario.nombre)
        const id_tmp = await userService.getIdFromEmail(usuario.email)
        console.log("ID del usuario:")
        console.log(id_tmp)
        setId(id_tmp)
    }, [usuario])
    
    return (
        tiendaVisible && <Card>
            <CardHeader>
                <CardTitle tag='h2' className='font-weight-bold mb-1'>
                Actualizar Usuario
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
                    value={areasOpcion}
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
                    value={opcionNivel}
                    isClearable={true}
                    onChange={e => {
                        validarNivel(e)
                    }}
                    />
                    {msgNivel.visible && <Alert color={msgNivel.color}>{msgNivel.texto} </Alert>}
                </FormGroup>
                <FormGroup>
                    <Label className='form-label' for='login-email'>
                    Tienda por Defecto
                    </Label>
                    <Filtro usuario={usuario} region={region} zona={zona} tienda={tienda} setRegion={setRegion} setZona={setZona} setTienda={setTienda} />
                </FormGroup>
                <FormGroup>
                <Label>Cambiar estatus</Label>
                <Select
                theme={selectThemeColors}
                value={estatusValue}
                className='react-select'
                classNamePrefix='select'
                name='estatus'
                menuPlacement='top'
                options={comboEstatus}
                onChange={(e) => setEstatusValue(e)}
                // isClearable={true}
                />
                </FormGroup>
                {visibleRazonRechazo && <FormGroup>
                <Label>Razón del rechazo</Label>
                <Input 
                    type='text'
                    id='registro-razonRechazo' 
                    autoFocus 
                    value={razonRechazo}
                    onChange={e => validarRazonRechazo(e.target.value)} 
                />
                {msgRazonRechazo.visible && <Alert color={msgRazonRechazo.color}>{msgRazonRechazo.texto} </Alert>}
                </FormGroup>}
                <br />
                {errorVisible && <Alert color="danger">
                    Ocurrió un error al actualizar la base de datos
                </Alert>}
                <Button.Ripple color='primary' type='submit' block>
                    Modificar Datos
                </Button.Ripple>
                {msgEnviar.visible && <Alert color={msgEnviar.color}>{msgEnviar.texto} </Alert>}
                </Form>
                </Col>
                </Row>
            </CardBody>
        </Card>
    )
}

export default UpdateUsuario