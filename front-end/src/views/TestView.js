import { Fragment } from 'react'
import { Row, Col } from 'reactstrap'
import BuggyComponent from '../componentes/auxiliares/BuggyComponent'
import {ErrorBoundary} from 'react-error-boundary'
import ErrorHandling from '../componentes/auxiliares/ErrorHandling'

const TestView = () => {
  return (
    <Fragment>
      <Row className='match-height'>
        <Col sm='12'>
          <ErrorBoundary 
            FallbackComponent={ErrorHandling.ErrorFallback} 
            // onError={ErrorHandling.myErrorHandler} 
            // onReset={() => {
            //   // reset the state of the app
            // }}
          >
            <BuggyComponent />
          </ErrorBoundary>
        </Col>
      </Row>
    </Fragment>
  )
}
export default TestView
