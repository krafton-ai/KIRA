import DefaultTheme from 'vitepress/theme'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app, router }) {
    // Track download button clicks
    if (typeof window !== 'undefined') {
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupTracking)
      } else {
        setupTracking()
      }

      // Also track on route changes (SPA navigation)
      router.onAfterRouteChanged = () => {
        setTimeout(setupTracking, 100)
      }
    }
  }
}

function setupTracking() {
  // Find all download links (dmg files)
  document.querySelectorAll('a[href*=".dmg"]').forEach(link => {
    // Avoid adding multiple listeners
    if (link.dataset.gaTracked) return
    link.dataset.gaTracked = 'true'

    link.addEventListener('click', () => {
      if (typeof gtag === 'function') {
        gtag('event', 'download', {
          event_category: 'engagement',
          event_label: link.href,
          value: 1
        })
      }
    })
  })
}
