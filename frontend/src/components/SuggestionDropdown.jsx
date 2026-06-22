/**
 * SuggestionDropdown Component
 * 
 * Displays search suggestions with keyboard navigation.
 * Shows loading state, empty state, and handles clicks.
 */

import React from 'react';

export function SuggestionDropdown({
  suggestions,
  isVisible,
  selectedIndex,
  onSelect,
  isLoading,
  hasSearched,
}) {
  if (!isVisible) {
    return null;
  }

  return (
    <div className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto">
      {/* Loading state */}
      {isLoading && (
        <div className="px-4 py-8 text-center text-gray-500">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2"></div>
          <p className="text-sm">Loading suggestions...</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && hasSearched && suggestions.length === 0 && (
        <div className="px-4 py-8 text-center text-gray-500">
          <svg
            className="w-12 h-12 mx-auto mb-2 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm">No results found</p>
          <p className="text-xs text-gray-400 mt-1">Try a different search term</p>
        </div>
      )}

      {/* Suggestions list */}
      {!isLoading && suggestions.length > 0 && (
        <ul className="py-2">
          {suggestions.map((suggestion, index) => (
            <li key={index}>
              <button
                onClick={() => onSelect(suggestion.query)}
                className={`w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors duration-150
                  ${index === selectedIndex ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
                  ${index !== suggestions.length - 1 ? 'border-b border-gray-100' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {suggestion.query}
                    </p>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                      {Math.round(suggestion.score)}
                    </span>
                  </div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Footer hint */}
      {!isLoading && suggestions.length > 0 && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 flex items-center justify-between">
          <span>Use ↑↓ to navigate</span>
          <span>Press Enter to search</span>
        </div>
      )}
    </div>
  );
}
