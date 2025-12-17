from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import streamlit as st


def tasks_table(
    tasks: List[Dict[str, Any]],
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    show_actions: bool = True,
) -> None:
    """
    Display tasks in a table with actions.

    Args:
        tasks: List of task dictionaries
        on_edit: Callback for edit action
        on_delete: Callback for delete action
        on_complete: Callback for complete action
        show_actions: Whether to show action buttons
    """
    if not tasks:
        st.info("No tasks found")
        return

    # Convert to DataFrame for display
    df_data = []
    for task in tasks:
        # Format schedule
        schedule_text = format_task_schedule(task)

        # Format next due date
        next_due = ""
        if task.get("next_due_date"):
            next_due = pd.to_datetime(task["next_due_date"]).strftime("%Y-%m-%d %H:%M")

        df_data.append(
            {
                "ID": task["id"],
                "Title": task["title"],
                "Schedule": schedule_text,
                "Next Due": next_due,
                "Status": format_task_status(task.get("status", "pending")),
                "Created": pd.to_datetime(task["created_at"]).strftime("%Y-%m-%d"),
            }
        )

    df = pd.DataFrame(df_data)

    # Display dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Title": st.column_config.TextColumn("Title", width="medium"),
            "Schedule": st.column_config.TextColumn("Schedule", width="large"),
            "Next Due": st.column_config.TextColumn("Next Due", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Created": st.column_config.TextColumn("Created", width="small"),
        },
    )

    # Action buttons
    if show_actions and (on_edit or on_delete or on_complete):
        st.markdown("### Actions")

        selected_id = st.selectbox(
            "Select task to perform action",
            options=[task["id"] for task in tasks],
            format_func=lambda x: next(
                task["title"] for task in tasks if task["id"] == x
            ),
            key="tasks_table_select",
        )

        # Get selected task
        selected_task = next(task for task in tasks if task["id"] == selected_id)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if on_complete and selected_task.get("status") == "pending":
                if st.button(
                    "✓ Complete", key="tasks_table_complete", use_container_width=True
                ):
                    on_complete(selected_id)

        with col2:
            if on_edit and st.button(
                "✏️ Edit", key="tasks_table_edit", use_container_width=True
            ):
                on_edit(selected_id)

        with col3:
            if on_delete and st.button(
                "🗑️ Delete", key="tasks_table_delete", use_container_width=True
            ):
                on_delete(selected_id)


def tasks_card_list(
    tasks: List[Dict[str, Any]],
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    show_actions: bool = True,
    compact: bool = False,
) -> None:
    """
    Display tasks as cards with schedule details.

    Args:
        tasks: List of task dictionaries
        on_edit: Callback for edit action
        on_delete: Callback for delete action
        on_complete: Callback for complete action
        show_actions: Whether to show action buttons
        compact: Use compact card layout
    """
    if not tasks:
        st.info("No tasks found")
        return

    for task in tasks:
        with st.container():
            if compact:
                _render_compact_task_card(
                    task, on_edit, on_delete, on_complete, show_actions
                )
            else:
                _render_full_task_card(
                    task, on_edit, on_delete, on_complete, show_actions
                )

            st.markdown("---")


def _render_full_task_card(
    task: Dict[str, Any],
    on_edit: Optional[Callable],
    on_delete: Optional[Callable],
    on_complete: Optional[Callable],
    show_actions: bool,
) -> None:
    """Render full task card with all details."""
    col1, col2 = st.columns([5, 1])

    with col1:
        # Status emoji and title
        status_emoji = {
            "pending": "⏳",
            "completed": "✅",
            "overdue": "⚠️",
            "snoozed": "😴",
        }.get(task.get("status", "pending"), "⏳")

        st.markdown(f"### {status_emoji} {task['title']}")

        # Description
        if task.get("description"):
            st.markdown(task["description"])

        # Schedule summary
        schedule_summary = get_schedule_summary(task)
        if schedule_summary:
            st.success(schedule_summary)

        # Metadata row
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if task.get("next_due_date"):
                from utils.formatting import format_relative_time

                st.caption(
                    f"📅 Next due: {format_relative_time(task['next_due_date'])}"
                )
            else:
                st.caption("📅 No due date")

        with col_b:
            if task.get("reminder_enabled") and task.get("reminder_time"):
                st.caption(f"⏰ Reminder: {task['reminder_time']}")
                if task.get("reminder_minutes_before"):
                    st.caption(f"   + {task['reminder_minutes_before']}min before")
            else:
                st.caption("🔕 No reminder")

        with col_c:
            if task.get("last_completed_date"):
                from utils.formatting import format_relative_time

                st.caption(
                    f"✓ Last: {format_relative_time(task['last_completed_date'])}"
                )

    with col2:
        # Action buttons
        if show_actions:
            if on_complete and task.get("status") == "pending":
                if st.button(
                    "✓",
                    key=f"complete_card_{task['id']}",
                    help="Complete",
                    use_container_width=True,
                ):
                    on_complete(task["id"])

            if on_edit:
                if st.button(
                    "✏️",
                    key=f"edit_card_{task['id']}",
                    help="Edit",
                    use_container_width=True,
                ):
                    on_edit(task["id"])

            if on_delete:
                if st.button(
                    "🗑️",
                    key=f"delete_card_{task['id']}",
                    help="Delete",
                    use_container_width=True,
                ):
                    on_delete(task["id"])


