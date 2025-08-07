import React from 'react';

/**
 * Highlights search matches in text
 * @param text The text to search in
 * @param searchQuery The search query to highlight
 * @returns React elements with highlighted matches
 */
export function highlightSearchMatches(
  text: string,
  searchQuery: string
): React.ReactNode {
  if (!searchQuery || !text) {
    return text;
  }

  const regex = new RegExp(`(${escapeRegExp(searchQuery)})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (part.toLowerCase() === searchQuery.toLowerCase()) {
      return (
        <mark
          key={index}
          className="bg-yellow-300 dark:bg-yellow-600 text-inherit rounded-sm px-0.5"
        >
          {part}
        </mark>
      );
    }
    return part;
  });
}

/**
 * Escapes special regex characters in a string
 */
function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
