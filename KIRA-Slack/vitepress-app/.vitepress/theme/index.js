import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import HomeDemo from './components/HomeDemo.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'home-features-before': () => h(HomeDemo)
    })
  },
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
  // Find all download links
  document.querySelectorAll('a[href*=".dmg"], a[href*=".zip"], a[href*=".exe"]').forEach(link => {
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
