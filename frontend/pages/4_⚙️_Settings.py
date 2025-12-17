import streamlit as st

from config import settings
from utils.navigation import show_sidebar
from utils.session import require_authentication

# Page config
st.set_page_config(
    page_title=f"Settings - {settings.APP_TITLE}", page_icon="⚙️", layout="wide"
)

# Require authentication
require_authentication()

# Show sidebar
show_sidebar()

# Main content
st.title("⚙️ Settings")

# Appearance settings
st.subheader("🎨 Appearance")

with st.expander("Theme Settings", expanded=True):
    st.info("Theme settings are configured in `.streamlit/config.toml`")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Current Theme:**")
        st.markdown("- Primary Color: #FF4B4B")
        st.markdown("- Background: #FFFFFF")
        st.markdown("- Font: Sans Serif")

    with col2:
        st.markdown("**To customize:**")
        st.code("""
# Edit .streamlit/config.toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
        """)

st.markdown("---")

# Display settings
st.subheader("📺 Display Settings")

with st.expander("Page Configuration", expanded=True):
    # Page size settings
    page_size = st.slider(
        "Items Per Page",
        min_value=10,
        max_value=100,
        value=settings.DEFAULT_PAGE_SIZE,
        step=10,
        help="Number of items to display per page in lists",
    )

    if page_size != settings.DEFAULT_PAGE_SIZE:
        st.warning("Page size changes require app restart to take effect")

    # Date format
    date_format = st.selectbox(
        "Date Format",
        options=["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%m/%d/%Y %I:%M %p", "%Y-%m-%d"],
        index=0,
        help="Choose your preferred date display format",
    )

    st.info(
        f"Example: {st.session_state.user.get('created_at', '2024-01-01T12:00:00')}"
    )

st.markdown("---")

# Notification settings
st.subheader("🔔 Notifications")

with st.expander("Notification Preferences", expanded=True):
    email_notifications = st.checkbox(
        "Email Notifications",
        value=True,
        help="Receive email notifications for important events",
    )

    if email_notifications:
        st.checkbox("New items created", value=True)
        st.checkbox("Items updated", value=True)
        st.checkbox("System announcements", value=True)

    st.info(
        "💡 Notification settings are stored locally and will be synced in a future update"
    )

st.markdown("---")

# Privacy settings
st.subheader("🔒 Privacy & Security")

with st.expander("Security Settings", expanded=True):
    st.markdown("### Session Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Session Timeout:** {settings.SESSION_TIMEOUT} minutes")
        st.markdown("**Current Session:** Active")

    with col2:
        if st.button("🔐 Change Password", use_container_width=True):
            st.info("Use the Profile page to change your password")

        if st.button("🚪 Logout All Devices", use_container_width=True):
            st.warning("This feature will be available in a future update")

    st.markdown("---")

    st.markdown("### Data Privacy")
    st.markdown("- Your data is encrypted in transit and at rest")
    st.markdown("- We never share your personal information")
    st.markdown("- You can request data export at any time")

st.markdown("---")

# Advanced settings
st.subheader("🔧 Advanced")

with st.expander("Developer Options", expanded=False):
    st.markdown("### API Information")
    st.code(f"""
API Base URL: {settings.API_BASE_URL}
App Version: 0.1.0
Debug Mode: {settings.DEBUG}
    """)

    st.markdown("### Cache Management")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared successfully!")

    with col2:
        if st.button("🔄 Reload App", use_container_width=True):
            st.rerun()

    st.markdown("### Session State")
    if st.checkbox("Show Session State (Debug)"):
        st.json(
            {
                k: str(v)
                for k, v in st.session_state.items()
                if k != "access_token"  # Don't show token for security
            }
        )

st.markdown("---")

# Danger zone
st.subheader("⚠️ Danger Zone")

with st.expander("Account Management", expanded=False):
    st.error("### Delete Account")
    st.markdown("""
    Permanently delete your account and all associated data.
    **This action cannot be undone!**
    """)

    if st.button("🗑️ Delete My Account", type="primary"):
        st.error(
            "Account deletion will be available in a future update. Contact support for assistance."
        )

    st.markdown("---")

    st.warning("### Export Data")
    st.markdown("Download all your data in JSON format")

    if st.button("📥 Export My Data"):
        import asyncio
        import json

        from services.api_client import get_api_client

        try:
            api_client = get_api_client()
            items = asyncio.run(api_client.get("/items", params={"limit": 10000}))
            user = st.session_state.user

            export_data = {
                "user": user,
                "items": items.get("items", []),
                "export_date": st.session_state.user.get("updated_at"),
            }

            st.download_button(
                label="💾 Download Data",
                data=json.dumps(export_data, indent=2),
                file_name="my_data_export.json",
                mime="application/json",
            )
        except Exception as e:
            st.error(f"Failed to export data: {str(e)}")
