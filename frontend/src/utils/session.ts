/**
 * Get a display-friendly title for a session
 * @param session Session object
 * @returns Display title for the session
 */
export function getSessionTitle(session: {
  summary?: string | null;
  session_id: string;
}): string {
  if (session.summary) {
    return session.summary;
  }

  // Fallback to session ID prefix if no summary
  return `Session ${session.session_id.slice(0, 8)}...`;
}

/**
 * Get a shortened version of the session title for constrained spaces
 * @param session Session object
 * @param maxLength Maximum length for the title
 * @returns Shortened title
 */
export function getShortSessionTitle(
  session: { summary?: string | null; session_id: string },
  maxLength: number = 50
): string {
  const title = getSessionTitle(session);

  if (title.length <= maxLength) {
    return title;
  }

  return title.slice(0, maxLength - 3) + '...';
}
