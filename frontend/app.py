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
                ...


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


def show_quick_stats(): ...


def show_urgent_tasks(): ...


def show_recent_activity(): ...


if __name__ == "__main__":
    main()
