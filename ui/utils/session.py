from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    defaults = {
        "ui_logs": [],
        "last_src": None,
        "last_cond": None,
        "drbg_instances": {},
        "last_drbg_output": None,
        "last_state_blob": None,
        "last_validation": None,
        "last_benchmarks": None,
        "ui_mode": "pedagogique",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def push_log(scope: str, message: str) -> None:
    logs = st.session_state.setdefault("ui_logs", [])
    logs.insert(0, {"scope": scope, "message": message})
    del logs[30:]
