import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts from 'highcharts'
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

const ColumnasDrilldown = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor }) => {
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
          url: `${CustomUrls.ApiUrl()}columnasDrilldown/${seccion}?titulo=${titulo}`,
          headers: authHeader(),
          data: {
            fechas,            
            region,
            zona,
            tienda,
            proveedor
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        const datos_tmp = res.data.res
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            setSeries_outer(datos_tmp.series_outer)
            setDrilldown_series(datos_tmp.drilldown_series)
        } else {
            setSeries_outer([])
            setDrilldown_series([])
        }
      }, [fechas, region, zona, tienda, proveedor])
    
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
            series: {
                dataLabels: {
                    enabled: true,
                    color: colorTexto
                }
            }
        },
        plotOptions: {
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

    return (
        <Card>
            <CardBody>
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${tituloEnviar}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <HighchartsReact
                    highcharts={Highcharts}
                    options={options}
                />}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default ColumnasDrilldown