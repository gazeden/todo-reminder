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
                ...
            
            if register:
                ...


def show_home_page():
    ...


if __name__ == "__main__":
    main()
