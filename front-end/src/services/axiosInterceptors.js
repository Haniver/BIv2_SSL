import axios from "axios"

axios.interceptors.request.use(function (config) {
    // Do something before request is sent
    console.log("El interceptor de Axios dice que vas a mandar: ")
    console.log(config)
    return config
  })
  
  axios.interceptors.response.use(function (response) {
    console.log('La API regresó:')
    console.log(response)
    return response
  }, function (error) {
    console.log("ERROR DE AXIOS")
    if (401 === error.response.status) {
      console.log("JWT INVALIDO")
      const authService = new AuthService()
      authService.logout()
    } else {
      console.log("Se dio otro error en la llamada a la API")
      return Promise.reject(error)
    }
  })
  
  