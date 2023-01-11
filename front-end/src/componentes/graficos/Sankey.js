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
import HighchartsSankey from "highcharts/modules/sankey"
HighchartsSankey(Highcharts)

const Sankey = ({ titulo, seccion, grupoDeptos, deptoAgrupado, periodo, agrupador, subDeptoAgrupado }) => {
    const [hayError, setHayError] = useState(false)
    const [data, setData] = useState([])
    const [colores, setColores] = useState(['#000'])
    // const [data, setData] = useState([
    //     ['ERP', 'Producto Omnicanal', 42541],
    //     ['Producto Omnicanal', 'Aptos para la venta', 27719],
    //     ['Producto Omnicanal', 'Baja', 14822],
    //     ['Aptos para la venta', 'Visibles en TL', 24789],
    //     ['Aptos para la venta', 'No visibles (en proceso)', 2920],
    //     ['Aptos para la venta', 'VoBo Falta', 10],
    //     ['Visibles en TL', 'CDB', 11335],
    //     ['Visibles en TL', 'Falta VoBo', 13454]
    // ])
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


    // Expoprtar
    // HC_exporting(Highcharts)
    // const chartComponent = useRef(null)
    // useEffect(() => {
    //     if (!cargando) {
    //         const chart = chartComponent.current.chart
    //     }
    //   }, [cargando])

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
        const res = await axios({
          method: 'post',
        //   url: `${CustomUrls.ApiUrl()}barras?titulo=${titulo}&seccion=${seccion}`,
          url: `${CustomUrls.ApiUrl()}sankey/${seccion}?titulo=${titulo}`,
          headers: authHeader(),
          data: {
            grupoDeptos, 
            deptoAgrupado,
            periodo, 
            agrupador, 
            subDeptoAgrupado
          }
        })
        dispatchLoader({tipo: 'recibirDeAPI'})
        const data_tmp = res.data.data
        // console.log('data:')
        // console.log(data_tmp)
        // console.log(`Hay resultados: ${res.data.hayResultados}`)
        if (res.data.hayResultados === 'error') {
            setHayError(true)
        } else if (res.data.hayResultados === 'si') {
        setHayError(false)
            setData(data_tmp)
            setColores(res.data.colors)
        } else {
            setData([])
        }
      }, [grupoDeptos, deptoAgrupado, periodo, subDeptoAgrupado])
    
      Highcharts.setOptions({
        lang: {
          thousandsSep: ','
        }
      })
  
    const options = {
        colors: colores,
        accessibility: {
            point: {
                valueDescriptionFormat: '{index}. {point.from} to {point.to}, {point.weight:,.0f}.'
            }
        },
        series: [
            {
            keys: ['from', 'to', 'weight'],
            data
        }
        ],
        plotOptions: {
            series: {
                colorByPoint: true
            }
        },        
        type: 'sankey',
        name: 'Métricas Básicas',
        chart: {
            type: 'sankey',
            backgroundColor: colorFondo
        },
        title: {
            text: ''
        },
        tooltip: {
            pointFormat: '{point.from} ➠ {point.to}: <b>{point.weight:,.0f}</b>',
            nodeFormat: '{point.name}: <b>{point.sum:,.0f}</b>',
            shared: true
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

export default Sankey