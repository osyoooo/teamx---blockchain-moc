import streamlit as st
from utils import css, header, card, primary_button, go, get_profile

st.set_page_config(page_title="全体像", page_icon="📊",
                   layout="centered", initial_sidebar_state="collapsed")

css(); header()
st.markdown('<div class="step-indicator">ステップ 3/3: システムの全体像</div>', unsafe_allow_html=True)

profile_json, _ = get_profile()
total_score = profile_json.get("user", {}).get("current_total_score", 782)

card(f"""
<h3>📊 記録された実績</h3>
<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
  <div><div class="big-number">{total_score}</div><p style="text-align:center; font-size:.8rem;">総合スコア</p></div>
  <div><div class="big-number">15</div><p style="text-align:center; font-size:.8rem;">完了クエスト</p></div>
  <div><div class="big-number">8</div><p style="text-align:center; font-size:.8rem;">NFT証明書</p></div>
</div>
""")

# デモ履歴
from hashlib import sha256
def h(s): return sha256(s.encode("utf-8")).hexdigest()[:20]
records = [("Python基礎講座",95),("データ分析入門",88),("機械学習基礎",92)]
card("<h3>🔍 検証可能な学習履歴</h3>"+ "".join([
    f"""<div class="highlight-box" style="margin-bottom:.5rem; padding:.8rem;">
    <p style="margin:0;"><strong>{title}</strong> ({score}点)</p>
    <p style="font-size:.7rem; color:#666; margin:.3rem 0 0 0;">Hash: {h(f"{title}-{score}")}...</p>
    </div>""" for title,score in records
]))

card("""
<h3>💰 運用コスト</h3>
<div class="highlight-box">
  <h4 style="font-size:1rem;">月間1,000人利用時</h4>
  <ul>
    <li>記録1件: <strong>約1円</strong></li>
    <li>月間記録数: 1,000件</li>
  </ul>
  <p style="text-align:center; margin-top:1rem;">
    <strong style="color:#1e3c72; font-size:1.3rem;">月額: 約1,000円</strong>
  </p>
</div>
""")

card("""
<h3>🔧 技術仕様</h3>
<div class="highlight-box">
  <h4 style="font-size:1rem;">推奨プラットフォーム</h4>
  <p><strong>🟣 Polygon PoS（Amoy testnet / Mainnet）</strong></p>
  <ul style="font-size:.85rem;">
    <li>EVM互換</li><li>高速処理（数秒/取引）</li><li>低コスト</li><li>環境負荷が少ない</li>
  </ul>
  <hr style="margin:1rem 0;">
  <h4 style="font-size:1rem;">データ保存</h4>
  <ul style="font-size:.85rem;">
    <li><strong>メタデータ:</strong> ブロックチェーン上</li>
    <li><strong>詳細データ:</strong> IPFSなど分散ストレージ</li>
    <li><strong>バックアップ:</strong> 既存DB併用</li>
  </ul>
</div>
<h3>🎯 期待効果</h3>
<div class="benefit-box" style="background:#fff3e0; border-color:#ffb74d;">
  <ul>
    <li>📈 <strong>信頼性向上</strong>による利用者増</li>
    <li>🤝 <strong>企業連携</strong>の拡大</li>
    <li>🌟 <strong>ブランド価値</strong>の向上</li>
    <li>🔄 <strong>データ活用</strong>の新規事業</li>
  </ul>
</div>
<h3>🎨 NFT証明書の種類</h3>
<div class="highlight-box">
  <h4 style="font-size:.95rem;">📚 学習系証明書</h4>
  <ul style="font-size:.85rem;">
    <li>各講座の修了証明書</li><li>スキルレベル認定証</li><li>総合スコア達成証</li>
  </ul>
</div>
<div class="highlight-box">
  <h4 style="font-size:.95rem;">🏆 実績系証明書</h4>
  <ul style="font-size:.85rem;">
    <li>クエスト完了証明</li><li>プロジェクト参加証</li><li>特別功績証</li>
  </ul>
</div>
""")

if primary_button("🔄 最初から見る"):
    go("../streamlit_app.py")  # ルートへ
