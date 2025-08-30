import os
import re
import requests
import streamlit as st
from textwrap import dedent
from html import escape
from datetime import datetime, timezone, timedelta

# ===== 基本設定（環境変数/Secrets対応） =====
DEFAULT_API_BASE = "https://teamx-quest-api-234584649227.asia-northeast1.run.app"

def api_base() -> str:
    base = os.getenv("API_BASE_URL")
    if not base:
        try:
            base = st.secrets.get("API_BASE_URL", DEFAULT_API_BASE)
        except Exception:
            base = DEFAULT_API_BASE
    return base

JST = timezone(timedelta(hours=9))
def now_jst_str(fmt="%Y-%m-%d %H:%M:%S"): return datetime.now(JST).strftime(fmt)

# ===== CSS / UI =====
def css():
    st.markdown("""
    <style>
      .stApp { max-width: 100%; padding: 0; }
      .main { padding: 0 1rem; }
      .main-header {
        text-align: center; padding: 1.5rem 1rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white; border-radius: 10px; margin-bottom: 1.5rem;
      }
      .main-header h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
      .main-header p { font-size: 0.9rem; margin-top: 0.5rem; }

      .demo-card {
        background: white; padding: 1.5rem; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem; border: 2px solid #f0f0f0;
      }
      .highlight-box { background:#f8f9fa; padding:1rem; border-radius:10px;
        border-left:4px solid #1e3c72; margin:1rem 0; font-size:0.9rem; }
      .benefit-box { background:#e3f2fd; padding:1rem; border-radius:10px;
        margin:1rem 0; border:1px solid #90caf9; font-size:0.9rem; }
      .big-number { font-size:2rem; font-weight:bold; color:#1e3c72; text-align:center; }
      .certificate { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
        color:white; padding:1.5rem; border-radius:15px; text-align:center; margin:1.5rem 0; }
      .step-indicator { background:#1e3c72; color:white; padding:0.4rem 0.8rem;
        border-radius:20px; display:inline-block; margin-bottom:1rem; font-size:0.85rem; }

      .demo-card div[data-testid="stButton"] > button,
      .step-nav  div[data-testid="stButton"] > button { width:100%; padding:0.8rem; font-size:1rem; }
      .demo-card div[data-testid="stButton"] > button:disabled,
      .step-nav  div[data-testid="stButton"] > button:disabled {
        background:#ccc !important; color:#666 !important; cursor:not-allowed !important; opacity:.6 !important;
      }
      div[data-testid="stButton"] > button:empty { display:none !important; padding:0 !important; border:0 !important; width:0 !important; height:0 !important; }

      .step-nav { margin-top: 1rem; }
      .soft-hr { border:none; border-top:1px solid #ECEFF4; margin:16px 0; }

      .status-float { position:fixed; right:16px; bottom:16px; z-index:1000; }
      @media (max-width:600px){ .status-float { right:10px; bottom:10px; transform:scale(.95);} }

      /* h3 のアンカーアイコンを非表示 */
      h3 a, .stMarkdown h3 a, h3 .anchor, h3 .anchor-link { display:none !important; }
    </style>
    """, unsafe_allow_html=True)

def header():
    st.markdown("""
    <div class="main-header">
      <h1>🎓 Team X ブロックチェーン学習・実績証明</h1>
      <p>実績を永久に、確実に、証明する</p>
    </div>
    """, unsafe_allow_html=True)

    # セッション既定
    st.session_state.setdefault("api_on", True)
    st.session_state.setdefault("api_last_ok", None)

    # 右上に控えめな⚙️
    col_left, col_right = st.columns([1,5])
    with col_right:
        cols = st.columns([8,2])
        with cols[1]:
            try:
                with st.popover("⚙️", use_container_width=False):
                    try:
                        toggled = st.toggle("API連携を有効化", value=st.session_state.api_on)
                    except TypeError:
                        toggled = st.checkbox("API連携を有効化", value=st.session_state.api_on)
                    if toggled != st.session_state.api_on:
                        st.session_state.api_on = bool(toggled)
                        st.rerun()
                    if st.button("接続テスト", use_container_width=True):
                        ok = ping_api()
                        st.session_state.api_last_ok = ok
                        if ok: st.success("APIはONLINEです。")
                        else:  st.warning("APIに接続できません（フォールバック表示）。")
            except Exception:
                pass

    # 右下ステータス
    status_float = st.empty()
    render_status_float(status_float, st.session_state.api_on, st.session_state.api_last_ok)

def card(md: str):
    st.markdown(f'<div class="demo-card">{dedent(md).strip()}</div>', unsafe_allow_html=True)

def hr(): st.markdown('<hr class="soft-hr" />', unsafe_allow_html=True)

def primary_button(label: str, disabled: bool=False):
    try:
        return st.button(label, type="primary", use_container_width=True, disabled=disabled)
    except TypeError:
        return st.button(label, disabled=disabled)

# ===== ページ遷移（プログラム制御） =====
def go(page_file: str):
    """pages/ 以下のファイルへ遷移（st.switch_page が無い環境はリンク表示にフォールバック）"""
    target = f"pages/{page_file}"
    try:
        st.switch_page(target)  # Streamlit 1.23+ 目安
    except Exception:
        try:
            st.page_link(target, label="次のページへ ▶️")
        except Exception:
            st.markdown(f"[次のページへ ▶️]({target})")

# ===== ステータス表示 =====
def render_status_float(container, mode_on: bool, last_ok):
    if not mode_on:
        text = "API: OFF（手動）"; bg, fg = "#F1F3F4", "#5F6368"
    else:
        if last_ok is True:  text, bg, fg = "API: 🟢 ONLINE", "#E6F4EA", "#137333"
        elif last_ok is False: text, bg, fg = "API: 🔴 OFFLINE（フォールバック）", "#FCE8E6", "#A50E0E"
        else:                 text, bg, fg = "API: ⏳ 未チェック", "#FFF4CE", "#5C2E00"
    container.markdown(
        f"<div class='status-float'><span style='padding:4px 10px; border-radius:12px;"
        f"background:{bg}; color:{fg}; font-size:0.85rem;'>{text}</span></div>", unsafe_allow_html=True
    )

# ===== API呼び出し =====
def ping_api(timeout=3) -> bool:
    try:
        r = requests.get(f"{api_base()}/api/v1/quests/available", timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False

def hit_api(path: str, timeout=5):
    try:
        r = requests.get(f"{api_base()}{path}", timeout=timeout)
        if r.status_code == 200:
            return r.json(), True
        return {}, False
    except requests.RequestException:
        return {}, False

def get_quests_available():
    if not st.session_state.get("api_on", True):
        return {"status":"available","quests":[],"total_count":0}, None
    data, ok = hit_api("/api/v1/quests/available")
    if not ok: data = {"status":"available","quests":[],"total_count":0}
    st.session_state.api_last_ok = ok
    return data, ok

def get_profile():
    if not st.session_state.get("api_on", True):
        return {}, None
    data, ok = hit_api("/api/v1/profile")
    if not ok: data = {}
    st.session_state.api_last_ok = ok
    return data, ok
