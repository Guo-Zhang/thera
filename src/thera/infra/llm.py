from openai import OpenAI

from src.thera.config import settings


def main():
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": "推理模型会给市场带来哪些新的机会"}],
        stream=True,
    )

    for chunk in response:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
        if chunk.choices[0].delta.reasoning_content:
            print(chunk.choices[0].delta.reasoning_content, end="", flush=True)


if __name__ == "__main__":
    main()
