import { useEffect, useState } from 'react'
import useSWR from 'swr'
import axios from 'axios'

interface NewsWidgetProps {
  stockSymbol: string | null
}

interface NewsArticle {
  title: string
  description: string
  url: string
  source: string
  published_at: string
}

const fetcher = (url: string) => axios.get(url).then(res => res.data)

export default function NewsWidget({ stockSymbol }: NewsWidgetProps) {
  const [activeTab, setActiveTab] = useState<'trending' | 'stock'>('trending')

  // Switch to stock news when a stock is selected
  useEffect(() => {
    if (stockSymbol) {
      setActiveTab('stock')
    }
  }, [stockSymbol])

  // Fetch trending news
  const { data: trendingNews, error: trendingError } = useSWR<NewsArticle[]>(
    '/api/v1/news/trending',
    fetcher,
    { refreshInterval: 300000 } // Refresh every 5 minutes
  )

  // Fetch stock-specific news
  const { data: stockNews, error: stockError } = useSWR<NewsArticle[]>(
    stockSymbol ? `/api/v1/news/stock/${stockSymbol}` : null,
    fetcher,
    { refreshInterval: 300000 }
  )

  if (trendingError || stockError) return <div>Failed to load news</div>
  if (!trendingNews && !stockNews) return <div>Loading...</div>

  const displayNews = activeTab === 'trending' ? trendingNews : stockNews

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Tabs */}
      <div className="border-b">
        <div className="flex">
          <button
            onClick={() => setActiveTab('trending')}
            className={`flex-1 py-3 px-4 text-sm font-medium text-center ${
              activeTab === 'trending'
                ? 'border-b-2 border-indigo-500 text-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Trending
          </button>
          <button
            onClick={() => setActiveTab('stock')}
            disabled={!stockSymbol}
            className={`flex-1 py-3 px-4 text-sm font-medium text-center ${
              activeTab === 'stock'
                ? 'border-b-2 border-indigo-500 text-indigo-600'
                : 'text-gray-500 hover:text-gray-700 disabled:opacity-50'
            }`}
          >
            {stockSymbol || 'Stock News'}
          </button>
        </div>
      </div>

      {/* News List */}
      <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
        {displayNews?.map((article, index) => (
          <article key={index} className="p-4 hover:bg-gray-50">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <p className="text-sm font-semibold text-gray-900 line-clamp-2">
                {article.title}
              </p>
              <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                {article.description}
              </p>
              <div className="mt-2 flex items-center text-xs text-gray-500">
                <span>{article.source}</span>
                <span className="mx-1">•</span>
                <time dateTime={article.published_at}>
                  {new Date(article.published_at).toLocaleDateString()}
                </time>
              </div>
            </a>
          </article>
        ))}
      </div>
    </div>
  )
} 