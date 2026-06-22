/**
 * TrendingSection Component
 * 
 * Displays trending searches as clickable chips.
 * Fetches trending data on mount.
 */

import React, { useState, useEffect } from 'react';
import { getTrendingSearches } from '../api/client';

export function TrendingSection({ onTrendingClick }) {
  const [trending, setTrending] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchTrending() {
      try {
        setIsLoading(true);
        const data = await getTrendingSearches();
        setTrending(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load trending searches:', err);
        setError('Failed to load trending searches');
      } finally {
        setIsLoading(false);
      }
    }

    fetchTrending();
  }, []);

  if (isLoading) {
    return (
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">
          🔥 Trending Searches
        </h2>
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-8 w-32 bg-gray-200 rounded-full animate-pulse"
            ></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">
          🔥 Trending Searches
        </h2>
        <p className="text-sm text-gray-500">{error}</p>
      </div>
    );
  }

  if (trending.length === 0) {
    return null;
  }

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center">
        <span className="mr-2">🔥</span>
        Trending Searches
      </h2>
      <div className="flex flex-wrap gap-2">
        {trending.map((item, index) => (
          <button
            key={index}
            onClick={() => onTrendingClick(item.query)}
            className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 
                       rounded-full text-sm font-medium text-gray-700 hover:bg-blue-50 
                       hover:border-blue-300 hover:text-blue-700 transition-all duration-200
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <span className="truncate max-w-xs">{item.query}</span>
            <span className="ml-2 text-xs text-gray-500">
              {Math.round(item.score)}
            </span>
          </button>
        ))}
      </div>
      <p className="mt-3 text-xs text-gray-500">
        Click any trending search to explore
      </p>
    </div>
  );
}
