import asyncio

import streamlit as st

from components.charts import (
    frequency_breakdown_chart,
    streak_display,
    task_completion_chart,
    task_status_chart,
)
from components.tables import tasks_card_list
from config import settings
from services.api_client import get_api_client
from utils.navigation import show_sidebar
from utils.session import require_authentication

# Page config
st.set_page_config(
    page_title=f"Dashboard - {settings.APP_TITLE}", page_icon="📊", layout="wide"
)

require_authentication()
show_sidebar()

st.title("📊 Dashboard")
st.markdown("Overview of your tasks and productivity")

api_client = get_api_client()


@st.cache_data(ttl=60)
def fetch_dashboard_data():
    """Fetch all dashboard data."""
    try:
        stats = asyncio.run(api_client.get_task_stats())
        tasks_result = asyncio.run(api_client.get_tasks(limit=1000))
        due_tasks = asyncio.run(api_client.get_due_tasks())
        overdue_tasks = asyncio.run(api_client.get_overdue_tasks())

        return {
            "stats": stats,
            "tasks": tasks_result.get("tasks", []),
            "due_tasks": due_tasks,
            "overdue_tasks": overdue_tasks,
        }
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return None


# Load data
with st.spinner("Loading dashboard..."):
    data = fetch_dashboard_data()

if not data:
    st.stop()

stats = data["stats"]
tasks = data["tasks"]
due_tasks = data["due_tasks"]
overdue_tasks = data["overdue_tasks"]

# Key metrics
st.subheader("📈 Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Tasks", stats.get("total_tasks", 0), help="Total active tasks")

with col2:
    st.metric(
        "Pending", stats.get("pending_tasks", 0), help="Tasks waiting to be completed"
    )

with col3:
    st.metric(
        "Completed Today", stats.get("completed_today", 0), help="Tasks completed today"
    )

with col4:
    overdue_count = stats.get("overdue_tasks", 0)
    st.metric(
        "Overdue",
        overdue_count,
        delta=f"-{overdue_count}" if overdue_count > 0 else None,
        delta_color="inverse",
        help="Tasks past their due date",
    )

st.markdown("---")

# Streak display
st.subheader("🔥 Your Streak")
streak_display(stats.get("streak_days", 0))

st.markdown("---")

# Due and overdue tasks using card list
col1, col2 = st.columns(2)


def handle_complete_due(task_id):
    try:
        asyncio.run(api_client.complete_task(task_id))
        st.success("Task completed!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Failed: {str(e)}")


with col1:
    st.subheader("⏰ Due Soon")
    if due_tasks:
        # Show first 5 in compact mode
        tasks_card_list(
            tasks=due_tasks[:5],
            on_complete=handle_complete_due,
            show_actions=True,
            compact=True,
        )

        if len(due_tasks) > 5:
            st.caption(f"... and {len(due_tasks) - 5} more")
            if st.button("View All Due Tasks", key="view_all_due"):
                st.switch_page("pages/2_📝_Tasks.py")
    else:
        st.info("No tasks due soon")

with col2:
    st.subheader("⚠️ Overdue")
    if overdue_tasks:
        # Show first 5 in compact mode
        tasks_card_list(
            tasks=overdue_tasks[:5],
            on_complete=handle_complete_due,
            show_actions=True,
            compact=True,
        )

        if len(overdue_tasks) > 5:
            st.caption(f"... and {len(overdue_tasks) - 5} more")
            if st.button("View All Overdue Tasks", key="view_all_overdue"):
                st.switch_page("pages/2_📝_Tasks.py")
    else:
        st.success("No overdue tasks! 🎉")

st.markdown("---")

# Charts
st.subheader("📊 Analytics")

if tasks:
    tab1, tab2, tab3 = st.tabs(
        ["Status Distribution", "Schedule Types", "Completion History"]
    )

    with tab1:
        task_status_chart(tasks)

    with tab2:
        frequency_breakdown_chart(tasks)

    with tab3:
        # Get recent completions
        @st.cache_data(ttl=60)
        def fetch_recent_completions():
            try:
                all_completions = []
                for task in tasks[:10]:
                    completions = asyncio.run(
                        api_client.get_task_completions(task["id"], limit=10)
                    )
                    all_completions.extend(completions)

                all_completions.sort(key=lambda x: x["completed_at"], reverse=True)
                return all_completions[:50]
            except Exception:
                return []

        completions = fetch_recent_completions()

        if completions:
            task_completion_chart(completions)
        else:
            st.info("No completion history yet")
else:
    st.info("No tasks yet. Create your first task to see analytics!")
    if st.button("➕ Create First Task"):
        st.switch_page("pages/2_📝_Tasks.py")

# Refresh button
st.markdown("---")
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
