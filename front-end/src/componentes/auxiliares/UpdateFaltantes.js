import { Card, CardBody, CardHeader, CardTitle, Button, Row, Col, Label } from "reactstrap"
import { selectThemeColors } from '@utils'
import { useEffect, useState } from 'react'
import Select from 'react-select'
import axios from 'axios'
import authHeader from '@src/services/auth.header'
import CustomUrls from "../../services/customUrls"

const UpdateFaltantes = ({producto, setProducto, reloadTabla, setReloadTabla, fecha, tienda}) => {

    const [comboMotivos, setComboMotivos] = useState({label: '', value: ''})
    const [motivoValue, setMotivoValue] = useState({label: '', value: ''})

    useEffect(async () => {
        const resp = await axios({
            method: 'get',
            url: `${CustomUrls.ApiUrl()}cargarMotivosFaltantes`,
            headers: authHeader()
        })
        console.log(resp.data)
        setComboMotivos(resp.data)

    }, [])

    return (
        <Card>
            <CardHeader>
                <CardTitle tag='h4'>Motivo Producto Faltante</CardTitle>
            </CardHeader>
            <CardBody>
                <Row>
                    <Col>
                        <p><strong>Producto: </strong>{producto.nombre}</p>
                        <p><strong>SKU: </strong>{producto.sku}</p>
                        <Label>¿Cuál fue el motivo del producto faltante?</Label>
                        <Select
                        theme={selectThemeColors}
                        value={motivoValue}
                        className='react-select'
                        classNamePrefix='select'
                        name='motivos'
                        options={comboMotivos}
                        onChange={(e) => setMotivoValue(e)}
                        // isClearable={true}
                        />
                        <br />
                        <Button
                            color='primary'
                            onClick={async (e) => {
                                axios({
                                    method: 'post',
                                    url: `${CustomUrls.ApiUrl()}updateMotivosFaltantes`,
                                    headers: authHeader(),
                                    data: {
                                        sku: parseInt(producto.sku.replace(/,/g, '')),
                                        motivo: parseInt(motivoValue.value),
                                        fecha: producto.fecha,
                                        tienda: parseInt(producto.tienda)
                                    }
                                }).then(resp => {
                                    if (resp.data.exito) {
                                        setProducto({nombre: '', sku: '', fecha: '', tienda: ''})
                                        setReloadTabla(reloadTabla + 1)
                                    }
                                })
                            }}
                        >
                            Enviar
                        </Button>
                    </Col>
                </Row>
            </CardBody>
        </Card>
      )
}

export default UpdateFaltantes