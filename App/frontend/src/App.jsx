import { useState, useEffect, useCallback } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const PRICE_RANGES = [
  { value: 1, label: '₹ Budget (1)' },
  { value: 2, label: '₹₹ Moderate (2)' },
  { value: 3, label: '₹₹₹ Upscale (3)' },
  { value: 4, label: '₹₹₹₹ Premium (4)' },
]

const RATINGS = [
  { value: 0, label: 'Any' },
  { value: 3.0, label: '3.0+' },
  { value: 3.5, label: '3.5+' },
  { value: 4.0, label: '4.0+' },
  { value: 4.5, label: '4.5+' },
]

const CUISINES = [
  'Italian', 'Indian', 'Chinese', 'Japanese', 'Mexican', 'Thai',
  'American', 'Cafe', 'Fast Food', 'Seafood', 'North Indian',
  'South Indian', 'Continental', 'Bakery', 'Desserts',
]

function App() {
  const [theme, setTheme] = useState(() =>
    localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  )
  const [place, setPlace] = useState('Pune')
  const [priceRange, setPriceRange] = useState(2)
  const [minRating, setMinRating] = useState(4.0)
  const [cuisines, setCuisines] = useState(['Italian', 'Cafe'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [apiBaseUrl, setApiBaseUrl] = useState(
    () => localStorage.getItem('apiBaseUrl') || API_BASE
  )

  useEffect(() => {
    localStorage.setItem('apiBaseUrl', apiBaseUrl)
  }, [apiBaseUrl])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'))
  }, [])

  const toggleCuisine = (c) => {
    setCuisines((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    )
  }

  const getRecommendation = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const base = apiBaseUrl.startsWith('http') ? apiBaseUrl : `${window.location.origin}${apiBaseUrl}`
      const url = `${base.replace(/\/$/, '')}/recommend`
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          place: place.trim(),
          price_range: priceRange,
          min_rating: minRating,
          cuisines,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      setResult(data)
    } catch (e) {
      setError(e.message || 'Failed to get recommendation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1 className="title">AI Restaurant Recommendation</h1>
        <div className="header-actions">
          <button
            type="button"
            className="icon-btn"
            onClick={() => setShowSettings(true)}
            title="Settings"
            aria-label="Settings"
          >
            ⚙️
          </button>
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            aria-label="Toggle theme"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>

      <main className="main">
        <div className="card form-card">
          <h2 className="card-title">Your preferences</h2>

          <div className="field">
            <label htmlFor="place">City / Place</label>
            <input
              id="place"
              type="text"
              value={place}
              onChange={(e) => setPlace(e.target.value)}
              placeholder="e.g. Pune, Mumbai"
            />
          </div>

          <div className="field">
            <label>Price range (₹)</label>
            <select
              value={priceRange}
              onChange={(e) => setPriceRange(Number(e.target.value))}
              aria-label="Price range"
            >
              {PRICE_RANGES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Minimum rating</label>
            <select
              value={minRating}
              onChange={(e) => setMinRating(Number(e.target.value))}
              aria-label="Minimum rating"
            >
              {RATINGS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Cuisines (multi-select)</label>
            <div className="cuisine-chips">
              {CUISINES.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`chip ${cuisines.includes(c) ? 'active' : ''}`}
                  onClick={() => toggleCuisine(c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            className="submit-btn"
            onClick={getRecommendation}
            disabled={loading}
          >
            {loading ? 'Finding...' : 'Get recommendation'}
          </button>
        </div>

        {error && (
          <div className="card error-card">
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="card result-card">
            <h2 className="card-title">Top recommendation</h2>
            <div className="recommendation">
              <h3 className="restaurant-name">{result.recommended_restaurant?.name || '—'}</h3>
              <p><strong>Location:</strong> {result.recommended_restaurant?.location || '—'}</p>
              <p><strong>Price:</strong> {result.recommended_restaurant?.price ?? '—'} / 4</p>
              <p><strong>Rating:</strong> {result.recommended_restaurant?.rating ?? '—'}</p>
              <p><strong>Cuisine:</strong> {result.recommended_restaurant?.cuisine || '—'}</p>
            </div>

            <h3 className="section-title">Rationale</h3>
            <p className="rationale">{result.rationale || '—'}</p>

            <h3 className="section-title">Alternatives</h3>
            {result.alternatives?.length ? (
              <ul className="alternatives">
                {result.alternatives.map((alt, i) => (
                  <li key={i} className="alt-item">
                    <strong>{alt.name}</strong> — {alt.location} • ₹{alt.price}/4 • {alt.rating} • {alt.cuisine}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No alternatives available.</p>
            )}
          </div>
        )}
      </main>

      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>API Settings</h2>
            <div className="field">
              <label>Backend base URL</label>
              <input
                type="text"
                value={apiBaseUrl}
                onChange={(e) => setApiBaseUrl(e.target.value)}
                placeholder="/api or http://localhost:8000"
              />
            </div>
            <p className="hint">Use /api for same-origin proxy, or full URL for CORS.</p>
            <button type="button" className="submit-btn" onClick={() => setShowSettings(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
