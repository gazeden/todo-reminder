import asyncio

import streamlit as st

from config import settings
from services.api_client import get_api_client
from utils.formatting import display_error, display_success
from utils.validators import validate_email, validate_password, validate_username

# Page config
st.set_page_config(
    page_title=f"Register - {settings.APP_TITLE}", page_icon="📝", layout="centered"
)

# Main content
st.title("📝 Create Account")
st.markdown("Join us today and start managing your tasks!")

# API client
api_client = get_api_client()

# Registration form
with st.form("register_form"):
    st.subheader("Account Information")

    col1, col2 = st.columns(2)

    with col1:
        email = st.text_input(
            "Email *",
            placeholder="user@example.com",
            help="We'll never share your email",
        )

        username = st.text_input(
            "Username *",
            placeholder="johndoe",
            max_chars=50,
            help="Letters, numbers, and underscores only",
        )

    with col2:
        full_name = st.text_input("Full Name", placeholder="John Doe", max_chars=100)

        # Spacer to align with left column
        st.empty()

    st.markdown("---")

    st.subheader("Password")

    col1, col2 = st.columns(2)

    with col1:
        password = st.text_input(
            "Password *",
            type="password",
            help="Minimum 8 characters, must include letters and numbers",
        )

    with col2:
        confirm_password = st.text_input("Confirm Password *", type="password")

    # Terms and conditions
    st.markdown("---")

    terms = st.checkbox(
        "I agree to the Terms of Service and Privacy Policy", value=False
    )

    # Submit button
    col1, col2 = st.columns([1, 1])

    with col1:
        submitted = st.form_submit_button(
            "Create Account", type="primary", use_container_width=True
        )

    with col2:
        if st.form_submit_button("Back to Login", use_container_width=True):
            st.switch_page("🏠_Home.py")

    if submitted:
        # Validate inputs
        errors = []

        is_valid, error = validate_email(email)
        if not is_valid:
            errors.append(error)

        is_valid, error = validate_username(username)
        if not is_valid:
            errors.append(error)

        is_valid, error = validate_password(password)
        if not is_valid:
            errors.append(error)

        if password != confirm_password:
            errors.append("Passwords do not match")

        if not terms:
            errors.append("You must agree to the Terms of Service")

        if errors:
            for error in errors:
                display_error(error)
        else:
            # Register user
            try:
                with st.spinner("Creating your account..."):
                    user_data = {
                        "email": email,
                        "username": username,
                        "full_name": full_name if full_name else None,
                        "password": password,
                        "is_active": True,
                    }

                    new_user = asyncio.run(api_client.register(user_data))

                    display_success("Account created successfully! Please login.")

                    # Wait a moment then redirect
                    import time

                    time.sleep(2)
                    st.switch_page("🏠_Home.py")

            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    display_error("Email or username already exists")
                else:
                    display_error(f"Registration failed: {error_msg}")

# Additional information
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### ✨ Features")
    st.markdown("- Set up task reminders")
    st.markdown("- Real-time updates")
    st.markdown("- Secure & private")

with col2:
    st.markdown("### 🔒 Security")
    st.markdown("- Encrypted data")
    st.markdown("- Secure authentication")
    st.markdown("- Privacy-focused")

with col3:
    st.markdown("### 📊 Analytics")
    st.markdown("- Detailed insights")
    st.markdown("- Activity tracking")
    st.markdown("- Visual reports")

st.markdown("---")

# Already have account
st.markdown(
    "<div style='text-align: center'>"
    "Already have an account? "
    "<a href='/' target='_self'>Login here</a>"
    "</div>",
    unsafe_allow_html=True,
)
