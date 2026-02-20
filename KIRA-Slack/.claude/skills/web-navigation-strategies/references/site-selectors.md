# Site-Specific Selectors Database

Comprehensive selector patterns for various websites and platforms.

## Korean Sites

### Naver (네이버)

#### Search Results Page
```javascript
// Blog search results
blog_list: '.blog_list'
blog_item: '.blog_list li'
blog_title: '.api_txt_lines.total_tit'
blog_snippet: '.api_txt_lines.dsc_txt'
blog_author: '.sub_txt.sub_name'
blog_date: '.sub_txt.sub_time'

// News search results
news_list: '.list_news'
news_item: '.news_wrap'
news_title: '.news_tit'
news_content: '.api_txt_lines.dsc_txt'
news_source: '.info.press'

// View original button
view_original: '.api_txt_lines.total_tit' // Click this to go to actual blog
```

#### Naver Blog (blog.naver.com)
```javascript
// Smart Editor 3.0
content_container: '.se-main-container'
title: '.se-title-text'
paragraphs: '.se-text-paragraph'
images: '.se-image-resource'

// Old editor
old_content: '#postViewArea'
old_title: '.pcol1'
```

#### Naver Cafe
```javascript
article_list: '.article-board'
article_title: '.article-list .inner_list'
article_content: '.article_container'
comments: '.comment_list'
```

### Daum (다음)

#### Search Results
```javascript
// Blog results
blog_results: '#blogColl'
blog_item: '.f_clear'
blog_title: '.f_link_b'
blog_content: '.f_eb.desc'

// Cafe results
cafe_item: '.cafe_info'
cafe_title: '.f_link_cafe'
```

### Tistory

```javascript
// Common patterns
post_list: '.post-item, .list_content'
post_title: '.title, .link_post'
post_content: '.entry-content, .article_content'
post_date: '.date, .datetime'
comments: '.comment-list'

// Skin variations
skin_1: {
    list: '#mArticle .post_article',
    content: '.blogview_content'
}
skin_2: {
    list: '.inner .post-item',
    content: '.tt_article_useless_p_margin'
}
```

### Brunch

```javascript
// Article list
article_list: '.wrap_article_list'
article_item: 'li[data-articleuid]'
article_link: 'a.link_post'

// Article content
article_title: '.wrap_title h1'
article_subtitle: '.wrap_title h2'
article_body: '.wrap_body'
article_author: '.txt_by'
article_date: '.txt_date'
```

### Velog

```javascript
// Post list
post_list: '[class*="PostList"]'
post_card: '[class*="PostCard"]'
post_title: 'h2'
post_preview: 'p'

// Post content
content: '[class*="PostContent"]'
tags: '[class*="Tag"]'
series: '[class*="SeriesInfo"]'
```

## Global Sites

### Medium

```javascript
// Article list
article_list: 'article'
article_link: '[data-action="open-post"]'
article_title: 'h2, h3'
article_preview: '.pw-post-body-preview'

// Article content
article_body: 'section.pw-post-body'
article_author: '[data-testid="authorName"]'
claps: '[aria-label*="clap"]'
responses: '[aria-label*="responses"]'
```

### Dev.to

```javascript
// Feed
article_card: '.crayons-story'
article_link: '.crayons-story__hidden-navigation-link'
article_title: '.crayons-story__title'
article_tags: '.crayons-tag'

// Article
article_content: '#article-body'
reactions: '[data-reaction-count]'
comments: '.comment-wrapper'
```

### Reddit

```javascript
// Post list  
post_container: '[data-testid="post-container"]'
post_title: 'h3'
post_content: '[data-click-id="text"]'
subreddit: '[data-click-id="subreddit"]'

// Comments
comment_tree: '[data-testid="comment-tree"]'
comment: '.Comment'
comment_author: '[data-testid="comment_author"]'
comment_score: '.j9NixHqtN2j8SKHcdJ0om'
```

### Hacker News

```javascript
// Story list
story_row: '.athing'
story_title: '.titleline > a'
story_domain: '.sitebit'
story_meta: '.subtext'
points: '.score'
comments_link: '.subtext a:last-child'

// Comments
comment_tree: '.comment-tree'
comment_text: '.commtext'
comment_author: '.hnuser'
```

### Stack Overflow

```javascript
// Question list
question_summary: '.s-post-summary'
question_title: '.s-link'
question_stats: '.s-post-summary--stats'
tags: '.s-tag'

// Question/Answer page
question_body: '.s-prose'
answer: '.answer'
accepted_answer: '.accepted-answer'
vote_count: '[data-value]'
```

### GitHub

```javascript
// Repository list
repo_list: '.repo-list'
repo_item: '.repo-list-item'
repo_name: 'h3 a'
repo_description: 'p.mb-1'
repo_stats: '[aria-label*="star"], [aria-label*="fork"]'

// Issues/PRs
issue_list: '.js-issue-row'
issue_title: '.js-navigation-open'
issue_labels: '.labels .label'
issue_comments: '.comment-body'
```

### Twitter/X

