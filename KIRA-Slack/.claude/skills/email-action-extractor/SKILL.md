---
name: email-action-extractor
description: Extract actionable tasks assigned to the user from email text. Filters out informational emails (announcements, newsletters, ads, automated reports) and only processes emails with clear action requests. Handles group emails by identifying user-specific assignments.
---

# Email Action Extractor

Extract actionable tasks assigned to the user from email text and prepare information for task management tool calls.

## Core Principles

**Filter Out Informational Emails**: Do not process emails that merely convey information. Only extract emails with clear, explicit action requests.

**Action-Oriented Keywords**: Focus on emails containing request expressions such as:
- Please [action] / Could you [action]
- Need you to / Would you
- Request for / Asking you to
- Review / Approve / Submit / Prepare / Complete
- By [deadline] / Due [date]
- Urgent / ASAP / High priority

**Group Email Handling**: For emails with multiple recipients, only extract actions when:
- User is explicitly mentioned by name (@username, "John please...")
- User's email is in To: field (not just CC)
- Action is directed at "everyone" or "team" without specific person mentioned

## Processing Steps

### 1. Email Analysis

For each email, determine:

**Is this actionable?**
- Does it contain explicit request verbs?
- Is there a specific task described?
- Is there a deadline or time constraint?
- Does it require a response or deliverable?

**Is this for me?**
- Am I in the To: field (not just CC)?
- Am I mentioned by name in the body?
- Is this a group email where someone else is the assignee?
- Is this directed at "everyone" or specifically at me?

**Action characteristics:**
- Clear and specific (not vague like "let me know your thoughts")
- Has measurable completion criteria
- Requires effort beyond simple acknowledgment

### 2. Action Identification

When an action is identified, extract:

- **Requester**: Who is asking (name and email)
- **Action description**: What needs to be done (be specific)
- **Deadline**: When is it due (if specified)
- **Priority signals**: "urgent", "ASAP", "high priority", etc.
- **Context**: Related links, attachments, email ID, thread context

### 3. Exclude Non-Actionable Emails

**Always exclude:**
- Simple announcements (company news, system notifications)
- FYI emails (informational only)
- Automated reports and alerts
- Meeting invites without action items
- One-way information sharing
- Marketing/promotional emails
- Newsletter/subscription emails (blog updates, product news)
- Emails from no-reply addresses
- Emails with unsubscribe links
- Status updates without requests
- "Thanks" / "Got it" acknowledgments

**Edge cases - be conservative:**
- "Let me know what you think" → Only if context requires formal feedback
- "Feel free to reach out" → Exclude (optional, not required)
- "For your information" → Exclude
- "Please be aware" → Exclude (informational)
- "Hope this helps" → Exclude

### 4. Priority Assessment

When present, identify priority indicators:

**High Priority:**
- Explicit: "urgent", "ASAP", "high priority", "critical"
- Near deadline: due today or tomorrow
- Executive request: from leadership
- Blocking others: "blocking", "dependency"

**Normal Priority:**
- Standard deadline: few days to weeks
- Regular business request
- No priority indicators mentioned

**Low Priority:**
- "When you get a chance"
- "No rush"
- Distant deadline: weeks or months away

## Examples

### ✅ Actionable - Direct Assignment

```
From: Manager Kim <kim@company.com>
To: you@company.com
Subject: [Urgent] Q4 Report Review Needed
Body: "Hi, please review the attached Q4 report and provide feedback by Friday EOD. 
Focus on the financial projections section."
```
→ **Extract**: Review Q4 report financial projections, provide feedback (Due: Friday EOD, Priority: High)

### ✅ Actionable - Meeting with Pre-work

```
From: Project Lead <lead@company.com>
To: team@company.com (5 people)
Subject: Design Review Tomorrow
Body: "Team, please review the design doc before tomorrow's 2pm meeting and come prepared 
with questions. Link: [doc]"
```
→ **Extract**: Review design doc before 2pm meeting tomorrow (Due: Tomorrow 2pm)

### ❌ Informational - No Action

```
From: HR Team <hr@company.com>
To: all@company.com
Subject: Holiday Policy Update
Body: "Hi everyone, please note that our holiday policy has been updated. 
See attached for details."
```
→ **Exclude**: Informational announcement, no specific action required

### ❌ Automated - System Email

```
From: notifications@jira.com
Subject: Daily Digest: 3 issues updated
Body: "Here's your daily summary of Jira updates..."
```
→ **Exclude**: Automated digest, informational only

### ✅ Group Email - User Mentioned

```
From: Tech Lead <lead@company.com>
To: dev-team@company.com (10 people)
Subject: Sprint Planning
Body: "Team update: @John please implement the login feature this sprint. 
@Sarah will handle the API integration."
```
→ **Extract** (if user is John): Implement login feature this sprint

### ❌ Group Email - Someone Else Assigned

```
From: Tech Lead <lead@company.com>
To: dev-team@company.com (10 people)
Subject: Sprint Planning
Body: "@Sarah please handle the API integration this sprint."
```
→ **Exclude** (if user is not Sarah): Action assigned to someone else

### ❌ Newsletter/Subscription

```
From: TechNews Weekly <newsletter@technews.com>
Subject: This Week in Tech: AI Advances
Body: "Here are this week's top stories... [Unsubscribe]"
```
→ **Exclude**: Newsletter, promotional content

### ❌ Vague Request

```
From: Colleague <colleague@company.com>
Subject: Quick question
Body: "Hey, when you get a chance, let me know your thoughts on the new process."
```
→ **Exclude**: Too vague, no specific deliverable, "when you get a chance" indicates low priority/optional

### ✅ Clear Request with Deadline

```
From: Client <client@external.com>
Subject: Contract Review
Body: "Could you review the attached contract and send back signed copy by Wednesday?
Please pay special attention to section 3.2."
```
→ **Extract**: Review contract (focus on section 3.2), sign and return (Due: Wednesday)

## Edge Case Guidelines

**"Please review" emails:**
- ✅ Include if: formal review required, feedback expected, deadline given
- ❌ Exclude if: casual "take a look", FYI context, no response needed

**Meeting invites:**
- ✅ Include if: requires preparation, deliverable needed beforehand
- ❌ Exclude if: simple attendance, no pre-work required

**CC'd emails:**
- ✅ Include if: explicitly mentioned in body despite being CC
- ❌ Exclude if: just CC'd for visibility, no direct action

**Thread replies:**
- Check if action already completed or superseded by later emails
- Avoid duplicate extraction from email chains

## Best Practices

- **Be conservative**: When in doubt, exclude rather than create noise
- **Context matters**: Consider the sender-recipient relationship
- **Avoid trivial tasks**: Skip courtesy responses unless explicitly requested
- **Check completeness**: Ensure extracted action is clear and self-contained
- **Preserve context**: Include enough information for the user to understand the task without re-reading the email
