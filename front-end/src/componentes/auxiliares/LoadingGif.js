import { Card, CardBody, CardTitle } from 'reactstrap'
import preloaderImg from '../../assets/images/hug.gif'

const LoadingGif = (mini = false) => {
    let size = '200px'
    if (mini) {
        size = '25px'
    }
    return (
        <Card>
            <CardBody>
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <img src={preloaderImg} style={{height: size, width: size}} />
                </div>
            </CardBody>
        </Card>
    )
}

export default LoadingGif