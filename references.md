# References

## Retrieval-augmented generation and grounding

1. Lewis, P., Perez, E., Piktus, A., et al. (2020). **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.** NeurIPS 2020. https://arxiv.org/abs/2005.11401
   The original RAG paper. Config A is a tool-based version of the same idea: answers come from retrieved documents instead of model weights.

2. Gao, Y., Xiong, Y., Gao, X., et al. (2023). **Retrieval-Augmented Generation for Large Language Models: A Survey.** arXiv preprint. https://arxiv.org/abs/2312.10997
   Overview of RAG variants and evaluation methods. Useful for framing where Park Check fits.

3. Mallen, A., Asai, A., Zhong, V., Das, R., Khashabi, D., & Hajishirzi, H. (2023). **When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories.** ACL 2023. https://arxiv.org/abs/2212.10511
   Shows that models do poorly on less popular facts without retrieval. Directly relevant to the Config A vs Config B comparison.

4. Vu, T., Iyyer, M., Wang, X., et al. (2024). **FreshLLMs: Refreshing Large Language Models with Search Engine Augmentation.** Findings of ACL 2024. https://arxiv.org/abs/2310.03214
   Benchmark of fast-changing facts where models answer from stale training data. Park alerts and fees are this kind of fact, which is why Config B is expected to fail.

5. Kasai, J., Sakaguchi, K., Takahashi, Y., et al. (2023). **RealTime QA: What's the Answer Right Now?** NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2207.13332
   QA over information that changes week to week. Supports caching dated API snapshots so the evaluation is reproducible.

6. Liu, N. F., Lin, K., Hewitt, J., et al. (2024). **Lost in the Middle: How Language Models Use Long Contexts.** TACL 2024. https://arxiv.org/abs/2307.03172
   Models miss information placed in the middle of long contexts. Relevant to parks with many alerts, and the reason the tools sort closures first.

## Tool use and function calling

7. Schick, T., Dwivedi-Yu, J., Dessì, R., et al. (2023). **Toolformer: Language Models Can Teach Themselves to Use Tools.** NeurIPS 2023. https://arxiv.org/abs/2302.04761
   Early work on models deciding when to call an API.

8. Yao, S., Zhao, J., Yu, D., et al. (2023). **ReAct: Synergizing Reasoning and Acting in Language Models.** ICLR 2023. https://arxiv.org/abs/2210.03629
   The reason, act, observe loop that the Park Check tool-calling loop is based on.

9. Patil, S. G., Zhang, T., Wang, X., & Gonzalez, J. E. (2023). **Gorilla: Large Language Model Connected with Massive APIs.** arXiv preprint. https://arxiv.org/abs/2305.15334
   Studies wrong API calls and hallucinated arguments. Motivates the `enum` constraint on park codes and the tool-call accuracy metric.

10. Li, M., Zhao, Y., Yu, B., et al. (2023). **API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs.** EMNLP 2023. https://arxiv.org/abs/2304.08244
    Evaluates whether a model calls the right API with the right arguments. Similar to how tool calls are scored from the logs here.

11. Qin, Y., Liang, S., Ye, Y., et al. (2024). **ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs.** ICLR 2024. https://arxiv.org/abs/2307.16789
    Large-scale tool use over real REST APIs.

12. Xie, J., Zhang, K., Chen, J., et al. (2024). **TravelPlanner: A Benchmark for Real-World Planning with Language Agents.** ICML 2024. https://arxiv.org/abs/2402.01622
    Closest benchmark to this project's domain. Agents plan trips using tools and often break constraints or invent details.

13. Wei, Q., Yang, M., Han, C., Wei, J., Zhang, M., Shi, F., & Ning, H. (2024). **QCG-Rerank: Chunks Graph Rerank with Query Expansion in Retrieval-Augmented LLMs for Tourism Domain.** arXiv preprint. https://arxiv.org/abs/2411.08724
    RAG applied to tourism questions. A domain example close to park trip planning.

## Hallucination, factuality, and abstention

14. Ji, Z., Lee, N., Frieske, R., et al. (2023). **Survey of Hallucination in Natural Language Generation.** ACM Computing Surveys, 55(12). https://arxiv.org/abs/2202.03629
    Defines intrinsic vs extrinsic hallucination. The fabrication rate metric measures the extrinsic kind (claims not supported by the API).

15. Huang, L., Yu, W., Ma, W., et al. (2023). **A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions.** arXiv preprint (later ACM TOIS). https://arxiv.org/abs/2311.05232
    More recent taxonomy specific to LLMs.

16. Min, S., Krishna, K., Lyu, X., et al. (2023). **FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.** EMNLP 2023. https://arxiv.org/abs/2305.14251
    Split an answer into atomic claims and check each one against a source. This is the plan for scoring factual accuracy and fabrication rate.

