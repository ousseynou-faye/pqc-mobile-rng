from __future__ import annotations

from typing import Iterable

import streamlit as st


BADGE_CLASS = {
    "implemented": "badge-implemented",
    "experimental": "badge-experimental",
    "future": "badge-future",
}

NOTE_CLASS = {
    "info": "note-info",
    "success": "note-success",
    "warning": "note-warning",
    "danger": "note-danger",
}


def hero(title: str, subtitle: str, *, eyebrow: str = "Dashboard scientifique") -> None:
    st.markdown(
        f"""
        <section class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str, *, badges: Iterable[tuple[str, str]] = ()) -> None:
    badge_html = "".join(
        f'<span class="ui-badge {BADGE_CLASS.get(style, "badge-implemented")}">{label}</span>'
        for label, style in badges
    )
    st.markdown(
        f"""
        <section class="ui-card">
          <div>{badge_html}</div>
          <h3>{title}</h3>
          <p>{body}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def metric_strip(metrics: Iterable[tuple[str, str]]) -> None:
    items = "".join(
        f"""
        <div class="metric-pill">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
        </div>
        """
        for label, value in metrics
    )
    st.markdown(f'<section class="metric-strip">{items}</section>', unsafe_allow_html=True)


def section_header(title: str, subtitle: str, *, kicker: str = "Section") -> None:
    st.markdown(
        f"""
        <section class="section-header">
          <div class="kicker">{kicker}</div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def note_panel(title: str, body: str, *, tone: str = "info") -> None:
    st.markdown(
        f"""
        <section class="ui-note {NOTE_CLASS.get(tone, "note-info")}">
          <strong>{title}</strong>
          <p>{body}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def text_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <section class="ui-panel">
          <h4>{title}</h4>
          <p>{body}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def step_grid(steps: Iterable[tuple[str, str]]) -> None:
    cards = "".join(
        f"""
        <section class="ui-step">
          <div class="step-index">{index}</div>
          <h4>{title}</h4>
          <p>{body}</p>
        </section>
        """
        for index, (title, body) in enumerate(steps, start=1)
    )
    st.markdown(f'<section class="ui-step-grid">{cards}</section>', unsafe_allow_html=True)


def action_strip(actions: Iterable[tuple[str, str]]) -> None:
    cards = "".join(
        f"""
        <section class="action-card">
          <strong>{title}</strong>
          <span>{body}</span>
        </section>
        """
        for title, body in actions
    )
    st.markdown(f'<section class="action-strip">{cards}</section>', unsafe_allow_html=True)


def render_logs(logs: list[dict[str, str]], *, limit: int = 10) -> None:
    if not logs:
        st.info("Aucun journal disponible pour le moment.")
        return
    for item in logs[:limit]:
        st.caption(f"[{item['scope']}] {item['message']}")
