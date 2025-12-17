from datetime import datetime
from typing import Any, Callable, Dict, Optional

import streamlit as st


def task_form(
    task: Optional[Dict[str, Any]] = None,
    on_submit: Optional[Callable] = None,
    form_key: str = "task_form",
) -> None:
    """
    Reusable task form component with flexible scheduling.

    Supports:
    - One-time tasks
    - Interval-based: Every N days/weeks/months
    - Specific weekdays: Every Tuesday, Thursday
    - Specific month days: 1st and 15th of month
    - Combinations: Every 2 weeks on Monday
    """
    is_edit = task is not None

    with st.form(form_key):
        st.subheader("✏️ Task Details" if is_edit else "➕ Create New Task")

        # Basic info
        title = st.text_input(
            "Task Title *",
            value=task.get("title", "") if task else "",
            placeholder="e.g., Water plants, Team meeting, Pay rent",
            max_chars=200,
        )

        description = st.text_area(
            "Description",
            value=task.get("description", "") if task else "",
            placeholder="Add details about this task (optional)",
            max_chars=2000,
            height=100,
        )

        st.markdown("---")
        st.subheader("🔄 Schedule")

        # Recurring toggle
        is_recurring = st.checkbox(
            "Recurring Task",
            value=task.get("is_recurring", False) if task else False,
            help="Task repeats on a schedule",
        )

        if is_recurring:
            # Choose scheduling method
            schedule_method = st.radio(
                "Schedule Type",
                options=["interval", "specific_weekdays", "specific_monthdays"],
                format_func=lambda x: {
                    "interval": "⏱️ Every N days/weeks/months",
                    "specific_weekdays": "📅 Specific days of the week",
                    "specific_monthdays": "📆 Specific days of the month",
                }[x],
                horizontal=True,
                key=f"{form_key}_schedule_method",
            )

            recurrence_interval = None
            recurrence_unit = None
            specific_days_of_week = None
            specific_days_of_month = None

            if schedule_method == "interval":
                col1, col2 = st.columns([1, 2])

                with col1:
                    recurrence_interval = st.number_input(
                        "Repeat every",
                        min_value=1,
                        max_value=999,
                        value=task.get("recurrence_interval", 1) if task else 1,
                        help="How often to repeat",
                    )

                with col2:
                    recurrence_unit = st.selectbox(
                        "Time unit",
                        options=["days", "weeks", "months"],
                        format_func=lambda x: {
                            "days": f"Day{'s' if recurrence_interval != 1 else ''}",
                            "weeks": f"Week{'s' if recurrence_interval != 1 else ''}",
                            "months": f"Month{'s' if recurrence_interval != 1 else ''}",
                        }[x],
                        index=["days", "weeks", "months"].index(
                            task.get("recurrence_unit", "days") if task else "days"
                        ),
                    )

                # Preview
                st.info(
                    f"📅 Task will repeat every {recurrence_interval} {recurrence_unit}"
                )

            elif schedule_method == "specific_weekdays":
                st.markdown("**Select days of the week:**")

                days_map = {
                    "Monday": 0,
                    "Tuesday": 1,
                    "Wednesday": 2,
                    "Thursday": 3,
                    "Friday": 4,
                    "Saturday": 5,
                    "Sunday": 6,
                }

                # Get existing selections
                existing_days = task.get("specific_days_of_week", []) if task else []

                # Create checkboxes for each day
                cols = st.columns(7)
                selected_days = []

                for idx, (day_name, day_num) in enumerate(days_map.items()):
                    with cols[idx]:
                        if st.checkbox(
                            day_name[:3],  # Mon, Tue, etc.
                            value=day_num in existing_days,
                            key=f"{form_key}_day_{day_num}",
                            help=day_name,
                        ):
                            selected_days.append(day_num)

                specific_days_of_week = selected_days if selected_days else None

                # Optional: Repeat every N weeks
                col1, col2 = st.columns([1, 3])
                with col1:
                    use_week_interval = st.checkbox(
                        "Every N weeks",
                        value=task.get("recurrence_interval") is not None
                        if task
                        else False,
                        key=f"{form_key}_use_week_interval",
                    )

                if use_week_interval:
                    with col2:
                        recurrence_interval = st.number_input(
                            "Repeat every N weeks",
                            min_value=1,
                            max_value=52,
                            value=task.get("recurrence_interval", 1) if task else 1,
                        )
                        recurrence_unit = "weeks"

                # Preview
                if selected_days:
                    day_names = [
                        list(days_map.keys())[d] for d in sorted(selected_days)
                    ]
                    interval_text = (
                        f" (every {recurrence_interval} weeks)"
                        if use_week_interval and recurrence_interval > 1
                        else ""
                    )
                    st.info(
                        f"📅 Task will repeat every {', '.join(day_names)}{interval_text}"
                    )
                else:
                    st.warning("⚠️ Please select at least one day")

            elif schedule_method == "specific_monthdays":
                st.markdown("**Select days of the month:**")

                # Get existing selections
                existing_days = task.get("specific_days_of_month", []) if task else []

                # Create number inputs or multiselect
                selected_month_days = st.multiselect(
                    "Days of month (1-31)",
                    options=list(range(1, 32)),
                    default=existing_days,
                    format_func=lambda x: f"{x}{'st' if x == 1 else 'nd' if x == 2 else 'rd' if x == 3 else 'th'}",
                    help="Select which days of the month (e.g., 1st and 15th)",
                    key=f"{form_key}_month_days",
                )

                specific_days_of_month = (
                    selected_month_days if selected_month_days else None
                )

                # Optional: Every N months
                col1, col2 = st.columns([1, 3])
                with col1:
                    use_month_interval = st.checkbox(
                        "Every N months",
                        value=task.get("recurrence_interval") is not None
                        if task
                        else False,
                        key=f"{form_key}_use_month_interval",
                    )

                if use_month_interval:
                    with col2:
                        recurrence_interval = st.number_input(
                            "Repeat every N months",
                            min_value=1,
                            max_value=12,
                            value=task.get("recurrence_interval", 1) if task else 1,
                        )
                        recurrence_unit = "months"

                # Preview
                if selected_month_days:
                    day_text = ", ".join(
                        [
                            f"{d}{'st' if d == 1 else 'nd' if d == 2 else 'rd' if d == 3 else 'th'}"
                            for d in sorted(selected_month_days)
                        ]
                    )
                    interval_text = (
                        f" (every {recurrence_interval} months)"
                        if use_month_interval and recurrence_interval > 1
                        else ""
                    )
                    st.info(
                        f"📅 Task will repeat on the {day_text} of each month{interval_text}"
                    )
                else:
                    st.warning("⚠️ Please select at least one day")

        else:
            # One-time task
            recurrence_interval = None
            recurrence_unit = None
            specific_days_of_week = None
            specific_days_of_month = None
            st.info("📅 This is a one-time task")

        st.markdown("---")
        st.subheader("⏰ Reminder Settings")

        col1, col2 = st.columns(2)

        with col1:
            reminder_enabled = st.checkbox(
                "Enable Reminders",
                value=task.get("reminder_enabled", True) if task else True,
            )

        with col2:
            if reminder_enabled:
                reminder_time = st.time_input(
                    "Reminder Time",
                    value=datetime.strptime(
                        task.get("reminder_time", "09:00"), "%H:%M"
                    ).time()
                    if task and task.get("reminder_time")
                    else datetime.strptime("09:00", "%H:%M").time(),
                    help="Time of day for reminders",
                )
            else:
                reminder_time = None

        # Additional reminder options
        if reminder_enabled:
            reminder_minutes_before = st.number_input(
                "Additional reminder (minutes before)",
                min_value=0,
                max_value=1440,
                value=task.get("reminder_minutes_before", 0) if task else 0,
                help="Send an additional reminder N minutes before due time (0 = disabled)",
            )
        else:
            reminder_minutes_before = None

        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col1:
            is_active = st.checkbox(
                "Active",
                value=task.get("is_active", True) if task else True,
                help="Inactive tasks won't trigger reminders",
            )

        with col2:
            submitted = st.form_submit_button(
                "Update Task" if is_edit else "Create Task",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not title:
                st.error("Task title is required")
                return

            # Validation for recurring tasks
            if is_recurring:
                if schedule_method == "interval":
                    if not recurrence_interval or not recurrence_unit:
                        st.error("Please specify recurrence interval and unit")
                        return
                elif schedule_method == "specific_weekdays":
                    if not specific_days_of_week:
                        st.error("Please select at least one day of the week")
                        return
                elif schedule_method == "specific_monthdays":
                    if not specific_days_of_month:
                        st.error("Please select at least one day of the month")
                        return

            data = {
                "title": title,
                "description": description if description else None,
                "is_recurring": is_recurring,
                "recurrence_interval": recurrence_interval,
                "recurrence_unit": recurrence_unit,
                "specific_days_of_week": specific_days_of_week,
                "specific_days_of_month": specific_days_of_month,
                "reminder_enabled": reminder_enabled,
                "reminder_time": reminder_time.strftime("%H:%M")
                if reminder_time
                else None,
                "reminder_minutes_before": reminder_minutes_before
                if reminder_minutes_before and reminder_minutes_before > 0
                else None,
                "is_active": is_active,
            }

            if on_submit:
                on_submit(data)


def user_profile_form(
    user: Dict[str, Any],
    on_submit: Optional[Callable] = None,
    form_key: str = "profile_form",
) -> None:
    """
    User profile edit form component.

    Args:
        user: Current user data
        on_submit: Callback function to handle form submission
        form_key: Unique key for the form
    """
    with st.form(form_key):
        st.subheader("👤 Edit Profile")

        col1, col2 = st.columns(2)

        with col1:
            email = st.text_input(
                "Email *",
                value=user.get("email", ""),
                disabled=True,  # Email usually can't be changed
                help="Contact support to change email",
            )

            username = st.text_input(
                "Username *",
                value=user.get("username", ""),
                max_chars=50,
                help="Your unique username",
            )

        with col2:
            full_name = st.text_input(
                "Full Name",
                value=user.get("full_name", "") if user.get("full_name") else "",
                max_chars=100,
                help="Your full name (optional)",
            )

            # Password change section
            change_password = st.checkbox(
                "Change Password", help="Check this to set a new password"
            )

        if change_password:
            st.markdown("---")
            st.markdown("**🔒 Change Password**")

            col_a, col_b = st.columns(2)

            with col_a:
                new_password = st.text_input(
                    "New Password",
                    type="password",
                    help="Minimum 8 characters with letters and numbers",
                )

            with col_b:
                confirm_password = st.text_input("Confirm Password", type="password")

        st.markdown("---")

        col1, col2 = st.columns([1, 3])

        with col1:
            submitted = st.form_submit_button(
                "💾 Save Changes", type="primary", use_container_width=True
            )

        if submitted:
            # Validation
            from utils.validators import validate_password, validate_username

            if not username:
                st.error("Username is required")
                return

            is_valid, error = validate_username(username)
            if not is_valid:
                st.error(error)
                return

            if change_password:
                if not new_password or not confirm_password:
                    st.error("Please enter and confirm your new password")
                    return

                is_valid, error = validate_password(new_password)
                if not is_valid:
                    st.error(error)
                    return

                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return

            # Prepare data
            data = {"username": username, "full_name": full_name if full_name else None}

            if change_password:
                data["password"] = new_password

            if on_submit:
                on_submit(data)
