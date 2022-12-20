import { Card, CardBody } from 'reactstrap'
import lupita from '../../assets/images/lupita.png'

const Lupita = () => {
    // let size = '200px'
    // if (mini) {
    //     size = '25px'
    // }
    return (
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0, margin: 0}}>
            {/* <img src={preloaderImg} style={{height: size, width: size}} /> */}
            <img src={lupita} />
        </div>
    )
}

export default Lupita