import streamlit as st

from config import settings

st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": "https://github.com/gazeden/todo-reminder/issues",
        "About": f"# {settings.APP_TITLE}\nVersion {settings.VERSION}",
    },
)


# Main page content
def main():
    """Main landing page."""

    # Check if user is authenticated
    if not st.session_state.get("authenticated", False):
        show_login_page()
    else:
        show_home_page()


def show_login_page():
    """Display login page for unauthenticated users."""

    st.title(f"Welcome to {settings.APP_TITLE}")

    st.markdown("""
    ### Your Personal Task Reminder Assistant

    Never forget important tasks again! Create flexible recurring reminders with:
    - ⏱️ Interval-based schedules (every N days/weeks/months)
    - 📅 Specific weekday patterns (e.g., every Tuesday and Thursday)
    - 📆 Monthly schedules (e.g., 1st and 15th of each month)
    - 🔔 Smart notifications at your preferred times
    """)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 Login")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")

            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("Login", use_container_width=True)
            with col_b:
                register = st.form_submit_button("Register", use_container_width=True)

            if submit:
                handle_login(email, password)

            if register:
                st.switch_page("pages/5_📝_Register.py")


def handle_login(email: str, password: str):
    """Handle login form submission."""
    import asyncio

    from services.api_client import get_api_client

    if not email or not password:
        st.error("Please enter both email and password")
        return

    try:
        with st.spinner("Logging in..."):
            api_client = get_api_client()
            result = asyncio.run(api_client.login(email, password))

            if result:
                st.session_state.authenticated = True
                st.session_state.user = result["user"]
                st.session_state.access_token = result["access_token"]

                # Set token in API client
                api_client.set_token(result["access_token"])

                st.success("Login successful!")
                st.rerun()
    except Exception as e:
        st.error(f"Login failed: {str(e)}")


