import { lazy } from 'react'

// ** Document title
const TemplateTitle = '%s - BI Omnicanal'

// ** Default Route
const DefaultRoute = '/home'

// ** Merge Routes
const Routes = [
  {
    path: '/home',
    component: lazy(() => import('../../views/Home'))
  },
  {
    path: '/second-page',
    component: lazy(() => import('../../views/SecondPage'))
  },
  {
    path: '/login',
    component: lazy(() => import('../../views/Login')),
    layout: 'BlankLayout',
    meta: {
      authRoute: true
    }
  },
  {
    path: '/registro',
    component: lazy(() => import('../../views/Registro')),
    layout: 'BlankLayout',
    meta: {
      publicRoute: true
    }
  },
  {
    path: '/checarHash',
    component: lazy(() => import('../../views/checarHash')),
    meta: {
      publicRoute: true
      // menuCollapsed: false
    }
  },
  {
    path: '/perfil',
    component: lazy(() => import('../../views/Perfil')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/error',
    component: lazy(() => import('../../views/Error')),
    layout: 'BlankLayout',
    meta: {
      publicRoute: true
    }
  },
  {
    path: '/recuperar',
    component: lazy(() => import('../../views/Recuperar')),
    layout: 'BlankLayout',
    meta: {
      publicRoute: true
    }
  },
  {
    path: '/cambiarPassword/:token',
    component: lazy(() => import('../../views/CambiarPassword')),
    layout: 'BlankLayout',
    meta: {
      publicRoute: true
    }
  },
  {
    path: '/ventaOmnicanal',
    component: lazy(() => import('../../views/VentaOmnicanal')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/nivelesDeServicio',
    component: lazy(() => import('../../views/NivelesDeServicio')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/foundRate',
    component: lazy(() => import('../../views/FoundRate')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidosPendientes',
    component: lazy(() => import('../../views/PedidosPendientes')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/ventaSinImpuesto',
    component: lazy(() => import('../../views/VentaSinImpuesto')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/faltantes',
    component: lazy(() => import('../../views/Faltantes')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/onTimeInFull',
    component: lazy(() => import('../../views/OnTimeInFull')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidoPerfecto',
    component: lazy(() => import('../../views/PedidoPerfecto')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/tablaMapas',
    component: lazy(() => import('../../views/TablaMapas')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/reporteFaltantes',
    component: lazy(() => import('../../views/ReporteFaltantes')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidoTimeslot',
    component: lazy(() => import('../../views/PedidoTimeslot')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidoDiario',
    component: lazy(() => import('../../views/PedidoDiario')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/NPSDetalle',
    component: lazy(() => import('../../views/NPSDetalle')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidosDevolucion',
    component: lazy(() => import('../../views/PedidosDevolucion')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidosSKU',
    component: lazy(() => import('../../views/PedidosSKU')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/skuCornershopChedraui',
    component: lazy(() => import('../../views/SkuCornershopChedraui')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/foundRateCornershop',
    component: lazy(() => import('../../views/FoundRateCornershop')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/nps',
    component: lazy(() => import('../../views/Nps')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/comparativoVentaXCanal',
    component: lazy(() => import('../../views/ComparativoVentaXCanal')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/resultadoRFM',
    component: lazy(() => import('../../views/ResultadoRFM')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/altaUsuarios',
    component: lazy(() => import('../../views/AltaUsuarios')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/catalogoArticulos',
    component: lazy(() => import('../../views/CatalogoArticulos')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/pedidosPicker',
    component: lazy(() => import('../../views/PedidosPicker')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/documentos/:id',
    component: lazy(() => import('../../views/Documentos')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/temporada',
    component: lazy(() => import('../../views/Temporada')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/costoPorPedido',
    component: lazy(() => import('../../views/CostoPorPedido')),
    meta: {
      publicRoute: false
      // menuCollapsed: false
    }
  },
  {
    path: '/testView',
    component: lazy(() => import('../../views/TestView')),
    meta: {
      publicRoute: true
      // menuCollapsed: false
    }
  }
]

export { DefaultRoute, TemplateTitle, Routes }
