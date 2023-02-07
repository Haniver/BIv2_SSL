import React, { useState, useEffect } from "react"
import Highcharts from "highcharts"
import HighchartsReact from "highcharts-react-official"

const options = {
  chart: {
    type: "column",
    events: {
      drilldown: null,
      drillup: null
    }
  },
  title: {
    text: "First-level chart"
  },
  xAxis: {
    categories: ["Fruit", "Vegetables", "Meat"]
  },
  yAxis: {
    title: {
      text: "Amount (kg)"
    }
  },
  plotOptions: {
    column: {
      stacking: "normal",
      dataLabels: {
        enabled: false
      },
      events: {
        click: (event) => {
          if (event.point.drilldown) {
            highcharts.chart.drilldown(event.point.drilldown)
          }
        }
      }
    }
  },
  series: [
    {
      name: "Apple",
      data: [10, 0, 0],
      color: "#ff0000",
      drilldown: "apple"
    },
    {
      name: "Banana",
      data: [0, 20, 0],
      color: "#00ff00",
      drilldown: "banana"
    },
    {
      name: "Carrot",
      data: [0, 0, 30],
      color: "#0000ff",
      drilldown: "carrot"
    }
  ],
  drilldown: {
    series: [
      {
        name: "Apple",
        id: "apple",
        data: [
          ["Red Apple", 5],
          ["Green Apple", 5]
        ],
        color: "#ff0000"
      },
      {
        name: "Banana",
        id: "banana",
        data: [
          ["Yellow Banana", 10],
          ["Green Banana", 10]
        ],
        color: "#00ff00"
      },
      {
        name: "Carrot",
        id: "carrot",
        data: [
          ["Orange Carrot", 15],
          ["Purple Carrot", 15]
        ],
        color: "#0000ff"
      }
    ]
  }
}

const TestView = () => {
  const [highcharts, setHighcharts] = useState(null)

  useEffect(() => {
    if (highcharts) {
      options.chart.events.drilldown = (e) => highcharts.setTitle({ text: e.point.name })
      options.chart.events.drillup = () => highcharts.setTitle({ text: "First-level chart" })
      options.plotOptions.column.events.click = (e) => {
        if (e.point.drilldown) {
          highcharts.chart.drilldown(e.point.drilldown)
        }
      }
    }
    console.log(JSON.stringify(cloneDeep(highcharts)))
  }, [highcharts])

  return (
    <HighchartsReact
      highcharts={Highcharts}
      options={options}
      ref={(chart) => setHighcharts(chart && chart.chart)}
    />
  )
}

export default TestView