import { useState, useEffect, useContext, useReducer } from 'react'
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import HighchartsMore from 'highcharts/highcharts-more'
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
HighchartsMore(Highcharts)

const Spiderweb = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, tituloAPI, periodo, agrupador, provLogist }) => {
    const [hayError, setHayError] = useState(false)
    const [series, setSeries] = useState([])
    const [categories, setCategories] = useState([])
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

    useEffect(() => {
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
        // console.log(`Periodo desde ColumnasNps = ${periodo}`)
        const tituloEnviar = (tituloAPI) ? tituloAPI : titulo // Como la API usa el título de la gráfica para regresar su valor, había un problema cuando ese título es variable, como cuando incluye la fecha actual. Entonces, si desde la vista le mandas el prop tituloAPI, es ese el que se usa para la API. Si lo omites, se usa la variable titulo como estaba pensado originalmente
        const res = await axios({
          method: 'post',
          url: `${CustomUrls.ApiUrl()}spiderweb/${seccion}?titulo=${tituloEnviar}`,
          headers: authHeader(),
          data: {
            fechas,            
            categoria,
            tipoEntrega,
            region,
            zona,
            tienda,
            proveedor,
            periodo,
            agrupador,
            provLogist
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            const series_tmp = []
            setCategories(res.data.categories)
            res.data.series.forEach(elemento => {
                series_tmp.push({
                    name: elemento.name,
                    data: elemento.data,
                    color: colors[elemento.color].main,
                    pointPlacement: elemento.pointPlacement
                })
            })
            setSeries(series_tmp)
            // console.log('Series desde Spiderweb:')
            // console.log(JSON.stringify(series_tmp))
        } else {
            setCategories([])
            setSeries([])
        }
      }, [fechas, region, zona, tienda, proveedor, categoria, tipoEntrega, periodo, agrupador, provLogist])
    
    const options = {
        chart: {
            type: 'line',
            polar: true
        },
        title: {
            text: ''
        },
        pane: {
            size: '80%'
        },
        xAxis: {
            categories,
            tickmarkPlacement: 'on',
            labels: {align: 'left'},
            lineWidth: 0
        },
        yAxis: {
            gridLineInterpolation: 'polygon',
            lineWidth: 0,
            // max: maximo,
            min: 0
        },
        tooltip: {
            shared: true,
            pointFormat: '<span style="color:{series.color}">{series.name}: <b>{point.y:,.2f}%</b><br/>'
        },
        legend: {
            /*    
            align: 'center',
            verticalAlign: 'bottom',
            layout: 'vertical'
            */
            enabled: false
        },
        series,
        responsive: {
            rules: [
            {
                condition: {
                    maxWidth: 500
                },
                chartOptions: {
                    legend: {
                        align: 'center',
                        verticalAlign: 'bottom',
                        layout: 'horizontal'
                    },
                    pane: {
                        size: '70%'
                    }
                }
            }
            ]
        },
        credits: {
            enabled: false
        }
    }

    return (
        <Card>
            <CardBody>
                {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${tituloEnviar}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
                {!hayError && estadoLoader.contador === 0 && <>
                    <CardTitle className='centrado'>{titulo}</CardTitle>
                    <HighchartsReact
                        highcharts={Highcharts}
                        options={options}
                        // ref={chartComponent}
                    />
                    {/* <button onClick={chartComponent.exportChart()}>Exportar</button> */}
                </>}
                {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
            </CardBody>
        </Card>
    )
}

export default Spiderweb