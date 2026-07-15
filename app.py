"""
Regulatory Intelligence Assistant — MVP1
Streamlit app that turns a pasted regulatory/SOP excerpt plus a
product-change scenario into a structured, source-grounded pre-review
analysis via OpenRouter.

Run locally:    streamlit run app.py
Data policy:    Synthetic examples only. Do not paste real regulated
                documents, patient data, confidential SOPs, or customer
                complaint data.
"""

from __future__ import annotations

import streamlit as st

from src.openrouter_client import OpenRouterError, call_openrouter
from src.prompts import build_messages
from src.response_parser import parse_analysis_response, result_to_markdown
from src.sample_data import (
    BLANK_LABEL,
    DOCUMENT_TYPES,
    get_scenario,
    get_scenario_labels,
)
from src.ui_helpers import render_result, render_sidebar_disclaimer

APP_TITLE = "Regulatory Intelligence Assistant"
MIN_RECOMMENDED_CHARS = 300

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="\U0001F4D8",
    layout="wide",
)


def init_session_state() -> None:
    defaults = {
        "regulatory_text": "",
        "scenario_question": "",
        "document_type": DOCUMENT_TYPES[0],
        "latest_result": None,
        "latest_markdown": None,
        "last_error": None,
        "selected_sample": BLANK_LABEL,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_sample_scenario(label: str) -> None:
    scenario = get_scenario(label)
    if scenario is None:
        st.session_state["regulatory_text"] = ""
        st.session_state["scenario_question"] = ""
        st.session_state["document_type"] = DOCUMENT_TYPES[0]
    else:
        st.session_state["regulatory_text"] = scenario["regulatory_text"]
        st.session_state["scenario_question"] = scenario["scenario_question"]
        doc_type = scenario["document_type"]
        st.session_state["document_type"] = (
            doc_type if doc_type in DOCUMENT_TYPES else "Other"
        )


def render_sidebar() -> None:
    st.sidebar.title(f"\U0001F4D8 {APP_TITLE}")
    st.sidebar.caption("MVP1 \u00b7 pre-review workspace, not a final decision")

    sample_label = st.sidebar.selectbox(
        "Load a sample scenario",
        options=get_scenario_labels(),
        index=get_scenario_labels().index(st.session_state["selected_sample"]),
        key="sample_selector",
        help="Loads synthetic regulatory text and a scenario question.",
    )
    if sample_label != st.session_state["selected_sample"]:
        st.session_state["selected_sample"] = sample_label
        apply_sample_scenario(sample_label)
        st.rerun()

    st.session_state["document_type"] = st.sidebar.selectbox(
        "Document type",
        options=DOCUMENT_TYPES,
        index=DOCUMENT_TYPES.index(st.session_state["document_type"]),
    )

    st.sidebar.divider()
    render_sidebar_disclaimer()

    st.sidebar.divider()
    if st.sidebar.button("Clear session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def render_input_form() -> bool:
    """Render the input form. Returns True if the user submitted it."""
    st.subheader("1. Provide source text and scenario")

    with st.form("analysis_form"):
        regulatory_text = st.text_area(
            "Regulatory or SOP text",
            value=st.session_state["regulatory_text"],
            height=240,
            placeholder=(
                "Paste the relevant regulatory guidance, standard excerpt, "
                "or internal SOP text here (synthetic data only)\u2026"
            ),
            help=f"At least {MIN_RECOMMENDED_CHARS} characters recommended "
            "for a well-grounded analysis.",
        )
        scenario_question = st.text_area(
            "Product-change scenario or regulatory question",
            value=st.session_state["scenario_question"],
            height=140,
            placeholder=(
                "Describe the product change, complaint, labeling question, "
                "validation question, or release question\u2026"
            ),
        )

        char_count = len(regulatory_text.strip())
        if char_count and char_count < MIN_RECOMMENDED_CHARS:
            st.caption(
                f"\u26A0\uFE0F {char_count} characters \u2014 "
                f"{MIN_RECOMMENDED_CHARS}+ recommended for a well-grounded "
                "analysis."
            )
        elif char_count:
            st.caption(f"{char_count} characters")

        submitted = st.form_submit_button(
            "Analyze Regulatory Impact", type="primary"
        )

    st.session_state["regulatory_text"] = regulatory_text
    st.session_state["scenario_question"] = scenario_question

    if submitted:
        if not regulatory_text.strip() or not scenario_question.strip():
            st.warning(
                "Please provide both the regulatory/SOP text and a "
                "scenario or question before analyzing."
            )
            return False
        return True
    return False


def run_analysis() -> None:
    with st.spinner("Generating structured analysis\u2026"):
        try:
            messages = build_messages(
                document_type=st.session_state["document_type"],
                regulatory_text=st.session_state["regulatory_text"],
                scenario_question=st.session_state["scenario_question"],
            )
            raw_response = call_openrouter(messages)
            result = parse_analysis_response(raw_response)
            markdown_report = result_to_markdown(
                result,
                document_type=st.session_state["document_type"],
                regulatory_text=st.session_state["regulatory_text"],
                scenario_question=st.session_state["scenario_question"],
            )
            st.session_state["latest_result"] = result
            st.session_state["latest_markdown"] = markdown_report
            st.session_state["last_error"] = None
        except OpenRouterError as exc:
            st.session_state["last_error"] = str(exc)
            st.session_state["latest_result"] = None
            st.session_state["latest_markdown"] = None


def render_optional_upload() -> None:
    with st.expander("Optional: upload a .txt or .md file instead of pasting"):
        uploaded = st.file_uploader(
            "Upload regulatory / SOP text file",
            type=["txt", "md"],
            help="PDF ingestion is out of scope for MVP1.",
        )
        if uploaded is not None:
            content = uploaded.read().decode("utf-8", errors="ignore")
            st.session_state["regulatory_text"] = content
            st.success(
                f"Loaded {len(content)} characters from {uploaded.name}. "
                "Scroll up to review before analyzing."
            )
            st.rerun()


def main() -> None:
    init_session_state()
    render_sidebar()

    st.title(f"\U0001F4D8 {APP_TITLE}")
    st.caption(
        "Paste regulatory or SOP text and a product-change scenario to get "
        "a structured, source-grounded pre-review analysis. This is not a "
        "final regulatory determination."
    )

    render_optional_upload()
    should_analyze = render_input_form()

    if should_analyze:
        run_analysis()

    if st.session_state.get("last_error"):
        st.error(f"\u26A0\uFE0F {st.session_state['last_error']}")

    if st.session_state.get("latest_result"):
        st.divider()
        st.subheader("2. AI-generated result")
        render_result(st.session_state["latest_result"])

        st.download_button(
            "\u2B07\uFE0F Download Markdown report",
            data=st.session_state["latest_markdown"],
            file_name="regulatory_pre_review_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
