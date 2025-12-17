import asyncio

import streamlit as st

from components.forms import user_profile_form
from config import settings
from services.api_client import get_api_client
from utils.formatting import display_error, display_success, format_date
from utils.navigation import show_sidebar
from utils.session import require_authentication

# Page config
st.set_page_config(
    page_title=f"Profile - {settings.APP_TITLE}", page_icon="👤", layout="wide"
)

require_authentication()
show_sidebar()

st.title("👤 User Profile")

api_client = get_api_client()
user = st.session_state.get("user", {})

# Profile information
st.subheader("Profile Information")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(
        f"""
        <div style="
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            color: white;
            font-weight: bold;
        ">
            {user.get("username", "U")[0].upper()}
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(f"### {user.get('full_name', user.get('username', 'User'))}")
    st.markdown(f"**Email:** {user.get('email', '')}")
    st.markdown(f"**Username:** {user.get('username', '')}")
    st.markdown(
        f"**Account Status:** {'✅ Active' if user.get('is_active') else '❌ Inactive'}"
    )
    st.markdown(f"**Member Since:** {format_date(user.get('created_at', ''))}")

st.markdown("---")

# Edit profile
st.subheader("Edit Profile")


def handle_profile_update(data):
    """Handle profile update submission."""
    try:
        with st.spinner("Updating profile..."):
            updated_user = asyncio.run(api_client.update_user(user["id"], data))

            st.session_state.user = updated_user
            display_success("Profile updated successfully!")
            st.rerun()
    except Exception as e:
        display_error(f"Failed to update profile: {str(e)}")


user_profile_form(user=user, on_submit=handle_profile_update)

st.markdown("---")

# Task statistics
st.subheader("📊 Task Statistics")


@st.cache_data(ttl=60)
def fetch_user_stats():
    """Fetch user statistics."""
    try:
        stats = asyncio.run(api_client.get_task_stats())
        tasks_result = asyncio.run(api_client.get_tasks(limit=1000))
        return {"stats": stats, "tasks": tasks_result.get("tasks", [])}
    except Exception:
        return {"stats": {}, "tasks": []}


data = fetch_user_stats()
stats = data["stats"]
tasks = data["tasks"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Tasks", stats.get("total_tasks", 0))

with col2:
    st.metric("Pending", stats.get("pending_tasks", 0))

with col3:
    st.metric("Completed Today", stats.get("completed_today", 0))

with col4:
    st.metric("Current Streak", f"{stats.get('streak_days', 0)} days")

st.markdown("---")

# Completion rate
st.subheader("📈 Completion Rate")

completion_rate = stats.get("completion_rate", 0.0)
st.progress(min(completion_rate / 10, 1.0))  # Assuming max 10 completions/day
st.caption(f"{completion_rate:.1f} tasks completed per day (30-day average)")

st.markdown("---")

# Recent activity
st.subheader("🕐 Recent Activity")

if tasks:
    recent_tasks = sorted(
        tasks, key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True
    )[:5]

    for task in recent_tasks:
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{task['title']}**")
                st.caption(f"Last updated: {format_date(task['updated_at'])}")

            with col2:
                status_emoji = {"pending": "⏳", "completed": "✅", "overdue": "⚠️"}.get(
                    task.get("status", "pending"), "⏳"
                )
                st.markdown(status_emoji)

            st.markdown("---")
else:
    st.info("No activity yet")

# Refresh button
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
