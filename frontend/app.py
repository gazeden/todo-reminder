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