def show_home_page():
    """Display home page for authenticated users."""
    st.title(f"Welcome back, {st.session_state.user.get('username', 'User')}! 👋")

    # Quick stats overview
    show_quick_stats()

    st.markdown("---")

    # Quick Actions
    st.markdown("## 🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px; color: white; text-align: center;">
            <h3>📊 Dashboard</h3>
            <p>View your productivity stats and upcoming tasks</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Dashboard", key="nav_dashboard", use_container_width=True):
            st.switch_page("pages/1_📊_Dashboard.py")

    with col2:
        st.markdown(
            """
        <div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 10px; color: white; text-align: center;">
            <h3>📝 Tasks</h3>
            <p>Manage all your recurring and one-time tasks</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Tasks", key="nav_tasks", use_container_width=True):
            st.switch_page("pages/2_📝_Tasks.py")

    with col3:
        st.markdown(
            """
        <div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 10px; color: white; text-align: center;">
            <h3>👤 Profile</h3>
            <p>Update your profile and account settings</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Profile", key="nav_profile", use_container_width=True):
            st.switch_page("pages/3_👤_Profile.py")

    st.markdown("---")

    # Due and overdue tasks
    show_urgent_tasks()

    st.markdown("---")

    # Recent Activity
    show_recent_activity()


def show_quick_stats():
    """Display quick statistics overview."""
    import asyncio

    from services.api_client import get_api_client

    try:
        api_client = get_api_client()

        # Fetch stats
        stats = asyncio.run(api_client.get_task_stats())

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Tasks", stats.get("total_tasks", 0), help="Total active tasks"
            )

        with col2:
            pending = stats.get("pending_tasks", 0)
            st.metric("Pending Tasks", pending, help="Tasks waiting to be completed")

        with col3:
            completed = stats.get("completed_today", 0)
            st.metric(
                "Completed Today",
                completed,
                delta=f"+{completed}" if completed > 0 else None,
                help="Tasks completed today",
            )

        with col4:
            streak = stats.get("streak_days", 0)
            st.metric(
                "🔥 Streak",
                f"{streak} day{'s' if streak != 1 else ''}",
                delta="+1" if streak > 0 else None,
                help="Consecutive days with completions",
            )

    except Exception as e:
        st.error(f"Failed to load stats: {str(e)}")


def show_urgent_tasks():
    """Display due and overdue tasks."""
    import asyncio

    from services.api_client import get_api_client
    from utils.formatting import format_relative_time

    try:
        api_client = get_api_client()

        due_tasks = asyncio.run(api_client.get_due_tasks())
        overdue_tasks = asyncio.run(api_client.get_overdue_tasks())

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⏰ Due Soon")
            if due_tasks:
                for task in due_tasks[:3]:  # Show top 3
                    with st.container():
                        col_a, col_b = st.columns([4, 1])

                        with col_a:
                            st.markdown(f"**{task['title']}**")

                            # Show schedule info
                            if task.get("is_recurring"):
                                schedule_icon = "🔄"
                                if task.get("specific_days_of_week"):
                                    schedule_icon = "📅"
                                elif task.get("specific_days_of_month"):
                                    schedule_icon = "📆"
                                st.caption(f"{schedule_icon} Recurring task")

                            if task.get("next_due_date"):
                                st.caption(
                                    f"Due: {format_relative_time(task['next_due_date'])}"
                                )

                        with col_b:
                            if st.button(
                                "✓",
                                key=f"complete_home_due_{task['id']}",
                                help="Complete",
                            ):
                                try:
                                    asyncio.run(api_client.complete_task(task["id"]))
                                    st.success("Completed!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {str(e)}")

                        st.markdown("---")

                if len(due_tasks) > 3:
                    st.caption(f"... and {len(due_tasks) - 3} more")
                    if st.button("View All Due Tasks", key="view_all_due"):
                        st.switch_page("pages/2_📝_Tasks.py")
            else:
                st.info("No tasks due soon")

        with col2:
            st.subheader("⚠️ Overdue")
            if overdue_tasks:
                for task in overdue_tasks[:3]:  # Show top 3
                    with st.container():
                        col_a, col_b = st.columns([4, 1])

                        with col_a:
                            st.markdown(f"**{task['title']}**")

                            if task.get("is_recurring"):
                                if task.get("recurrence_interval") and task.get(
                                    "recurrence_unit"
                                ):
                                    interval = task["recurrence_interval"]
                                    unit = task["recurrence_unit"]
                                    st.caption(f"🔄 Every {interval} {unit}")
                                elif task.get("specific_days_of_week"):
                                    st.caption("📅 Weekly schedule")

                            if task.get("next_due_date"):
                                st.caption(
                                    f"⚠️ Was due: {format_relative_time(task['next_due_date'])}"
                                )

                        with col_b:
                            if st.button(
                                "✓",
                                key=f"complete_home_overdue_{task['id']}",
                                help="Complete",
                            ):
                                try:
                                    asyncio.run(api_client.complete_task(task["id"]))
                                    st.success("Completed!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {str(e)}")

                        st.markdown("---")

                if len(overdue_tasks) > 3:
                    st.caption(f"... and {len(overdue_tasks) - 3} more")
                    if st.button("View All Overdue Tasks", key="view_all_overdue"):
                        st.switch_page("pages/2_📝_Tasks.py")
            else:
                st.success("No overdue tasks! Great job! 🎉")

    except Exception as e:
        st.error(f"Failed to load tasks: {str(e)}")


def show_recent_activity():
    """Display recent task activity."""
    import asyncio

    from services.api_client import get_api_client
    from utils.formatting import format_date

    st.subheader("🕐 Recent Activity")

    try:
        api_client = get_api_client()

        # Fetch recent tasks
        tasks_result = asyncio.run(api_client.get_tasks(limit=100))
        tasks = tasks_result.get("tasks", [])

        if not tasks:
            st.info("No tasks yet. Create your first task to get started!")
            if st.button("➕ Create First Task", key="create_first_task"):
                st.switch_page("pages/2_📝_Tasks.py")
            return

        # Sort by most recently updated
        recent_tasks = sorted(
            tasks,
            key=lambda x: x.get("updated_at", x.get("created_at", "")),
            reverse=True,
        )[:5]

        for task in recent_tasks:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    # Status emoji
                    status_emoji = {
                        "pending": "⏳",
                        "completed": "✅",
                        "overdue": "⚠️",
                    }.get(task.get("status", "pending"), "⏳")

                    st.markdown(f"{status_emoji} **{task['title']}**")

                    if task.get("description"):
                        st.caption(
                            task["description"][:80] + "..."
                            if len(task.get("description", "")) > 80
                            else task.get("description", "")
                        )

                with col2:
                    # Schedule info
                    if task.get("is_recurring"):
                        if task.get("recurrence_interval") and task.get(
                            "recurrence_unit"
                        ):
                            interval = task["recurrence_interval"]
                            unit = task["recurrence_unit"].rstrip("s")
                            if interval == 1:
                                st.caption(f"🔄 Every {unit}")
                            else:
                                st.caption(f"🔄 Every {interval} {unit}s")
                        elif task.get("specific_days_of_week"):
                            days_count = len(task["specific_days_of_week"])
                            st.caption(
                                f"📅 {days_count} day{'s' if days_count != 1 else ''}/week"
                            )
                        elif task.get("specific_days_of_month"):
                            days_count = len(task["specific_days_of_month"])
                            st.caption(
                                f"📆 {days_count} day{'s' if days_count != 1 else ''}/month"
                            )
                        else:
                            st.caption("🔄 Recurring")
                    else:
                        st.caption("📌 One-time")

                with col3:
                    st.caption(format_date(task["updated_at"], "%m/%d"))

                st.markdown("---")

        # View all button
        if len(tasks) > 5:
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button(
                    "View All Tasks", key="view_all_tasks", use_container_width=True
                ):
                    st.switch_page("pages/2_📝_Tasks.py")

    except Exception as e:
        st.error(f"Failed to load activity: {str(e)}")


if __name__ == "__main__":
    main()
