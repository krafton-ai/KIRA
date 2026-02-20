# Advanced Navigation Patterns

Sophisticated techniques for complex web navigation scenarios using Playwright MCP.

## Multi-Level Navigation

### Hierarchical Exploration
Navigate through category → subcategory → article structure

```javascript
// Level 1: Categories
mcp_playwright.navigate('https://site.com')
categories = mcp_playwright.query_selector_all('.category-link')

for (category in categories) {
    mcp_playwright.click(category)
    
    // Level 2: Subcategories
    subcategories = mcp_playwright.query_selector_all('.subcategory')
    for (subcategory in subcategories) {
        mcp_playwright.click(subcategory)
        
        // Level 3: Articles
        articles = mcp_playwright.query_selector_all('.article-link')
        for (article in articles.slice(0, 5)) {
            mcp_playwright.click(article)
            // Extract content
            mcp_playwright.go_back()
        }
        
        mcp_playwright.go_back() // To subcategory list
    }
    
    mcp_playwright.go_back() // To main categories
}
```

### Breadcrumb Navigation
Use breadcrumbs to maintain context while exploring

```javascript
// Save breadcrumb trail
breadcrumbs = mcp_playwright.query_selector_all('.breadcrumb a')
breadcrumb_urls = []

for (crumb in breadcrumbs) {
    url = mcp_playwright.get_attribute(crumb, 'href')
    breadcrumb_urls.push(url)
}

// Navigate using breadcrumbs
mcp_playwright.navigate(breadcrumb_urls[0]) // Back to home
mcp_playwright.navigate(breadcrumb_urls[1]) // Back to category
```

## Session Management

### Login-Protected Content
Handle authentication before navigation

```javascript
// Check if login required
login_form = mcp_playwright.query_selector('form[action*="login"]')

if (login_form) {
    // Notify user authentication needed
    return "Login required. Please authenticate first."
}

// Or handle cookie-based sessions
mcp_playwright.evaluate(`
    document.cookie = "session_id=xxx; path=/";
`)
```

### Maintaining State
Preserve filters and search parameters

```javascript
// Save current state
current_url = mcp_playwright.get_url()
filters = mcp_playwright.evaluate(`
    new URLSearchParams(window.location.search).toString()
`)

// Navigate and return with state
mcp_playwright.navigate('https://site.com/article')
// ... extract content ...

// Return to exact state
mcp_playwright.navigate(current_url + '?' + filters)
```

## Dynamic Content Handling

### Wait Strategies

```javascript
// Strategy 1: Wait for specific element
mcp_playwright.wait_for_selector('.content-loaded', {
    timeout: 10000,
    state: 'visible'
})

// Strategy 2: Wait for network idle
mcp_playwright.wait_for_load_state('networkidle')

// Strategy 3: Wait for custom condition
mcp_playwright.evaluate(`
    new Promise(resolve => {
        const checkContent = setInterval(() => {
            if (document.querySelectorAll('.article').length > 10) {
                clearInterval(checkContent);
                resolve();
            }
        }, 500);
    })
`)

// Strategy 4: Progressive waiting
delays = [500, 1000, 2000, 5000]
for (delay in delays) {
    content = mcp_playwright.query_selector('.content')
    if (content) break
    mcp_playwright.wait_for_timeout(delay)
}
```

### AJAX Content Loading

```javascript
// Intercept AJAX responses
mcp_playwright.evaluate(`
    const originalFetch = window.fetch;
    window.fetchResponses = [];
    window.fetch = async (...args) => {
        const response = await originalFetch(...args);
        const clone = response.clone();
        const data = await clone.json();
        window.fetchResponses.push(data);
        return response;
    };
`)

// Trigger AJAX load
mcp_playwright.click('.load-more')

// Get AJAX data
ajax_data = mcp_playwright.evaluate('window.fetchResponses')
```

### Lazy Loading Images

```javascript
// Scroll to trigger lazy loading
mcp_playwright.evaluate(`
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => {
        img.scrollIntoView();
        // Wait for intersection observer
        setTimeout(() => {}, 100);
    });
