import { Card, CardBody } from 'reactstrap'
import { useEffect } from 'react'

const BuggyComponent = () => {

  useEffect(() => {
    throw new Error('This is an error')
  }, [])

  return (
    <Card className='text-center'>
      <CardBody>
        <p>This shouldn't show</p>
      </CardBody>
    </Card>
  )
}

export default BuggyComponent