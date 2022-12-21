// ** Icons Import
import { Heart } from 'react-feather'

const Footer = () => {
  return (
    <p className='clearfix mb-0'>
      <span className='float-md-left d-block d-md-inline-block mt-25'>
        Grupo Comercial Chedraui ® {new Date().getFullYear()}{' '}
        {/* <a href='https://1.envato.market/pixinvent_portfolio' target='_blank' rel='noopener noreferrer'>
          Pixinvent
        </a> */}
        <span className='d-none d-sm-inline-block'>, Todos los derechos reservados</span>
      </span>
      {/* <span className='float-md-right d-none d-md-block'>
        Hecho a 🖐 por el Departamento Omnicanal
      </span> */}
    </p>
  )
}

export default Footer
