/**
 * API client for backend communication.
 * Wraps fetch with error handling and base URL management.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch suggestions for a given prefix.
 * 
 * @param {string} prefix - Search prefix
 * @returns {Promise<Array>} Array of suggestion objects with query and score
 */
export async function getSuggestions(prefix) {
  if (!prefix || prefix.trim() === '') {
    return [];
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/suggest?q=${encodeURIComponent(prefix)}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch suggestions:', error);
    throw error;
  }
}

/**
 * Submit a search query.
 * 
 * @param {string} query - Search query to submit
 * @returns {Promise<Object>} Response object with message
 */
export async function submitSearch(query) {
  if (!query || query.trim() === '') {
    throw new Error('Query cannot be empty');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to submit search:', error);
    throw error;
  }
}

/**
 * Fetch trending searches.
 * Uses an empty prefix to get top trending queries.
 * 
 * @returns {Promise<Array>} Array of trending queries
 */
export async function getTrendingSearches() {
  try {
    // Get top queries starting with common letters
    const response = await fetch(`${API_BASE_URL}/suggest?q=`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    // Return top 5 for trending section
    return data.slice(0, 5);
  } catch (error) {
    console.error('Failed to fetch trending searches:', error);
    return [];
  }
}
