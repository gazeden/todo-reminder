import asyncio

import streamlit as st

from components.forms import task_form
from components.tables import (
    format_task_schedule,
    paginated_table,
    task_summary_stats,
    tasks_card_list,
    tasks_table,
)
from config import settings
from services.api_client import get_api_client
from utils.formatting import display_error, display_success
from utils.navigation import show_sidebar
from utils.session import require_authentication

# Page config
st.set_page_config(
    page_title=f"Tasks - {settings.APP_TITLE}", page_icon="📝", layout="wide"
)

require_authentication()
show_sidebar()

st.title("📝 Task Management")

api_client = get_api_client()

# Initialize session state
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None

if "delete_task_id" not in st.session_state:
    st.session_state.delete_task_id = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "cards"  # 'cards' or 'table'


# Fetch tasks
@st.cache_data(ttl=30)
def fetch_tasks(status_filter=None):
    """Fetch all tasks."""
    try:
        result = asyncio.run(
            api_client.get_tasks(
                limit=1000, status=status_filter if status_filter != "all" else None
            )
        )
        return result.get("tasks", [])
    except Exception as e:
        st.error(f"Failed to load tasks: {str(e)}")
        return []


# Action buttons
col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

with col1:
    if st.button("➕ Create New Task", use_container_width=True):
        st.session_state.show_create_form = not st.session_state.show_create_form
        st.session_state.edit_task_id = None

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col3:
    # View mode toggle
    view_mode = st.selectbox(
        "View",
        options=["cards", "table", "compact"],
        format_func=lambda x: {
            "cards": "📋 Cards",
            "table": "📊 Table",
            "compact": "📝 Compact",
        }[x],
        key="view_mode_select",
        label_visibility="collapsed",
    )
    st.session_state.view_mode = view_mode

st.markdown("---")

# Create form
if st.session_state.show_create_form:
    with st.expander("✏️ Create New Task", expanded=True):

        def handle_create(data):
            try:
                with st.spinner("Creating task..."):
                    asyncio.run(api_client.create_task(data))
                    display_success("Task created successfully!")
                    st.session_state.show_create_form = False
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                display_error(f"Failed to create task: {str(e)}")

        task_form(on_submit=handle_create, form_key="create_task_form")

# Filter options
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    status_filter = st.selectbox(
        "Status",
        options=["all", "pending", "completed", "overdue"],
        format_func=lambda x: {
            "all": "All Tasks",
            "pending": "⏳ Pending",
            "completed": "✅ Completed",
            "overdue": "⚠️ Overdue",
        }[x],
        key="status_filter",
    )

with col2:
    schedule_filter = st.selectbox(
        "Schedule Type",
        options=["all", "one_time", "interval", "weekdays", "monthdays"],
        format_func=lambda x: {
            "all": "All Schedules",
            "one_time": "📌 One-time",
            "interval": "⏱️ Interval",
            "weekdays": "📅 Weekdays",
            "monthdays": "📆 Month days",
        }[x],
        key="schedule_filter",
    )

with col3:
    sort_by = st.selectbox(
        "Sort By",
        options=["due_date", "created", "updated", "title"],
        format_func=lambda x: {
            "due_date": "📅 Due Date",
            "created": "🆕 Created",
            "updated": "🔄 Updated",
            "title": "🔤 Title",
        }[x],
        key="sort_by",
    )

with col4:
    search_query = st.text_input(
        "Search",
        placeholder="🔍 Search tasks...",
        key="search_tasks",
        label_visibility="collapsed",
    )

# Load tasks
tasks = fetch_tasks(status_filter if status_filter != "all" else None)

# Apply schedule filter
if schedule_filter != "all":
    if schedule_filter == "one_time":
        tasks = [t for t in tasks if not t.get("is_recurring")]
    elif schedule_filter == "interval":
        tasks = [
            t
            for t in tasks
            if t.get("recurrence_interval") and t.get("recurrence_unit")
        ]
    elif schedule_filter == "weekdays":
        tasks = [t for t in tasks if t.get("specific_days_of_week")]
    elif schedule_filter == "monthdays":
        tasks = [t for t in tasks if t.get("specific_days_of_month")]

# Apply search filter
if search_query:
    tasks = [
        t
        for t in tasks
        if search_query.lower() in t["title"].lower()
        or (t.get("description") and search_query.lower() in t["description"].lower())
    ]

