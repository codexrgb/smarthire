# Job Family Clustering Evaluation & Interpretability Report

**Dataset Rows:** 200 jobs  
**TF-IDF Dimension:** 1722 features  
**Evaluated K Range:** K=2 to K=15  

## Candidate Cluster Evaluations

| K | Inertia | Silhouette | ARI (vs Category) | NMI (vs Category) | V-Measure |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 2 | 182.46 | 0.0245 | 0.0641 | 0.3302 | 0.3302 |
| 3 | 177.33 | 0.0357 | 0.0893 | 0.4424 | 0.4424 |
| 4 | 172.39 | 0.0452 | 0.1191 | 0.5167 | 0.5167 |
| 5 | 167.65 | 0.0595 | 0.1787 | 0.6023 | 0.6023 |
| 6 | 163.29 | 0.0699 | 0.2249 | 0.6506 | 0.6506 |
| 7 | 158.64 | 0.0802 | 0.2414 | 0.6960 | 0.6960 |
| 8 | 154.77 | 0.0855 | 0.3649 | 0.7610 | 0.7610 |
| 9 | 149.33 | 0.1018 | 0.2869 | 0.7529 | 0.7529 |
| 10 | 146.20 | 0.1108 | 0.4019 | 0.7896 | 0.7896 |
| 11 | 140.66 | 0.1231 | 0.4728 | 0.8284 | 0.8284 |
| 12 | 136.86 | 0.1338 | 0.4856 | 0.8382 | 0.8382 |
| 13 | 132.28 | 0.1473 | 0.4408 | 0.8439 | 0.8439 |
| 14 | 128.73 | 0.1524 | 0.5494 | 0.8740 | 0.8740 |
| 15 | 125.44 | 0.1604 | 0.6349 | 0.8918 | 0.8918 |

## Geometric & Distance Concentration Analysis

> **Why Silhouette Scores Rise with Higher K in TF-IDF Space:**  
> In high-dimensional sparse TF-IDF spaces, pairwise document distances are constrained by the unit hypersphere (Euclidean distance ≈ 1.414 between orthogonal texts). Partitioning points into more clusters (e.g., K=10..15) naturally decreases average within-cluster distance, creating micro-clusters around nearest neighbors and artificially inflating the silhouette score. **The highest silhouette score does NOT establish optimal operational clusters.**

## Elbow Analysis

- **Suggested Elbow K:** `9`  
- **Max Second Difference:** `2.31`  
- **Assessment:** The inertia curve exhibits gradual, diffuse decay (max second diff: 2.31). A sharp geometric elbow is absent. Domain-informed selection (e.g. matching major occupational job families) is more defensible than relying strictly on an ambiguous mathematical elbow.  

## Cluster Interpretability (Top Centroid Terms)

### K = 5 (Operational Job Families):
- **Cluster 0:** `management, pmo, project, sales, project management, health, jira, stakeholder`
- **Cluster 1:** `developer, python, sql, data, etl, required, developer domain, sap`
- **Cluster 2:** `engineer, testing, required, autocad, engineering, network, security, network security`
- **Cluster 3:** `advocate, contract, contract negotiation, litigation, law, corporate law, corporate, arbitration`
- **Cluster 4:** `web, web designing, javascript, react, hr, web design, css, wordpress`

### K = 15 (Max Silhouette = 0.1604):
- **Cluster 0:** `dotnet, dotnet developer, csharp, server, sql server, framework, entity framework, entity`
- **Cluster 1:** `etl, etl developer, sql, database, ssis, informatica, data warehousing, warehousing`
- **Cluster 2:** `sap, sap developer, hana, sap hana, erp, sap mm, mm, erp sap`
- **Cluster 3:** `devops, devops engineer, engineer, kubernetes, jenkins, aws, ci, ci cd`
- **Cluster 4:** `hr, employee relations, employee, relations, acquisition, talent acquisition, talent, policies`
- **Cluster 5:** `network, network security, security, testing, security engineer, penetration testing, penetration, wireshark`
- **Cluster 6:** `web, web designing, javascript, react, web design, css, wordpress, figma`
- **Cluster 7:** `health, fitness, health fitness, training, personal, personal training, health assessment, assessment`
- **Cluster 8:** `management, pmo, project, jira, sales, project management, stakeholder, stakeholder management`
- **Cluster 9:** `electrical, electrical engineering, engineering, matlab, plc, power systems, power, scada`
- **Cluster 10:** `data science, science, data, learning, learn, scikit, scikit learn, pandas`
- **Cluster 11:** `advocate, contract, contract negotiation, litigation, law, corporate law, corporate, arbitration`
- **Cluster 12:** `python developer, developer, python, hadoop, java, postgresql, git, celery`
- **Cluster 13:** `blockchain, arts, writing, creative, creative writing, animation, web3, web3 js`
- **Cluster 14:** `mechanical, engineer, autocad, mechanical engineer, civil, solidworks, civil engineer, manufacturing`

## Production Integrity Notice
The production model `models/kmeans_clustering.pkl` and primary report `reports/metrics/clustering_metrics.json` were preserved without modification. This evaluation was run purely as an independent experimental assessment.
