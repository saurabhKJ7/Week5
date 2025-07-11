import { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
} from 'chart.js'
import useSWR from 'swr'
import axios from 'axios'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface StockDashboardProps {
  onSelectStock: (symbol: string) => void
  selectedStock: string | null
}

interface StockData {
  symbol: string
  price: number
  day_change: number
  volume: number
}

const DEFAULT_STOCKS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']

const fetcher = (url: string) => axios.get(url).then(res => res.data)

export default function StockDashboard({ onSelectStock, selectedStock }: StockDashboardProps) {
  const [historicalData, setHistoricalData] = useState<ChartData<'line'> | null>(null)

  // Fetch real-time stock data
  const { data: stocksData, error } = useSWR<StockData[]>(
    `/api/v1/stocks/live?symbols=${DEFAULT_STOCKS.join(',')}`,
    fetcher,
    { refreshInterval: 5000 } // Refresh every 5 seconds
  )

  // Fetch historical data for selected stock
  useEffect(() => {
    if (selectedStock) {
      axios.get(`/api/v1/stocks/history/${selectedStock}`)
        .then(response => {
          const data = response.data
          setHistoricalData({
            labels: data.map((d: any) => new Date(d.timestamp).toLocaleDateString()),
            datasets: [
              {
                label: selectedStock,
                data: data.map((d: any) => d.price),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
              }
            ]
          })
        })
        .catch(console.error)
    }
  }, [selectedStock])

  if (error) return <div>Failed to load stock data</div>
  if (!stocksData) return <div>Loading...</div>

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Stock Dashboard</h2>
      
      {/* Stock Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {stocksData.map((stock) => (
          <button
            key={stock.symbol}
            onClick={() => onSelectStock(stock.symbol)}
            className={`p-4 rounded-lg border transition-colors ${
              selectedStock === stock.symbol
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-indigo-300'
            }`}
          >
            <div className="flex justify-between items-center">
              <span className="font-semibold">{stock.symbol}</span>
              <span className={`text-sm ${
                stock.day_change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {stock.day_change >= 0 ? '↑' : '↓'} {Math.abs(stock.day_change)}%
              </span>
            </div>
            <div className="mt-2 text-2xl font-bold">${stock.price.toFixed(2)}</div>
            <div className="mt-1 text-sm text-gray-500">
              Vol: {(stock.volume / 1000000).toFixed(1)}M
            </div>
          </button>
        ))}
      </div>

      {/* Historical Chart */}
      {selectedStock && historicalData && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">
            {selectedStock} Price History
          </h3>
          <div className="h-80">
            <Line
              data={historicalData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top' as const,
                  },
                  title: {
                    display: true,
                    text: '7-Day Price History'
                  }
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
} 