'use client'

import { useState } from 'react'
import StockDashboard from '@/components/StockDashboard'
import ChatInterface from '@/components/ChatInterface'
import NewsWidget from '@/components/NewsWidget'

export default function Home() {
  const [selectedStock, setSelectedStock] = useState<string | null>(null)

  return (
    <div className="min-h-full">
      <main className="py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Stock Dashboard */}
            <div className="lg:col-span-2">
              <StockDashboard
                onSelectStock={(symbol) => setSelectedStock(symbol)}
                selectedStock={selectedStock}
              />
            </div>

            {/* News Widget */}
            <div className="lg:col-span-1">
              <NewsWidget stockSymbol={selectedStock} />
            </div>

            {/* Chat Interface */}
            <div className="lg:col-span-3">
              <ChatInterface selectedStock={selectedStock} />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
