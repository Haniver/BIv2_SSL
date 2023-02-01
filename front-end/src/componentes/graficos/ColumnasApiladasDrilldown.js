// import { useState, useEffect, useContext, useReducer } from 'react'
// import Highcharts, { data } from 'highcharts'
// import HighchartsReact from 'highcharts-react-official'
// import authHeader from '../../services/auth.header'
// import axios from 'axios'
// import CustomUrls from '../../services/customUrls'
// import { ThemeColors } from '@src/utility/context/ThemeColors'
// import { useSkin } from '@hooks/useSkin'
// import { Card, CardBody, CardTitle } from 'reactstrap'
// import drilldown from 'highcharts/modules/drilldown'
// import LoadingGif from '../auxiliares/LoadingGif'
// import fechas_srv from '../../services/fechas_srv'
// require('highcharts/modules/data')(Highcharts)
// require('highcharts/modules/exporting')(Highcharts)
// require('highcharts/modules/export-data')(Highcharts)

// const ColumnasApiladasDrilldown = ({ titulo, yLabel, seccion, formato, fechas, region, zona, tienda, proveedor, tipoEntrega, origen }) => {
//     const [hayError, setHayError] = useState(false)
//     const [series_outer, setSeries_outer] = useState([])
//     const [drilldown_series, setDrilldown_series] = useState([])
//         const [estadoLoader, dispatchLoader] = useReducer((estadoLoader, accion) => {
//         switch (accion.tipo) {
//           case 'llamarAPI':
//             return { contador: estadoLoader.contador + 1 }
//           case 'recibirDeAPI':
//             return { contador: estadoLoader.contador - 1 }
//           default:
//             throw new Error()
//         }
//       }, {contador: 0})


//     //Skins
//     const [skin, setSkin] = useSkin()
//     const colorTextoDark = '#CDCCCF'
//     const colorTextoLight = '#272F44'
//     const colorFondoDark = '#272F44'
//     const colorFondoLight = 'white'
//     // Esto es lo que tienes que cambiar manualmente para los colores del skin
//     const [colorFondo, setColorFondo] = useState(colorFondoLight)
//     const [colorTexto, setColorTexto] = useState(colorTextoLight)
//     const { colors } = useContext(ThemeColors)
    
//     drilldown(Highcharts)

//     useEffect(async () => {
//         // Aquí también cambiar los colores dependiendo del skin, según líneas 18-19
//         if (skin === 'dark') {
//             setColorFondo(colorFondoDark)
//             setColorTexto(colorTextoDark)
//         } else {
//             setColorFondo(colorFondoLight)
//             setColorTexto(colorTextoLight)
//         }
//     }, [skin])

//     useEffect(async () => {
//         dispatchLoader({tipo: 'llamarAPI'})
//         const res = await axios({
//           method: 'post',
//           url: `${CustomUrls.ApiUrl()}columnasDrilldown/${seccion}?titulo=${titulo}`,
//           headers: authHeader(),
//           data: {
//             fechas,            
//             region,
//             zona,
//             tienda,
//             proveedor, 
//             tipoEntrega,
//             origen
//           }
//         })
//         dispatchLoader({tipo: 'recibirDeAPI'})
//         // const datos_tmp = res.data.res
//         if (res.data.hayResultados === 'error') {
//             setHayError(true)
//         } else if (res.data.hayResultados === 'si') {
//             setHayError(false)
//             var tituloApiladas = data.res.tituloApiladas
//             var colores = data.res.colores
//             var categoriasN1 = data.res.categoriasN1
//             var categoriasN2 = data.res.categoriasN2
//             var series_outer_tmp = []
//             for (let bar = 0; bar < length(tituloApiladas); bar++) {
//                 for (let cat1 = 0; cat1 < length(categoriasN1); cat1++) {
//                     series_outer_tmp.push({
//                         name: tituloApiladas[bar],
//                         color: colores[bar],
//                         data: [{
//                             name: categorias[cat1],
//                             y: dataN1[bar][cat1],
//                             drilldown: true
//                         }]
//                     })
//                 }
//             }
//             setSeries_outer(series_outer_tmp)
//             var drilldown_series_tmp = []
//             for (let cat1 = 0; cat1 < length(categoriasN1); cat1++) {
//                 for (let bar = 0; bar < tituloApiladas; bar++) {
//                     let data_tmp = []
//                     for (let cat2 = 0; cat2 < length(categoriasN2); cat2++) {
//                         data_tmp.push([categoriasN2[cat2][]])
//                     }
//                     drilldown_series_tmp.push({
//                         [categoriasN1[cat1]]: {
//                             name: tituloApiladas[bar],
//                             color: colores[bar], 
//                             data: [
//                                 ['2009', 4.0],
//                                 ['2010', 4.0],
//                                 ['2011', 3.7],
//                                 ['2012', 3.7],
//                                 ['2013', 3.3],
//                                 ['2014', 3.3],
//                                 ['2015', 3.4],
//                                 ['2016', 3.6],
//                                 ['2017', 3.7]
//                             ]
//                         }
//                     })
//                 }
//             }
//             setDrilldown_series(drilldown_series_tmp)
//         } else {
//             setSeries_outer([])
//             setDrilldown_series([])
//         }
//       }, [fechas, region, zona, tienda, proveedor, tipoEntrega, origen])
    
