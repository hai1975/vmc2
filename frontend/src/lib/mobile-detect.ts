/** Mobile browsers often cannot render PDF inside iframe (blob URL). */
export function isMobilePdfViewer(): boolean {
  if (typeof window === 'undefined') return false
  const narrow = window.matchMedia('(max-width: 720px)').matches
  const mobileUa = /Android|iPhone|iPad|iPod|Mobile|webOS|BlackBerry/i.test(navigator.userAgent)
  return narrow || mobileUa
}
