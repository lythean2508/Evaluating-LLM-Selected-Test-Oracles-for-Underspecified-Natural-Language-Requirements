# Nguồn cho nghiên cứu về lựa chọn test oracle từ yêu cầu chưa rõ ràng

Tài liệu này đối chiếu các nhận định về hai pilot và thực nghiệm RQ4 trong *Evaluating LLM-Selected Test Oracles for Underspecified Natural-Language Requirements* với gói tái lập, liệt kê đủ 48 tài liệu trong bản thảo (đối chiếu DOI, phiên bản, tác giả và thông tin xuất bản) và tổng hợp định hướng nơi nộp bài. Thông tin được đối chiếu ngày 25/11/2026. [Bản thảo LaTeX](paper.tex) · [BibTeX](references.bib) · [Metadata và tác giả](references.json)

## Bằng chứng cho các nhận định về bản thảo

| Nhận định | Bằng chứng và cách đọc | Nguồn |
| --- | --- | --- |
| Bộ lọc giao điểm làm thay đổi cả mức hỗ trợ theo yêu cầu và mức giữ lại assertion | Với REST API mơ hồ (bản lưu CPU 0.5B), số assertion thiếu căn cứ giảm từ 56/84 xuống 0/17, độ bao phủ giảm từ 28/48 xuống 17/48 (giữ 17/28 lựa chọn đúng của LLM, loại 11 lựa chọn đúng do quy tắc thiếu diễn đạt đồng nghĩa như trên R2 và R6). Với yêu cầu chính xác, cả 47 assertion có căn cứ do LLM chọn đều được giữ (47/81). | [Bản thảo §§4, 6.1–6.4, Bảng 4](paper.tex) · [Bảng API](api/restest-extension/results/summary.csv) |
| Pilot ngưỡng kiểm chứng đầy đủ cả biến thể đầy đủ (`exact`) và khuyết thông tin (`partial`) | Có 12 cặp yêu cầu (4 thiếu comparator, 4 thiếu cutoff, 4 thiếu fallback), 7 probe/biến thể, 2 prompt, 3 seed = 144 completion. Trên `partial`, lọc sau `abstain` giảm đoán mò từ 58/126 xuống 0/126 (theo loại khuyết: 3/12 comparator, 31/72 cutoff, 24/42 fallback) và giữ 29/126 probe xác định; rules đạt 42/42. Trên `exact`, lọc xóa hết cảnh báo giả (33/36 xuống 0/36 suite) và tăng diệt mutant đủ điều kiện từ 9/216 lên 115/216 (rules: 68/72). | [Bản thảo §§5.1, 6.1–6.3, Bảng 2 & 3](paper.tex) · [Bảng controlled](controlled/results/summary.csv) |
| Mô hình 7B giảm tỷ lệ assertion thô thiếu căn cứ và tăng số lượt diệt tương thích trên FastAPI mơ hồ | Dưới runtime Vulkan ghép cặp, Qwen-7B giảm tỷ lệ thiếu căn cứ thô trên FastAPI mơ hồ từ 49/80 (61,3%) xuống 31/67 (46,3%) và tăng số mutant bị diệt trên các suite qua bản gốc từ 2/51 lên 23/51 (8/18 suite); tuy nhiên 18/23 lượt diệt đến từ 6 suite chứa ít nhất một assertion thiếu căn cứ nên chỉ còn 5/51 lượt diệt đủ điều kiện trước lọc và 21/51 sau lọc (so với 22/51 ở 0.5B). | [Bản thảo §7.2, Bảng 6 & 7](followup/manuscript-results.tex) · [Bảng so sánh mô hình](followup/results/api-summary.csv) |
| Quy tắc đóng băng bộc lộ trần từ vựng trên văn bản mơ hồ và lỗi rò rỉ phạm vi liên bước trên tập giữ lại | Trên TodoApp mơ hồ, quy tắc đóng băng chọn 0 ứng viên nên cả 0.5B và 7B đều cho 12/12 bộ rỗng. Trên TodoApp R6 chính xác (`DELETE` kèm bước kiểm tra `GET 404` theo sau), quy tắc chọn tập mâu thuẫn `{http_200, success, denied}` ($2\text{xx}\wedge 4\text{xx}$), vi phạm điều kiện mọi assertion đều có căn cứ trong $Q(R,r)$ và giữ lại cặp mâu thuẫn khi cả LLM lẫn quy tắc cùng nhầm phạm vi bước. | [Bản thảo §7.3, Bảng 8](followup/manuscript-results.tex) · [Bảng TodoApp](followup/results/heldout-summary.csv) |
| Kết luận so sánh cỡ mô hình phụ thuộc vào chính sách diễn giải yêu cầu | Phân tích đủ $2^3=8$ tổ hợp chính sách nhãn trên cùng dữ liệu FastAPI: giữ nhãn gốc cho độ bao phủ sau lọc 18/48 (0.5B) so với 20/48 (7B), nhưng yêu cầu nêu tường minh trường phản hồi `PUT` (R6) đảo ngược thứ tự thành 16/36 so với 14/36 (hoặc 16/33 so với 14/33 khi bật đủ ba ràng buộc). | [Bản thảo §7.4](followup/manuscript-results.tex) · [Bảng độ nhạy](followup/results/label-sensitivity.csv) |