def _render_compact_task_card(
    task: Dict[str, Any],
    on_edit: Optional[Callable],
    on_delete: Optional[Callable],
    on_complete: Optional[Callable],
    show_actions: bool,
) -> None:
    """Render compact task card for lists."""
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        # Status emoji and title
        status_emoji = {
            "pending": "⏳",
            "completed": "✅",
            "overdue": "⚠️",
            "snoozed": "😴",
        }.get(task.get("status", "pending"), "⏳")

        st.markdown(f"{status_emoji} **{task['title']}**")

        # Brief description
        if task.get("description"):
            desc = task["description"]
            if len(desc) > 60:
                desc = desc[:60] + "..."
            st.caption(desc)

    with col2:
        # Schedule info
        schedule_text = format_task_schedule(task, compact=True)
        st.caption(schedule_text)

        # Next due
        if task.get("next_due_date"):
            from utils.formatting import format_relative_time

            st.caption(f"Due: {format_relative_time(task['next_due_date'])}")

    with col3:
        # Action buttons
        if show_actions:
            if on_complete and task.get("status") == "pending":
                if st.button(
                    "✓", key=f"complete_compact_{task['id']}", help="Complete"
                ):
                    on_complete(task["id"])


def paginated_table(
    data: List[Dict[str, Any]], page_size: int = 20, key: str = "paginated_table"
) -> List[Dict[str, Any]]:
    """
    Display data with pagination controls.

    Args:
        data: List of data dictionaries
        page_size: Number of items per page
        key: Unique key for pagination state

    Returns:
        Current page data
    """
    # Initialize page number in session state
    page_key = f"{key}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    total_pages = max(1, (len(data) + page_size - 1) // page_size)
    current_page = st.session_state[page_key]

    # Ensure current page is valid
    if current_page >= total_pages:
        current_page = 0
        st.session_state[page_key] = 0

    # Calculate slice indices
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(data))

    # Display current page data
    page_data = data[start_idx:end_idx]

    # Pagination controls
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First", key=f"{key}_first", disabled=current_page == 0):
            st.session_state[page_key] = 0
            st.rerun()

    with col2:
        if st.button("◀️ Prev", key=f"{key}_prev", disabled=current_page == 0):
            st.session_state[page_key] = current_page - 1
            st.rerun()

    with col3:
        st.markdown(
            f"<div style='text-align: center; padding-top: 8px;'>"
            f"Page {current_page + 1} of {total_pages} "
            f"({len(data)} total items)</div>",
            unsafe_allow_html=True,
        )

    with col4:
        if st.button(
            "Next ▶️", key=f"{key}_next", disabled=current_page >= total_pages - 1
        ):
            st.session_state[page_key] = current_page + 1
            st.rerun()

    with col5:
        if st.button(
            "Last ⏭️", key=f"{key}_last", disabled=current_page >= total_pages - 1
        ):
            st.session_state[page_key] = total_pages - 1
            st.rerun()

    return page_data


def format_task_schedule(task: Dict[str, Any], compact: bool = False) -> str:
    """
    Format task schedule as readable text.

    Args:
        task: Task dictionary
        compact: Use compact format

    Returns:
        Formatted schedule string
    """
    if not task.get("is_recurring"):
        return "📌 One-time" if compact else "One-time task"

    parts = []

    # Interval-based
    if task.get("recurrence_interval") and task.get("recurrence_unit"):
        interval = task["recurrence_interval"]
        unit = task["recurrence_unit"]

        if compact:
            if interval == 1:
                parts.append(f"Every {unit.rstrip('s')}")
            else:
                parts.append(f"Every {interval} {unit}")
        else:
            if interval == 1:
                parts.append(f"🔄 Every {unit.rstrip('s')}")
            else:
                parts.append(f"🔄 Every {interval} {unit}")

    # Specific weekdays
    if task.get("specific_days_of_week"):
        days_map = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun",
        }
        days_full = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        }

        day_nums = sorted(task["specific_days_of_week"])

        if len(day_nums) == 7:
            parts.append("📅 Daily" if compact else "📅 Every day")
        elif compact:
            day_names = [days_map[d] for d in day_nums]
            parts.append(f"📅 {', '.join(day_names)}")
        else:
            day_names = [days_full[d] for d in day_nums]
            if len(day_names) == 1:
                parts.append(f"📅 Every {day_names[0]}")
            elif len(day_names) == 2:
                parts.append(f"📅 Every {day_names[0]} and {day_names[1]}")
            else:
                parts.append(
                    f"📅 Every {', '.join(day_names[:-1])} and {day_names[-1]}"
                )

    # Specific month days
    if task.get("specific_days_of_month"):
        days = sorted(task["specific_days_of_month"])

        if compact:
            parts.append(f"📆 {len(days)} day{'s' if len(days) != 1 else ''}/month")
        else:

            def ordinal(n: int) -> str:
                return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"

            day_strs = [ordinal(d) for d in days]

            if len(day_strs) == 1:
                parts.append(f"📆 {day_strs[0]} of each month")
            elif len(day_strs) == 2:
                parts.append(f"📆 {day_strs[0]} and {day_strs[1]} of each month")
            else:
                parts.append(
                    f"📆 {', '.join(day_strs[:-1])} and {day_strs[-1]} of each month"
                )

    return (
        " ".join(parts) if parts else ("🔄 Recurring" if compact else "Recurring task")
    )


