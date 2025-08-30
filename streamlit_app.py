import streamlit as st
from utils import css, header, card, hr, primary_button, go

st.set_page_config(page_title="Team X ブロックチェーン学習証明", page_icon="🎓",
                   layout="centered", initial_sidebar_state="collapsed")

css()
header()

card("""
<h3>🤔 現在の課題</h3>
<div class="highlight-box">
  <ul>
    <li>学習履歴の<strong>信頼性</strong>が保証できない</li>
    <li>他機関での<strong>実績証明</strong>が困難</li>
    <li>データの<strong>改ざんリスク</strong></li>
    <li>システム終了で<strong>記録が消失</strong></li>
  </ul>
</div>
<h3>✨ ブロックチェーンで解決</h3>
<div class="benefit-box">
  <ul>
    <li>🔒 <strong>改ざん不可能</strong>な記録</li>
    <li>🌍 <strong>世界中で証明</strong>可能</li>
    <li>♾️ <strong>永久保存</strong></li>
    <li>💰 <strong>低コスト</strong>（1件1円）</li>
  </ul>
</div>
""")

hr()
if primary_button("🚀 実際に体験してみる"):
    go("01_record.py")