# Sort tasks
if sort_by == "due_date":
    tasks = sorted(tasks, key=lambda x: x.get("next_due_date") or "9999-12-31")
elif sort_by == "created":
    tasks = sorted(tasks, key=lambda x: x["created_at"], reverse=True)
elif sort_by == "updated":
    tasks = sorted(tasks, key=lambda x: x["updated_at"], reverse=True)
elif sort_by == "title":
    tasks = sorted(tasks, key=lambda x: x["title"].lower())

# Display count and summary
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"**Showing {len(tasks)} task(s)**")

with col2:
    if tasks:
        with st.expander("📊 Summary Stats"):
            task_summary_stats(tasks)

if not tasks:
    st.info("No tasks found. Create your first task!")
    st.stop()


# Define action callbacks
def handle_complete(task_id):
    try:
        with st.spinner("Completing task..."):
            asyncio.run(api_client.complete_task(task_id))
            display_success("Task completed!")
            st.cache_data.clear()
            st.rerun()
    except Exception as e:
        display_error(f"Failed to complete task: {str(e)}")


def handle_edit(task_id):
    st.session_state.edit_task_id = task_id
    st.session_state.show_create_form = False
    st.rerun()


def handle_delete(task_id):
    st.session_state.delete_task_id = task_id
    st.rerun()


# Display tasks based on view mode
st.markdown("---")

if st.session_state.view_mode == "table":
    # Table view
    tasks_table(
        tasks=tasks,
        on_edit=handle_edit,
        on_delete=handle_delete,
        on_complete=handle_complete,
        show_actions=True,
    )

elif st.session_state.view_mode == "compact":
    # Compact card view with pagination
    page_tasks = paginated_table(
        tasks, page_size=settings.DEFAULT_PAGE_SIZE, key="tasks_page"
    )
    tasks_card_list(
        tasks=page_tasks,
        on_edit=handle_edit,
        on_delete=handle_delete,
        on_complete=handle_complete,
        show_actions=True,
        compact=True,
    )

else:  # cards view (default)
    # Full card view with pagination
    page_tasks = paginated_table(
        tasks, page_size=settings.DEFAULT_PAGE_SIZE, key="tasks_page"
    )
    tasks_card_list(
        tasks=page_tasks,
        on_edit=handle_edit,
        on_delete=handle_delete,
        on_complete=handle_complete,
        show_actions=True,
        compact=False,
    )

# Edit modal
if st.session_state.edit_task_id:
    task_to_edit = next(
        (task for task in tasks if task["id"] == st.session_state.edit_task_id), None
    )

    if task_to_edit:
        with st.expander("✏️ Edit Task", expanded=True):

            def handle_update(data):
                try:
                    with st.spinner("Updating task..."):
                        asyncio.run(
                            api_client.update_task(st.session_state.edit_task_id, data)
                        )
                        display_success("Task updated successfully!")
                        st.session_state.edit_task_id = None
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    display_error(f"Failed to update task: {str(e)}")

            task_form(
                task=task_to_edit,
                on_submit=handle_update,
                form_key=f"edit_task_form_{st.session_state.edit_task_id}",
            )

            if st.button("Cancel", key="cancel_edit"):
                st.session_state.edit_task_id = None
                st.rerun()

# Delete confirmation
if st.session_state.delete_task_id:
    task_to_delete = next(
        (task for task in tasks if task["id"] == st.session_state.delete_task_id), None
    )

    if task_to_delete:
        st.warning(f"⚠️ Are you sure you want to delete **{task_to_delete['title']}**?")

        # Show task details
        st.caption(f"Schedule: {format_task_schedule(task_to_delete)}")

        col1, col2, col3 = st.columns([1, 1, 4])

        with col1:
            if st.button("✅ Confirm Delete", type="primary", key="confirm_delete"):
                try:
                    with st.spinner("Deleting task..."):
                        asyncio.run(
                            api_client.delete_task(st.session_state.delete_task_id)
                        )
                        display_success("Task deleted successfully!")
                        st.session_state.delete_task_id = None
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    display_error(f"Failed to delete task: {str(e)}")

        with col2:
            if st.button("❌ Cancel", key="cancel_delete"):
                st.session_state.delete_task_id = None
                st.rerun()
