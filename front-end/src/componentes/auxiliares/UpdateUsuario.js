import { selectThemeColors } from '@utils'
import { useEffect, useState } from 'react'
import axios from 'axios'
import authHeader from '@src/services/auth.header'
import CustomUrls from "../../services/customUrls"
import { Row, Col, CardTitle, Card, CardHeader, CardBody, CardText, Form, FormGroup, Label, Input, CustomInput, Button, Alert } from 'reactstrap'
import Select from 'react-select'
import '@styles/base/pages/page-auth.scss'
import Logo from '@src/assets/images/logo/logo.svg'
import Filtro from './Filtro'
import { isStrongPassword, isAlpha, isEmail } from "validator"
import userService from '../../services/user.service'
import cargarFiltros from '../../services/cargarFiltros'

const UpdateUsuario = ({usuario, setUsuario, reloadTabla, setReloadTabla}) => {

    const [estatusValue, setEstatusValue] = useState({label: '', value: ''})
    const [errorVisible, setErrorVisible] = useState(false)

    const comboEstatus = [
        {label: 'revisión', value: 'revisión'},
        {label: 'activo', value: 'activo'},
        {label: 'bloqueado', value: 'bloqueado'},
        {label: 'rechazado', value: 'rechazado'}
    ]

    return (
        <Card>
            <CardHeader>
                <CardTitle tag='h4'>Actualizar estatus de usuario</CardTitle>
            </CardHeader>
            <CardBody>
                <Row>
                    <Col>
                        <p><strong>usuario: </strong>{usuario.email}</p>
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
                        <Button
                            color='primary'
                            onClick={async (e) => {
                                axios({
                                    method: 'post',
                                    url: `${CustomUrls.ApiUrl()}updateEstatusUsuario`,
                                    headers: authHeader(),
                                    data: {
                                        email: usuario.email,
                                        estatus: estatusValue.value
                                    }
                                }).then(resp => {
                                    if (resp.data.exito) {
                                        setUsuario({email: '', estatus: ''})
                                        setReloadTabla(reloadTabla + 1)
                                    } else {
                                        setErrorVisible(true)
                                    }
                                })
                            }}
                        >
                            Enviar
                        </Button>
                        {errorVisible && <Alert color="danger">
                            Ocurrió un error al actualizar la base de datos
                        </Alert>}
                    </Col>
                </Row>
            </CardBody>
        </Card>
      )
}

export default UpdateUsuario