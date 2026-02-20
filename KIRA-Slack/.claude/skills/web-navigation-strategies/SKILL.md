---
name: web-navigation-strategies
description: Strategic navigation patterns and selector guides for thorough web exploration using Playwright MCP. Provides decision trees, navigation strategies, and site-specific selectors for reading multiple pages systematically. Use when planning how to navigate websites, determining reading depth, or finding the right selectors for Playwright MCP commands.
---

# Web Navigation Strategies for Playwright MCP

Strategic guide for systematic web exploration using Playwright MCP tools. This skill provides navigation patterns, not executable code.

## Reading Depth Decision Framework

### 1. Analyze User Intent

```
Query Analysis Decision Tree:
├── Keywords: "간단히, 요약, 훑어, quick, summary, overview"
│   → **QUICK MODE**
│   → Extract: Titles + First paragraphs only
│   → Pages: 30-50 (fast scan)
│
├── Keywords: "자세히, 상세, 모든, 댓글, detailed, comprehensive, everything"
│   → **DEEP MODE**
│   → Extract: Full content + Comments + Metadata + Related links
│   → Pages: 5-10 (thorough read)
│
└── No specific keywords
    → **STANDARD MODE**
    → Extract: Main content + Basic metadata
    → Pages: 15-20 (balanced)
```

### 2. Execute Based on Depth

#### Quick Mode Strategy
```javascript
// Get titles and summaries only
mcp_playwright.navigate(url)
links = mcp_playwright.query_selector_all('h2 a, h3 a')
for (link in links.slice(0, 50)) {
    mcp_playwright.click(link)
    title = mcp_playwright.get_text('h1')
    summary = mcp_playwright.get_text('p:first-of-type')
    mcp_playwright.go_back()
}
```

#### Standard Mode Strategy
```javascript
// Get full main content
mcp_playwright.navigate(url)
links = mcp_playwright.query_selector_all('article a')
for (link in links.slice(0, 20)) {
    mcp_playwright.click(link)
    mcp_playwright.wait_for_load_state('networkidle')
    content = mcp_playwright.get_text('main, article, .content')
    mcp_playwright.go_back()
}
```

#### Deep Mode Strategy
```javascript
// Get everything including discussions
mcp_playwright.navigate(url)
links = mcp_playwright.query_selector_all('article a')
for (link in links.slice(0, 10)) {
    mcp_playwright.click(link)
    mcp_playwright.wait_for_load_state('networkidle')
    
    // Main content
    content = mcp_playwright.get_text('article, main')
    
    // Comments
    comments = mcp_playwright.query_selector_all('.comment')
    for (comment in comments) {
        comment_text = mcp_playwright.get_text(comment)
    }
    
    // Metadata
    author = mcp_playwright.get_text('.author, .writer')
    date = mcp_playwright.get_text('time, .date')
    
    // Related links
    related = mcp_playwright.query_selector_all('.related a')
    
    mcp_playwright.go_back()
}
```

## Core Navigation Patterns

### Pattern 1: List-Detail Navigation

**Use for**: Blog indexes, search results, news listings

```
Step-by-Step Process:
1. Navigate to list page
2. Collect all article links
3. For each link:
   a. Click link
   b. Wait for page load
   c. Extract content
   d. Navigate back
   e. Continue with next
```

MCP Commands:
```javascript
// Navigate to list
mcp_playwright.navigate('https://blog.com/posts')

// Get all article links
article_links = mcp_playwright.query_selector_all('article a[href]')

// Process each
for (link in article_links) {
    // Enter detail page
    mcp_playwright.click(link)
    mcp_playwright.wait_for_load_state('networkidle')
    
    // Extract content
    text = mcp_playwright.get_text('article')
    
    // Return to list
    mcp_playwright.go_back()
    mcp_playwright.wait_for_load_state('networkidle')
}
```

### Pattern 2: Pagination Traversal

**Use for**: Multi-page results, forums, archives

```
Process:
1. Process current page
2. Find "Next" button
3. Click and repeat
4. Stop when no more pages
```

