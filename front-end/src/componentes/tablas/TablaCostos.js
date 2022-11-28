import { React, useState, useMemo, useEffect, useContext, useReducer } from 'react'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody, Input, Button, Row, Col } from 'reactstrap'
import { Link } from 'react-router-dom'
import DataTable, { ExpanderComponentProps } from 'react-data-table-component'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
import Label from 'reactstrap/lib/Label'
import Barras from '../graficos/Barras'

// Búsqueda
const FilterComponent = ({ origen, tituloFiltro, onFilter, onClear }) => {
    // useEffect(() => {
    //     console.log(`filterTextEnvio: ${filterTextEnvio}`)
    //     console.log(`filterTextRH: ${filterTextRH}`)
    //     console.log(`filterTextTotal: ${filterTextTotal}`)
    // }, [filterTextEnvio, filterTextRH, filterTextTotal])
    return (
    <>
        <Col className='mb-1' xl='3' md='6' xs='12'>
            <Label>{tituloFiltro}</Label>
            <Input
                id="search"
                type="text"
                placeholder="100"
                aria-label="Search Input"
                value={origen}
                onChange={onFilter}
                className="w-25"
            />
        </Col>
    </>
) 
}

const TablaCostos = ({titulo, tituloAPI, seccion, quitarBusqueda, quitarExportar, quitarPaginacion, fechas, region, zona, tienda, proveedor, tipoEntrega, depto, subDepto, mes, canal, agrupador, periodo, reload, setProducto, setUsuario, setEstatus, tipoEntrega2, tipoEntrega3, detalle, estatus, formato, sku, e3, canal2, opcionesPaginacion = [5, 10, 15], setSibling, botonEnviar, mesRFM, anioRFM, fromSibling, origen, anio, metodoEnvio}) => {
    const tituloEnviar = (tituloAPI !== undefined) ? tituloAPI : titulo
    // Skins
    const [skin, setSkin] = useSkin()
    const colorTextoDark = '#CDCCCF'
    const colorTextoLight = '#272F44'
    const colorFondoDark = '#272F44'
    const colorFondoLight = 'white'
    const [colorFondo, setColorFondo] = useState(colorFondoDark)
    const [colorTexto, setColorTexto] = useState(colorTextoDark)
    // const [tituloMod, setTituloMod] = useState(tituloEnviar)
    const { colors } = useContext(ThemeColors)

    // Datos iniciales
    const [hayError, setHayError] = useState(false)
        const [estadoLoader, dispatchLoader] = useReducer((estadoLoader, accion) => {
        switch (accion.tipo) {
          case 'llamarAPI':
            return { contador: estadoLoader.contador + 1 }
          case 'recibirDeAPI':
            return { contador: estadoLoader.contador - 1 }
          default:
            throw new Error()
        }
      }, {contador: 0})

    const [columns, setColumns] = useState([
        {
            name: 'Mensaje',
            selector: 'mensaje',
            sortable: true,
            minWidth: '150px'
        }
    ])
    
    const [data, setData] = useState([
        {
            mensaje: 'Por favor espera en lo que se cargan los datos...'
        }
    ])

    // Estilo de la fila cuando es un total (o sea, viene desde el back end con una propiedad esTotal = True)
    const conditionalRowStyles = [
        {
          when: row => row.esTotal,
          style: {
            backgroundColor: colors.secondary.main,
            fontWeight: 'bolder !important',
            '&:hover': {
              cursor: 'pointer'
            }
          }
        }
      ]

    // Skins
    useEffect(async () => {
        // Aquí también cambiar los colores dependiendo del skin, según líneas 18-19
        if (skin === 'dark') {
            setColorFondo(colorFondoDark)
            setColorTexto(colorTextoDark)
        } else {
            setColorFondo(colorFondoLight)
            setColorTexto(colorTextoLight)
        }
    }, [skin])

    // Para debugging
    // useEffect(() => {
    //     // Aquí también cambiar los colores dependiendo del skin, según líneas 18-19
    //     console.log(`tipoEntrega desde Tabla: ${tipoEntrega}`)
    // }, [tipoEntrega])

    // Traer datos de API
    useEffect(async () => {
        dispatchLoader({tipo: 'llamarAPI'})
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}tablasExpandibles/${seccion}?titulo=${tituloEnviar}`,
          headers: authHeader(),
          data: {
            tipoEntrega,
            fechas,
            region,
            zona,
            tienda,
            proveedor,
            depto, 
            subDepto, 
            mes,
            canal,
            agrupador,
            periodo,
            tipoEntrega2,
            tipoEntrega3,
            detalle,
            estatus,
            formato,
            sku,
            e3,
            canal2, 
            mesRFM, 
            anioRFM,
            fromSibling,
            origen,
            anio,
            metodoEnvio
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            const columns_tmp = res.data.columns
            // console.log('Columnas:')
            // console.log(columns_tmp)
            const formatos = {}
            const columns = []
            columns_tmp.forEach(columna => {
                const objeto_columna = {
                    name: columna.name,
                    selector: columna.selector, 
                    sortable: true,
                    sortFunction: Function("a", "b", `{
                        let aField = ''
                        let bField = ''
                        // En el caso de que sea una fecha
                        if (a.${columna.selector}.length === 10 && a.${columna.selector}.substring(2,3) === '/' && a.${columna.selector}.substring(5,6) === '/' && b.${columna.selector}.length === 10 && b.${columna.selector}.substring(2,3) === '/' && b.${columna.selector}.substring(5,6) === '/') {
                            // console.log(a.${columna.selector}.substring(6,10)+a.${columna.selector}.substring(3,5)+a.${columna.selector}.substring(0,2))
                            aField = parseInt(a.${columna.selector}.substring(6,10)) * 10000000 + parseInt(a.${columna.selector}.substring(3,5)) * 1000 + parseInt(a.${columna.selector}.substring(0,2))
                            bField = parseInt(b.${columna.selector}.substring(6,10)) * 10000000 + parseInt(b.${columna.selector}.substring(3,5)) * 1000 + parseInt(b.${columna.selector}.substring(0,2))
                        // En el caso de que sea texto
                        } else {
                            const aField_tmp =  parseFloat(a.${columna.selector}.replaceAll('$', '').replaceAll(',', '').replaceAll('%', '').replaceAll(' ', ''))
                            const bField_tmp =  parseFloat(b.${columna.selector}.replaceAll('$', '').replaceAll(',', '').replaceAll('%', '').replaceAll(' ', ''))
                            // En el caso de que sea un valor numérico
                            if (!isNaN(aField_tmp) && !isNaN(bField_tmp)) {
                                // console.log('Entró a número')
                                aField = aField_tmp
                                bField = bField_tmp
                            // En el caso de que sea texto
                            } else  {
                                // console.log('Entró a texto')
                                aField =  a.${columna.selector}.toLowerCase()
                                bField =  b.${columna.selector}.toLowerCase()
                            }
                        }
                        // console.log(aField + ' vs. ' + bField)
                        let comparison = 0
                        if (aField > bField) {
                            comparison = 1
                        } else if (aField < bField) {
                            comparison = -1
                        }
                        return comparison
                    }`)
                }
                // if (columna.formato === 'texto' || columna.formato === 'url') { // Esto es para que se haga más ancha la columna si el texto es muy largo
                //     const TxtWrap = row => <span>{row[columna.selector]}</span>
                //     objeto_columna.minWidth = '180px'
                //     // objeto_columna.width = 'auto'
                //     objeto_columna.cell = row => <TxtWrap {...row} />
                // }
                // if (columna.formato === 'entero') { // Esto es para que se haga más ancha la columna si el número es muy largo
                //     objeto_columna.minWidth = '110px'
                // }

                // Esto es para determinar el ancho de columna desde el backend
                if (columna.ancho !== undefined) {
                    objeto_columna.width = columna.ancho
                }
                if (columna.formato === 'url') {
                    objeto_columna.cell = (d) => (
                        <>
                            <a href={d.url} target="_blank" className="dlink">
                            Ir a mapa
                            </a>
                        </>
                    )
                } else if (columna.formato === 'botonProducto') {
                    // console.log(columna.formato)
                    objeto_columna.cell = (d) => (
                        <Button
                            color='dark'
                            onClick={e => {
                                setProducto({nombre: d.Articulo, sku: d.SKU, fecha: d.Fecha, tienda: d.IdTienda})
                            }}
                        >
                            ✎
                        </Button>
                    )
                } else if (columna.formato === 'botonUsuario') {
                    // console.log(columna.formato)
                    objeto_columna.cell = (d) => (
                        <Button
                            color='dark'
                            onClick={e => {
                                setUsuario({email: d.Email, estatus: d.Estatus, nombre: d.Nombre, areas: d.Areas, nivel: d.Nivel, tienda: d.Tienda})
                            }}
                        >
                            ✎
                        </Button>
                    )
                } else if (columna.formato === 'sibling') {
                    objeto_columna.cell = (d) => (
                        <Button
                            color='white'
                            onClick={e => {
                                // console.log('Llamar a setSibling')
                                // console.log(d.sibling.replace(/""/g, '"'))
                                // console.log(JSON.parse(d.sibling.replace(/""/g, '"')))
                                setSibling(JSON.parse(d.sibling.replace(/""/g, '"')))
                                // console.log(JSON.parse(d.sibling))
                            }}
                        >
                            🔗
                        </Button>
                    )
                } else if (columna.formato === 'detalleAgente') {
                    // console.log("Entró a detalleAgente en Tabla.js")
                    objeto_columna.cell = (d) => (
                        <Button
                            color='white'
                            onClick={e => {
                                setSibling(d.Agente)
                            }}
                        >
                            🔗
                        </Button>
                    )
                } else if (columna.formato === 'detalleDepartamento') {
                    objeto_columna.cell = (d) => (
                        d.IdDepto !== '--' && <Button
                            color='white'
                            onClick={e => {
                                setSibling(d.IdDepartamento)
                            }}
                        >
                            🔗
                        </Button>
                    )
                } else if (columna.formato === 'detalleSubDepartamento') {
                    objeto_columna.cell = (d) => (
                        <Button
                            color='white'
                            onClick={e => {
                                const subDepto_a_enviar = d.IdSubDepartamento.replace(/,/g, '')
                                setSibling(subDepto_a_enviar)
                            }}
                        >
                            🔗
                        </Button>
                    )
                } else if (columna.formato === 'detalleClase') {
                    objeto_columna.cell = (d) => (
                        <Button
                            color='white'
                            onClick={e => {
                                const clase_a_enviar = d.IdClase.replace(/,/g, '')
                                setSibling(clase_a_enviar)
                            }}
                        >
                            🔗
                        </Button>
                    )
                } else if (columna.formato === 'detalleSubClase') {
                    objeto_columna.cell = (d) => (
                        <Button
                            color='white'
                            onClick={e => {
                                const subClase_a_enviar = d.IdSubClase.replace(/,/g, '')
                                setSibling(subClase_a_enviar)
                            }}
                        >
                            🔗
                        </Button>
                    )
                }
                // Esto es para poner un código de colores a las celdas
                if (columna.colores === true) {
                    const color_bajo = (res.data.colores[0] === 'normal') ? 'texto-rojo' : 'texto-verde'
                    const color_alto = (res.data.colores[0] === 'normal') ? 'texto-verde' : 'texto-rojo'
                    objeto_columna.cell = (d) => (
                        <span className={(d[objeto_columna.selector] !== undefined) ? ((parseFloat(d[objeto_columna.selector].replace(/,/g, '').replace(/%/g, '').replace(/\$/g, '')) <= res.data.colores[1]) ? color_bajo : ((parseFloat(d[objeto_columna.selector].replace(/,/g, '').replace(/%/g, '').replace(/\$/g, '')) >= res.data.colores[2]) ? color_alto : 'texto-amarillo')) : ''}>{d[objeto_columna.selector]}</span>
                        // <span>{d[objeto_columna.selector].replace(/,/g, '').replace(/%/g, '').replace(/\$/g, '')}</span>
                    )
                }
                columns.push(objeto_columna)
                formatos[columna.selector] = columna.formato
            })
            const data_tmp = res.data.data
            // console.log("Data de tabla:")
            // console.log(data_tmp)
            const data = []
            data_tmp.forEach(fila => {
                const fila_a_insertar = {}
                for (const [key, value] of Object.entries(fila)) {
                    // console.log(`Key, Value: ${key}, ${value}`)
                    if (formatos[key] === 'texto' || formatos[key] === 'url' || formatos[key] === 'sibling') {
                        fila_a_insertar[key] = value
                    } else if (formatos[key] === 'entero') {
                        if (value === '--') {
                            fila_a_insertar[key] = '--'
                        } else {
                            fila_a_insertar[key] = Math.round(value).toLocaleString('es-MX', {minimumFractionDigits: 0, maximumFractionDigits: 0})
                        }
                    } else if (formatos[key] === 'moneda') {
                        if (value === '--') {
                            fila_a_insertar[key] = '--'
                        } else {
                            fila_a_insertar[key] = `$${fila_a_insertar[key] = value.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`
                        }
                    } else if (formatos[key] === 'decimales') {
                        if (value === '--') {
                            fila_a_insertar[key] = '--'
                        } else {
                            fila_a_insertar[key] = value.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})
                        }
                    } else if (formatos[key] === 'porcentaje') {
                        if (value === '--') {
                            fila_a_insertar[key] = '--'
                        } else {
                            const x100 = value * 100
                            fila_a_insertar[key] = `${x100.toLocaleString('es-MX', {minimumFractionDigits: 2, maximumFractionDigits: 2})}%`
                        }
                    } else if (formatos[key] === 'sinComas') {
                        if (value === '--') {
                            fila_a_insertar[key] = '--'
                        } else {
                            fila_a_insertar[key] = Math.round(value).toLocaleString('es-MX', {minimumFractionDigits: 0, maximumFractionDigits: 0}).replace(/,/g, '')
                        }
                    // Conservar el esTotal, en caso de existir
                    } else if (key === 'esTotal') {
                        fila_a_insertar[key] = true
                    } else {
                        fila_a_insertar[key] = value
                    }
                }
                data.push(fila_a_insertar)
            })
            setColumns(columns)
            // console.log("La data de la tabla es:")
            // console.log(data)
            setData(data)
        } else {
            setColumns([
            {
                name: 'Sin resultados',
                selector: 'mensaje'
            }
            ])
            setData([
            {
                mensaje: 'Prueba usar otros filtros'
            }
            ])
            // console.log("Tabla sin resultados")
            // console.log(`Query de ${titulo}:`)
            // console.log(JSON.stringify(res.data.pipeline)) // Esto lo estás comentando para ponerlo más abajo, independiente de que haya resultados o no
        }
        // console.log(`Query de ${tituloEnviar}:`)
        // console.log(JSON.stringify(res.data.pipeline))
    }, [fechas, region, zona, tienda, tipoEntrega, depto, subDepto, mes, canal, agrupador, periodo, reload, tipoEntrega2, tipoEntrega3, detalle, estatus, formato, sku, e3, canal2, botonEnviar, mesRFM, anioRFM, fromSibling, origen, anio, metodoEnvio])

    //Búsqueda
    const [filterTextEnvio, setFilterTextEnvio] = useState('0')
    const [filterTextRH, setFilterTextRH] = useState('0')
    const [filterTextTotal, setFilterTextTotal] = useState('0')
    const [resetPaginationToggle, setResetPaginationToggle] = useState(false)

    // Exportar a CSV
    function convertArrayOfObjectsToCSV(array) {
        let result
        const columnDelimiter = '","'
        const lineDelimiter = '"\n"'
        const keys = Object.keys(data[0])

        result = '"'
        result += keys.join(columnDelimiter)
        result += lineDelimiter

        array.forEach(item => {
            let ctr = 0
            keys.forEach(key => {
                if (ctr > 0) result += columnDelimiter
                result += item[key]
                ctr++
            })
            result += lineDelimiter
        })

        return result
    }
    function downloadCSV(array) {
        const link = document.createElement('a')
        let csv = convertArrayOfObjectsToCSV(array)
        if (csv === null) return

        const filename = `${tituloEnviar}.csv`

        if (!csv.match(/^data:text\/csv/i)) {
            csv = `data:text/csv;charset=utf-8,${csv}`
        }

        link.setAttribute('href', encodeURI(csv))
        link.setAttribute('download', filename)
        link.click()
    }
    const Export = ({ onExport }) => <Button color='primary' onClick={e => onExport(e.target.value)}>Exportar a Excel</Button>
    const actionsMemo = <Export onExport={() => downloadCSV(data)} />

    //Búsqueda
    const filteredItems = data.filter(item => {
        if (item.CostoEnvioRH && item.CostoRHPorPedido && item.TotalGtosXPedido) {
            const EnvioAsFloat = parseFloat(item.CostoEnvioRH.replace(/[^0-9.-]/g, ''))
            const filterTextEnvioAsFloat = parseFloat(filterTextEnvio.replace(/[^0-9.-]/g, ''))
            const RHAsFloat = parseFloat(item.CostoRHPorPedido.replace(/[^0-9.-]/g, ''))
            const filterTextRHAsFloat = parseFloat(filterTextRH.replace(/[^0-9.-]/g, ''))
            const TotalAsFloat = parseFloat(item.TotalGtosXPedido.replace(/[^0-9.-]/g, ''))
            const filterTextTotalAsFloat = parseFloat(filterTextTotal.replace(/[^0-9.-]/g, ''))
            
            if ((parseFloat(EnvioAsFloat) < parseFloat(filterTextEnvioAsFloat)) || (parseFloat(RHAsFloat) < parseFloat(filterTextRHAsFloat)) || (parseFloat(TotalAsFloat) < parseFloat(filterTextTotalAsFloat))) {
                return false
            }
        } else {
            return false
        }
        return true
    })

    //Búsqueda y Paginación
    const subHeaderComponentMemo = useMemo(() => {
        const handleClear = () => {
            if (filterTextEnvio) {
                setResetPaginationToggle(!resetPaginationToggle)
                setFilterTextEnvio('')
            }
            if (filterTextRH) {
                setResetPaginationToggle(!resetPaginationToggle)
                setFilterTextRH('')
            }
            if (filterTextTotal) {
                setResetPaginationToggle(!resetPaginationToggle)
                setFilterTextTotal('')
            }
        }

        return (
            <>
                <Row className='match-height'>
                    <FilterComponent onFilter={e => setFilterTextEnvio(e.target.value)} onClear={handleClear} tituloFiltro="🚚 Costo de Envío RH mayor a:" origen={filterTextEnvio} />
                    <FilterComponent onFilter={e => setFilterTextRH(e.target.value)} onClear={handleClear} tituloFiltro="👷 Costo RH Por Pedido mayor a:" origen={filterTextRH} />
                    <FilterComponent onFilter={e => setFilterTextTotal(e.target.value)} onClear={handleClear} tituloFiltro="📦 Gasto Total por Pedido mayor a:" origen={filterTextTotal} />
                </Row>
            </>
        )    
    }, [filterTextEnvio, filterTextRH, filterTextTotal, resetPaginationToggle])

    // const opcionesPaginacion = (opcionesPaginacion === undefined) ? [5,15] : opcionesPaginacion

    //Opciones de paginación
    const paginationComponentOptions = {
        rowsPerPageText: 'Filas por página',
        rangeSeparatorText: 'de',
        selectAllRowsItem: false
        // selectAllRowsItemText: 'Todos'
    }

    //Estilos
    const customStyles = {
        table: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        rows: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        header: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        subHeader: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        head: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        headRow: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        headCells: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            },
            activeSortStyle: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        },
        pagination: {
            style: {
                color: colorTexto,
                backgroundColor: colorFondo
            }
        }
    }

    // const ExpandedComponent = ({ data }) => {
    //     // <pre>{JSON.stringify(data, null, 2)}</pre>
    //     const dataSub = JSON.parse(data.subTabla)
    //     { (dataSub.data !== undefined) ? <DataTable
    //         // title={titulo}
    //         columns={JSON.parse(dataSub.columns)}
    //         data={JSON.parse(dataSub.data)}
    //         paginationResetDefaultPage={resetPaginationToggle} // optionally, a hook to reset pagination to page 1
    //         onColumnOrderChange={cols => console.log(cols)}
    //         paginationComponentOptions={paginationComponentOptions}
    //         customStyles={customStyles}
    //         highlightOnHover
    //         // Algunas filas vienen con una propiedad "esTotal = true" desde el back end. Si lo tienen, usarlo para darle formato de Total a esa fila:
    //         conditionalRowStyles={conditionalRowStyles}
    //     /> : <></> }
    // }

    const ExpandedComponent = ({ data }) => {
        if (data.subTabla) {
            const subTabla = JSON.parse(data.subTabla)
            if (subTabla.data.length > 0) {
                console.log(`subtabla.data:`)
                console.log(subTabla.data)
                return (<DataTable
                    columns={subTabla.columns}
                    data={subTabla.data}
                    actions={false}
                    paginationResetDefaultPage={resetPaginationToggle} // optionally, a hook to reset pagination to page 1
                    onColumnOrderChange={cols => console.log(cols)}
                    customStyles={{
                        headRow: {
                            style: {
                                backgroundColor: colors.light.main
                            }
                        },
                        rows: {
                            style: {
                                backgroundColor: colors.light.main
                            }
                        }
                    }}
                    highlightOnHover
                    // Algunas filas vienen con una propiedad "esTotal = true" desde el back end. Si lo tienen, usarlo para darle formato de Total a esa fila:
                    conditionalRowStyles={conditionalRowStyles}
                />)
            }
        }
        return ''
    }
        
    return (
        <Card>
            <CardBody>
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${tituloEnviar}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <DataTable
                    title={titulo}
                    columns={columns}
                    data={filteredItems}
                    expandableRows 
                    expandableRowsComponent={ExpandedComponent}
                    actions={(quitarExportar) ? false : actionsMemo}
                    // Paginación
                    paginationResetDefaultPage={resetPaginationToggle} // optionally, a hook to reset pagination to page 1
                    subHeader
                    subHeaderComponent={subHeaderComponentMemo}
                    onColumnOrderChange={cols => console.log(cols)}
                    paginationComponentOptions={paginationComponentOptions}
                    pagination={!quitarPaginacion} paginationRowsPerPageOptions={opcionesPaginacion}
                    paginationPerPage={opcionesPaginacion[0]}
                    customStyles={customStyles}
                    highlightOnHover
                    // Algunas filas vienen con una propiedad "esTotal = true" desde el back end. Si lo tienen, usarlo para darle formato de Total a esa fila:
                    conditionalRowStyles={conditionalRowStyles}
                />}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default TablaCostos