import { defineConfig } from 'vitepress'

const siteUrl = 'https://kira.krafton-ai.com'

export default defineConfig({
  title: 'KIRA Documentation',
  description: 'KIRA is an AI virtual coworker that works 24/7. Install a desktop app and start working with your own AI assistant. Integrates with Slack, Outlook, Confluence, Jira, and more.',
  ignoreDeadLinks: true,

  // Sitemap generation
  sitemap: {
    hostname: siteUrl,
    lastmodDateOnly: false
  },

  head: [
    // Google Analytics (GA4)
    ['script', { async: '', src: 'https://www.googletagmanager.com/gtag/js?id=G-05X6YL37F9' }],
    ['script', {}, `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-05X6YL37F9');`],

    // Favicon
    ['link', { rel: 'icon', type: 'image/x-icon', href: '/images/favicon.ico' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '16x16', href: '/images/favicon-16x16.png' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/images/favicon-32x32.png' }],
    ['link', { rel: 'apple-touch-icon', sizes: '180x180', href: '/images/apple-touch-icon.png' }],

    // Primary Meta Tags
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { name: 'author', content: 'KRAFTON AI' }],
    ['meta', { name: 'robots', content: 'index, follow' }],
    ['meta', { name: 'keywords', content: 'AI assistant, virtual coworker, Slack bot, AI agent, desktop app, productivity, automation, Claude, KRAFTON AI, KIRA' }],

    // Open Graph / Facebook
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'KIRA - AI Virtual Coworker' }],
    ['meta', { property: 'og:url', content: siteUrl }],
    ['meta', { property: 'og:title', content: 'KIRA - Your AI Virtual Coworker' }],
    ['meta', { property: 'og:description', content: 'Install a desktop app and work with your own AI virtual coworker. Works 24/7, integrates with Slack, Outlook, Confluence, and more.' }],
    ['meta', { property: 'og:image', content: `${siteUrl}/images/android-chrome-512x512.png` }],
    ['meta', { property: 'og:image:width', content: '1200' }],
    ['meta', { property: 'og:image:height', content: '630' }],
    ['meta', { property: 'og:locale', content: 'en_US' }],
    ['meta', { property: 'og:locale:alternate', content: 'ko_KR' }],

    // Twitter Card
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:title', content: 'KIRA - Your AI Virtual Coworker' }],
    ['meta', { name: 'twitter:description', content: 'Install a desktop app and work with your own AI virtual coworker. Works 24/7, integrates with Slack, Outlook, Confluence, and more.' }],
    ['meta', { name: 'twitter:image', content: `${siteUrl}/images/android-chrome-512x512.png` }],

    // Canonical
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
          { text: 'Setup Guide', link: '/setup/' },
          { text: 'Features', link: '/features/' },
          { text: 'Troubleshooting', link: '/troubleshooting' },
        ],
        sidebar: {
          '/setup/': [
            {
              text: 'MCP Setup',
              items: [
                { text: 'Perplexity Web Search', link: '/setup/perplexity' },
                { text: 'DeepL (Document Translation)', link: '/setup/deepl' },
                { text: 'GitHub', link: '/setup/github' },
                { text: 'GitLab', link: '/setup/gitlab' },
                { text: 'Microsoft 365 (Outlook/OneDrive/SharePoint)', link: '/setup/ms365' },
                { text: 'Confluence & Jira', link: '/setup/atlassian' },
                { text: 'Tableau', link: '/setup/tableau' },
                { text: 'X (Twitter)', link: '/setup/x' },
                { text: 'Clova Speech (Meeting Notes)', link: '/setup/voice' },
              ]
            },
            {
              text: 'Advanced Setup',
              items: [
                { text: 'Computer Use', link: '/setup/computer-use' },
                { text: 'Web Interface (Voice Input)', link: '/setup/web-interface' },
              ]
            }
          ],
          '/features/': [
            {
              text: 'Core Features',
              items: [
                { text: 'Chat', link: '/features/chat' },
                { text: 'Task Execution', link: '/features/tasks' },
                { text: 'Scheduling', link: '/features/scheduling' },
                { text: 'Memory System', link: '/features/memory' },
              ]
            },
            {
              text: 'Active Channels',
              items: [
                { text: 'Email Monitoring', link: '/features/email-monitoring' },
                { text: 'Confluence Tracking', link: '/features/confluence' },
                { text: 'Jira Tracking', link: '/features/jira' },
              ]
            },
            {
              text: 'Proactive Features',
              items: [
                { text: 'Proactive Suggestions', link: '/features/proactive' },
              ]
            }
          ]
        },
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
          { text: '설정 가이드', link: '/ko/setup/' },
          { text: '업무 시작하기', link: '/ko/features/' },
          { text: '문제 해결', link: '/ko/troubleshooting' },
        ],
        sidebar: {
          '/ko/setup/': [
            {
              text: 'MCP 설정',
              items: [
                { text: 'Perplexity 웹 검색', link: '/ko/setup/perplexity' },
                { text: 'DeepL (문서 번역)', link: '/ko/setup/deepl' },
                { text: 'GitHub', link: '/ko/setup/github' },
                { text: 'GitLab', link: '/ko/setup/gitlab' },
                { text: 'Microsoft 365 (Outlook/OneDrive/SharePoint)', link: '/ko/setup/ms365' },
                { text: 'Confluence & Jira', link: '/ko/setup/atlassian' },
                { text: 'Tableau', link: '/ko/setup/tableau' },
                { text: 'X (Twitter)', link: '/ko/setup/x' },
                { text: 'Clova Speech (회의록)', link: '/ko/setup/voice' },
              ]
            },
            {
              text: '고급 설정',
              items: [
                { text: 'Computer Use', link: '/ko/setup/computer-use' },
                { text: '웹 인터페이스 (음성 입력)', link: '/ko/setup/web-interface' },
              ]
            }
          ],
          '/ko/features/': [
            {
              text: '기본 기능',
              items: [
                { text: '대화하기', link: '/ko/features/chat' },
                { text: '작업 수행', link: '/ko/features/tasks' },
                { text: '스케줄링', link: '/ko/features/scheduling' },
                { text: '메모리 시스템', link: '/ko/features/memory' },
              ]
            },
            {
              text: '능동 수신 채널',
              items: [
                { text: '이메일 모니터링', link: '/ko/features/email-monitoring' },
                { text: 'Confluence 추적', link: '/ko/features/confluence' },
                { text: 'Jira 추적', link: '/ko/features/jira' },
              ]
            },
            {
              text: '선제적 제안',
              items: [
                { text: '선제적 제안', link: '/ko/features/proactive' },
              ]
            }
          ]
        },
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
    // 다크모드/라이트모드 별로 다른 로고 사용
    // 같은 이미지를 사용할 경우 아래처럼 동일하게 설정
    // 다른 이미지가 있으면 light/dark 경로를 각각 변경하세요
    logo: {
      light: '/images/kira-icon-light.png',  // 라이트모드용
      dark: '/images/kira-icon-dark.png'    // 다크모드용
    },

    footer: {
      message: 'Made with ❤️ by <a href="https://www.krafton.ai" target="_blank" rel="noopener">KRAFTON AI</a><br/>Technical Support: <a href="mailto:batteryho@krafton.com">batteryho@krafton.com</a> | Business Inquiry: <a href="mailto:enzo@krafton.com">enzo@krafton.com</a>',
      copyright: 'Copyright © 2025-present KIRA'
    },

    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: 'Search',
                buttonAriaLabel: 'Search'
              },
              modal: {
                noResultsText: 'No results found',
                resetButtonTitle: 'Reset',
                footer: {
                  selectText: 'Select',
                  navigateText: 'Navigate',
                  closeText: 'Close'
                }
              }
            }
          },
          ko: {
            translations: {
              button: {
                buttonText: '검색',
                buttonAriaLabel: '검색'
              },
              modal: {
                noResultsText: '결과를 찾을 수 없습니다',
                resetButtonTitle: '초기화',
                footer: {
                  selectText: '선택',
                  navigateText: '이동',
                  closeText: '닫기'
                }
              }
            }
          }
        }
      }
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/krafton-ai/kira' }
    ]
  }
})
