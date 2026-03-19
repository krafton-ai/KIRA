import { defineConfig } from 'vitepress'

const siteUrl = 'https://kira.krafton-ai.com'

export default defineConfig({
  title: 'KiraClaw Documentation',
  description: 'KiraClaw is an agentic desktop runtime with local chat, channels, skills, schedules, and run logs.',
  ignoreDeadLinks: true,
  sitemap: {
    hostname: siteUrl,
    lastmodDateOnly: false
  },
  head: [
    ['script', { async: '', src: 'https://www.googletagmanager.com/gtag/js?id=G-05X6YL37F9' }],
    ['script', {}, `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-05X6YL37F9');`],
    ['link', { rel: 'icon', type: 'image/x-icon', href: '/images/favicon.ico' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '16x16', href: '/images/favicon-16x16.png' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/images/favicon-32x32.png' }],
    ['link', { rel: 'apple-touch-icon', sizes: '180x180', href: '/images/apple-touch-icon.png' }],
    ['meta', { name: 'theme-color', content: '#f9423a' }],
    ['meta', { name: 'author', content: 'KRAFTON AI' }],
    ['meta', { name: 'robots', content: 'index, follow' }],
    ['meta', { name: 'keywords', content: 'KiraClaw, AI agent, desktop runtime, Slack, Telegram, local AI, KRIM, KRAFTON AI' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'KiraClaw Documentation' }],
    ['meta', { property: 'og:url', content: siteUrl }],
    ['meta', { property: 'og:title', content: 'KiraClaw Documentation' }],
    ['meta', { property: 'og:description', content: 'Install KiraClaw and run a local agentic desktop runtime with chat, channels, skills, schedules, and logs.' }],
    ['meta', { property: 'og:image', content: `${siteUrl}/images/android-chrome-512x512.png` }],
    ['meta', { property: 'og:locale', content: 'en_US' }],
    ['meta', { property: 'og:locale:alternate', content: 'ko_KR' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:title', content: 'KiraClaw Documentation' }],
    ['meta', { name: 'twitter:description', content: 'Install KiraClaw and run a local agentic desktop runtime.' }],
    ['meta', { name: 'twitter:image', content: `${siteUrl}/images/android-chrome-512x512.png` }],
    ['link', { rel: 'canonical', href: siteUrl }]
  ],
  locales: {
    root: {
      label: 'English',
      lang: 'en',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/' },
          { text: 'Getting Started', link: '/getting-started' },
          { text: 'Troubleshooting', link: '/troubleshooting' },
          { text: 'GitHub', link: 'https://github.com/krafton-ai/KIRA/tree/main/KiraClaw' }
        ],
        outline: {
          label: 'On this page',
          level: [2, 3]
        },
        docFooter: {
          prev: 'Previous',
          next: 'Next'
        },
        darkModeSwitchLabel: 'Theme',
        sidebarMenuLabel: 'Menu',
        returnToTopLabel: 'Back to top',
        langMenuLabel: 'Change language'
      }
    },
    ko: {
      label: '한국어',
      lang: 'ko-KR',
      link: '/ko/',
      themeConfig: {
        nav: [
          { text: '홈', link: '/ko/' },
          { text: '시작하기', link: '/ko/getting-started' },
          { text: '문제 해결', link: '/ko/troubleshooting' },
          { text: 'GitHub', link: 'https://github.com/krafton-ai/KIRA/tree/main/KiraClaw' }
        ],
        outline: {
          label: '목차',
          level: [2, 3]
        },
        docFooter: {
          prev: '이전',
          next: '다음'
        },
        darkModeSwitchLabel: '테마',
        sidebarMenuLabel: '메뉴',
        returnToTopLabel: '맨 위로',
        langMenuLabel: '언어 변경'
      }
    }
  },
  themeConfig: {
    logo: {
      light: '/images/kira-icon-light.png',
      dark: '/images/kira-icon-dark.png'
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/krafton-ai/KIRA/tree/main/KiraClaw' }
    ],
    search: {
      provider: 'local'
    }
  }
})
