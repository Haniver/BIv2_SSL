// ** React Imports
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

// ** Custom Components
import Avatar from '@components/avatar'

// ** Utils
// import { isUserLoggedIn } from '@utils'

// ** Store & Actions
import { useDispatch } from 'react-redux'
// import { handleLogout } from '@store/actions/auth'

// ** Third Party Components
import { UncontrolledDropdown, DropdownMenu, DropdownToggle, DropdownItem } from 'reactstrap'
import { User, Mail, CheckSquare, MessageSquare, Settings, CreditCard, HelpCircle, Power } from 'react-feather'

// ** Default Avatar Image
import defaultAvatar from '@src/assets/images/portrait/small/avatar-s-11.jpg'
// Importar Auth Service para manejar el logout
import AuthService from "@src/services/auth.service"

const UserDropdown = () => {
  // ** Store Vars
  const dispatch = useDispatch()

  // ** State
  const [userData, setUserData] = useState(null)

  //** ComponentDidMount
  useEffect(() => {
    if (AuthService.isUserLoggedIn() !== null) {
      setUserData(JSON.parse(localStorage.getItem('userData')))
    }
    // console.log("La data de usuario es:")
    // console.log(localStorage.getItem('userData'))
  }, [])

  // Un handleLogout que yo le puse para que no use la autenticación de la plantilla
  const handleLogout = () => {
    // console.log("Se llamó al handleLogout de @src/@core/layouts/components/navbar/UserDropdown.js como debe ser, nada más que esta función todavía no hace nada.")
    AuthService.logout()
  }

  //** Vars
  const userAvatar = (userData && userData.avatar) || defaultAvatar

  return (
    <UncontrolledDropdown tag='li' className='dropdown-user nav-item'>
      <DropdownToggle href='/' tag='a' className='nav-link dropdown-user-link' onClick={e => e.preventDefault()}>
        <div className='user-nav d-sm-flex d-none'>
          <span className='user-name font-weight-bold'>{(userData && userData['nombre']) || 'Nombre no encontrado'}</span>
          <span className='user-status'>{(userData && userData.rol) || 'Rol no encontrado'}</span>
        </div>
        {/* <Avatar img={userAvatar} imgHeight='40' imgWidth='40' status='online' /> */}
      </DropdownToggle>
      <DropdownMenu right>
        {/* <DropdownItem tag={Link} to='/perfil' onClick={e => e.preventDefault()}> */}
        <DropdownItem tag={Link} to='/perfil'>
          <User size={14} className='mr-75' />
          <span className='align-middle'>Perfil</span>
        </DropdownItem>
        {/* <DropdownItem tag={Link} to='#' onClick={e => e.preventDefault()}>
          <Mail size={14} className='mr-75' />
          <span className='align-middle'>Inbox</span>
        </DropdownItem> */}
        {/* <DropdownItem tag={Link} to='#' onClick={e => e.preventDefault()}>
          <CheckSquare size={14} className='mr-75' />
          <span className='align-middle'>Tasks</span>
        </DropdownItem> */}
        {/* <DropdownItem tag={Link} to='#' onClick={e => e.preventDefault()}>
          <MessageSquare size={14} className='mr-75' />
          <span className='align-middle'>Chats</span>
        </DropdownItem> */}
        <DropdownItem tag={Link} to='/login' onClick={() => handleLogout()}>
          <Power size={14} className='mr-75' />
          <span className='align-middle'>Cerrar Sesión</span>
        </DropdownItem>
      </DropdownMenu>
    </UncontrolledDropdown>
  )
}

export default UserDropdown
