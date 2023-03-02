import React, { Component } from 'react'
import Router from './router/Router'
import ReactGA from 'react-ga'

class App extends Component {
  componentDidMount() {
    ReactGA.initialize('G-QFSBHP9D9F')
    ReactGA.pageview(window.location.pathname + window.location.search)
  }

  render() {
    return (
      <Router />
    )
  }
}

export default App