import axios from "axios"
import Cookies from 'js-cookie'
import authHeader from '@src/services/auth.header'
import CustomUrls from './customUrls'

class AuthService {
  login(username, password) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    const urlencoded = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }
    // axios.post('/foo', params);
    return axios
      .post(`${CustomUrls.ApiUrl()}token`, params, urlencoded)
      .then(response => {
        // Aquí la API se supone que devuelve id, name, role and jwt token. Los posibles roles son: ROLE_ADMIN, ROLE_MODERATOR o ninguno de esos dos para usuario normal.
        let respuesta = response.data
        if (response.data.access_token) {
          // localStorage.setItem("user", JSON.stringify(response.data));
          const token = JSON.stringify(response.data.access_token)
          // const id_rol = JSON.stringify(response.data.id_rol)
          const punto1 = token.indexOf('.')
          const punto2 = token.indexOf('.', punto1 + 1)
          const headerPayload = token.substring(0, punto2)
          const signature = token.substring(punto2)
          // Para leerlo, usa Cookies.get('tokenHeaderPayload') + Cookies.get('tokenSignature')
          Cookies.set('tokenHeaderPayload', headerPayload)
          Cookies.set('tokenSignature', signature, { sameSite: 'strict' })
          respuesta = this.escribir_user_data()
        }

        // return response.data;
        return respuesta
      })
  }

  logout() {
    localStorage.removeItem("userData")
    Cookies.remove('tokenHeaderPayload')
    Cookies.remove('tokenSignature')
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  register(username, email, password) {
    return axios.post(`${CustomUrls.ApiUrl()}signup`, {
      username,
      email,
      password
    })
  }

  getCurrentUser() {
    return JSON.parse(localStorage.getItem('userData'))
  }

  isUserLoggedIn() {
    return localStorage.getItem('userData')
  }

  async escribir_user_data() {
    return axios
      .get(`${CustomUrls.ApiUrl()}users/me`, { headers: authHeader() })
      .then(response => {
        localStorage.setItem("userData", JSON.stringify(response.data))
        // console.log(response.data)
        return response.data
      })
  }
}

export default new AuthService()
