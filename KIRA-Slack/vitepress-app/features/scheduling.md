# Scheduling

KIRA can schedule messages and tasks. Receive notifications at specific times or automate recurring tasks.

## 📅 Basic Usage

### One-Time Schedule

When you want to receive a message at a specific time:

```
User: Remind me to prepare for the meeting tomorrow at 9am
KIRA: Scheduled reminder for tomorrow at 9am!
```

```
User: Remind me about the report deadline in 3 hours
KIRA: Scheduled reminder for 3 hours from now.
```

### Specific Task Scheduling

You can schedule not just notifications but also tasks:

```
User: Every morning at 9am, summarize today's schedule
KIRA: Scheduled daily schedule summary for 9am.
```

```
User: Friday at 5pm, compile work status and share in team channel
KIRA: Scheduled work status sharing for Friday at 5pm.
```

---

## 🎯 Usage Examples

### Reminders

```
User: Remind me about standup meeting in 30 minutes
KIRA: Set standup meeting reminder for 30 minutes from now.
```

### Regular Reports

```
User: Every Monday at 10am, summarize last week's emails
KIRA: Scheduled email summary for every Monday at 10am.
```

### Deadline Alerts

```
User: Send checklist reminder one day before project deadline
KIRA: Scheduled checklist reminder for one day before deadline.
```

---

## 🔧 Managing Schedules

### View Schedule List

```
User: Show my scheduled reminders
KIRA: Current scheduled reminders:
      1. Tomorrow 9am - Meeting prep reminder
      2. Friday 5pm - Weekly report writing
      3. Every Monday - Email summary
```

### Cancel Schedule

```
User: Cancel the tomorrow 9am reminder
KIRA: Cancelled the tomorrow 9am reminder.
```

---

## 💡 Tips

### Specify Clear Times

- **Good examples**: "tomorrow at 9am", "in 3 hours", "Friday at 5pm"
- **Ambiguous examples**: "later", "soon" (please specify exact time)

### Be Clear About Task Content

Make it clear what KIRA should do when the scheduled task runs:

```
# Good example
"Tomorrow at 9am share today's task list in team channel"

# Ambiguous example
"Do something tomorrow morning"
```

### Recurring Tasks

Setting up regular tasks as recurring schedules is convenient:

- Daily morning schedule reminder
- Weekly Friday report
- Monthly 1st review

---

## ⚠️ Limitations

- Scheduled tasks only run when KIRA server is running
- Cannot schedule for past times
- Complex conditional scheduling (e.g., "notify me if it rains") is not supported

---

## ❓ Next Steps

- [Task Execution](/features/tasks) - Available tasks
- [Memory System](/features/memory) - Context utilization