```javascript
// Tweet list
tweet: 'article[data-testid="tweet"]'
tweet_text: '[data-testid="tweetText"]'
tweet_author: '[data-testid="User-Names"]'
tweet_stats: '[aria-label*="likes"], [aria-label*="retweets"]'
tweet_media: '[data-testid="tweetPhoto"]'
```

### LinkedIn

```javascript
// Feed
post: '.feed-shared-update-v2'
post_content: '.feed-shared-text'
post_author: '.feed-shared-actor__name'
post_reactions: '.social-details-social-counts'

// Articles  
article_title: '.article-title'
article_content: '.article-content'
```

## E-commerce Sites

### Amazon

```javascript
// Product list
product_list: '[data-component-type="s-search-result"]'
product_title: 'h2 a span'
product_price: '.a-price-whole'
product_rating: '.a-icon-alt'
product_image: '.s-image'

// Product page
product_details: '#feature-bullets'
reviews: '[data-hook="review"]'
```

### eBay

```javascript
// Search results
item_list: '.s-item'
item_title: '.s-item__title'
item_price: '.s-item__price'
item_shipping: '.s-item__shipping'
item_seller: '.s-item__seller-info'
```

## News Sites

### CNN

```javascript
article_list: '.cn-list-hierarchical-xs'
article_link: '.media a'
article_headline: '.cd__headline'
article_content: '.l-container .zn-body__paragraph'
```

### BBC

```javascript
article_list: '[data-testid="edinburgh-card"]'
article_title: '[data-testid="card-headline"]'
article_summary: '[data-testid="card-description"]'
article_body: '[data-component="text-block"]'
```

### The Guardian

```javascript
article_list: '.fc-item'
article_link: '.fc-item__link'
article_headline: '.fc-item__headline'
article_body: '.article-body-commercial-selector'
```

## Forum/Community Sites

### Discourse Forums

```javascript
topic_list: '.topic-list-item'
topic_title: '.title'
topic_category: '.category-name'
post_content: '.cooked'
post_author: '.username'
```

### phpBB Forums

```javascript
forum_list: '.forumbg'
topic_list: '.topiclist .row'
topic_title: '.topictitle'
post_body: '.postbody .content'
```

### XenForo Forums

```javascript
thread_list: '.structItem--thread'
thread_title: '.structItem-title'
post_content: '.message-body .bbWrapper'
reactions: '.reactionsBar'
```

## Generic Patterns

### Common Article Patterns
```javascript
// Semantic HTML5
article: 'article'
main_content: 'main'
header: 'header'
footer: 'footer'
nav: 'nav'
aside: 'aside'

// Common class names
content_areas: '.content, .main-content, .post-content, .entry-content, .article-content'
titles: '.title, .post-title, .entry-title, .article-title, h1'
dates: 'time, .date, .published, .posted, .timestamp'
authors: '.author, .by-author, .writer, .posted-by'
comments: '.comments, .comment-list, .discussion, #comments'
```

### Common List Patterns
```javascript
// Lists
item_lists: '.list, .list-item, .item, .post-list, .article-list'
cards: '.card, .tile, .block, .panel'
grids: '.grid, .grid-item, .col, .column'

// Pagination
next_page: '.next, .pagination-next, [rel="next"], .load-more'
prev_page: '.prev, .pagination-prev, [rel="prev"]'
page_numbers: '.pagination a, .page-numbers'
```

## Dynamic Content Patterns

### Infinite Scroll Detection
```javascript
// Common infinite scroll containers
scroll_containers: '[data-infinite-scroll], .infinite-scroll, .endless-scroll'

// Loading indicators
loading: '.loading, .spinner, .loader, [aria-busy="true"]'

// End of content markers
end_markers: '.no-more-posts, .end-of-results, .all-loaded'
```

### AJAX Content
```javascript
// Common AJAX containers
ajax_content: '[data-ajax], .ajax-content, .dynamic-content'

// Update triggers
load_triggers: '[data-load-more], .load-more-button, .show-more'
```

## Accessibility Selectors

### ARIA Labels
```javascript
// Navigation
main_nav: '[role="navigation"]'
main_content: '[role="main"]'
articles: '[role="article"]'

// Interactive
buttons: '[role="button"]'
links: '[role="link"]'
```

### Semantic Markup
```javascript
// Headings
page_title: 'h1'
section_titles: 'h2'
subsection_titles: 'h3'

// Lists
unordered_lists: 'ul'
ordered_lists: 'ol'
definition_lists: 'dl'
```

## Special Cases

### Single Page Applications (SPA)
```javascript
// React apps
react_root: '#root, #app, .app'
react_router: '[data-reactroot]'

// Vue apps
vue_app: '#app, [id^="vue-"]'

// Angular apps
angular_app: 'app-root, [ng-app]'
```

### Shadow DOM Content
```javascript
// Custom elements
web_components: ':defined'

// Shadow hosts
shadow_hosts: ':host'
```

## Usage Tips

1. **Fallback Strategy**: Always have multiple selector options
2. **Specificity**: Start specific, then broaden if needed
3. **Performance**: Use efficient selectors (ID > class > tag)
4. **Robustness**: Don't rely on dynamic classes or IDs
5. **Testing**: Verify selectors in browser DevTools first