MCP Commands:
```javascript
while (true) {
    // Process current page
    articles = mcp_playwright.query_selector_all('article')
    for (article in articles) {
        // Extract content
    }
    
    // Check for next page
    next_button = mcp_playwright.query_selector('a.next, [rel="next"]')
    if (!next_button) break
    
    // Go to next page
    mcp_playwright.click(next_button)
    mcp_playwright.wait_for_load_state('networkidle')
}
```

### Pattern 3: Infinite Scroll

**Use for**: Social media, modern blogs, dynamic content

```javascript
// Scroll and load pattern
current_height = 0
while (true) {
    // Get current height
    new_height = mcp_playwright.evaluate('document.body.scrollHeight')
    
    if (new_height == current_height) break
    
    // Scroll to bottom
    mcp_playwright.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    mcp_playwright.wait_for_timeout(2000)  // Wait for content load
    
    current_height = new_height
}

// Then extract all loaded content
all_articles = mcp_playwright.query_selector_all('article')
```

## Site-Specific Selector Patterns

### Korean Portals

#### Naver (네이버)
```javascript
// Search results
list_selector: '.blog_list li'
link_selector: '.api_txt_lines.total_tit'
content_selector: '.se-main-container'
comment_selector: '.u_cbox_contents'

// Blog specific
blog_content: '#postViewArea, .se-main-container'
blog_title: '.se-title-text, .pcol1'
```

#### Daum (다음)
```javascript
// Search results  
list_selector: '.list_info'
link_selector: '.f_link_b, .tit_main'
content_selector: '.article_view'

// Tistory blogs
tistory_content: '.entry-content, .article-view'
tistory_comments: '.comment-list'
```

#### Brunch
```javascript
article_list: '.wrap_article_list li'
article_link: 'a.link_post'
article_content: '.wrap_body'
```

### Global Sites

#### Medium
```javascript
article_list: 'article'
article_link: 'h2 a, h3 a'
article_content: 'section.pw-post-body'
clap_count: '[aria-label*="clap"]'
```

#### Reddit
```javascript
post_list: '[data-testid="post-container"]'
post_content: '[data-click-id="text"]'
comments: '.Comment'
upvotes: '[aria-label*="upvote"]'
```

#### Generic Patterns
```javascript
// Works on most blogs
article_containers: 'article, .post, .entry, .blog-post'
title_selectors: 'h1, .title, .post-title, .entry-title'
content_selectors: 'main, .content, .post-content, .entry-content'
comment_selectors: '.comments, .comment-list, #comments'
author_selectors: '.author, .by-author, .writer, [rel="author"]'
date_selectors: 'time, .date, .published, .post-date'
```

## Intelligent Navigation Decisions

### When to Use Each Pattern

| Scenario | Pattern | Depth | Example |
|----------|---------|-------|---------|
| "뉴스 헤드라인 훑어봐" | List-Detail | Quick | 50 titles |
| "블로그 글 10개 읽어줘" | List-Detail | Standard | Full content |
| "포럼 댓글까지 분석해" | List-Detail | Deep | With comments |
| "모든 페이지 다 봐" | Pagination | Standard | All pages |
| "인스타 피드 쭉 봐" | Infinite Scroll | Quick | Social media |

### Selector Priority Strategy

```
1. Try specific selector first
   → '.se-main-container' (Naver specific)
   
2. Fallback to semantic HTML
   → 'article', 'main'
   
3. Try common class patterns
   → '.content', '.post-content'
   
4. Last resort: get all text
   → 'body' (then clean up)
```

## MCP Command Reference

### Essential Commands

