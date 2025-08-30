import streamlit as st
import hashlib, time
from utils import css, header, card, primary_button, go, get_quests_available, render_status_float

st.set_page_config(page_title="NFT証明書", page_icon="🏅",
                   layout="centered", initial_sidebar_state="collapsed")

css(); header()
st.markdown('<div class="step-indicator">ステップ 2/3: デジタル証明書の発行</div>', unsafe_allow_html=True)

st.session_state.setdefault("show_certificate", False)
st.session_state.setdefault("nft_issued", False)
st.session_state.setdefault("nft_hash", None)
st.session_state.setdefault("certificate_id", None)

quests_json, ok = get_quests_available()
quests = quests_json.get("quests", [])
if quests:
    q = quests[0]
    quest_title = str(q.get("title", "地域農産物PR用SNS運用"))
    quest_provider = str(q.get("provider_name") or q.get("provider") or "Team X")
else:
    quest_title = "地域農産物PR用SNS運用"
    quest_provider = "Team X"

card(f"""
<h3>🎓 クエスト完了！</h3>
<p><strong>「{quest_title}」</strong></p>
<div class="highlight-box">
  <p><strong>提供元:</strong> {quest_provider}</p>
  <p><strong>期間:</strong> 3ヶ月</p>
  <p><strong>成果:</strong> フォロワー2,000人獲得</p>
  <p><strong>獲得スキル:</strong> SNS運用、マーケティング、データ分析</p>
</div>
""")

if not st.session_state.show_certificate:
    if primary_button("🎨 NFT証明書を発行"):
        with st.spinner("NFT証明書を生成中..."):
            time.sleep(1.0)
        hv = hashlib.sha256(f"QuestNFT-{quest_title}-拓叶".encode("utf-8")).hexdigest()
        st.session_state.nft_hash = hv
        st.session_state.certificate_id = "TXQ-0023"
        st.session_state.show_certificate = True
        st.session_state.nft_issued = True
        st.rerun()
else:
    primary_button("✅ NFT証明書発行済み", disabled=True)
    card(f"""
    <div class="certificate">
      <h3>🏅 デジタル証明書</h3>
      <p>Quest Completion NFT</p>
      <p><strong>ID:</strong> #{st.session_state.certificate_id}</p>
      <p><strong>所有者:</strong> 拓叶</p>
      <p style="font-size:.7rem;"><strong>Hash:</strong> {st.session_state.nft_hash[:12]}...</p>
      <hr style="opacity:.3; margin:1rem 0;">
      <p style="font-size:.85rem;">この証明書は世界中で有効です</p>
    </div>
    """)
    st.success("✅ NFT証明書が発行されました！")

card("""
<h3>🏢 採用企業での活用</h3>
<div class="benefit-box">
  <h4>株式会社〇〇 人事部</h4>
  <p><strong>応募者:</strong> 拓叶</p>
  <p><strong>証明書ID:</strong> #TXQ-0023</p>
  <p><strong>検証結果:</strong> <span style="color:green;">✓ 真正性確認済み</span></p>
  <hr style="margin:.5rem 0;">
  <p><strong>確認された実績:</strong></p>
  <ul style="font-size:.85rem;">
    <li>Python基礎講座 (95点)</li>
    <li>地域農産物PR用SNS運用</li>
    <li>総合スコア: 782点</li>
  </ul>
</div>
""")

# ナビゲーション
cols = st.columns(2)
with cols[0]:
    if primary_button("← 戻る"):
        go("01_record.py")
with cols[1]:
    if primary_button("次のステップへ →", disabled=not st.session_state.nft_issued):
        go("03_overview.py")
