import Cookies from 'js-cookie'
import authService from './auth.service'

export default function authHeader() {
  // const user = JSON.parse(localStorage.getItem('user')); // No vas a usar esto porque no necesitas obtener toda la información del usuario del almacenamiento local para saber el token; ese lo sacas de las cookies

  let jwt = Cookies.get('tokenHeaderPayload') + Cookies.get('tokenSignature')
  if (jwt.length > 0) {
    jwt = jwt.slice(1, -1)
  } else {
    authService.logout
  }
  // if (user && user.accessToken) { // Lo mismo que arriba
  if (jwt) {
    return { Authorization: `Bearer ${jwt}` } // for Spring Boot back-end
  } else {
    return {}
  }
}