`)

// Wait for images to load
mcp_playwright.wait_for_function(`
    document.querySelectorAll('img[data-src]').length === 0
`)
```

## Pagination Strategies

### Numeric Pagination

```javascript
// Get total pages
total_pages = mcp_playwright.evaluate(`
    const pagination = document.querySelector('.pagination');
    const lastPage = pagination.querySelector('a:last-child');
    parseInt(lastPage.textContent);
`)

// Navigate through pages
for (page = 1; page <= Math.min(total_pages, 10); page++) {
    mcp_playwright.navigate(`${base_url}?page=${page}`)
    
    // Process page content
    articles = mcp_playwright.query_selector_all('.article')
    // ... extract ...
}
```

### Load More Button

```javascript
max_loads = 10
loads = 0

while (loads < max_loads) {
    // Check for load more button
    load_more = mcp_playwright.query_selector('.load-more:not([disabled])')
    
    if (!load_more) break
    
    // Click and wait
    mcp_playwright.click(load_more)
    mcp_playwright.wait_for_timeout(2000)
    loads++
}

// Extract all loaded content
all_content = mcp_playwright.query_selector_all('.item')
```

### Infinite Scroll with Threshold

```javascript
// Advanced infinite scroll handling
mcp_playwright.evaluate(`
    let lastHeight = 0;
    let sameHeightCount = 0;
    const maxSameHeight = 3;
    
    const scrollToBottom = async () => {
        const height = document.body.scrollHeight;
        
        if (height === lastHeight) {
            sameHeightCount++;
            if (sameHeightCount >= maxSameHeight) {
                return false; // No more content
            }
        } else {
            sameHeightCount = 0;
        }
        
        lastHeight = height;
        window.scrollTo(0, height);
        await new Promise(r => setTimeout(r, 2000));
        return true;
    };
    
    // Scroll until no more content
    while (await scrollToBottom()) {}
`)
```

## Tab and Window Management

### Multi-Tab Navigation

```javascript
// Open link in new tab (simulate)
link_url = mcp_playwright.get_attribute('.external-link', 'href')

// Save current URL
main_url = mcp_playwright.get_url()

// Navigate to new "tab"
mcp_playwright.navigate(link_url)
// ... process content ...

// Return to original "tab"
mcp_playwright.navigate(main_url)
```

### Popup Handling

```javascript
// Detect and handle popups
popup = mcp_playwright.query_selector('.popup, .modal')

if (popup) {
    // Close popup
    close_button = mcp_playwright.query_selector('.close, .dismiss, [aria-label="Close"]')
    if (close_button) {
        mcp_playwright.click(close_button)
    } else {
        // Press Escape
        mcp_playwright.keyboard_press('Escape')
    }
}
```

## Advanced Selectors

### Dynamic Selector Building

```javascript
// Build selector based on content
function buildSelector(tag, text) {
    return `${tag}:has-text("${text}")`
}

// Use dynamic selector
article_with_keyword = buildSelector('article', 'important')
mcp_playwright.click(article_with_keyword)
```

### XPath Selectors

```javascript
// When CSS selectors aren't enough
xpath = "//div[@class='container']//a[contains(text(), 'Read more')]"
element = mcp_playwright.evaluate(`
    document.evaluate(
        "${xpath}",
        document,
        null,
        XPathResult.FIRST_ORDERED_NODE_TYPE,
        null
    ).singleNodeValue
`)
```

### Text-Based Selection

```javascript
// Select by text content
mcp_playwright.click('text="Next Page"')
mcp_playwright.click('text=/Read.*more/i') // Regex

// Select containing text
mcp_playwright.query_selector('*:has-text("Important")')
```

## Performance Optimization

### Parallel Processing Simulation

```javascript
// Collect all URLs first
urls = []
links = mcp_playwright.query_selector_all('.article-link')

for (link in links) {
    url = mcp_playwright.get_attribute(link, 'href')
    urls.push(url)
}

// Process in batches
batch_size = 5
for (i = 0; i < urls.length; i += batch_size) {
    batch = urls.slice(i, i + batch_size)
    
    // Process batch sequentially (MCP doesn't support true parallel)
    for (url in batch) {
        mcp_playwright.navigate(url)
        // Quick extraction
        mcp_playwright.go_back()
    }
}
```

