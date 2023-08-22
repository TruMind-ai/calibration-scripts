
BAICHUAN = 'baichuan-inc/Baichuan-13B-Base'
L2_ORCA = 'OpenAssistant/llama2-13b-orca-8k-3319'
L2_OPENCHAT = 'openchat/openchat_v3.1'
L2_VOICELAB = 'Voicelab/trurl-2-13b'
L2 = 'meta-llama/Llama-2-13b-hf'
L2_ORCA_CIRCULUS = 'circulus/Llama-2-13b-orca-v1'


ALL_DIMENSIONS = [ 'authority', 'consensus',
              'consistency', 'scarcity', 'unity', 'liking', 'reciprocity']

ALL_LLMS = [BAICHUAN, L2_OPENCHAT, L2_OPENCHAT, L2_VOICELAB, L2]

LLM_ABBR_MAP = {
    'OpenAssistant/llama2-13b-orca-8k-3319': 'BAICHUAN',
    'openchat/openchat_v3.1': 'L2_OPENCHAT',
    'baichuan-inc/Baichuan-13B-Base': 'L2_ORCA',
    'Voicelab/trurl-2-13b': 'L2_VOICELAB'
}

DEFAULT_TEMPLATE_V2 = 'task:\n{prompt}\nYour rating: '
CHAT_TEMPLATE_V2 = 'task:\n{prompt}\nEND OF SAMPLE. Now, output the rating as an integer from 1-10:\n'
GUANACO_TEMPLATE_V2 = "task:\n{prompt}\n### Assistant: Rating: "
ORCA_TEMPLATE_V2 = 'task:\n{prompt}\n</s><|assistant|>Rating: ' 
OPENCHAT_TEMPLATE_V2 = "task:\n{prompt}\n<|end_of_turn|>GPT4 Assistant: Rating: "
VICUNA_TEMPLATE_V2 = 'User: {prompt} Assistant:Rating: ', 
VOICELAB_TEMPLATE = '<s>[INST] human prompt [/INST] task:\n{prompt}\ngpt response </s> Rating: '


LLM_TEMPLATES_V2 = {
    'ai21-j2-mid': CHAT_TEMPLATE_V2,
    'gpt-3.5-turbo': CHAT_TEMPLATE_V2,
    'cohere-command-nightly': CHAT_TEMPLATE_V2,
    'TheBloke/wizardLM-13B-1.0-fp16': DEFAULT_TEMPLATE_V2,
    'timdettmers/guanaco-33b-merged': DEFAULT_TEMPLATE_V2,
    'meta-llama/Llama-2-13b-hf': DEFAULT_TEMPLATE_V2,
    'meta-llama/Llama-2-70b-hf': DEFAULT_TEMPLATE_V2,
    'WizardLM/WizardLM-13B-V1.2': DEFAULT_TEMPLATE_V2,
    'TheBloke/llama-2-70b-Guanaco-QLoRA-fp16': DEFAULT_TEMPLATE_V2,
    'baichuan-inc/Baichuan-13B-Base': DEFAULT_TEMPLATE_V2,
    'OpenAssistant/llama2-13b-orca-8k-3319': DEFAULT_TEMPLATE_V2,
    'openchat/openchat_v3.1': DEFAULT_TEMPLATE_V2,
    'augtoma/qCammel-70-x': VICUNA_TEMPLATE_V2,
    L2_VOICELAB: VOICELAB_TEMPLATE, 
    L2: DEFAULT_TEMPLATE_V2,
    L2_ORCA_CIRCULUS: DEFAULT_TEMPLATE_V2
}
