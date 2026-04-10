# BLOCK 1 — CHECKLIST FOR COMPLIANCE WITH THE NOTICE

**Category considered for this textual version:** MASTER AND DOCTOR (technical adoption due to lack of category filled in the statement).  
**Research line/subtopic:** Artificial Intelligence and the Environment.  
**Language:** Portuguese (full).  
**Required structure covered:** title; author; advisor; link institution; institution where the research was carried out; summary; introduction; objectives; material and methods; Results and discussion; conclusions; bibliographic references; keywords.  
**Target page range (A4, Arial 12, 1.5 spacing):** text written with density for expanded version of submission, dependent on final layout.  
**Requirement for final results:** met by description of results effectively observable in the real state of the base project.  
**Practical application requirement:** met, focusing on operational flow of assistive AI to validate PANC records.  
**AI use statement:** included in specific mandatory section.

---

# BLOCK 2 — COMPLETE SCIENTIFIC WORK

## Title
**CollaboratesPANC: Assistive Artificial Intelligence for Georeferenced Mapping, Human Validation and Territorial Prioritization of Non-Conventional Food Plants**

## Author
ColaboraPANC Team

## Advisor
ColaboraPANC Team

## Link institution
ColaboraPANC Project — institutional information under internal governance of the repository.

## Institution where the research was carried out
ColaboraPANC Project — institutional information under internal governance of the repository.

## Summary
This work presents the technical-scientific consolidation of the ColaboraPANC project, a platform applied to the collaborative mapping of Non-Conventional Food Plants (PANCs), articulating geotechnologies, integration of image identification services and role-oriented human validation. The central problem faced is the difficulty of transforming distributed field records into reliable and auditable knowledge for social and environmental use, especially when there is uncertainty in botanical identification. The research was completed within the scope of implementation and documentation of the existing operational scientific flow in the system: registration of georeferenced points, image sending, inference assisted by Artificial Intelligence, expert review, recording of decision-making history, production of metrics and calculation of territorial prioritization. Methodologically, an audit of the source code and backend modules, API and mobile application was conducted, followed by documentary standardization in line with the actual implementation, without including unproven functionalities. The final results obtained include the explanation and organization of a traceable human-in-the-loop cycle, the formal description of the trust and risk components of inference, the detailing of effectively available scientific endpoints and the systematization of territorial prioritization explainable by heuristics. It is concluded that the main contribution of the work to the theme “Artificial Intelligence for the Common Good” lies in the responsible application of AI as decision support, with governance, transparency and explicit delimitation of technical limits.

## Introduction
Expanding the use of Artificial Intelligence in problems of public interest requires technical mechanisms that reconcile operational performance, reliability and social responsibility. In the context of food biodiversity and socio-environmental security, mapping PANCs depends on heterogeneous field records, with different levels of image quality, variable popular nomenclature and gaps in specialized validation. This scenario creates a concrete problem: without a structured flow of human inference and review, potentially relevant observations remain of little use for territorial planning, food education and environmental monitoring.

The ColaboraPANC project was developed to face this challenge through an architecture that integrates georeferencing, collaborative registration, botanical image identification services and expert review mechanisms. The scientific perspective adopted in this work is that of assistive AI for the common good, that is, the use of AI as a component to support decision-making, and not as a replacement for human validation in contexts of uncertainty.

In the current state of implementation, the system presents an operational scientific core with an audit trail: each inference can be persisted, compared with human decision and incorporated into tracking metrics. This characteristic responds directly to contemporary demands for algorithmic governance, especially in applications with environmental and territorial impact. Thus, the relevance of this work lies in demonstrating, in an applied way, how a real system can structure the complete cycle between citizen data collection, automated inference and specialized validation, preserving traceability and transparency.

## Objectives
The general objective was to consolidate and present, in a technical-scientific format, the completed operation of ColaboraPANC as an assistive AI system for mapping and validating PANCs for public purposes.

As specific objectives, we sought to: characterize the operational problem of identifying and validating PANC records in a collaborative environment; describe the actual system architecture with an emphasis on backend, API, external integration and mobile application; formalize the scientific flow implemented between inference, human review and decision-making history; explain the territorial prioritization method based on interpretable criteria; document effectively observable final results in implementation; and establish governance guidelines, limits and responsible use of AI within the scope of the application.

## Material and Methods
The research was conducted as an applied technical study on a functional software system, with a descriptive and analytical approach to the computational artifact. The main material was the ColaboraPANC project repository, including source code, data models, integration services, API routes, mobile components, existing tests and technical documentation.

The first step consisted of a structured audit of the actual implementation. Django backend and REST API modules were verified, focusing on central scientific flow entities, such as georeferenced point models, AI prediction, expert validation and validation history. In parallel, inference services with multiple providers and the territorial prioritization mechanism using a composite score were analyzed.

In the second stage, a consistency analysis was carried out between previous documentation and the effective state of the code. This procedure allowed us to separate implemented, partially implemented and planned functionalities, avoiding the description of unproven capabilities.