//     const options = {
//         chart: {
//             type: 'column',
//             backgroundColor: colorFondo
//         },
//         title: {
//             text: ''
//         },
//         subtitle: {
//             text: 'Haz clic en una columna para ver el detalle'
//         },
//         accessibility: {
//             announceNewData: {
//                 enabled: true
//             }
//         },
//         xAxis: {
//             type: 'category',
//             labels: {
//                 style: {
//                     color: colorTexto
//                 }
//             }
//         },
//         yAxis: {
//             title: {
//                 text: yLabel
//             },
//             labels: {
//                 style: {
//                    color: colorTexto
//                 }
//             } 
//         },
//         legend: {
//             enabled: false
//         },
//         plotOptions: {
//             column: {
//                 stacking: 'normal',
//                 dataLabels: {
//                     enabled: true
//                 }
//             },
//            series: {
//                 dataLabels: {
//                     enabled: true,
//                     // format: '${point.y:,.2f}',
//                     formatter(tooltip) {
//                         if (formato === 'moneda') {
//                             return `$${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
//                         } else if (formato === 'entero') {
//                             return `${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
//                         } else if (formato === 'porcentaje') {
//                             return `${Highcharts.numberFormat(this.value * 100, 2, '.', ',')}%`
//                         }
//                     },
//                     color: colorTexto,
//                     textOutline: colorTexto
//                 },
//                 borderWidth: 0,
//                 color: colors.dark.main
//             }
//         },
//         tooltip: {
//             headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
//             // pointFormat: '<span style="color:{point.color}">{point.name}</span>: ${point.y:,.2f}<br/>'
//             formatter(tooltip) {
//                 if (formato === 'moneda') {
//                     return `${this.point.name}: $${Highcharts.numberFormat(this.point.y, 2, '.', ',')}`
//                 } else if (formato === 'entero') {
//                     return `${this.point.name}: ${Highcharts.numberFormat(this.point.y, 0, '.', ',')}`
//                 } else if (formato === 'porcentaje') {
//                     return `${this.point.name}: ${Highcharts.numberFormat(this.point.y * 100, 2, '.', ',')}%`
//                 }
//             }
//         },
//         series: series_outer,
//         drilldown: {
//             series: drilldown_series,
//             activeAxisLabelStyle: {
//                 textDecoration: 'none',
//                 color: colorTexto
//             },
//             activeDataLabelStyle: {
//                 textDecoration: 'none',
//                 color: colorTexto
//             },
//             credits: {
//             enabled: false
//             }
//         },
//         credits: {
//             enabled: false
//         }
//     }

//     return (
//         <Card>
//             <CardBody>
//                 {hayError && <p classname='texto-rojo'>{`Error en la carga del componente "${titulo}" el ${fechas_srv.fechaYHoraActual()}`}</p>}
//                 {!hayError && estadoLoader.contador === 0 && <HighchartsReact
//                     highcharts={Highcharts}
//                     options={options}
//                 />}
//                 {!hayError && estadoLoader.contador !== 0 && <LoadingGif />}
//             </CardBody>
//         </Card>
//     )
// }

// export default ColumnasApiladasDrilldown