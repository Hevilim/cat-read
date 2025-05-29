from transformers import pipeline


# Загружаем пайплайн один раз
summarizer = pipeline("summarization", model="csebuetnlp/mT5_multilingual_XLSum")


def summarize_text_llm(text, max_length=130, min_length=30):
    # Обрезаем текст, если он слишком длинный
    if len(text) > 1024:
        text = text[:1024]
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']