Lệnh `python verify_all.py --output verification-run` kiểm tra toàn bộ mã băm SHA-256 và tái tạo lại tất cả bảng tổng hợp của hai pilot gốc, thực nghiệm ghép cặp 0.5B/7B, tập giữ lại TodoApp, phân hoạch bốn phần và tám chính sách nhãn.

## Hội nghị, workshop và tạp chí phù hợp

| Nơi nộp | Mức phù hợp và lịch đã công bố | Nguồn chính thức |
| --- | --- | --- |
| IEEE RE 2027 | Ưu tiên Research Papers (*Evaluation-focused*) hoặc RE@Next! vì đóng góp trung tâm là đánh giá căn cứ yêu cầu ở cấp độ từng assertion và độ nhạy theo chính sách diễn giải. Abstract Research: 22/02/2027; Full paper: 01/03/2027 (AoE). RE@Next!: 12/03/2027 / 19/03/2027. | [Research Papers](https://conf.researchr.org/track/RE-2027/RE-2027-papers) · [RE@Next!](https://conf.researchr.org/track/RE-2027/RE-2027-re-next) |
| NLP4RE 2027 (cùng REFSQ 2027) | Rất sát chủ đề xử lý mơ hồ/thiếu đặc tả ngôn ngữ tự nhiên khi nối yêu cầu với kiểm thử. Dự kiến tổ chức ngày 12/04/2027 cùng REFSQ. | [Thông báo NLP4RE 2027](https://github.com/nlp4re/2027/blob/main/index.html) · [Lịch REFSQ 2027](https://conf.researchr.org/dates/refsq-2027) |
| Journal of Systems and Software / Automated Software Engineering | Phù hợp cho phiên bản mở rộng sau khi bổ sung đo độ đồng thuận hai người gán nhãn độc lập (Cohen's $\kappa$) và chạy thực thi mutant trên dịch vụ thứ hai. | [JSS](https://shop.elsevier.com/journals/journal-of-systems-and-software/0164-1212) · [ASE Journal](https://link.springer.com/journal/10515/aims-and-scope) |

## Danh mục 48 nguồn trong bản thảo

Các mục theo đúng thứ tự trong `paper.tex`, `references.bib` và `references.json`. Các mục có DOI được đối chiếu với bản ghi nhà xuất bản, Crossref hoặc hồ sơ công bố của tác giả. Các bản tiền ấn phẩm và hiện vật dùng trang lưu trữ chính thức.

### Kiểm thử từ yêu cầu và xử lý mơ hồ đặc tả
1. **The Oracle Problem in Software Testing: A Survey** (Barr et al., TSE 2015). [DOI](https://doi.org/10.1109/TSE.2014.2372785)
2. **Requirements-Based Test Generation: A Comprehensive Survey** (Yang et al., TOSEM 2026). [DOI](https://doi.org/10.1145/3771727)
3. **Software Testing with Large Language Models: Survey, Landscape, and Vision** (Wang et al., TSE 2024). [DOI](https://doi.org/10.1109/TSE.2024.3368208)
4. **AI-Driven Test Case Generation from Natural Language Requirements: A Survey of Techniques and Research Gaps** (Folorunsho & Reza, 2026). [arXiv](https://arxiv.org/abs/2606.06563)
5. **Automatic Generation of Acceptance Test Cases from Use Case Specifications: An NLP-Based Approach** (Wang et al., TSE 2022). [DOI](https://doi.org/10.1109/TSE.2020.2998503)
6. **Automatic Creation of Acceptance Tests by Extracting Conditionals from Requirements: NLP Approach and Case Study** (Fischbach et al., JSS 2023). [DOI](https://doi.org/10.1016/j.jss.2022.111549)
7. **Generating Test Scenarios from NL Requirements using Retrieval-Augmented LLMs: An Industrial Study** (Arora et al., RE 2024). [DOI](https://doi.org/10.1109/RE59067.2024.00031)
8. **Acceptance Test Generation with Large Language Models: An Industrial Case Study** (Ferreira et al., AST 2025). [DOI](https://doi.org/10.1109/AST66626.2025.00007)
9. **Generating High-Level Test Cases from Requirements using LLM: An Industry Study** (Masuda et al., ACDSA 2026). [DOI](https://doi.org/10.1109/ACDSA67686.2026.11467785)
10. **An empirical study of LoRA-based fine-tuning of large language models for automated test case generation** (Moradi et al., 2026). [arXiv](https://arxiv.org/abs/2604.06946)
11. **Explicating Tacit Regulatory Knowledge from LLMs to Auto-Formalize Requirements for Compliance Test Case Generation** (Xue et al., 2026). [arXiv](https://arxiv.org/abs/2601.09762)

### Sinh và đánh giá test oracle
12. **Can Large Language Models Transform Natural Language Intent into Formal Method Postconditions?** (Endres et al., PACMSE / FSE 2024). [DOI](https://doi.org/10.1145/3660791)
13. **TOGA: A Neural Method for Test Oracle Generation** (Dinella et al., ICSE 2022). [DOI](https://doi.org/10.1145/3510003.3510141)
14. **Neural-Based Test Oracle Generation: A Large-scale Evaluation and Lessons Learned** (Hossain et al., ESEC/FSE 2023). [DOI](https://doi.org/10.1145/3611643.3616265)
15. **Do LLMs generate test oracles that capture the actual or the expected program behaviour?** (Konstantinou et al., 2024). [arXiv v1](https://arxiv.org/abs/2410.21136v1)
16. **Do LLMs Generate Useful Test Oracles? An Empirical Study with an Unbiased Dataset** (Molinelli et al., ASE 2025). [DOI](https://doi.org/10.1109/ASE63991.2025.00031)
17. **LLMs and Prompting for Unit Test Generation: A Large-Scale Evaluation** (Ouédraogo et al., ASE 2024). [DOI](https://doi.org/10.1145/3691620.3695330)

### Benchmark, kiểm thử REST API và kiểm thử đột biến
18. **RESTestBench: A Benchmark for Evaluating the Effectiveness of LLM-Generated REST API Test Cases from NL Requirements** (Kogler et al., EASE 2026). [arXiv](https://arxiv.org/abs/2604.25862)
19. **From Business Requirements to Test Assertions: Evaluating LLM-Generated Oracles on Real Bugs** (Ma & Eisty, 2026). [arXiv](https://arxiv.org/abs/2607.10277)
20. **ReqTestAgent: execution-grounded language-model agents for acceptance testing under requirement ambiguity** (Shi & Song, Frontiers in AI 2026). [DOI](https://doi.org/10.3389/frai.2026.1960601)
21. **Benchmarking LLM Agents for Behaviorally Adequate Test Generation from Software Requirements** (Qi et al., 2026). [arXiv](https://arxiv.org/abs/2610.36584)
22. **RESTifAI: LLM-Based Workflow for Reusable REST API Testing** (Kogler et al., ICSE-Companion 2026). [DOI](https://doi.org/10.1145/3774748.3787598)
23. **Testing RESTful APIs: A Survey** (Golmohammadi et al., TOSEM 2024). [DOI](https://doi.org/10.1145/3617175)
24. **RESTest: Automated Black-Box Testing of RESTful Web APIs** (Martín-López et al., ISSTA 2021). [DOI](https://doi.org/10.1145/3460319.3469082)
25. **Property-Based Mutation Testing** (Bartocci et al., ICST 2023). [DOI](https://doi.org/10.1109/ICST57152.2023.00029)
26. **Mutation Testing Advances: An Analysis and Survey** (Papadakis et al., Advances in Computers 2019). [DOI](https://doi.org/10.1016/bs.adcom.2018.03.015)
27. **Validating Formal Specifications with LLM-generated Test Cases** (Cunha & Macedo, FM 2026). [DOI](https://doi.org/10.1007/978-3-032-26204-2_15)

### Mô hình, công cụ, đặc tả, thống kê và nguồn đối chiếu mở rộng
28. **Qwen2.5-0.5B-Instruct-GGUF** (Qwen Team, 2024). [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF)
29. **llama.cpp, release b5046** (2025). [GitHub](https://github.com/ggml-org/llama.cpp/releases/tag/b5046)
30. **Full Stack FastAPI Template** (2026). [GitHub](https://github.com/fastapi/full-stack-fastapi-template)
31. **OpenAPI Specification, version 3.1.0** (2021). [OAS](https://spec.openapis.org/oas/v3.1.0)
32. **RESTestBench replication repository** (commit `4decc1e`). [GitHub](https://github.com/casablancahotelsoftware/RESTestBench/tree/4decc1e36ea3dd41b64ce3e3ac6a85bc72df36ae)
33. **SLR-on-RBTG: collection of 267 primary studies** (2025). [GitHub](https://github.com/aimeenorwind/SLR-on-RBTG)
34. **A Coefficient of Agreement for Nominal Scales** (Cohen, EPM 1960). [DOI](https://doi.org/10.1177/001316446002000104)
35. **Qwen2.5-7B-Instruct-GGUF** (Qwen Team, 2024). [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)
36. **What the Specification Did Not Say: Specification-Oracle Gaps in Test-Graded Coding-Agent Benchmarks** (Ding, 2026). [arXiv](https://arxiv.org/abs/2610.30635)
37. **Requirements Sufficiency Gating for LLM-Assisted Automation: When Should Generation Proceed?** (Madani, Nahhas, Chernigovskaya & Turowski, IEEE RE 2026). [DOI](https://doi.org/10.1109/RE68928.2026.00028)
38. **LLM-Based Test Oracles: Source-of-Authority Taxonomy—A Systematic Literature Review** (Mughal & Bilal, IEEE Access 2026). [DOI](https://doi.org/10.1109/ACCESS.2026.3729738)
39. **TOGLL: Correct and Strong Test Oracle Generation with LLMs** (Hossain & Dwyer, ICSE 2025). [DOI](https://doi.org/10.1109/ICSE55347.2025.00098)
40. **TOGBench: A Developer-Written Multi-Variant Dataset and Benchmark Suite for Test Oracle Generation** (Tasnim, Dwyer & Hossain, AIware 2026). [DOI](https://doi.org/10.1145/3805760.3814927)
41. **Ambiguity in Requirements Specification** (Berry & Kamsties, Springer 2004). [DOI](https://doi.org/10.1007/978-1-4615-0465-8_2)
42. **Automated Handling of Anaphoric Ambiguity in Requirements: A Multi-solution Study** (Ezzini et al., ICSE 2022). [DOI](https://doi.org/10.1145/3510003.3510157)
43. **On the Foundations of Noise-free Selective Classification** (El-Yaniv & Wiener, JMLR 2010). [JMLR](https://www.jmlr.org/papers/v11/el-yaniv10a.html)
44. **Know Your Limits: A Survey of Abstention in Large Language Models** (Wen et al., TACL 2025). [DOI](https://doi.org/10.1162/tacl_a_00754)
45. **ClarifyGPT: A Framework for Enhancing LLM-based Code Generation via Requirements Clarification** (Mu et al., PACMSE / FSE 2024). [DOI](https://doi.org/10.1145/3660810)
46. **Breaking the Silence: The Threats of Using LLMs in Software Engineering** (Sallou, Durieux & Panichella, ICSE-NIER 2024). [DOI](https://doi.org/10.1145/3639476.3639764)
47. **Mutation-Guided LLM-based Test Generation at Meta** (Harman et al., FSE Companion 2025). [DOI](https://doi.org/10.1145/3696630.3728544)
48. **Understanding LLM-Driven Test Oracle Generation** (Bodicoat, Jahangirova & Terragni, AIware 2025). [DOI](https://doi.org/10.1109/AIware69974.2025.00011)
