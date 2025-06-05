# streamlit_app.py

import streamlit as st
from openai import OpenAI
from parse_hh import get_html, extract_vacancy_data, extract_resume_data

import os

# Настройка client: берём ключ из переменных среды или из streamlit secrets
api_key = None
# 1) Если вы используете streamlit Cloud и сохранили ключ в secrets.toml:
if "openai_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    # 2) Иначе попытаемся прочитать из переменной окружения
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Ошибка: не найден ключ OPENAI_API_KEY. Проверьте переменные среды или файл secrets.toml")
    st.stop()

client = OpenAI(api_key=api_key)

# Системный промпт, задающий поведение модели
SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.
Сначала напиши краткий аналитический комментарий, поясняющий свою оценку.
Отдельно оцени качество оформления резюме (ясно ли описаны задачи, решения и результаты).
В конце представь итоговую оценку соответствия кандидата вакансии по шкале от 1 до 10.
""".strip()


def request_gpt(system_prompt: str, user_prompt: str) -> str:
    """
    Отправляет запрос в openai GPT, возвращает ответ модели.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",         # используем компактную версию GPT-4
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0.0,             # точная оценка, без креатива
    )
    return response.choices[0].message.content


# Интерфейс Streamlit
st.set_page_config(page_title="ИИ-ассистент: прескоринг кандидатов", layout="centered")
st.title("🤖 ИИ-ассистент для прескоринга кандидатов на вакансии")

st.markdown(
    """
    **Как пользоваться:**  
    1. Введите **ссылку** на вакансию (страница hh.ru или другого сайта), либо скопируйте и вставьте **текст** вакансии.  
    2. Введите **ссылку** на резюме кандидата, либо скопируйте и вставьте **текст** резюме.  
    3. Нажмите кнопку **«Проанализировать кандидата»**, дождитесь обработки.  
    4. Результатом будет аналитический комментарий от модели и оценка по шкале от 1 до 10.
    """
)

# Ввод данных
col1, col2 = st.columns(2)
with col1:
    job_input = st.text_area("Введите ссылку на вакансию или сам текст вакансии", height=150)
with col2:
    cv_input = st.text_area("Введите ссылку на резюме или сам текст резюме", height=150)

# Кнопка запуска анализа
if st.button("🔍 Проанализировать кандидата"):
    with st.spinner("Идёт анализ резюме и вакансии..."):
        # Проверим, является ли введённая строка ссылкой (начинается с http)
        try:
            # Обработка вакансии
            if job_input.strip().lower().startswith("http"):
                job_html = get_html(job_input)
                job_text = extract_vacancy_data(job_html)
            else:
                job_text = job_input.strip()

            # Обработка резюме
            if cv_input.strip().lower().startswith("http"):
                resume_html = get_html(cv_input)
                resume_text = extract_resume_data(resume_html)
            else:
                resume_text = cv_input.strip()

            # Формируем единый пользовательский промпт
            user_prompt = f"# Вакансия\n{job_text}\n\n# Резюме\n{resume_text}"

            # Запрос к GPT
            result = request_gpt(SYSTEM_PROMPT, user_prompt)
            st.subheader("📊 Результат анализа:")
            st.markdown(result)

        except Exception as e:
            st.error(f"Произошла ошибка при обработке: {e}")