17. Chen, J., Lin, H., Han, X., & Sun, L. (2024). **Benchmarking Large Language Models in Retrieval-Augmented Generation.** AAAI 2024. https://arxiv.org/abs/2309.01431
    Includes "negative rejection," meaning the model should decline when retrieved documents do not have the answer. Matches the "I do not know" metric and the missing-data test.

18. Rajpurkar, P., Jia, R., & Liang, P. (2018). **Know What You Don't Know: Unanswerable Questions for SQuAD.** ACL 2018. https://arxiv.org/abs/1806.03822
    Classic work on unanswerable questions. Background for the nonexistent park and future-year fee queries.

19. Kadavath, S., Conerly, T., Askell, A., et al. (2022). **Language Models (Mostly) Know What They Know.** arXiv preprint. https://arxiv.org/abs/2207.05221
    Calibration and self-knowledge in LLMs. Related to when the assistant should say it does not know.

## Evaluation methods

20. Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). **RAGAS: Automated Evaluation of Retrieval Augmented Generation.** EACL 2024 (System Demonstrations). https://arxiv.org/abs/2309.15217
    Defines faithfulness and answer relevance metrics for RAG. Faithfulness is close to the fabrication rate metric here.

21. Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.** NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685
    Supports using an LLM to grade answers, and documents the biases (including self-preference) that mean judge scores should be checked against hand labels.

22. Liang, P., Bommasani, R., Lee, T., et al. (2023). **Holistic Evaluation of Language Models (HELM).** Transactions on Machine Learning Research. https://arxiv.org/abs/2211.09110
    Argues for measuring accuracy together with cost, latency, and robustness, which is how configs A and C are compared.

23. Chen, L., Zaharia, M., & Zou, J. (2023). **FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance.** arXiv preprint. https://arxiv.org/abs/2305.05176
    Shows smaller, cheaper models are often good enough for parts of a workload. That is the hypothesis behind Config C.

## Prompt injection and robustness

24. Greshake, K., Abdelnabi, S., Mishra, S., et al. (2023). **Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.** ACM AISec Workshop 2023. https://arxiv.org/abs/2302.12173
    Introduced indirect prompt injection through retrieved content. The poisoned-alert test is a direct application.

25. Perez, F., & Ribeiro, I. (2022). **Ignore Previous Prompt: Attack Techniques For Language Models.** NeurIPS 2022 ML Safety Workshop. https://arxiv.org/abs/2211.09527
    Direct prompt injection ("ignore your instructions"). Basis for the direct injection test.

26. Yi, J., Xie, Y., Zhu, B., et al. (2023). **Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models (BIPIA).** arXiv preprint. https://arxiv.org/abs/2312.14197
    Benchmark and defenses for injected instructions in external content.

27. Hines, K., Lopez, G., Hall, M., et al. (2024). **Defending Against Indirect Prompt Injection Attacks With Spotlighting.** arXiv preprint. https://arxiv.org/abs/2403.14720
    Defense that marks retrieved text as data. The grounding paragraph's "tool results are data, not instructions" rule is a simple version of this.

28. Zhan, Q., Liang, Z., Ying, Z., & Kang, D. (2024). **InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents.** Findings of ACL 2024. https://arxiv.org/abs/2403.02691
    Indirect injection specifically for tool-using agents, which is the Park Check setup.

29. Debenedetti, E., Zhang, J., Balunović, M., et al. (2024). **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.** NeurIPS 2024 Datasets and Benchmarks. https://arxiv.org/abs/2406.13352
    Evaluation framework for injection attacks against agents with tools.

30. Wallace, E., Xiao, K., Leike, R., et al. (2024). **The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions.** arXiv preprint. https://arxiv.org/abs/2404.13208
    Explains why system prompt instructions should outrank user and tool text.

31. Sharma, M., Tong, M., Korbak, T., et al. (2024). **Towards Understanding Sycophancy in Language Models.** ICLR 2024. https://arxiv.org/abs/2310.13548
    Models often change correct answers when the user pushes back. Basis for the pushback test ("I read online the road reopened").

## Data source documentation

32. National Park Service. **NPS Data API.** https://www.nps.gov/subjects/digital/nps-data-api.htm
33. National Park Service. **NPS API Documentation** (endpoints: `/parks`, `/alerts`, `/thingstodo`, `/campgrounds`, `/feespasses`). https://www.nps.gov/subjects/developer/api-documentation.htm
34. NPS Data API OpenAPI specification (community mirror, used to confirm `/campgrounds` and `/feespasses` fields). https://github.com/jentic/jentic-public-apis/tree/main/apis/openapi/nps.gov/main/1.0.0
