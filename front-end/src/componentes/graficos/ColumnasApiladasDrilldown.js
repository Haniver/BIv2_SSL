import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts, { data } from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import authHeader from '../../services/auth.header'
import axios from 'axios'
import CustomUrls from '../../services/customUrls'
import { ThemeColors } from '@src/utility/context/ThemeColors'
import { useSkin } from '@hooks/useSkin'
import { Card, CardBody, CardTitle } from 'reactstrap'
import drilldown from 'highcharts/modules/drilldown'
import LoadingGif from '../auxiliares/LoadingGif'
import fechas_srv from '../../services/fechas_srv'
require('highcharts/modules/data')(Highcharts)
require('highcharts/modules/exporting')(Highcharts)
require('highcharts/modules/export-data')(Highcharts)

const ColumnasApiladasDrilldown = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, tipoEntrega, origen }) => {
    const [hayError, setHayError] = useState(false)
    const [series_outer, setSeries_outer] = useState([])
    const [drilldown_series, setDrilldown_series] = useState([])
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


    //Skins
    const [skin, setSkin] = useSkin()
    const colorTextoDark = '#CDCCCF'
    const colorTextoLight = '#272F44'
    const colorFondoDark = '#272F44'
    const colorFondoLight = 'white'
    // Esto es lo que tienes que cambiar manualmente para los colores del skin
    const [colorFondo, setColorFondo] = useState(colorFondoLight)
    const [colorTexto, setColorTexto] = useState(colorTextoLight)
    const { colors } = useContext(ThemeColors)
    
    drilldown(Highcharts)


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

    useEffect(async () => {
        dispatchLoader({tipo: 'llamarAPI'})
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}columnasApiladasDrilldown/${seccion}?titulo=${titulo}`,
          headers: authHeader(),
          data: {
            fechas,            
            region,
            zona,
            tienda,
            proveedor, 
            tipoEntrega,
            origen
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        // const datos_tmp = res.data.res
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
            setHayError(false)
            const tituloApiladas = res.data.tituloApiladas
            const colores = res.data.colores
            const categorias = res.data.categorias
            const subCategorias = res.data.subCategorias
            const dataN1 = res.data.dataN1
            const dataN2 = res.data.dataN2
            console.log("tituloApiladas:")
            console.log(tituloApiladas)
            console.log("colores:")
            console.log(colores)
            console.log("categorias:")
            console.log(categorias)
            console.log("subCategorias:")
            console.log(subCategorias)
            console.log("dataN1:")
            console.log(dataN1)
            console.log("dataN2:")
            console.log(dataN2)
            const series_outer_tmp = []
            for (let stack = 0; stack < tituloApiladas.length; stack++) {
                const data_tmp = []
                for (let cat = 0; cat < categorias.length; cat++) {
                    data_tmp.push({
                        name: categorias[cat],
                        y: dataN1[stack][cat],
                        drilldown: categorias[cat]
                    })
                }
                series_outer_tmp.push({
                    name: tituloApiladas[stack],
                    color: colores[stack],
                    data: data_tmp
                })
            }
            console.log('series_outer:')
            console.log(JSON.stringify(series_outer_tmp))
            setSeries_outer(series_outer_tmp)
            // const drilldown_series_tmp = []
            // for (let cat = 0; cat < categorias.length; cat++) {
            //     const dataN2_tmp = []
            //     for (let stack = 0; stack < tituloApiladas.length; stack++) {
            //         const dataN2_2_tmp = []
            //         for (let subCat = 0; subCat < subCategorias[cat].length; subCat++) {
            //             dataN2_2_tmp.push({
            //                 name: subCategorias[cat][subCat],
            //                 y: dataN2[cat][subCat][stack]
            //             })
            //         }
            //         dataN2_tmp.push({
            //             name: tituloApiladas[stack],
            //             color: colores[stack],
            //             data: dataN2_2_tmp
            //         })
            //         drilldown_series_tmp.push({
            //             name: tituloApiladas[stack],
            //             id: categorias[cat],
            //             color: colores[stack],
            //             data: dataN2_tmp
            //         })
            //     }
            // }
            const drilldown_series_tmp = []
            for (let cat = 0; cat < categorias.length; cat++) {
                for (let stack = 0; stack < tituloApiladas.length; stack++) {
                    const dataN2_tmp = []
                    for (let subCat = 0; subCat < subCategorias[cat].length; subCat++) {
                        const dataN2_2_tmp = []
                        for (let stack = 0; stack < tituloApiladas.length; stack++) {
                            dataN2_2_tmp.push({
                                name: tituloApiladas[stack],
                                y: dataN2[cat][subCat][stack]
                            })
                        }
                        dataN2_tmp.push({
                            name: subCategorias[cat][subCat],
                            data: dataN2_2_tmp
                        })
                    }
                    drilldown_series_tmp.push({
                        name: tituloApiladas[stack],
                        id: categorias[cat],
                        color: colores[stack],
                        data: dataN2_tmp
                    })
                }
            }
            console.log("drilldown_series:")
            console.log(JSON.stringify(drilldown_series_tmp))
            setDrilldown_series(drilldown_series_tmp)
        } else {
            setSeries_outer([])
            setDrilldown_series([])
        }
      }, [fechas, region, zona, tienda, proveedor, tipoEntrega, origen])
    
    const options = {
        chart: {
            type: 'column',
            backgroundColor: colorFondo
        },
        title: {
            text: ''
        },
        subtitle: {
            text: 'Haz clic en una columna para ver el detalle'
        },
        accessibility: {
            announceNewData: {
                enabled: true
            }
        },
        xAxis: {
            type: 'category',
            labels: {
                style: {
                    color: colorTexto
                }
            }
        },
        yAxis: {
            title: {
                text: yLabel
            },
            labels: {
                style: {
                   color: colorTexto
                }
            } 
        },
        legend: {
            enabled: false
        },
        plotOptions: {
            column: {
                stacking: 'normal',
                dataLabels: {
                    enabled: true
                }
            },
           series: {
                dataLabels: {
                    enabled: true,
                    // format: '${point.y:,.2f}',
                    formatter(tooltip) {
                        if (formato === 'moneda') {
                            return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                        } else if (formato === 'entero') {
                            return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                        } else if (formato === 'porcentaje') {
                            return `${Highcharts.numberFormat(this.value * 100, 2, '.', ',')}%`
                        }
                    },
                    color: colorTexto,
                    textOutline: colorTexto
                },
                borderWidth: 0,
                color: colors.dark.main
            }
        },
        tooltip: {
            headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
            // pointFormat: '<span style="color:{point.color}">{point.name}</span>: ${point.y:,.2f}<br/>'
            formatter(tooltip) {
                if (formato === 'moneda') {
                    return `${this.point.name}: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
                } else if (formato === 'entero') {
                    return `${this.point.name}: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
                } else if (formato === 'porcentaje') {
                    return `${this.point.name}: ${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%`
                }
            }
        },
        series: series_outer,
        drilldown: {
            series: drilldown_series,
            activeAxisLabelStyle: {
                textDecoration: 'none',
                color: colorTexto
            },
            activeDataLabelStyle: {
                textDecoration: 'none',
                color: colorTexto
            },
            credits: {
            enabled: false
            }
        },
        credits: {
            enabled: false
        }
    }

    useEffect(() => {
        console.log("series_outer:")
        console.log(series_outer)    
        console.log("drilldown_series:")
        console.log(drilldown_series)    
    }, [drilldown_series])

    return (
        <Card>
            <CardBody>
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${titulo}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <HighchartsReact
                    highcharts={Highcharts}
                    options={options}
                />}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default ColumnasApiladasDrilldown