In the third stage, the scientific systematization of the operational flow was carried out, including: point registration, image attachment, inference execution, confidence classification, referral for human review, final decision by an expert, registration of auditable events and provision of aggregated metrics. External integrations used in botanical identification and environmental context were also examined.

In the fourth stage, the final technical text was prepared with scientific language and adherence to the theme of the notice, maintaining a commitment to observable results and without quantitative inferences not supported by formal data published within the scope of this research.

## Survey results and discussion
The first final result consists of the characterization of an assistive AI flow operationalized in an auditable way. The implementation allows an image associated with a PANC point to be processed by external botanical identification providers, with normalized return in top-k format and confidence score. This result is technically relevant because it transforms heterogeneous outputs from third-party services into a uniform structure for internal system consumption.

The second result is the explicit incorporation of human-in-the-loop governance. The final validation decision is not automated. Instead, the platform maintains a record of algorithmic prediction, authorized reviewer decision and event history, including the possibility of justifying divergence between AI hypothesis and human conclusion. This solution meets the principle of accountability in AI applied to the common good, reducing the risk of uncritical use of automation.

The third result was the formalization of the territorial prioritization component into explainable logic. The implemented territorial score combines local incidence, climate risk, validation reliability and observation recency, with defined and traceable weights. Although it is a heuristic and not a trained predictive model, the approach offers a transparent basis for initial operational prioritization, subject to future review and calibration.

The fourth result refers to the availability of operational metrics aggregated in the scientific dashboard, including count of points submitted, inferences made, validation and rejection rates, distribution by confidence and agreement indicators between AI and expert. Even without the presentation of extensive statistical series in this text, the existence of these indicators in the system represents a methodological advance as it allows continuous monitoring of the quality of the process.

From a practical application point of view, the results demonstrate that it is feasible to structure a complete chain of collaborative collection and qualification of environmental data with AI support, as long as the inference is treated as a suggestion and subjected to expert review. This design reduces the risk of inappropriate automatic decisions and increases the social usefulness of records for education, conservation and territorial planning actions.

As a critical discussion, it was identified that dependence on external identification providers imposes limitations on availability, cost and taxonomic coverage. Furthermore, image quality and collection context directly influence the confidence of predictions. These factors reinforce the relevance of the methodological choice of mandatory human review in intermediate or low trust scenarios. It is also recognized that the evolution towards more robust scientific metrics requires expansion of the validated base and dedicated experimental evaluation design.

## Conclusions
The research concluded, based on the implemented system, that ColaboraPANC materializes a concrete application of Artificial Intelligence for the Common Good by combining assistive inference, human validation and decision-making traceability in a socio-environmental context. The work demonstrates that the main contribution is not in unrestricted automation, but in organizing a reliable decision support process for collaborative food biodiversity data.

It is also concluded that the analyzed architecture offers an original contribution in the articulation between georeferencing, multi-provider AI, validation governance and explainable territorial prioritization in the same operational flow. This integration strengthens the public utility of the system and creates conditions for methodological replication in other participatory environmental monitoring scenarios.

Finally, the study shows that final results in applied AI projects must be presented with scope delimitation and transparency regarding technical limits, preserving scientific and ethical responsibility in the use of algorithms in real problems.

## Keywords
Assistive Artificial Intelligence; Common Good; PANC; Human Validation; Territorial Prioritization.

## Bibliographic references
BRAZIL. National Council for Scientific and Technological Development. **32nd Young Scientist Award 2026: Theme Artificial Intelligence for the Common Good**. Brasília: CNPq, 2026.

DJANGO SOFTWARE FOUNDATION. **Django Documentation**. Available at: <https://docs.djangoproject.com/>. Accessed on: 10 April. 2026.

POSTGIS PROJECT. **PostGIS Documentation**. Available at: <https://postgis.net/documentation/>. Accessed on: 10 April. 2026.

PLANTNET. **Pl@ntNet API**. Available at: <https://my.plantnet.org/>. Accessed on: 10 April. 2026.

PLANT.ID. **Plant.id API Documentation**. Available at: <https://web.plant.id/>. Accessed on: 10 April. 2026.

OPEN-METEO. **Weather API Documentation**. Available at: <https://open-meteo.com/>. Accessed on: 10 April. 2026.

MAPBIOMES. **MapBiomas Alert**. Available at: <https://plataforma.alerta.mapbiomas.org/>. Accessed on: 10 April. 2026.

## Declaration on the use of Artificial Intelligence tools
A generative Artificial Intelligence tool was used to support technical-scientific writing, textual organization and review of the manuscript's structural coherence, without replacing the technical analysis of the base project. The intellectual, scientific and ethical responsibility for the final content lies entirely with the author of the work.

---

# BLOCK 3 — FINAL ADEQUACY CHECK

The text fully meets the **structure of the MASTER AND DOCTOR category** and the central requirements of the notice regarding language, formality, practical application, final results and declaration of use of AI.

Final checkpoints for submission:
1. Confirm the candidate's official category on the institutional form.
2. Validate whether the institutional identification adopted complies with the local notice.
3. Review pagination after final layout (A4, Arial 12, 1.5 spacing).
4. Confirm whether the institution requires complementary bibliographic standards (ABNT, APA or its own).
