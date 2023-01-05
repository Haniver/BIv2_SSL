class ErrorHandling {

  myErrorHandler = (error, info) => {
    // Do something with the error
    // E.g. log to an error logging client here
    console.log(`Error: ${error}. Info:`)
    console.log(info)
  }

  ErrorFallback = ({error, resetErrorBoundary}) => {
    return (
      <>
        <p>Something went wrong:</p>
        <pre>{error.message}</pre>
        <button onClick={resetErrorBoundary}>Try again</button>
      </>
    )
  }

}

export default new ErrorHandling()
// Pon esto en el componente cuyos hijos pueden fallar:
// <ErrorBoundary FallbackComponent={ErrorFallback} onError={myErrorHandler} >
// <Leyenda seccion={seccion} titulo='Última actualización:' />
// </ErrorBoundary>