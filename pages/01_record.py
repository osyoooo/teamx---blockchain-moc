import streamlit as st
import hashlib, time
from utils import css, header, card, primary_button, go, now_jst_str

st.set_page_config(page_title="学習記録", page_icon="📝",
                   layout="centered", initial_sidebar_state="collapsed")

css(); header()

st.markdown('<div class="step-indicator">ステップ 1/3: 学習記録を保存</div>', unsafe_allow_html=True)

# state 初期化
for k, v in dict(blockchain_recorded=False, hash_value=None, block_info=None, records=[]).items():
    st.session_state.setdefault(k, v)

card("""
<h3>📝 拓叶さんが「Python基礎講座」を完了</h3>
<div class="highlight-box">
  <p><strong>受講者:</strong> 拓叶さん</p>
  <p><strong>コース:</strong> Python基礎講座</p>
  <p><strong>完了日:</strong> 2025年8月30日</p>
  <p><strong>スコア:</strong> 95点</p>
</div>
""")

if not st.session_state.blockchain_recorded:
    if primary_button("🔗 ブロックチェーンに記録する"):
        with st.spinner("記録を保存中..."):
            time.sleep(1.0)
        payload = f"拓叶-Python基礎講座-95点-{now_jst_str()}"
        hv = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        st.session_state.hash_value = hv
        st.session_state.block_info = {"number": 1247, "timestamp": now_jst_str()}
        st.session_state.records.append({"name":"拓叶","course":"Python基礎講座","score":95,"hash":hv,"date":"2025-08-30"})
        st.session_state.blockchain_recorded = True
        st.rerun()
else:
    primary_button("✅ ブロックチェーンに記録済み", disabled=True)

if st.session_state.blockchain_recorded and st.session_state.hash_value:
    card(f"""
    <div class="highlight-box" style="background:#e8f5e9;">
      <p><strong>🔐 記録ID:</strong></p>
      <code>{st.session_state.hash_value[:24]}...</code>
      <p style="margin-top:1rem;"><em>この記録は永久に保存され、改ざんできません</em></p>
    </div>
    <div class="highlight-box" style="background:#f5f5f5;">
      <p><strong>📦 ブロック情報:</strong></p>
      <p>ブロック番号: #1247</p>
      <p>タイムスタンプ: {st.session_state.block_info['timestamp']}</p>
      <p>ネットワーク: Polygon Amoy (testnet)</p>
    </div>
    <div class="benefit-box" style="background:#e8f4ff;border-color:#90caf9;">
      💡 学習記録もNFT証明書として発行できます
    </div>
    """)

if st.session_state.blockchain_recorded:
    if primary_button("次のステップへ →"):
        go("02_nft.py")
