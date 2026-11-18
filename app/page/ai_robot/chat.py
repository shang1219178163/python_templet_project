"""DeepSeek 风格 AI 聊天界面：流式问答、历史会话与图片/文档输入。"""

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from datetime import date, datetime, timedelta

import anthropic
import streamlit as st

from chat_store import (
    DATA_DIR,
    add_message,
    create_conversation,
    delete_conversation,
    get_messages,
    init_db,
    list_conversations,
    make_title,
    save_upload,
    set_pinned,
    touch_conversation,
)
from file_reader import DOC_EXTS, IMAGE_EXTS, extract_text, is_image
from llm_client import (
    build_messages,
    format_api_error,
    pick_model,
    stream_reply,
)

APP_NAME = "DeepSeek"
USER_NAME = "SoaringHeart"
ASSISTANT_AVATAR = ":material/auto_awesome:"

st.set_page_config(
    page_title=APP_NAME,
    page_icon=":material/forum:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()
conversations = list_conversations()
conversation_ids = {conv["id"] for conv in conversations}

# 首次进入默认打开最近会话；主动新建会话时保持空状态。
if "current_id" not in st.session_state:
    st.session_state.current_id = conversations[0]["id"] if conversations else None
if st.session_state.current_id not in conversation_ids:
    st.session_state.current_id = None
st.session_state.setdefault("ds_search_open", False)


CSS = """
:root {
    --ds-bg: #1e1e20;
    --ds-panel: #17171a;
    --ds-panel-2: #222227;
    --ds-panel-3: #2a2a31;
    --ds-border: #2c2c33;
    --ds-text: #e9e9ee;
    --ds-muted: #9696a1;
    --ds-blue: #4d6bfe;
    --ds-blue-soft: rgba(77, 107, 254, 0.14);
    --ds-gap: 0.9rem;
    --ds-pad: 1.25rem;
}

html, body, .stApp, button, input, textarea {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
}

body,
.stApp,
[data-testid="stAppViewContainer"] {
    background: var(--ds-bg);
    color: var(--ds-text);
}
[data-testid="stAppViewContainer"] > .main {
    background: var(--ds-bg);
}

#MainMenu, footer, header[data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stAppDeployButton"] {
    display: none !important;
}

.block-container {
    padding: 0.75rem var(--ds-pad) 0 !important;
    max-width: 100% !important;
}

::selection { background: rgba(77, 107, 254, 0.35); }
* { scrollbar-width: thin; scrollbar-color: #3b3b43 transparent; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #3b3b43; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #4a4a55; }

[data-testid="stHorizontalBlock"] { gap: var(--ds-gap); }

/* ---------- 左侧栏 ---------- */
.st-key-ds_sidebar {
    background: var(--ds-panel);
    border: 1px solid #232328;
    border-radius: 18px;
    box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
    padding: 12px 10px 10px;
    height: calc(100vh - 1.5rem) !important;
    min-height: calc(100vh - 1.5rem) !important;
    width: calc(
        (100% - 2 * var(--ds-pad) - var(--ds-gap)) * 0.2222
    ) !important;
    position: fixed;
    top: 0.75rem;
    left: var(--ds-pad);
    z-index: 40;
    display: flex;
    flex-direction: column;
    gap: 0.2rem !important;
    overflow: hidden;
}
.st-key-ds_sidebar > [data-testid="stLayoutWrapper"]:has(.st-key-ds_history) {
    flex: 1 1 auto;
    min-height: 0;
    display: flex;
    flex-direction: column;
}
.st-key-ds_history {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 2px 4px 6px 2px;
    margin-right: -4px;
    display: flex;
    flex-direction: column;
    gap: 0.15rem !important;
}
.st-key-ds_history > * { flex: 0 0 auto; }
.st-key-ds_history [data-testid="stElementContainer"] {
    margin: 0 !important;
}
.st-key-ds_history [data-testid="stMarkdown"] > div {
    height: auto !important;
    align-items: flex-start !important;
}
.st-key-ds_history [data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
}
.st-key-ds_sidebar > [data-testid="stLayoutWrapper"]:has(.st-key-ds_user) {
    margin-top: auto;
}
.st-key-ds_history [data-testid="stHorizontalBlock"] {
    gap: 0.15rem;
    align-items: center;
}
.st-key-ds_history [data-testid="stColumn"] { min-width: 0; }
.st-key-ds_history [data-testid="stColumn"]:last-child {
    display: flex;
    justify-content: flex-end;
}

.ds-brand {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 4px 8px 12px;
    color: var(--ds-blue);
    font-size: 1.18rem;
    font-weight: 800;
    letter-spacing: 0.2px;
}
.ds-brand svg {
    width: 26px;
    height: 26px;
    filter: drop-shadow(0 3px 8px rgba(77, 107, 254, 0.35));
}

.st-key-ds_search_toggle button {
    background: transparent !important;
    border: 0 !important;
    color: #8f8f9a !important;
    min-height: 34px !important;
    padding: 5px !important;
    border-radius: 10px !important;
}
.st-key-ds_search_toggle button:hover {
    background: var(--ds-panel-3) !important;
    color: #fff !important;
}
.st-key-ds_search_toggle button p { display: none !important; }
.st-key-ds_search_toggle button [data-testid="stIconMaterial"] {
    font-size: 19px !important;
}

.st-key-ds_new_chat { margin: 6px 0 4px; }
.st-key-ds_new_chat button {
    background: #26262b !important;
    color: #f2f2f6 !important;
    border: 1px solid #323239 !important;
    border-radius: 12px !important;
    padding: 0.62rem 0.8rem !important;
    font-weight: 600 !important;
    justify-content: flex-start !important;
    transition: background 0.15s ease, border-color 0.15s ease;
}
.st-key-ds_new_chat button:hover {
    background: #2e2e35 !important;
    border-color: #41414a !important;
    color: #fff !important;
}
.st-key-ds_new_chat button [data-testid="stIconMaterial"] {
    color: #d8d8e0 !important;
}

.st-key-ds_search { margin: 2px 0 6px; }
.st-key-ds_search [data-testid="stTextInputRootElement"] {
    background: #202025 !important;
    border: 1px solid #303037 !important;
    border-radius: 10px !important;
}
.st-key-ds_search input {
    color: var(--ds-text) !important;
    background: transparent !important;
    font-size: 0.84rem;
}
.st-key-ds_search input::placeholder { color: #6f6f7a !important; }
.st-key-ds_search [data-testid="stTextInputRootElement"]:focus-within {
    border-color: var(--ds-blue) !important;
    box-shadow: 0 0 0 2px var(--ds-blue-soft);
}

.ds-group {
    color: #6f6f79;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 13px 9px 5px;
    user-select: none;
}
.ds-empty {
    color: #6f6f79;
    font-size: 0.8rem;
    padding: 10px 9px;
}

.st-key-ds_history [data-testid="stElementContainer"] button {
    background: transparent !important;
    color: #c6c6cf !important;
    border: 0 !important;
    border-radius: 10px !important;
    justify-content: flex-start !important;
    padding: 7px 9px !important;
    min-height: 34px !important;
    font-size: 0.86rem !important;
    font-weight: 400 !important;
}
.st-key-ds_history [data-testid="stElementContainer"] button:hover {
    background: #26262c !important;
    color: #fff !important;
}
.st-key-ds_history button[kind="primary"] {
    background: #2d2d34 !important;
    color: #fff !important;
}
.st-key-ds_history
    [data-testid="stElementContainer"]:has(button[kind="primary"]) {
    position: relative;
}
.st-key-ds_history
    [data-testid="stElementContainer"]:has(button[kind="primary"])::before {
    content: "";
    position: absolute;
    left: 0;
    top: 50%;
    width: 3px;
    height: 16px;
    border-radius: 999px;
    background: var(--ds-blue);
    transform: translateY(-50%);
}
.st-key-ds_history [data-testid="stElementContainer"] button {
    text-align: left !important;
}
.st-key-ds_history
    [data-testid="stElementContainer"]
    button
    > div {
    width: 100% !important;
    justify-content: flex-start !important;
}
.st-key-ds_history
    [data-testid="stElementContainer"]
    button
    > div
    > span {
    width: 100% !important;
}
.st-key-ds_history .stMarkdownEllipsis,
.st-key-ds_history button [data-testid="stMarkdownContainer"] {
    width: 100% !important;
    text-align: left !important;
    margin: 0 !important;
}
.st-key-ds_history button p {
    width: 100% !important;
    text-align: left !important;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.st-key-ds_history [data-testid="stPopoverButton"] {
    background: transparent !important;
    border: 0 !important;
    color: #7f7f8a !important;
    padding: 5px !important;
    min-height: 32px !important;
}
.st-key-ds_history [data-testid="stPopoverButton"] p {
    display: none !important;
}
.st-key-ds_history [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {
    font-size: 18px !important;
}
.st-key-ds_history [data-testid="stPopoverButton"]:hover {
    background: #2a2a31 !important;
    color: #fff !important;
}
.st-key-ds_history
    [data-testid="stPopoverButton"] > div > div[aria-hidden="true"] {
    display: none !important;
}

[data-testid="stPopoverBody"] {
    background: #232329 !important;
    border: 1px solid #36363e !important;
    border-radius: 12px !important;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.45) !important;
    padding: 5px !important;
    width: 176px !important;
    min-width: 176px !important;
    max-width: 176px !important;
}
[data-testid="stPopoverBody"] button {
    background: transparent !important;
    border: 0 !important;
    color: #d9d9e2 !important;
    justify-content: flex-start !important;
    border-radius: 8px !important;
    padding: 0.45rem 0.6rem !important;
    width: 100% !important;
}
[data-testid="stPopoverBody"] button:hover { background: #2e2e36 !important; }
[data-testid="stPopoverBody"] button p { font-size: 0.82rem; }

.st-key-ds_user {
    margin-top: 6px;
    padding-top: 8px;
    border-top: 1px solid #27272d;
}
.st-key-ds_user [data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
}
.st-key-ds_user [data-testid="stMarkdownContainer"] > div {
    height: auto !important;
    align-items: flex-start !important;
}
.st-key-ds_user [data-testid="stMarkdown"] {
    height: auto !important;
}
.ds-user-row {
    display: flex;
    align-items: center;
    gap: 11px;
    min-width: 0;
}
.ds-avatar {
    flex: 0 0 34px;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #4d6bfe, #8b5cf6);
    color: #fff;
    font-size: 0.88rem;
    font-weight: 700;
    box-shadow: 0 4px 14px rgba(77, 107, 254, 0.25);
}
.ds-user-meta {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
}
.ds-username {
    color: #e9e9ef;
    font-size: 0.84rem;
    font-weight: 600;
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.ds-plan {
    color: #777781;
    font-size: 0.68rem;
    line-height: 1.3;
}

/* ---------- 主聊天区 ---------- */
.st-key-ds_main {
    max-width: 880px;
    margin: 0 auto;
    width: 100%;
}
.st-key-ds_main > [data-testid="stLayoutWrapper"]:has(.st-key-ds_topbar) {
    position: sticky;
    top: 0;
    z-index: 30;
    background: var(--ds-bg);
}
.st-key-ds_topbar {
    background: linear-gradient(
        180deg,
        rgba(30, 30, 32, 0.98) 60%,
        rgba(30, 30, 32, 0)
    );
    padding: 10px 2px 14px;
    margin-bottom: 2px;
}
.st-key-ds_topbar [data-testid="stHorizontalBlock"] {
    align-items: center;
    gap: 0.4rem;
}
.ds-chat-title {
    color: #f1f1f5;
    font-size: 1.02rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 5px 2px;
}
.ds-icon-btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    color: #9a9aa5;
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
    margin-left: auto;
}
.ds-icon-btn:hover { background: #2a2a31; color: #fff; }
.ds-icon-btn svg { width: 18px; height: 18px; fill: currentColor; }

.st-key-ds_chat { padding: 2px 0 165px; }

.ds-welcome { text-align: center; padding: 16vh 1rem 40px; }
.ds-welcome-badge {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    margin: 0 auto 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #4d6bfe, #8b5cf6);
    box-shadow: 0 12px 40px rgba(77, 107, 254, 0.3);
}
.ds-welcome-badge svg { width: 32px; height: 32px; }
.ds-welcome h1 {
    color: #f3f3f7;
    font-size: 1.55rem;
    font-weight: 700;
    margin: 0 0 10px;
    letter-spacing: -0.01em;
}
.ds-welcome p { color: #8f8f9b; font-size: 0.9rem; margin: 0; }

.st-key-ds_chat [data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 0.55rem 0 !important;
    gap: 0.6rem !important;
}
.st-key-ds_chat [data-testid="stChatMessageAvatarCustom"] {
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #4d6bfe, #7c5cff) !important;
    color: #fff !important;
    box-shadow: 0 4px 14px rgba(77, 107, 254, 0.25);
}
.st-key-ds_chat
    [data-testid="stChatMessageAvatarCustom"]
    [data-testid="stIconMaterial"] {
    color: #fff !important;
    font-size: 17px !important;
}
.st-key-ds_chat [data-testid="stChatMessageContent"] {
    color: var(--ds-text) !important;
    font-size: 0.94rem;
    line-height: 1.75;
    padding-top: 3px;
}
.st-key-ds_chat
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    justify-content: flex-end !important;
}
.st-key-ds_chat
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageAvatarUser"] {
    display: none !important;
}
.st-key-ds_chat
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] {
    flex: 0 1 auto !important;
    width: fit-content !important;
    max-width: 78%;
    background: #2a2a31;
    border: 1px solid #35353d;
    border-radius: 16px 16px 5px 16px;
    padding: 0.6rem 0.95rem;
    margin-left: auto;
    margin-right: 0 !important;
}

.st-key-ds_chat [data-testid="stMarkdownContainer"] p {
    margin: 0 0 0.7rem;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] p:last-child {
    margin-bottom: 0;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] strong {
    color: #fff;
    font-weight: 600;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] code:not(pre code) {
    background: #2f2f37;
    color: #f0c987;
    border: 1px solid #3a3a43;
    border-radius: 6px;
    padding: 0.08rem 0.34rem;
    font-size: 0.85em;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] ul,
.st-key-ds_chat [data-testid="stMarkdownContainer"] ol {
    padding-left: 1.3rem;
    margin: 0.35rem 0 0.75rem;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] li { margin: 0.22rem 0; }
.st-key-ds_chat [data-testid="stMarkdownContainer"] a { color: #8ba3ff; }
.st-key-ds_chat [data-testid="stMarkdownContainer"] blockquote {
    border-left: 3px solid #3b3b45;
    color: #b7b7c2;
    padding-left: 0.9rem;
    margin: 0.5rem 0;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] h1,
.st-key-ds_chat [data-testid="stMarkdownContainer"] h2,
.st-key-ds_chat [data-testid="stMarkdownContainer"] h3,
.st-key-ds_chat [data-testid="stMarkdownContainer"] h4 {
    color: #f4f4f8;
    font-weight: 650;
    line-height: 1.4;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] h1 {
    font-size: 1.5rem;
    margin: 1.1rem 0 0.55rem;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] h2 {
    font-size: 1.28rem;
    margin: 1rem 0 0.5rem;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] h3 {
    font-size: 1.1rem;
    margin: 0.9rem 0 0.45rem;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] h4 {
    font-size: 0.98rem;
    margin: 0.8rem 0 0.4rem;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] table {
    border-collapse: collapse;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] th,
.st-key-ds_chat [data-testid="stMarkdownContainer"] td {
    border: 1px solid #34343c;
    padding: 6px 10px;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] pre {
    background: #151517 !important;
    border: 1px solid #2e2e36;
    border-radius: 12px;
    padding: 14px 16px !important;
    overflow: auto;
}
.st-key-ds_chat [data-testid="stMarkdownContainer"] pre code {
    background: transparent !important;
    border: 0 !important;
    color: #e6e6ec;
    font-size: 0.84rem;
}

/* 带语言标签的自定义代码块 */
[class*="st-key-ds_code_"] {
    background: #151517 !important;
    border: 1px solid #2e2e36 !important;
    border-radius: 12px !important;
    overflow: hidden;
    gap: 0 !important;
    margin: 0.8rem 0 1rem;
}
[class*="st-key-ds_code_"] [data-testid="stElementContainer"] {
    margin: 0 !important;
}
[class*="st-key-ds_code_"] [data-testid="stMarkdown"] > div {
    height: auto !important;
    align-items: flex-start !important;
}
[class*="st-key-ds_code_"] [data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
}
.ds-code-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #1b1b1f;
    border-bottom: 1px solid #2a2a32;
    color: #8f8f9a;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.73rem;
    padding: 7px 13px;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] {
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    position: relative;
    overflow: visible !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] pre {
    margin: 0 !important;
    padding: 12px 14px !important;
    background: #151517 !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] code,
[class*="st-key-ds_code_"] [data-testid="stCode"] pre {
    color: #d8d8e2 !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.keyword,
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.boolean {
    color: #ff7b72 !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.string,
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.char {
    color: #a5d6ff !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.comment {
    color: #8b949e !important;
    font-style: italic;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.number {
    color: #79c0ff !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.function,
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.class-name {
    color: #d2a8ff !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.builtin,
[class*="st-key-ds_code_"] [data-testid="stCode"] .token.property {
    color: #ffa657 !important;
}
[class*="st-key-ds_code_"] [data-testid="stCode"] > div:last-child {
    position: absolute;
    top: -30px;
    right: 8px;
    z-index: 4;
    opacity: 1 !important;
    visibility: visible !important;
}
[class*="st-key-ds_code_"]
    [data-testid="stCode"]
    > div:last-child
    *:not(button) {
    background-color: transparent !important;
}
[class*="st-key-ds_code_"] [data-testid="stElementToolbarButton"] {
    opacity: 1 !important;
    visibility: visible !important;
}
[class*="st-key-ds_code_"] [data-testid="stElementToolbarButton"] button {
    background: #232329 !important;
    border: 1px solid #34343d !important;
    border-radius: 8px !important;
    color: #a9a9b4 !important;
}
[class*="st-key-ds_code_"]
    [data-testid="stElementToolbarButton"]
    button:hover {
    color: #fff !important;
    background: #303038 !important;
    border-color: #45454f !important;
}

.ds-msg-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 6px;
    color: #777781;
}
.ds-msg-actions span {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 27px;
    height: 27px;
    border-radius: 7px;
    cursor: pointer;
}
.ds-msg-actions span:hover { background: #2a2a31; color: #dcdce4; }
.ds-msg-actions svg { width: 15px; height: 15px; fill: currentColor; }

.ds-file-chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #24242a;
    border: 1px solid #36363e;
    color: #c9c9d3;
    border-radius: 9px;
    padding: 7px 10px;
    font-size: 0.8rem;
    margin: 4px 0;
    max-width: 100%;
}
.ds-file-chip span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.ds-file-chip svg {
    width: 15px;
    height: 15px;
    flex: 0 0 auto;
    color: #8fa3ff;
}

.st-key-ds_chat [data-testid="stImage"] img {
    border-radius: 12px;
    border: 1px solid #36363e;
}
.st-key-ds_chat [data-testid="stStatus"] {
    background: #202026 !important;
    border: 1px solid #2e2e36 !important;
    border-radius: 12px !important;
    padding: 7px 10px !important;
}
.st-key-ds_chat [data-testid="stStatus"] p {
    color: #9a9aa5 !important;
    font-size: 0.8rem;
}
.st-key-ds_chat [data-testid="stStatus"] [data-testid="stStatusWidget"] {
    color: #8fa3ff;
}

/* ---------- 底部输入区 ---------- */
[data-testid="stBottom"] {
    background: transparent !important;
    padding-left: calc(
        var(--ds-pad) +
        (100% - 2 * var(--ds-pad) - var(--ds-gap)) * 0.2222 +
        var(--ds-gap)
    ) !important;
    box-sizing: border-box;
    pointer-events: none !important;
}
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > [data-testid="stVerticalBlock"] {
    pointer-events: none !important;
}
[data-testid="stBottom"] [data-testid="stChatInput"] {
    pointer-events: auto !important;
}
[data-testid="stBottom"] > div {
    background: linear-gradient(
        180deg,
        rgba(30, 30, 32, 0) 0%,
        #1e1e20 26%,
        #1e1e20 100%
    ) !important;
}
[data-testid="stBottomBlockContainer"] {
    padding: 0.2rem var(--ds-pad) 1rem 0 !important;
    max-width: 100% !important;
}
[data-testid="stBottom"] [data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
}
[data-testid="stBottom"] [data-testid="stMarkdownContainer"] > div {
    height: auto !important;
    align-items: flex-start !important;
}
[data-testid="stBottom"] [data-testid="stMarkdown"] {
    height: auto !important;
}
[data-testid="stBottomBlockContainer"] > [data-testid="stVerticalBlock"] {
    max-width: 880px;
    margin: 0 auto;
    gap: 0.5rem !important;
}

.ds-tools {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 0 0 6px 3px;
}
.ds-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border: 1px solid #34343b;
    border-radius: 999px;
    background: #232328;
    color: #b8b8c2;
    font-size: 0.78rem;
    cursor: default;
    transition: background 0.15s ease, color 0.15s ease;
}
.ds-chip:hover {
    background: #2b2b32;
    color: #e6e6ec;
    border-color: #45454f;
}
.ds-chip.think {
    color: #9db0ff;
    border-color: #35427a;
    background: rgba(77, 107, 254, 0.1);
}
.ds-chip svg { width: 13px; height: 13px; fill: currentColor; }

[data-testid="stChatInput"] {
    background: #24242a !important;
    border: 1px solid #35353d !important;
    border-radius: 22px !important;
    padding: 7px 9px !important;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.28);
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stChatInput"] > div {
    background: transparent !important;
    border-color: transparent !important;
}
[data-testid="stChatInputTextArea"] {
    color: #f0f0f4 !important;
    caret-color: #4d6bfe;
    font-size: 0.92rem;
}
[data-testid="stChatInputTextArea"]::placeholder {
    color: #777781 !important;
}
[data-testid="stChatInputSubmitButton"] {
    background: #4d6bfe !important;
    color: #fff !important;
    border-radius: 50% !important;
    width: 32px !important;
    height: 32px !important;
    padding: 5px !important;
}
[data-testid="stChatInputSubmitButton"]:hover {
    background: #5d79ff !important;
}
[data-testid="stChatInputSubmitButton"]:disabled {
    background: #34343c !important;
    color: #71717b !important;
}
[data-testid="stChatInputSubmitButton"] svg { fill: currentColor !important; }
[data-testid="stChatInputFileUploadButton"] button {
    color: #8f8f9a !important;
    background: transparent !important;
    border-radius: 50% !important;
}
[data-testid="stChatInputFileUploadButton"] button:hover {
    color: #fff !important;
    background: #33333b !important;
}
[data-testid="stChatInput"] [data-testid="stFileUploaderFile"] {
    background: #2c2c34 !important;
    border: 1px solid #3a3a43 !important;
    border-radius: 9px !important;
}

[data-testid="stTooltipContent"] {
    background: #2a2a31 !important;
    color: #e6e6ec !important;
    border: 1px solid #3a3a43 !important;
    border-radius: 8px !important;
}

@media (max-width: 900px) {
    .block-container { padding: 0.6rem 0.8rem 0 !important; }
    .st-key-ds_sidebar {
        position: static !important;
        left: auto !important;
        width: auto !important;
        height: auto !important;
        min-height: 0 !important;
        max-height: 42vh;
        margin-bottom: 0.5rem;
    }
    .st-key-ds_history { max-height: 18vh; }
    .st-key-ds_sidebar [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; }
    .st-key-ds_sidebar [data-testid="stColumn"] { min-width: 0 !important; }
    .st-key-ds_main { max-width: 100%; }
    .st-key-ds_chat { padding-bottom: 150px; }
    [data-testid="stBottom"] { padding-left: 0.8rem !important; }
    [data-testid="stBottomBlockContainer"] {
        padding: 0.2rem 0.8rem 0.8rem 0 !important;
    }
    [data-testid="stBottomBlockContainer"] > [data-testid="stVerticalBlock"] {
        max-width: 100%;
    }
}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


LOGO_SVG = """
<svg viewBox="0 0 32 32" aria-hidden="true">
  <rect width="32" height="32" rx="9" fill="#4d6bfe"/>
  <path d="M7 20.5c2.8 1.9 6.4 2 9.4.3 2.4-1.4 3.6-3.6 3.6-6.1
           0-1.3.8-2.1 2-2.1 1.4 0 2.4 1 2.8 2.4"
        fill="none" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>
  <circle cx="18.7" cy="14.2" r="1.1" fill="#fff"/>
</svg>
"""

SHARE_SVG = """
<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7
           s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34
           3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31
           6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31
           2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92
           2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/>
</svg>
"""

DOC_SVG = """
<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9
           2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
</svg>
"""

ACTIONS_HTML = """
<div class="ds-msg-actions">
  <span title="复制">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
  </span>
  <span title="有帮助">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>
  </span>
  <span title="没帮助">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.58-6.59c.37-.36.59-.86.59-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/></svg>
  </span>
  <span title="重新生成">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.65 6.35A7.95 7.95 0 0 0 12 4a8 8 0 1 0 7.73 10h-2.08A6 6 0 1 1 12 6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
  </span>
</div>
"""

TOOLS_HTML = """
<div class="ds-tools">
  <span class="ds-chip think">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-4 12.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26A7 7 0 0 0 12 2Zm-3 18h6v1a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-1Z"/></svg>
    深度思考
  </span>
  <span class="ds-chip">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm6.93 6h-2.95a15.7 15.7 0 0 0-1.38-3.56A8.03 8.03 0 0 1 18.93 8ZM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96ZM4.26 14a7.9 7.9 0 0 1 0-4h3.38a16.5 16.5 0 0 0 0 4H4.26Zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56A8.03 8.03 0 0 1 5.08 16Zm2.95-8H5.08a8.03 8.03 0 0 1 4.33-3.56A15.7 15.7 0 0 0 8.03 8ZM12 19.96a13.7 13.7 0 0 1-1.91-3.96h3.82A13.7 13.7 0 0 1 12 19.96ZM14.34 14H9.66a14.6 14.6 0 0 1 0-4h4.68a14.6 14.6 0 0 1 0 4Zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95a8.03 8.03 0 0 1-4.33 3.56ZM16.64 14a16.5 16.5 0 0 0 0-4h3.38a7.9 7.9 0 0 1 0 4h-3.38Z"/></svg>
    智能搜索
  </span>
</div>
"""

CODE_FENCE = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)
_code_index = 0


def render_markdown(text: str, seed: str) -> None:
    """渲染 Markdown，并把围栏代码块拆成带语言标签的 st.code。"""
    global _code_index
    position = 0
    for match in CODE_FENCE.finditer(text):
        before = text[position : match.start()]
        if before.strip():
            st.markdown(before)

        info = (match.group(1) or "").strip()
        language = info.split()[0] if info else "text"
        code = match.group(2).rstrip("\n")
        _code_index += 1
        with st.container(key=f"ds_code_{seed}_{_code_index}"):
            st.markdown(
                f'<div class="ds-code-head"><span>{html.escape(language)}</span></div>',
                unsafe_allow_html=True,
            )
            st.code(
                code,
                language=None if language == "text" else language,
                wrap_lines=True,
            )
        position = match.end()

    rest = text[position:]
    if rest.strip():
        st.markdown(rest)


def render_attachments(attachments: list[dict]) -> None:
    for attachment in attachments:
        if attachment.get("kind") == "image":
            path = DATA_DIR / attachment["path"]
            if path.exists():
                st.image(str(path), width=220, alt=attachment["name"])
            continue
        st.markdown(
            f'<div class="ds-file-chip">{DOC_SVG}'
            f"<span>{html.escape(attachment['name'])}</span></div>",
            unsafe_allow_html=True,
        )


def render_message(message: dict) -> None:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            if message["text"]:
                render_markdown(message["text"], f"m{message['id']}")
            render_attachments(message["attachments"])
            st.markdown(ACTIONS_HTML, unsafe_allow_html=True)
        return

    with st.chat_message("user"):
        render_attachments(message["attachments"])
        if message["text"]:
            render_markdown(message["text"], f"m{message['id']}")


def render_welcome() -> None:
    st.markdown(
        f"""
        <div class="ds-welcome">
          <div class="ds-welcome-badge">{LOGO_SVG}</div>
          <h1>你好，我是 DeepSeek</h1>
          <p>可以帮你写代码、读文档、分析图片。今天想聊点什么？</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(title: str) -> None:
    with st.container(key="ds_topbar"):
        title_col, share_col = st.columns(
            [0.92, 0.08], gap="small", vertical_alignment="center"
        )
        with title_col:
            st.markdown(
                f'<div class="ds-chat-title">{html.escape(title)}</div>',
                unsafe_allow_html=True,
            )
        with share_col:
            st.markdown(
                f'<div class="ds-icon-btn" title="分享">{SHARE_SVG}</div>',
                unsafe_allow_html=True,
            )


def _parse_day(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value).date()
    except (TypeError, ValueError):
        return None


def group_conversations(items: list[dict]) -> list[tuple[str, list[dict]]]:
    """按置顶与日期分组，顺序：置顶、今天、昨天、更早。"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    groups: dict[str, list[dict]] = {
        "置顶": [],
        "今天": [],
        "昨天": [],
        "更早": [],
    }
    for conv in items:
        if conv["pinned"]:
            groups["置顶"].append(conv)
            continue
        day = _parse_day(conv["updated_at"])
        if day == today:
            groups["今天"].append(conv)
        elif day == yesterday:
            groups["昨天"].append(conv)
        else:
            groups["更早"].append(conv)
    return [(name, group) for name, group in groups.items() if group]


def render_conversation_item(conv: dict, current_id: str | None) -> None:
    title = conv["title"]
    name_col, menu_col = st.columns(
        [0.82, 0.18], gap="small", vertical_alignment="center"
    )
    with name_col:
        if st.button(
            title,
            key=f"conv_{conv['id']}",
            type="primary" if conv["id"] == current_id else "tertiary",
            width="stretch",
        ):
            st.session_state.current_id = conv["id"]
            st.rerun()

    with menu_col:
        with st.popover(
            "更多",
            icon=":material/more_horiz:",
            type="tertiary",
        ):
            pin_label = "取消置顶" if conv["pinned"] else "置顶"
            if st.button(
                pin_label,
                icon=":material/push_pin:",
                key=f"pin_{conv['id']}",
                width="stretch",
            ):
                set_pinned(conv["id"], not conv["pinned"])
                st.rerun()
            if st.button(
                "删除会话",
                icon=":material/delete:",
                key=f"delete_{conv['id']}",
                width="stretch",
            ):
                delete_conversation(conv["id"])
                if conv["id"] == current_id:
                    st.session_state.current_id = None
                st.rerun()


def render_sidebar(items: list[dict], current_id: str | None) -> None:
    with st.container(key="ds_sidebar"):
        brand_col, search_col = st.columns(
            [0.8, 0.2], gap="small", vertical_alignment="center"
        )
        with brand_col:
            st.markdown(
                f'<div class="ds-brand">{LOGO_SVG}<span>{APP_NAME}</span></div>',
                unsafe_allow_html=True,
            )
        with search_col:
            if st.button(
                "搜索",
                icon=":material/search:",
                key="ds_search_toggle",
                help="搜索会话",
                type="tertiary",
                width="stretch",
            ):
                st.session_state.ds_search_open = not st.session_state.ds_search_open
                st.rerun()

        query = ""
        if st.session_state.ds_search_open:
            query = st.text_input(
                "搜索会话",
                placeholder="搜索会话…",
                label_visibility="collapsed",
                key="ds_search",
            )

        if st.button(
            "新建对话",
            icon=":material/add:",
            key="ds_new_chat",
            type="secondary",
            width="stretch",
        ):
            st.session_state.current_id = None
            st.rerun()

        filtered = items
        if query.strip():
            needle = query.strip().lower()
            filtered = [conv for conv in items if needle in conv["title"].lower()]

        with st.container(key="ds_history"):
            groups = group_conversations(filtered)
            if not groups:
                st.markdown(
                    '<div class="ds-empty">没有找到相关会话</div>',
                    unsafe_allow_html=True,
                )
            for group_name, group_items in groups:
                st.markdown(
                    f'<div class="ds-group">{group_name}</div>',
                    unsafe_allow_html=True,
                )
                for conv in group_items:
                    render_conversation_item(conv, current_id)

        with st.container(key="ds_user"):
            st.markdown(
                '<div class="ds-user-row">'
                f'<div class="ds-avatar">{html.escape(USER_NAME[:1])}</div>'
                '<div class="ds-user-meta">'
                f'<div class="ds-username">{html.escape(USER_NAME)}</div>'
                '<div class="ds-plan">免费版</div>'
                "</div>"
                "</div>",
                unsafe_allow_html=True,
            )


def stream_with_status(messages: list[dict], status) -> Iterator[str]:
    """等待后端时显示动态状态，收到首块内容后切换为生成中。"""
    started = False
    for chunk in stream_reply(messages):
        if not started:
            status.update(label=":shimmer[正在生成回答…]", state="running")
            started = True
        yield chunk


def handle_submission(submission) -> None:
    text = (submission.text or "").strip()
    uploads = list(submission.files or [])
    if not text and not uploads:
        return

    if st.session_state.current_id:
        conv_id = st.session_state.current_id
    else:
        conv_id = create_conversation(
            make_title(text, [upload.name for upload in uploads])
        )
        st.session_state.current_id = conv_id

    attachments = []
    doc_sections = []
    for upload in uploads:
        data = upload.getvalue()
        rel_path = save_upload(conv_id, upload.name, data)
        if is_image(upload.name):
            attachments.append({"kind": "image", "name": upload.name, "path": rel_path})
            continue

        extracted, error = extract_text(upload.name, data)
        attachments.append({"kind": "document", "name": upload.name, "path": rel_path})
        if error:
            st.warning(f"{upload.name}：{error}")
        if extracted:
            doc_sections.append(f"### 文件：{upload.name}\n{extracted}")

    model_text = "\n\n".join(part for part in [text, *doc_sections] if part)
    if not model_text:
        model_text = "请阅读并分析我上传的内容。"

    add_message(
        conv_id,
        "user",
        text=text,
        model_text=model_text,
        attachments=attachments,
    )
    touch_conversation(conv_id)

    with st.chat_message("user"):
        render_attachments(attachments)
        if text:
            render_markdown(text, "live_user")

    api_messages = build_messages(get_messages(conv_id), DATA_DIR)
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        status = st.status(
            ":shimmer[正在等待后端响应…]",
            type="compact",
            expanded=False,
        )
        status.caption(f"模型：`{pick_model(api_messages)}`")
        try:
            answer = st.write_stream(stream_with_status(api_messages, status))
            status.update(label="回答完成", state="complete")
        except anthropic.APIError as exc:
            status.update(label="请求失败", state="error")
            st.error(format_api_error(exc))
            answer = ""

    if answer:
        add_message(conv_id, "assistant", text=answer)
        touch_conversation(conv_id)
        st.rerun()


left, main = st.columns([1, 3.5], gap="small")

with left:
    render_sidebar(conversations, st.session_state.current_id)

current_id = st.session_state.current_id
current_title = next(
    (conv["title"] for conv in conversations if conv["id"] == current_id),
    "新的对话",
)

with main:
    main_body = st.container(key="ds_main")
    with main_body:
        render_topbar(current_title)
        chat_body = st.container(key="ds_chat")
        with chat_body:
            history = get_messages(current_id) if current_id else []
            if history:
                for message in history:
                    render_message(message)
            else:
                render_welcome()

with st.bottom:
    st.markdown(TOOLS_HTML, unsafe_allow_html=True)

submission = st.chat_input(
    "给 DeepSeek 发送消息",
    key="ds_chat_input",
    accept_file="multiple",
    file_type=sorted(IMAGE_EXTS | DOC_EXTS),
    max_upload_size=20,
    submit_mode="disable",
)

if submission:
    with chat_body:
        handle_submission(submission)
