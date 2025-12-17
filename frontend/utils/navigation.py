import streamlit as st

from utils.session import logout


def show_sidebar():
    """
    Display sidebar navigation.
    """
    with st.sidebar:
        st.title("🚀 Navigation")

        # Show user info if authenticated
        if st.session_state.get("authenticated", False):
            user = st.session_state.get("user", {})
            st.markdown(f"""
            **Logged in as:**  
            👤 {user.get("username", "User")}  
            📧 {user.get("email", "")}
            """)
            st.markdown("---")

            # Navigation menu
            st.subheader("📋 Menu")

            if st.button("🏠 Home", use_container_width=True):
                st.switch_page("🏠_Home.py")

            if st.button("📊 Dashboard", use_container_width=True):
                st.switch_page("pages/1_📊_Dashboard.py")

            if st.button("📝 Items", use_container_width=True):
                st.switch_page("pages/2_📝_Items.py")

            if st.button("👤 Profile", use_container_width=True):
                st.switch_page("pages/3_👤_Profile.py")

            if st.button("⚙️ Settings", use_container_width=True):
                st.switch_page("pages/4_⚙️_Settings.py")

            st.markdown("---")

            # Logout button
            if st.button("🚪 Logout", use_container_width=True, type="primary"):
                logout()
                st.rerun()

        else:
            st.info("Please login to access the application")
            if st.button("🔐 Login", use_container_width=True, type="primary"):
                st.switch_page("🏠_Home.py")

            if st.button("📝 Register", use_container_width=True):
                st.switch_page("pages/5_📝_Register.py")

        # Footer
        st.markdown("---")
        st.caption("Version 0.1.0")
        st.caption("© 2024 My Application")


def navigate_to(page: str):
    """
    Navigate to a specific page.

    Args:
        page: Page name to navigate to
    """
    st.session_state.current_page = page
    st.switch_page(page)
