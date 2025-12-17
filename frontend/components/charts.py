from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def task_completion_chart(completions: List[Dict[str, Any]]) -> None:
    """
    Display task completion timeline.

    Args:
        completions: List of task completion records
    """
    if not completions:
        st.info("No completion data to display")
        return

    # Prepare data
    dates = [
        datetime.fromisoformat(c["completed_at"].replace("Z", "+00:00"))
        for c in completions
    ]
    df = pd.DataFrame({"date": dates})
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Count completions per day
    daily_counts = df.groupby("date").size().reset_index(name="count")

    # Create chart
    fig = px.bar(
        daily_counts,
        x="date",
        y="count",
        title="Tasks Completed Over Time",
        labels={"date": "Date", "count": "Tasks Completed"},
    )

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Tasks Completed", hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)


def task_status_chart(tasks: List[Dict[str, Any]]) -> None:
    """
    Display task status distribution.

    Args:
        tasks: List of task dictionaries
    """
    if not tasks:
        st.info("No data to display")
        return

    # Count by status
    from collections import Counter

    status_counts = Counter(task.get("status", "pending") for task in tasks)

    # Create pie chart
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[s.title() for s in status_counts.keys()],
                values=list(status_counts.values()),
                hole=0.3,
                marker_colors=["#ffa500", "#00cc96", "#ef553b", "#636efa"],
            )
        ]
    )

    fig.update_layout(title="Task Status Distribution", showlegend=True)

    st.plotly_chart(fig, use_container_width=True)


def streak_display(streak_days: int) -> None:
    """
    Display completion streak with visual indicator.

    Args:
        streak_days: Number of consecutive days with completions
    """
    if streak_days == 0:
        st.info("🔥 Start your streak! Complete a task today.")
    elif streak_days == 1:
        st.success("🔥 You have a 1-day streak! Keep it up!")
    else:
        st.success(f"🔥 Amazing! You're on a {streak_days}-day streak!")

    # Visual streak indicator
    if streak_days > 0:
        progress_bar_value = min(streak_days / 30, 1.0)  # Cap at 30 days for display
        st.progress(progress_bar_value)

        if streak_days >= 7:
            st.balloons()


def task_schedule_summary(task: Dict[str, Any]) -> None:
    """
    Display a human-readable summary of task schedule.

    Args:
        task: Task dictionary
    """
    if not task.get("is_recurring"):
        st.info("📅 One-time task")
        return

    schedule_parts = []

    # Interval-based
    if task.get("recurrence_interval") and task.get("recurrence_unit"):
        interval = task["recurrence_interval"]
        unit = task["recurrence_unit"]

        if interval == 1:
            schedule_parts.append(f"Every {unit.rstrip('s')}")
        else:
            schedule_parts.append(f"Every {interval} {unit}")

    # Specific weekdays
    if task.get("specific_days_of_week"):
        days_map = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        }
        day_names = [days_map[d] for d in sorted(task["specific_days_of_week"])]

        if len(day_names) == 7:
            schedule_parts.append("every day")
        elif len(day_names) == 1:
            schedule_parts.append(f"on {day_names[0]}s")
        else:
            schedule_parts.append(f"on {', '.join(day_names[:-1])} and {day_names[-1]}")

    # Specific month days
    if task.get("specific_days_of_month"):
        days = sorted(task["specific_days_of_month"])

        def ordinal(n: int) -> str:
            return (
                f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"
            )

        day_strs = [ordinal(d) for d in days]

        if len(day_strs) == 1:
            schedule_parts.append(f"on the {day_strs[0]} of each month")
        else:
            schedule_parts.append(
                f"on the {', '.join(day_strs[:-1])} and {day_strs[-1]} of each month"
            )

    # Combine parts
    if schedule_parts:
        schedule_text = " ".join(schedule_parts)
        st.success(f"🔄 Repeats: {schedule_text.capitalize()}")

    # Reminder info
    if task.get("reminder_enabled") and task.get("reminder_time"):
        st.info(f"⏰ Reminder at {task['reminder_time']}")

        if task.get("reminder_minutes_before"):
            st.caption(
                f"   + Additional reminder {task['reminder_minutes_before']} minutes before"
            )


def frequency_breakdown_chart(tasks: List[Dict[str, Any]]) -> None:
    """
    Display breakdown of task scheduling patterns.

    Args:
        tasks: List of task dictionaries
    """
    if not tasks:
        st.info("No data to display")
        return

    import pandas as pd
    import plotly.express as px

    # Categorize tasks
    categories = {
        "One-time": 0,
        "Daily": 0,
        "Weekly": 0,
        "Monthly": 0,
        "Custom Days": 0,
        "Custom Interval": 0,
    }

    for task in tasks:
        if not task.get("is_recurring"):
            categories["One-time"] += 1
        elif task.get("specific_days_of_week"):
            if len(task["specific_days_of_week"]) == 7:
                categories["Daily"] += 1
            else:
                categories["Custom Days"] += 1
        elif task.get("specific_days_of_month"):
            categories["Custom Days"] += 1
        elif task.get("recurrence_interval") and task.get("recurrence_unit"):
            interval = task["recurrence_interval"]
            unit = task["recurrence_unit"]

            if interval == 1 and unit == "days":
                categories["Daily"] += 1
            elif interval == 1 and unit == "weeks":
                categories["Weekly"] += 1
            elif interval == 1 and unit == "months":
                categories["Monthly"] += 1
            else:
                categories["Custom Interval"] += 1

    # Filter out zero categories
    categories = {k: v for k, v in categories.items() if v > 0}

    if not categories:
        st.info("No scheduling data available")
        return

    df = pd.DataFrame(
        {"Schedule Type": list(categories.keys()), "Count": list(categories.values())}
    )

    fig = px.bar(
        df,
        x="Schedule Type",
        y="Count",
        title="Task Schedule Distribution",
        labels={"Count": "Number of Tasks"},
        color="Schedule Type",
        text="Count",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)

    st.plotly_chart(fig, use_container_width=True)
