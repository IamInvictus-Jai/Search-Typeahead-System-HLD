/**
 * SearchBox Component
 * 
 * Main search input with keyboard navigation support.
 * Handles user input and triggers suggestion fetching.
 */

import React from 'react';

export function SearchBox({
  value,
  onChange,
  onSubmit,
  onKeyDown,
  placeholder = 'Search for products...',
  isLoading = false,
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg 
                     focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200
                     transition-all duration-200"
          autoComplete="off"
          autoFocus
        />
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}
        
        {/* Search icon */}
        {!isLoading && (
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        )}
      </div>
    </form>
  );
}
