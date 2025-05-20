# cv_prescore.py
import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup

# ─── Configuration ─────────────────────────────────────────────────────────────
openai.api_key = st.secrets["OPENAI_API_KEY"]  # or set via ENV var OPENAI_API_KEY

SYSTEM_PROMPT = """
You are an HR-assistant. Your task is:
1) Provide a concise analytical comment on how well the candidate matches.
2) Then give a single score from 1 to 10 for overall fit.
Always respond in two parts: first analysis, then "Score: X/10".
Be objective and professional.
"""


# ─── Helpers ────────────────────────────────────────────────────────────────────
def fetch_hh_vacancy_text(url: str) -> str:
	"""Fetch and clean main vacancy text from hh.ru."""
	resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
	resp.raise_for_status()
	soup = BeautifulSoup(resp.text, "html.parser")
	blocks = []
	# Title
	title = soup.select_one("h1")
	if title:
		blocks.append(f"# {title.get_text().strip()}\n")
	# Key sections
	for sel in [".vacancy-description__text", ".bloko-section"]:
		for node in soup.select(sel):
			text = node.get_text(separator="\n").strip()
			if text:
				blocks.append(text + "\n")
	return "\n".join(blocks)


def build_user_prompt(vacancy: str, resume: str) -> str:
	return f"""# Vacancy description:
{vacancy}

# Candidate résumé:
{resume}

Please analyze and score."""


def query_openai(system: str, user: str) -> str:
	resp = openai.ChatCompletion.create(
		model="gpt-4",
		messages=[
			{"role": "system", "content": system},
			{"role": "user", "content": user},
		],
		temperature=0.0,
		max_tokens=512,
		n=1,
	)
	return resp.choices[0].message.content.strip()


# ─── Streamlit UI ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Prescorer", layout="centered")
st.title("🤖 AI-Assistant: Prescoring Candidates")

st.markdown(
	"""
	Paste a vacancy link from hh.ru or enter text manually, then paste the candidate’s résumé.
	The assistant will first give a short analysis, then a score 1–10.
	"""
)

vacancy_input_mode = st.radio("Vacancy input:", ["URL (hh.ru)", "Manual text"])
vacancy_text = ""
if vacancy_input_mode == "URL (hh.ru)":
	url = st.text_input("Vacancy URL")
	if url:
		with st.spinner("Fetching vacancy..."):
			try:
				vacancy_text = fetch_hh_vacancy_text(url)
			except Exception as e:
				st.error(f"Failed to fetch: {e}")
else:
	vacancy_text = st.text_area("Paste vacancy description")

resume_text = st.text_area("Paste candidate résumé here")

if st.button("Analyze & Score") and vacancy_text and resume_text:
	with st.spinner("Calling AI-assistant…"):
		user_prompt = build_user_prompt(vacancy_text, resume_text)
		try:
			result = query_openai(SYSTEM_PROMPT, user_prompt)
			st.markdown("**Result:**")
			# split Analysis vs Score
			if "Score:" in result:
				analysis, score = result.rsplit("Score:", 1)
				st.markdown(f"**Analysis:**\n>{analysis.strip()}")
				st.markdown(f"**Score:** {score.strip()}")
			else:
				st.markdown(f"> {result}")
		except Exception as e:
			st.error(f"OpenAI error: {e}")

# ─── End ────────────────────────────────────────────────────────────────────────
