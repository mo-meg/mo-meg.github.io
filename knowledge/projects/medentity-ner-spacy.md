---
title: Cloud-Based Information Extraction with spaCy NER (MedEntity)
source_label: MedEntity NER — Project Documentation
category: projects
url: https://github.com/mmm-megahed/MedEntity_NER_spaCy
---

# Overview

MedEntity is a Named Entity Recognition (NER) project based on the spaCy framework and Google Cloud Platform (GCP). It identifies entities in scientific (biomedical/medical) articles. It was developed during Mohamed's research internship ("Fachpraktikum CIE") at FernUniversität in Hagen.

Type: academic research. Repository: https://github.com/mmm-megahed/MedEntity_NER_spaCy

# Technical details

- The spaCy NER model "MedEntity" was trained from scratch on the CRAFT corpus (Colorado Richly Annotated Full-Text corpus).
- Entity types are based on biomedical ontologies: CHEBI (chemical entities of biological interest), CL (Cell Ontology), GO_BP / GO_CC / GO_MF (Gene Ontology: biological process, cellular component, molecular function), MONDO (diseases), MOP (Molecular Process Ontology), NCBITaxon (NCBI Taxonomy), PR (Protein Ontology), SO (Sequence Ontology), UBERON (anatomy).
- A web-based annotation interface supported creating labelled data.
- A Streamlit web application lets users enter text and highlights the extracted entities with spaCy's displaCy visualizer.
- The application is containerized with Docker and deployed on Google Cloud Platform; GCP resources were configured and optimized for training and serving.

# Workflow

Scientific articles (CRAFT corpus) → annotation interface → spaCy NER training → Docker image (model + Streamlit UI) → GCP deployment → entity extraction for user text.

# Technologies

Python, spaCy, displaCy, Streamlit, Docker, Google Cloud Platform.

# Not documented

Model accuracy / F1 scores are not contained in the knowledge base.
