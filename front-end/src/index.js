// ** React Imports
import { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom'

// ** Redux Imports
import { Provider } from 'react-redux'
import { store } from './redux/storeConfig/store'

// ** Toast & ThemeColors Context
import { ToastContainer } from 'react-toastify'
import { ThemeContext } from './utility/context/ThemeColors'

// ** Spinner (Splash Screen)
import Spinner from './@core/components/spinner/Fallback-spinner'

// ** Ripple Button
import './@core/components/ripple-button'

// ** PrismJS
import 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-jsx.min'

// ** React Perfect Scrollbar
import 'react-perfect-scrollbar/dist/css/styles.css'

// ** React Toastify
import '@styles/react/libs/toastify/toastify.scss'

// ** Core styles
import './@core/assets/fonts/feather/iconfont.css'
import './@core/scss/core.scss'
import './assets/scss/style.scss'

// ** Service Worker
import * as serviceWorker from './serviceWorker'

// Interceptores de Axios
import axios from "axios"
import AuthService from "@src/services/auth.service"

// Google Analytics
import ReactGA from 'react-ga'

axios.interceptors.request.use(function (config) {
    // Do something before request is sent
    // console.log("El interceptor de Axios dice que vas a mandar: ")
    // console.log(config)
    return config
  })
  
  axios.interceptors.response.use(function (response) {
    // console.log('La API regresó:')
    // console.log(response)
    return response
  }, function (error) {
    // console.log("ERROR DE AXIOS")
    if (401 === error.response.status) {
      console.log("JWT INVALIDO")
      AuthService.logout()
    } else {
      console.log("Se dio otro error en la llamada a la API")
      return Promise.reject(error)
    }
  })

// ** Lazy load app
const LazyApp = lazy(() => import('./App'))

// Inicializar Google Analytics
ReactGA.initialize('G-QFSBHP9D9F')

ReactDOM.render(
  <Provider store={store}>
    <Suspense fallback={<Spinner />}>
      <ThemeContext>
        <LazyApp />
        <ToastContainer newestOnTop />
      </ThemeContext>
    </Suspense>
  </Provider>,
  document.getElementById('root')
)

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()
