---
name: confluence-deep-reader
description: Read a Confluence page and recursively explore its child pages up to 3 levels deep. Use when users want to comprehensively read a Confluence page tree, understand hierarchical documentation, or analyze content across parent and child pages.
---

# Confluence Deep Reader

This skill guides you to recursively read Confluence pages and their descendants up to 3 levels deep.

## When to Use This Skill

Use this skill when:
- User provides a Confluence link and wants to read "everything" or "all related pages"
- User asks to "read this page and subpages"
- User wants to understand the full content tree of a Confluence page
- User needs comprehensive analysis of hierarchical documentation

## Workflow

### Step 1: Read the Starting Page

Use `getConfluencePage` to read the initial page provided by the user.

### Step 2: Discover Child Pages

Use `getConfluencePageDescendants` to find all child pages of the current page. This tool returns the hierarchical structure of descendants.

### Step 3: Read Each Child Page (Depth 1)

For each child page found:
1. Use `getConfluencePage` to read its content
2. Track that this is depth 1

### Step 4: Recursively Explore Deeper Levels

For each child page read in Step 3:
1. Use `getConfluencePageDescendants` to check if it has its own children
2. If children exist and current depth < 3:
   - Read each grandchild page (depth 2)
   - Repeat this process for depth 3

**IMPORTANT: Stop at depth 3.** Do not explore beyond 3 levels from the starting page.

### Step 5: Synthesize Information

After reading all pages within the depth limit:
1. Organize information hierarchically
2. Provide comprehensive summary or answer user's question
3. Note if there are deeper levels that were not explored (beyond depth 3)

## Depth Tracking

Keep track of the current depth level:
- **Depth 0**: Starting page (the one user provided)
- **Depth 1**: Direct children of starting page
- **Depth 2**: Grandchildren
- **Depth 3**: Great-grandchildren (STOP HERE)

## Best Practices

- **Show progress**: Let user know which pages you're reading (e.g., "Reading main page... Found 5 child pages... Reading child 1/5...")
- **Respect the limit**: Never go beyond depth 3
- **Be efficient**: If there are many pages (>20), consider asking user if they want to continue or focus on specific sections
- **Handle errors gracefully**: If a page cannot be accessed, note it and continue with others
- **Provide structure**: When presenting results, maintain the hierarchical structure so users understand the page relationships

## Example Usage

```
User: "Read this Confluence page and all its subpages: [link]"

Your workflow:
1. Read the starting page (depth 0)
2. Find its children using getConfluencePageDescendants
3. Read each child (depth 1) and find their children
4. Read each grandchild (depth 2) and find their children
5. Read each great-grandchild (depth 3) - STOP
6. Synthesize all information into a comprehensive summary
```

## When to Ask for Clarification

- If there are 50+ pages in the tree, ask if user wants to proceed with all or focus on specific branches
- If user asks for content "deeper than 3 levels", explain the limit and offer to focus on specific deep branches
