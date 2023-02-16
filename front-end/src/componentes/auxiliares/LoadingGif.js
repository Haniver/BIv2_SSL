import { Card, CardBody, CardTitle } from 'reactstrap'
import preloaderImg from '../../assets/images/hug.gif'

const LoadingGif = (mini = false, filtro = false) => {
    if (mini) {
        return (
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <img src={preloaderImg} style={{height: 25, width: 25}} />
            </div>
        )    
    } else {
        return (
            <Card>
                <CardBody>
                    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                        <img src={preloaderImg} style={{height: 250, width: 250}} />
                    </div>
                </CardBody>
            </Card>
        )    
    }
}

export default LoadingGif