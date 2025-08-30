import os
import re
import time
import hashlib
import requests
import streamlit as st
from html import escape
from textwrap import dedent
from datetime import datetime, timezone, timedelta

# components はフォールバック用に遅延import（未使用環境でもエラーにしない）
try:
    import streamlit.components.v1 as components
except Exception:
    components = None

# ==============================
# 基本設定（環境変数/Secrets対応）
# ==============================
DEFAULT_API_BASE = "https://teamx-quest-api-234584649227.asia-northeast1.run.app"
# 優先順: 1) OS環境変数 2) Streamlit Secrets 3) デフォルト
API_BASE_URL = os.getenv("API_BASE_URL") or st.secrets.get("API_BASE_URL", DEFAULT_API_BASE)
JST = timezone(timedelta(hours=9))

st.set_page_config(
    page_title="Team X ブロックチェーン学習・クエスト証明",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"  # サイドバーは使わない
)

# ==============================
# CSS（カード/ボタン/フローティング・ステータス、h3アンカー消し）
# ==============================
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
        animation: slideDown 0.5s ease-out;
    }
    
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .highlight-box {
        background: #f8f9fa; padding: 1rem; border-radius: 10px;
        border-left: 4px solid #1e3c72; margin: 1rem 0; font-size: 0.9rem;
    }
    .big-number { font-size: 2rem; font-weight: bold; color: #1e3c72; text-align: center; }
    .certificate {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1.5rem; border-radius: 15px;
        text-align: center; margin: 1.5rem 0;
    }
    .benefit-box {
        background: #e3f2fd; padding: 1rem; border-radius: 10px;
        margin: 1rem 0; border: 1px solid #90caf9; font-size: 0.9rem;
    }
    .step-indicator {
        background: #1e3c72; color: white; padding: 0.4rem 0.8rem;
        border-radius: 20px; display: inline-block; margin-bottom: 1rem; font-size: 0.85rem;
    }
    
    .step-completed {
        background: #4caf50; color: white; padding: 0.4rem 0.8rem;
        border-radius: 20px; display: inline-block; margin-bottom: 1rem; font-size: 0.85rem;
    }

    /* ボタンはカード/ナビ内のみワイド化 */
    .demo-card div[data-testid="stButton"] > button,
    .step-nav  div[data-testid="stButton"] > button { width: 100%; padding: 0.8rem; font-size: 1rem; }
    .demo-card div[data-testid="stButton"] > button:disabled,
    .step-nav  div[data-testid="stButton"] > button:disabled {
        background-color: #cccccc !important; color: #666666 !important;
        cursor: not-allowed !important; opacity: 0.6 !important;
    }

    /* ラベル無し内部ボタンを非表示（謎の空白pill対策） */
    div[data-testid="stButton"] > button:empty { display:none !important; padding:0 !important; border:0 !important; width:0 !important; height:0 !important; }

    .step-nav { margin-top: 1rem; }
    .soft-hr { border: none; border-top: 1px solid #ECEFF4; margin: 16px 0; }

    /* 右下フローティング・ステータス */
    .status-float { position: fixed; right: 16px; bottom: 16px; z-index: 1000; }
    @media (max-width: 600px) { .status-float { right: 10px; bottom: 10px; transform: scale(.95); } }

    /* h3 見出しのアンカーリンクアイコンを非表示 */
    h3 a, .stMarkdown h3 a, h3 .anchor, h3 .anchor-link { display: none !important; }
    
    /* 完了セクションを少し薄く */
    .completed-section {
        opacity: 0.9;
    }
    
    /* プログレスバー */
    .progress-container {
        background: #f0f0f0;
        border-radius: 10px;
        height: 8px;
        margin: 1rem 0;
        overflow: hidden;
    }
    .progress-bar {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        height: 100%;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# ユーティリティ
# ==============================
def now_jst_str(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.now(JST).strftime(fmt)

def clean_html(s: str) -> str:
    s = dedent(s)
    s = re.sub(r'^[ \t]+', '', s, flags=re.MULTILINE)
    return s.strip()

def card(md: str, completed=False):
    class_name = "demo-card completed-section" if completed else "demo-card"
    st.markdown(f'<div class="{class_name}">{clean_html(md)}</div>', unsafe_allow_html=True)

def hr():
    st.markdown('<hr class="soft-hr" />', unsafe_allow_html=True)

def primary_button(label: str, disabled: bool = False):
    try:
        return st.button(label, type="primary", use_container_width=True, disabled=disabled)
    except TypeError:
        return st.button(label, disabled=disabled)

# --- Query Params helpers（新旧API両対応） ---
def _qp_get():
    try:
        return dict(st.query_params)
    except Exception:
        return st.experimental_get_query_params()

def _qp_update(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

def goto_next_step():
    # 次のステップへ進む（スクロールは不要に）
    st.session_state.demo_step += 1
    _qp_update(step=str(st.session_state.demo_step), api='1' if st.session_state.api_on else '0')
    st.rerun()

def reset_demo():
    # デモをリセット
    st.session_state.demo_step = 0
    defaults = dict(
        records=[],
        show_certificate=False,
        blockchain_recorded=False,
        nft_issued=False,
        hash_value=None,
        block_info=None,
        nft_hash=None,
        certificate_id=None,
    )
    for k, v in defaults.items():
        st.session_state[k] = v
    _qp_update(step='0', api='1' if st.session_state.api_on else '0')
    st.rerun()

# --- APIラッパー ---
def render_status_float(container, mode_on: bool, last_ok: bool | None):
    if not mode_on:
        text = "API: OFF（手動）"; bg, fg = "#F1F3F4", "#5F6368"
    else:
        if last_ok is True:
            text = "API: 🟢 ONLINE"; bg, fg = "#E6F4EA", "#137333"
        elif last_ok is False:
            text = "API: 🔴 OFFLINE（フォールバック）"; bg, fg = "#FCE8E6", "#A50E0E"
        else:
            text = "API: ⏳ 未チェック"; bg, fg = "#FFF4CE", "#5C2E00"
    container.markdown(
        f"<div class='status-float'><span style='padding:4px 10px; border-radius:12px; background:{bg}; color:{fg}; font-size:0.85rem;'>{text}</span></div>",
        unsafe_allow_html=True
    )

def ping_api(timeout=3) -> bool:
    try:
        r = requests.get(f"{API_BASE_URL}/api/v1/quests/available", timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False

def hit_api(path: str, timeout=5):
    try:
        r = requests.get(f"{API_BASE_URL}{path}", timeout=timeout)
        if r.status_code == 200:
            return r.json(), True
        return {}, False
    except requests.RequestException:
        return {}, False

def get_quests_available():
    if not st.session_state.api_on:
        return {"status": "available", "quests": [], "total_count": 0}, None
    data, ok = hit_api("/api/v1/quests/available")
    if not ok:
        data = {"status": "available", "quests": [], "total_count": 0}
    st.session_state.api_last_ok = ok
    return data, ok

def get_profile():
    if not st.session_state.api_on:
        return {}, None
    data, ok = hit_api("/api/v1/profile")
    if not ok:
        data = {}
    st.session_state.api_last_ok = ok
    return data, ok

# ==============================
# セッション状態 初期化
# ==============================
if "demo_step" not in st.session_state:
    qp = _qp_get()
    raw = qp.get("step")
    if isinstance(raw, list):
        raw = raw[0]
    try:
        st.session_state.demo_step = int(raw) if raw is not None else 0
    except Exception:
        st.session_state.demo_step = 0

if "api_on" not in st.session_state:
    qp = _qp_get()
    raw_api = qp.get("api")
    if isinstance(raw_api, list):
        raw_api = raw_api[0]
    st.session_state.api_on = (raw_api is None) or (str(raw_api) == "1")  # デフォルトON
if "api_last_ok" not in st.session_state:
    st.session_state.api_last_ok = None

defaults = dict(
    records=[],
    show_certificate=False,
    blockchain_recorded=False,
    nft_issued=False,
    hash_value=None,
    block_info=None,
    nft_hash=None,
    certificate_id=None,
)
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ==============================
# ヘッダー（右上に⚙️ポップオーバー）
# ==============================
st.markdown("""
<div class="main-header">
    <h1>🎓 Team X ブロックチェーン学習・実績証明</h1>
    <p>実績を永久に、確実に、証明する</p>
</div>
""", unsafe_allow_html=True)

# プログレスバー
progress = (st.session_state.demo_step / 4) * 100
st.markdown(f"""
<div class="progress-container">
    <div class="progress-bar" style="width: {progress}%;"></div>
</div>
""", unsafe_allow_html=True)

# ヘッダー直下の右寄せ行に、控えめな設定ボタン
c_left, c_right = st.columns([1, 5])
with c_right:
    cols = st.columns([8, 2])  # 右端に小さく
    with cols[1]:
        try:
            with st.popover("⚙️", use_container_width=False):
                try:
                    toggled = st.toggle("API連携を有効化", value=st.session_state.api_on)
                except TypeError:
                    toggled = st.checkbox("API連携を有効化", value=st.session_state.api_on)
                if toggled != st.session_state.api_on:
                    st.session_state.api_on = bool(toggled)
                    _qp_update(step=str(st.session_state.demo_step), api='1' if toggled else '0')
                    st.rerun()

                if st.button("接続テスト", use_container_width=True):
                    ok = ping_api()
                    st.session_state.api_last_ok = ok
                    if ok:
                        st.success("APIはONLINEです。")
                    else:
                        st.warning("APIに接続できません（フォールバック表示）。")
        except Exception:
            with st.expander("⚙️ API設定", expanded=False):
                try:
                    toggled = st.toggle("API連携を有効化", value=st.session_state.api_on)
                except TypeError:
                    toggled = st.checkbox("API連携を有効化", value=st.session_state.api_on)
                if toggled != st.session_state.api_on:
                    st.session_state.api_on = bool(toggled)
                    _qp_update(step=str(st.session_state.demo_step), api='1' if toggled else '0')
                    st.rerun()

                if st.button("接続テストを実行", use_container_width=True):
                    ok = ping_api()
                    st.session_state.api_last_ok = ok
                    if ok:
                        st.success("APIはONLINEです。")
                    else:
                        st.warning("APIに接続できません（フォールバック表示）。")

# 右下のフローティング・ステータス（常に1つだけ）
status_float = st.empty()
render_status_float(status_float, st.session_state.api_on, st.session_state.api_last_ok)

# ==============================
# コンテンツ（累積表示方式）
# ==============================

# ステップ 0: はじめに（常に表示）
if st.session_state.demo_step >= 0:
    is_completed = st.session_state.demo_step > 0
    if is_completed:
        st.markdown('<div class="step-completed">✅ 導入: 完了</div>', unsafe_allow_html=True)
    
    card("""
    <h3>🤔 現在の課題</h3>
    <div class="highlight-box">
        <ul>
            <li>学習やクエスト履歴の<strong>信頼性</strong>が保証できない</li>
            <li>他機関での<strong>実績証明</strong>が困難</li>
            <li>データの<strong>改ざんリスク</strong></li>
        </ul>
    </div>
    <h3>✨ ブロックチェーンで解決</h3>
    <div class="benefit-box">
        <ul>
            <li>🔒 <strong>改ざん不可能</strong>な記録</li>
            <li>🌍 <strong>世界中で証明</strong>可能</li>
            <li>♾️ <strong>永久保存</strong></li>
        </ul>
    </div>
    """, completed=is_completed)
    
    if st.session_state.demo_step == 0:
        hr()
        if primary_button("🚀 実際に体験してみる"):
            goto_next_step()

# ステップ 1: 学習記録を保存
if st.session_state.demo_step >= 1:
    hr()
    is_completed = st.session_state.demo_step > 1
    if is_completed:
        st.markdown('<div class="step-completed">✅ ステップ 1/3: 完了</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-indicator">ステップ 1/3: 学習記録を保存</div>', unsafe_allow_html=True)
    
    card("""
    <h3>📝 拓叶さんが「Python基礎講座」を完了</h3>
    <div class="highlight-box">
        <p><strong>受講者:</strong> 拓叶さん</p>
        <p><strong>コース:</strong> Python基礎講座</p>
        <p><strong>完了日:</strong> 2025年8月30日</p>
        <p><strong>スコア:</strong> 95点</p>
    </div>
    """, completed=is_completed)
    
    if st.session_state.demo_step == 1:
        if not st.session_state.blockchain_recorded:
            if primary_button("🔗 ブロックチェーンに記録する"):
                with st.spinner("記録を保存中..."):
                    time.sleep(1.2)
                payload = f"拓叶-Python基礎講座-95点-{now_jst_str()}"
                hash_value = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                st.session_state.hash_value = hash_value
                st.session_state.block_info = {"number": 1247, "timestamp": now_jst_str()}
                st.session_state.records.append({
                    "name": "拓叶", "course": "Python基礎講座", "score": 95,
                    "hash": hash_value, "date": "2025-08-30",
                })
                st.session_state.blockchain_recorded = True
                st.rerun()
        else:
            primary_button("✅ ブロックチェーンに記録済み", disabled=True)

    if st.session_state.blockchain_recorded and st.session_state.hash_value:
        card(f"""
        <div class="highlight-box" style="background: #e8f5e9;">
            <p><strong>🔐 記録ID:</strong></p>
            <code>{st.session_state.hash_value[:24]}...</code>
        </div>
        <div class="highlight-box" style="background: #f5f5f5;">
            <p><strong>📦 ブロック情報:</strong></p>
            <p>ブロック番号: #{st.session_state.block_info['number']}</p>
            <p>タイムスタンプ: {st.session_state.block_info['timestamp']}</p>
            <p>ネットワーク: Polygon Amoy (testnet)</p>
        </div>
        <div class="benefit-box" style="background:#e8f4ff;border-color:#90caf9;">
            💡 学習記録もNFT証明書として発行できます
        </div>
        """, completed=is_completed)

    if st.session_state.demo_step == 1 and st.session_state.blockchain_recorded:
        st.markdown('<div class="step-nav">', unsafe_allow_html=True)
        if primary_button("次のステップへ"):
            goto_next_step()
        st.markdown('</div>', unsafe_allow_html=True)

# ステップ 2: デジタル証明書の発行
if st.session_state.demo_step >= 2:
    hr()
    is_completed = st.session_state.demo_step > 2
    if is_completed:
        st.markdown('<div class="step-completed">✅ ステップ 2/3: 完了</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-indicator">ステップ 2/3: デジタル証明書の発行</div>', unsafe_allow_html=True)
    
    quests_json, ok = get_quests_available()
    quests = quests_json.get("quests", [])
    if isinstance(quests, list) and quests:
        q = quests[0]
        quest_title = str(q.get("title", "地域農産物PR用SNS運用"))
        quest_provider = str(q.get("provider_name") or q.get("provider") or "Team X")
    else:
        quest_title = "地域農産物PR用SNS運用"
        quest_provider = "Team X"
    render_status_float(status_float, st.session_state.api_on, ok if st.session_state.api_on else None)

    card(f"""
    <h3>🎓 クエスト完了！</h3>
    <p><strong>「{escape(quest_title)}」</strong></p>
    <div class="highlight-box">
        <p><strong>提供元:</strong> {escape(quest_provider)}</p>
        <p><strong>期間:</strong> 3ヶ月</p>
        <p><strong>成果:</strong> フォロワー2,000人獲得</p>
        <p><strong>獲得スキル:</strong> SNS運用、マーケティング、データ分析</p>
    </div>
    """, completed=is_completed)
    
    if st.session_state.demo_step == 2:
        if not st.session_state.show_certificate:
            if primary_button("🎨 NFT証明書を発行"):
                with st.spinner("NFT証明書を生成中..."):
                    time.sleep(1.2)
                nft_data = f"QuestNFT-{quest_title}-拓叶-{now_jst_str()}"
                st.session_state.nft_hash = hashlib.sha256(nft_data.encode("utf-8")).hexdigest()
                st.session_state.certificate_id = "TXQ-0023"
                st.session_state.show_certificate = True
                st.session_state.nft_issued = True
                st.rerun()
        else:
            primary_button("✅ NFT証明書発行済み", disabled=True)
    
    if st.session_state.show_certificate:
        card(f"""
        <div class="certificate">
            <h3>🏅 デジタル証明書</h3>
            <p>Quest Completion NFT</p>
            <p><strong>ID:</strong> #{st.session_state.certificate_id}</p>
            <p><strong>所有者:</strong> 拓叶</p>
            <p style="font-size: 0.7rem;"><strong>Hash:</strong> {st.session_state.nft_hash[:12]}...</p>
            <hr style="opacity: 0.3; margin: 1rem 0;">
        </div>
        """, completed=is_completed)
        if st.session_state.demo_step == 2:
            st.success("✅ NFT証明書が発行されました！")
    
    if st.session_state.demo_step == 2 and st.session_state.nft_issued:
        st.markdown('<div class="step-nav">', unsafe_allow_html=True)
        if primary_button("次のステップへ"):
            goto_next_step()
        st.markdown('</div>', unsafe_allow_html=True)

# ステップ 3: 企業での活用
if st.session_state.demo_step >= 3:
    hr()
    is_completed = st.session_state.demo_step > 3
    if is_completed:
        st.markdown('<div class="step-completed">✅ ステップ 3/4: 完了</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-indicator">ステップ 3/4: 企業での活用</div>', unsafe_allow_html=True)
    
    card("""
    <h3>🏢 採用企業での活用</h3>
    <div class="benefit-box">
        <h4>株式会社〇〇 人事部</h4>
        <p><strong>応募者:</strong> 拓叶</p>
        <p><strong>証明書ID:</strong> #TXQ-0023</p>
        <p><strong>検証結果:</strong> <span style="color: green;">✓ 真正性確認済み</span></p>
        <hr style="margin: 0.5rem 0;">
        <p><strong>確認された実績:</strong></p>
        <ul style="font-size: 0.85rem;">
            <li>Python基礎講座 (95点)</li>
            <li>地域農産物PR用SNS運用</li>
            <li>総合スコア: 782点</li>
        </ul>
    </div>
    """, completed=is_completed)
    
    card("""
    <h3>🔍 証明書の検証プロセス</h3>
    <div class="highlight-box">
        <ol style="font-size: 0.9rem;">
            <li><strong>証明書IDの入力</strong><br>応募者が提出した証明書IDを入力</li>
            <li><strong>ブロックチェーン照会</strong><br>分散台帳から該当記録を検索</li>
            <li><strong>真正性の確認</strong><br>改ざん不可能なデータで実績を確認</li>
            <li><strong>詳細情報の取得</strong><br>学習履歴、スコア、完了日時を確認</li>
        </ol>
    </div>
    """, completed=is_completed)
    
    if st.session_state.demo_step == 3:
        st.markdown('<div class="step-nav">', unsafe_allow_html=True)
        if primary_button("次のステップへ"):
            goto_next_step()
        st.markdown('</div>', unsafe_allow_html=True)

# ステップ 4: システムの全体像
if st.session_state.demo_step >= 4:
    hr()
    st.markdown('<div class="step-indicator">ステップ 4/4: システムの全体像</div>', unsafe_allow_html=True)
    profile_json, ok = get_profile()
    render_status_float(status_float, st.session_state.api_on, ok if st.session_state.api_on else None)

    total_score = profile_json.get("user", {}).get("current_total_score") if profile_json else None
    if total_score is None:
        total_score = 782

    card(f"""
    <h3>📊 記録された実績</h3>
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
        <div><div class="big-number">{total_score}</div><p style="text-align:center; font-size:0.8rem;">総合スコア</p></div>
        <div><div class="big-number">15</div><p style="text-align:center; font-size:0.8rem;">完了クエスト</p></div>
        <div><div class="big-number">8</div><p style="text-align:center; font-size:0.8rem;">NFT証明書</p></div>
    </div>
    """)

    rec_html = []
    sample_records = [
        {"title": "Python基礎講座", "score": 95},
        {"title": "データ分析入門", "score": 88},
        {"title": "機械学習基礎", "score": 92},
    ]
    for r in sample_records:
        hv = hashlib.sha256(f"{r['title']}-{r['score']}".encode("utf-8")).hexdigest()
        rec_html.append(f"""
<div class="highlight-box" style="margin-bottom: 0.5rem; padding: 0.8rem;">
<p style="margin: 0;"><strong>{escape(r['title'])}</strong> ({r['score']}点)</p>
<p style="font-size: 0.7rem; color: #666; margin: 0.3rem 0 0 0;">Hash: {hv[:20]}...</p>
</div>""")
    card("""
    <h3>🔍 検証可能な学習履歴</h3>
    """ + "\n".join(rec_html))

    card("""
    <h3>🔧 技術仕様</h3>
    <div class="highlight-box">
        <h4 style="font-size: 1rem;">推奨プラットフォーム</h4>
        <p><strong>🟣 Polygon PoS（Amoy testnet / Mainnet）</strong></p>
        <ul style="font-size: 0.85rem;">
            <li>EVM互換</li><li>高速処理（数秒/取引）</li><li>低コスト</li><li>環境負荷が少ない</li>
        </ul>
        <hr style="margin: 1rem 0;">
        <h4 style="font-size: 1rem;">データ保存</h4>
        <ul style="font-size: 0.85rem;">
            <li><strong>メタデータ:</strong> ブロックチェーン上</li>
            <li><strong>詳細データ:</strong> IPFSなど分散ストレージ</li>
            <li><strong>バックアップ:</strong> 既存DB併用</li>
        </ul>
    </div>
    <h3>🎯 期待効果</h3>
    <div class="benefit-box" style="background: #fff3e0; border-color: #ffb74d;">
        <ul>
            <li>📈 <strong>信頼性向上</strong>による利用者増</li>
            <li>🤝 <strong>企業連携</strong>の拡大</li>
            <li>🔄 <strong>データ活用</strong>の新規事業</li>
        </ul>
    </div>
    <h3>🎨 NFT証明書の種類</h3>
    <div class="highlight-box">
        <h4 style="font-size: 0.95rem;">📚 学習系証明書</h4>
        <ul style="font-size: 0.85rem;">
            <li>各講座の修了証明書</li><li>スキルレベル認定証</li><li>総合スコア達成証</li>
        </ul>
    </div>
    <div class="highlight-box">
        <h4 style="font-size: 0.95rem;">🏆 実績系証明書</h4>
        <ul style="font-size: 0.85rem;">
            <li>クエスト完了証明</li><li>プロジェクト参加証</li><li>特別功績証</li>
        </ul>
    </div>
    """)

    st.markdown('<div class="step-nav">', unsafe_allow_html=True)
    if primary_button("🔄 最初から見る"):
        reset_demo()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# フッター
# ==============================
hr()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    <p>Team X - ブロックチェーン　モック</p>
</div>
""", unsafe_allow_html=True)
