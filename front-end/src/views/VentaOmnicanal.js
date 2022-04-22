import VentaOmnicanalTab1 from "./VentaOmnicanalTab1"
import VentaOmnicanalTab2 from "./VentaOmnicanalTab2"
import { Fragment, useState, useEffect } from 'react'
import { ThumbsUp, Truck } from 'react-feather'
import { TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap'
import { useSkin } from '@hooks/useSkin'


const VentaOmnicanal = () => {
  const [active, setActive] = useState('1')

  const [skin, setSkin] = useSkin()

  // useEffect(() => {
  //   console.log(`Nueva skin desde VentaOmnicanal: ${skin}`)
  // }, [skin])

  const toggle = tab => {
    if (active !== tab) {
      setActive(tab)
    }
  }
  return (
    <Fragment>
      <Nav tabs>
        <NavItem>
          <NavLink
            active={active === '1'}
            onClick={() => {
              toggle('1')
            }}
          >
            <ThumbsUp size={14} />
            <span className='align-middle'>Ventas Marketing</span>
          </NavLink>
        </NavItem>
        <NavItem>
          <NavLink
            active={active === '2'}
            onClick={() => {
              toggle('2')
            }}
          >
            <Truck size={14} />
            <span className='align-middle'>Proveedores</span>
          </NavLink>
        </NavItem>
      </Nav>
      <TabContent className='py-50' activeTab={active}>
        <TabPane tabId='1'>
          <VentaOmnicanalTab1 />
        </TabPane>
        <TabPane tabId='2'>
          <VentaOmnicanalTab2 />
        </TabPane>
      </TabContent>
    </Fragment>
  )
}

export default VentaOmnicanal