### Resource Blocking

```javascript
// Block unnecessary resources
mcp_playwright.evaluate(`
    // Override fetch for specific resources
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const url = args[0];
        if (url.includes('analytics') || url.includes('ads')) {
            return Promise.resolve(new Response('', {status: 200}));
        }
        return originalFetch(...args);
    };
`)
```

### Minimal Extraction

```javascript
// Extract only essential data
essential_data = mcp_playwright.evaluate(`
    {
        title: document.querySelector('h1')?.textContent,
        summary: document.querySelector('p')?.textContent,
        url: window.location.href
    }
`)
```

## Error Recovery

### Retry Logic

```javascript
max_retries = 3
retry_count = 0

while (retry_count < max_retries) {
    try {
        mcp_playwright.click('.article-link')
        mcp_playwright.wait_for_selector('.content', {timeout: 5000})
        break  // Success
    } catch (error) {
        retry_count++
        if (retry_count >= max_retries) {
            // Final failure
            return "Failed after " + max_retries + " attempts"
        }
        // Wait before retry
        mcp_playwright.wait_for_timeout(1000 * retry_count)
    }
}
```

### Fallback Strategies

```javascript
// Primary selector
content = mcp_playwright.query_selector('.main-content')

if (!content) {
    // Fallback 1
    content = mcp_playwright.query_selector('main')
}

if (!content) {
    // Fallback 2
    content = mcp_playwright.query_selector('[role="main"]')
}

if (!content) {
    // Last resort
    content = mcp_playwright.query_selector('body')
}
```

### State Recovery

```javascript
// Save state before risky operation
saved_url = mcp_playwright.get_url()
saved_scroll = mcp_playwright.evaluate('window.scrollY')

try {
    // Risky navigation
    mcp_playwright.click('.unstable-link')
} catch (error) {
    // Restore state
    mcp_playwright.navigate(saved_url)
    mcp_playwright.evaluate(`window.scrollTo(0, ${saved_scroll})`)
}
```

## Special Techniques

### Content Diffing

```javascript
// Detect new content on dynamic pages
initial_content = mcp_playwright.query_selector_all('.item')
initial_count = initial_content.length

// Trigger update
mcp_playwright.click('.refresh')
mcp_playwright.wait_for_timeout(2000)

// Find new items
new_content = mcp_playwright.query_selector_all('.item')
new_items = new_content.slice(initial_count)
```

### Smart Scrolling

```javascript
// Scroll to specific content
mcp_playwright.evaluate(`
    // Find target element
    const target = document.querySelector('.target-section');
    
    // Smooth scroll
    target.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
`)
```

### Form Interaction

```javascript
// Search within site
search_input = mcp_playwright.query_selector('input[type="search"]')
mcp_playwright.type(search_input, 'search term')
mcp_playwright.keyboard_press('Enter')

// Wait for results
mcp_playwright.wait_for_selector('.search-results')
```

## Navigation Decision Tree

```
Start
  ↓
Is content paginated?
  Yes → Use Pagination Pattern
  No ↓
  
Is content dynamically loaded?
  Yes → Use AJAX/Infinite Scroll Pattern
  No ↓
  
Is it a list-detail structure?
  Yes → Use List-Detail Pattern
  No ↓
  
Is it hierarchical?
  Yes → Use Multi-Level Pattern
  No ↓
  
Use Direct Navigation
```

## Best Practices Summary

1. **Always wait** after navigation actions
2. **Use multiple selectors** as fallbacks
3. **Handle errors gracefully** with try-catch
4. **Limit depth** to avoid infinite loops
5. **Save state** before complex operations
6. **Optimize selectors** for performance
7. **Respect rate limits** with delays
8. **Test selectors** in browser first
9. **Document patterns** for reuse
10. **Monitor performance** and adjust