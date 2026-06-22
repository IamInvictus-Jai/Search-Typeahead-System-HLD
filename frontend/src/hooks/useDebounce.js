/**
 * Custom hook for debouncing values.
 * Prevents excessive API calls during rapid user input.
 * 
 * @param {any} value - Value to debounce
 * @param {number} delay - Delay in milliseconds (default: 300ms)
 * @returns {any} Debounced value
 */

import { useState, useEffect } from 'react';

export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Set up a timer to update the debounced value after delay
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timer if value changes before delay completes
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
