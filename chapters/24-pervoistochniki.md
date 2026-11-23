# Первоисточники

<!--
Черновик механической выгрузки из manual/source.docx (см. scripts/extract_docx_draft.py).
Источник книги: manual/source.docx + правки editorial_content.py; этот файл не участвует в сборке.
Элементы DOCX: 255–286.
-->

<!-- e:255 заголовок -->
## 24 Первоисточники

<!-- e:256 -->
Источники объясняют конкретные механизмы и результаты. Год в библиографии соответствует первой публикации препринта; год конференции или журнала может отличаться. Ранняя статья устанавливает идею или эксперимент, но не задаёт предел возможностей всех будущих моделей. Учебник намеренно не привязан к текущим ценам, лидербордам и закрытым деталям конкретных коммерческих продуктов.

<!-- e:257 -->
[1] PyTorch. Automatic Differentiation with torch.autograd. Официальное руководство по графу вычислений и градиентам. https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html

<!-- e:258 -->
[2] Sennrich et al. Neural Machine Translation of Rare Words with Subword Units. 2015. Subword токенизация и BPE. https://arxiv.org/abs/1508.07909

<!-- e:259 -->
[3] Vaswani et al. Attention Is All You Need. 2017. Исходная архитектура Transformer. https://arxiv.org/abs/1706.03762

<!-- e:260 fix -->
[4] Touvron et al. LLaMA Open and Efficient Foundation Language Models. 2023. Конкретная архитектура и обучение decoder-моделей. https://arxiv.org/abs/2302.13971

<!-- e:261 fix -->
[5] Su et al. RoFormer Enhanced Transformer with Rotary Position Embedding. 2021. Механизм RoPE. https://arxiv.org/abs/2104.09864

<!-- e:262 fix -->
[6] Brown et al. Language Models are Few Shot Learners. 2020. Задачи по примерам в контексте. https://arxiv.org/abs/2005.14165

<!-- e:263 fix -->
[7] Hoffmann et al. Training Compute Optimal Large Language Models. 2022. Баланс параметров, данных и бюджета обучения. https://arxiv.org/abs/2203.15556

<!-- e:264 -->
[8] Gebru et al. Datasheets for Datasets. 2018. Документирование наборов данных. https://arxiv.org/abs/1803.09010

<!-- e:265 -->
[9] Ouyang et al. Training language models to follow instructions with human feedback. 2022. SFT и RLHF в InstructGPT. https://arxiv.org/abs/2203.02155

<!-- e:266 fix -->
[10] Rafailov et al. Direct Preference Optimization Your Language Model is Secretly a Reward Model. 2023. DPO. https://arxiv.org/abs/2305.18290

<!-- e:267 fix -->
[11] Hu et al. LoRA Low Rank Adaptation of Large Language Models. 2021. Низкоранговые адаптеры. https://arxiv.org/abs/2106.09685

<!-- e:268 fix -->
[12] Dettmers et al. QLoRA Efficient Finetuning of Quantized LLMs. 2023. Обучение адаптеров с квантованной базой. https://arxiv.org/abs/2305.14314

<!-- e:269 fix -->
[13] DeepSeek AI. DeepSeek R1 Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. 2025. Reasoning, RL и distillation. https://arxiv.org/abs/2501.12948

<!-- e:270 fix -->
[14] Wei et al. Chain of Thought Prompting Elicits Reasoning in Large Language Models. 2022. Промежуточные решения в prompt. https://arxiv.org/abs/2201.11903

<!-- e:271 -->
[15] Turpin et al. Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting. 2023. Ограничения объяснений модели. https://arxiv.org/abs/2305.04388

<!-- e:272 fix -->
[16] Liu et al. Lost in the Middle How Language Models Use Long Contexts. 2023. Использование информации в длинном контексте. https://arxiv.org/abs/2307.03172

<!-- e:273 -->
[17] Kwon et al. Efficient Memory Management for Large Language Model Serving with PagedAttention. 2023. Управление KV cache. https://arxiv.org/abs/2309.06180

<!-- e:274 fix -->
[18] Dao et al. FlashAttention Fast and Memory Efficient Exact Attention with IO Awareness. 2022. Оптимизация attention. https://arxiv.org/abs/2205.14135

<!-- e:275 fix -->
[19] Lewis et al. Retrieval Augmented Generation for Knowledge Intensive NLP Tasks. 2020. Параметрическая и внешняя память. https://arxiv.org/abs/2005.11401

<!-- e:276 fix -->
[20] Park et al. Generative Agents Interactive Simulacra of Human Behavior. 2023. Внешняя память агентов в симуляции. https://arxiv.org/abs/2304.03442

<!-- e:277 -->
[21] Jiang et al. Mixtral of Experts. 2024. Sparse MoE и выбор экспертов. https://arxiv.org/abs/2401.04088

<!-- e:278 fix -->
[22] Schick et al. Toolformer Language Models Can Teach Themselves to Use Tools. 2023. Обучение использованию инструментов. https://arxiv.org/abs/2302.04761

<!-- e:279 fix -->
[23] Yao et al. ReAct Synergizing Reasoning and Acting in Language Models. 2022. Действия и наблюдения в цикле. https://arxiv.org/abs/2210.03629

<!-- e:280 fix -->
[24] Zhou et al. WebArena A Realistic Web Environment for Building Autonomous Agents. 2023. Проверка агентных задач. https://arxiv.org/abs/2307.13854

<!-- e:281 -->
[25] Greshake et al. Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. 2023. Indirect prompt injection. https://arxiv.org/abs/2302.12173

<!-- e:282 fix -->
[26] Devlin et al. BERT Pre training of Deep Bidirectional Transformers for Language Understanding. 2018. Двунаправленные представления и другая цель pretraining. https://arxiv.org/abs/1810.04805

<!-- e:283 fix -->
[27] Raffel et al. Exploring the Limits of Transfer Learning with a Unified Text to Text Transformer. 2019. T5 и перенос обучения. https://arxiv.org/abs/1910.10683

<!-- e:284 -->
[28] Zhang et al. Siren's Song in the AI Ocean: A Survey on Hallucination in Large Language Models. 2023. Определения и типы галлюцинаций. https://arxiv.org/abs/2309.01219

<!-- e:285 -->
[29] Zheng et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. 2023. Проверка оценок и систематические смещения LLM-судей. https://arxiv.org/abs/2306.05685

<!-- e:286 -->
[30] scikit-learn. Common pitfalls and recommended practices. Официальная документация об утечке данных и разделении обучения и оценки. https://scikit-learn.org/stable/common_pitfalls.html