def get_schedule_summary(task: Dict[str, Any]) -> Optional[str]:
    """
    Get detailed schedule summary for display.

    Args:
        task: Task dictionary

    Returns:
        Formatted schedule summary or None
    """
    if not task.get("is_recurring"):
        return None

    schedule_parts = []

    # Interval-based
    if task.get("recurrence_interval") and task.get("recurrence_unit"):
        interval = task["recurrence_interval"]
        unit = task["recurrence_unit"]

        if interval == 1:
            schedule_parts.append(f"Repeats every {unit.rstrip('s')}")
        else:
            schedule_parts.append(f"Repeats every {interval} {unit}")

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
            schedule_parts.append("on every day of the week")
        elif len(day_names) == 5 and set(task["specific_days_of_week"]) == {
            0,
            1,
            2,
            3,
            4,
        }:
            schedule_parts.append("on weekdays")
        elif len(day_names) == 2 and set(task["specific_days_of_week"]) == {5, 6}:
            schedule_parts.append("on weekends")
        elif len(day_names) == 1:
            schedule_parts.append(f"on {day_names[0]}s")
        elif len(day_names) == 2:
            schedule_parts.append(f"on {day_names[0]}s and {day_names[1]}s")
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
        elif len(day_strs) == 2:
            schedule_parts.append(
                f"on the {day_strs[0]} and {day_strs[1]} of each month"
            )
        else:
            schedule_parts.append(
                f"on the {', '.join(day_strs[:-1])} and {day_strs[-1]} of each month"
            )

    if schedule_parts:
        return "🔄 " + " ".join(schedule_parts).capitalize()

    return "🔄 Recurring task"


def format_task_status(status: str) -> str:
    """
    Format task status with emoji.

    Args:
        status: Task status string

    Returns:
        Formatted status
    """
    status_map = {
        "pending": "⏳ Pending",
        "completed": "✅ Completed",
        "overdue": "⚠️ Overdue",
        "snoozed": "😴 Snoozed",
    }
    return status_map.get(status.lower(), status.capitalize())


def task_summary_stats(tasks: List[Dict[str, Any]]) -> None:
    """
    Display summary statistics for a list of tasks.

    Args:
        tasks: List of task dictionaries
    """
    if not tasks:
        return

    # Count by type
    one_time = sum(1 for t in tasks if not t.get("is_recurring"))
    recurring = sum(1 for t in tasks if t.get("is_recurring"))

    # Count by status
    pending = sum(1 for t in tasks if t.get("status") == "pending")
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    overdue = sum(1 for t in tasks if t.get("status") == "overdue")

    # Count by schedule type
    interval_based = sum(
        1 for t in tasks if t.get("recurrence_interval") and t.get("recurrence_unit")
    )
    weekday_based = sum(1 for t in tasks if t.get("specific_days_of_week"))
    monthday_based = sum(1 for t in tasks if t.get("specific_days_of_month"))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**By Type**")
        st.caption(f"📌 One-time: {one_time}")
        st.caption(f"🔄 Recurring: {recurring}")

    with col2:
        st.markdown("**By Status**")
        st.caption(f"⏳ Pending: {pending}")
        st.caption(f"✅ Completed: {completed}")
        if overdue > 0:
            st.caption(f"⚠️ Overdue: {overdue}")

    with col3:
        st.markdown("**By Schedule**")
        if interval_based > 0:
            st.caption(f"⏱️ Interval: {interval_based}")
        if weekday_based > 0:
            st.caption(f"📅 Weekdays: {weekday_based}")
        if monthday_based > 0:
            st.caption(f"📆 Month days: {monthday_based}")
