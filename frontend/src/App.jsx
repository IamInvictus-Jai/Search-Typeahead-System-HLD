/**
 * Main App Component
 * 
 * Orchestrates the search typeahead interface with:
 * - Debounced search input
 * - Real-time suggestions dropdown
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - Trending searches section
 * - Search submission with feedback
 */

import React, { useState, useEffect, useRef } from 'react';
import { SearchBox } from './components/SearchBox';
import { SuggestionDropdown } from './components/SuggestionDropdown';
import { TrendingSection } from './components/TrendingSection';
import { useDebounce } from './hooks/useDebounce';
import { getSuggestions, submitSearch } from './api/client';

function App() {
  // State management
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);

  // Debounce search query (300ms delay)
  const debouncedQuery = useDebounce(searchQuery, 300);

  // Ref for click outside detection
  const containerRef = useRef(null);

  // Fetch suggestions when debounced query changes
  useEffect(() => {
    async function fetchSuggestions() {
      if (!debouncedQuery.trim()) {
        setSuggestions([]);
        setShowDropdown(false);
        setHasSearched(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await getSuggestions(debouncedQuery);
        setSuggestions(data);
        setShowDropdown(true);
        setHasSearched(true);
        setSelectedIndex(-1);
      } catch (err) {
        console.error('Error fetching suggestions:', err);
        setError('Failed to load suggestions. Please try again.');
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchSuggestions();
  }, [debouncedQuery]);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showDropdown || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;

      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectSuggestion(suggestions[selectedIndex].query);
        } else if (searchQuery.trim()) {
          handleSubmitSearch(searchQuery);
        }
        break;

      case 'Escape':
        e.preventDefault();
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;

      default:
        break;
    }
  };

  // Handle suggestion selection
  const handleSelectSuggestion = async (query) => {
    setSearchQuery(query);
    setShowDropdown(false);
    setSelectedIndex(-1);
    await handleSubmitSearch(query);
  };

  // Handle search submission
  const handleSubmitSearch = async (query) => {
    if (!query || !query.trim()) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      await submitSearch(query);
      
      // Show success feedback
      setFeedback({
        type: 'success',
        message: `Searched for "${query}"`,
      });

      // Clear feedback after 3 seconds
      setTimeout(() => setFeedback(null), 3000);
    } catch (err) {
      console.error('Error submitting search:', err);
      setError('Failed to submit search. Please try again.');
      setFeedback({
        type: 'error',
        message: 'Failed to submit search',
      });
      setTimeout(() => setFeedback(null), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle trending chip click
  const handleTrendingClick = (query) => {
    setSearchQuery(query);
    setShowDropdown(false);
    handleSubmitSearch(query);
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShowDropdown(false);
        setSelectedIndex(-1);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Search Typeahead
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Real-time suggestions with distributed caching
              </p>
            </div>
            <div className="hidden md:flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                System Online
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          {/* Feedback Toast */}
          {feedback && (
            <div
              className={`mb-4 px-4 py-3 rounded-lg shadow-lg transition-all duration-300 ${
                feedback.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-800'
                  : 'bg-red-50 border border-red-200 text-red-800'
              }`}
            >
              <div className="flex items-center">
                {feedback.type === 'success' ? (
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                <span className="font-medium">{feedback.message}</span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && !feedback && (
            <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-800">
              <div className="flex items-center">
                <svg
                  className="w-5 h-5 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Search Box Container */}
          <div ref={containerRef} className="relative">
            <SearchBox
              value={searchQuery}
              onChange={setSearchQuery}
              onSubmit={() => handleSubmitSearch(searchQuery)}
              onKeyDown={handleKeyDown}
              isLoading={isLoading}
              placeholder="Search for products... (try 'iphone', 'wireless', 'laptop')"
            />

            {/* Suggestions Dropdown */}
            <SuggestionDropdown
              suggestions={suggestions}
              isVisible={showDropdown}
              selectedIndex={selectedIndex}
              onSelect={handleSelectSuggestion}
              isLoading={isLoading}
              hasSearched={hasSearched}
            />
          </div>

          {/* Trending Section */}
          <TrendingSection onTrendingClick={handleTrendingClick} />

          {/* Info Section */}
          <div className="mt-12 p-6 bg-white rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              ℹ️ How it works
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">•</span>
                <span>
                  <strong>Debounced Search:</strong> Suggestions appear 300ms after you stop typing
                </span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">•</span>
                <span>
                  <strong>Keyboard Navigation:</strong> Use ↑↓ arrow keys to navigate, Enter to select, Esc to close
                </span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">•</span>
                <span>
                  <strong>Trending Score:</strong> Shows recency-weighted popularity (higher = more popular + recent)
                </span>
              </li>
              <li className="flex items-start">
                <span className="font-medium text-blue-600 mr-2">•</span>
                <span>
                  <strong>Distributed Cache:</strong> Powered by consistent hashing across 3 Redis nodes
                </span>
              </li>
            </ul>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 py-6 border-t border-gray-200 bg-white">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600">
          <p>
            Search Typeahead System • Phase 7 Complete
          </p>
          <p className="mt-1 text-xs text-gray-500">
            Built with React, Tailwind CSS, FastAPI, PostgreSQL, and Redis
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
