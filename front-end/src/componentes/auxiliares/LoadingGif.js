import { Card, CardBody } from 'reactstrap'
import preloaderImg from '../../assets/images/hug.gif'

const LoadingGif = () => {
    return (
        <Card>
            <CardBody>
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <img src={preloaderImg} style={{height: '200px', width: '200px'}} />
                </div>
            </CardBody>
        </Card>
    )
}

export default LoadingGif