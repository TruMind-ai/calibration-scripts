rating_suffix = 'Rating: Level '
DEFAULT_TEMPLATE = '{prompt} Output the rating as an integer. ASSISTANT:' + rating_suffix
CHAT_TEMPLATE = '{prompt} \nEND OF SAMPLE. Now, the rating as an integer from 1-10:\n'
GUANACO_TEMPLATE = "A chat between a curious human and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions. ### Human: {prompt} ### Assistant:" + rating_suffix
ORCA_TEMPLATE = '<|system|>You are an AI assistant that follows instruction extremely well. Help as much as you can.</s><|prompter|>{prompt}</s><|assistant|>' + rating_suffix
OPENCHAT_TEMPLATE = "GPT4 User: {prompt}<|end_of_turn|>GPT4 Assistant:" + rating_suffix
VICUNA_TEMPLATE = 'User: {prompt} Assistant:' + rating_suffix
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