```javascript
// Navigation
mcp_playwright.navigate(url)
mcp_playwright.go_back()
mcp_playwright.go_forward()
mcp_playwright.reload()

// Element Selection
mcp_playwright.query_selector(selector)        // First match
mcp_playwright.query_selector_all(selector)    // All matches

// Interaction
mcp_playwright.click(element_or_selector)
mcp_playwright.type(selector, text)
mcp_playwright.scroll_to(x, y)

// Content Extraction
mcp_playwright.get_text(selector)
mcp_playwright.get_attribute(selector, attribute)
mcp_playwright.get_url()
mcp_playwright.get_title()

// Waiting
mcp_playwright.wait_for_selector(selector)
mcp_playwright.wait_for_load_state('networkidle')
mcp_playwright.wait_for_timeout(milliseconds)

// JavaScript Execution
mcp_playwright.evaluate(javascript_code)
```

## Practical Examples

### Example 1: Quick News Scan
```javascript
// User: "네이버 뉴스 제목만 빠르게 훑어줘"
mcp_playwright.navigate('https://news.naver.com')
headlines = mcp_playwright.query_selector_all('.news_tit')
for (headline in headlines.slice(0, 30)) {
    title = mcp_playwright.get_text(headline)
    // Store title
}
```

### Example 2: Blog Deep Dive
```javascript
// User: "이 블로그 최신글 5개 댓글까지 자세히 봐줘"
mcp_playwright.navigate('https://blog.example.com')
posts = mcp_playwright.query_selector_all('.post-link')

for (post in posts.slice(0, 5)) {
    mcp_playwright.click(post)
    
    // Get everything
    title = mcp_playwright.get_text('h1')
    content = mcp_playwright.get_text('article')
    author = mcp_playwright.get_text('.author')
    date = mcp_playwright.get_text('.date')
    
    // Get all comments
    comments = mcp_playwright.query_selector_all('.comment')
    for (comment in comments) {
        text = mcp_playwright.get_text(comment)
    }
    
    mcp_playwright.go_back()
}
```

### Example 3: Forum Thread Analysis
```javascript
// User: "레딧 스레드 전체 토론 분석해줘"
mcp_playwright.navigate(reddit_url)

// Main post
main_post = mcp_playwright.get_text('[data-click-id="text"]')
upvotes = mcp_playwright.get_text('[aria-label*="upvote"]')

// All comments with nested replies
all_comments = mcp_playwright.query_selector_all('.Comment')
for (comment in all_comments) {
    text = mcp_playwright.get_text(comment)
    // Parse nested structure
}
```

## Error Handling Strategies

### Common Issues and Solutions

1. **Selector Not Found**
   ```javascript
   // Try multiple selectors
   content = mcp_playwright.query_selector('article') 
           || mcp_playwright.query_selector('main')
           || mcp_playwright.query_selector('.content')
           || mcp_playwright.query_selector('body')
   ```

2. **Dynamic Content Not Loaded**
   ```javascript
   // Wait strategies
   mcp_playwright.wait_for_load_state('networkidle')
   mcp_playwright.wait_for_selector('.content', timeout=10000)
   mcp_playwright.wait_for_timeout(2000)  // Last resort
   ```

3. **Navigation Failed**
   ```javascript
   try {
       mcp_playwright.go_back()
   } catch {
       // Fallback: navigate directly
       mcp_playwright.navigate(list_page_url)
   }
   ```

## Best Practices

### DO ✅
- Wait for content to load before extraction
- Use specific selectors when possible
- Handle pagination and infinite scroll
- Extract metadata (author, date) when available
- Respect rate limits with waits between requests

### DON'T ❌
- Don't assume selectors work on all sites
- Don't skip wait_for_load_state
- Don't extract without checking element exists
- Don't ignore error handling
- Don't process too many pages in deep mode

## Decision Flow Summary

```
User Request
    ↓
Analyze Keywords → Determine Depth (Quick/Standard/Deep)
    ↓
Identify Site Type → Choose Selectors
    ↓
Select Pattern → (List-Detail/Pagination/Scroll)
    ↓
Execute with MCP Commands
    ↓
Handle Errors → Fallback Strategies
```

## Reference

For detailed patterns and selectors by site type, see:
- [references/site-selectors.md](references/site-selectors.md) - Comprehensive selector database
- [references/navigation-patterns.md](references/navigation-patterns.md) - Advanced navigation techniques