DEFAULT_TEMPLATE = '{prompt} Output the rating as an integer. ASSISTANT: Rating (1-10): '
CHAT_TEMPLATE = '{prompt} \nEND OF SAMPLE. Now, the rating as an integer from 1-10:\n'
GUANACO_TEMPLATE = "A chat between a curious human and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions. ### Human: {prompt} ### Assistant: Rating (1-10): "
ORCA_TEMPLATE = '<|system|>You are an AI assistant that follows instruction extremely well. Help as much as you can.</s><|prompter|>{prompt}</s><|assistant|>Rating (1-10): '
OPENCHAT_TEMPLATE = "GPT4 User: {prompt}<|end_of_turn|>GPT4 Assistant: Rating (1-10): "
VICUNA_TEMPLATE = 'User: {prompt} Assistant: Rating (1-10): '
LLM_TEMPLATES = {
    'ai21-j2-mid': CHAT_TEMPLATE,
    'gpt-3.5-turbo': CHAT_TEMPLATE,
    'cohere-command-nightly': CHAT_TEMPLATE,
    'TheBloke/wizardLM-13B-1.0-fp16': DEFAULT_TEMPLATE,
    'timdettmers/guanaco-33b-merged': DEFAULT_TEMPLATE,
    'meta-llama/Llama-2-13b-hf': DEFAULT_TEMPLATE,
    'meta-llama/Llama-2-70b-hf': DEFAULT_TEMPLATE,
    'WizardLM/WizardLM-13B-V1.2': DEFAULT_TEMPLATE,
    'TheBloke/llama-2-70b-Guanaco-QLoRA-fp16': DEFAULT_TEMPLATE,
    'baichuan-inc/Baichuan-13B-Base': DEFAULT_TEMPLATE,
    'OpenAssistant/llama2-13b-orca-8k-3319': ORCA_TEMPLATE,
    'openchat/openchat_v3.1': OPENCHAT_TEMPLATE,
    'augtoma/qCammel-70-x': VICUNA_TEMPLATE
}
