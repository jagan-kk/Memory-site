# AI AR Augmentation/AI AR Memory Palace

An innovative AI + Augmented Reality system that transforms uploaded PDF documents into interactive 3D AR cards. The project combines Artificial Intelligence, depth estimation, document understanding, and AR visualization to create immersive digital experiences.

## Overview

AI AR Augmentation allows users to upload images or PDF files and automatically converts them into dynamic 3D cards that can be visualized in Augmented Reality. The system uses AI-powered depth estimation and content summarization to generate visually enhanced AR-ready assets.

When a PDF is uploaded:

* The first page is converted into an image preview
* AI extracts and summarizes the document content
* A 3D card is generated using the preview and summary
* The card becomes interactable inside the AR environment

Users can later scan or detect the generated AR card and interact with it in real-world space.

---

## Features

* AI-powered document understanding
* Automatic PDF summarization
* 3D card generation
* Depth estimation using AI models
* Real-time AR visualization
* UV mapping of image to 3D
* Tap-to-download original files
* Support for only text extractable PDFs
* Mobile AR experience using Unity

---

## Tech Stack

### AR(App)

* Unity
* ARFoundation


### AI / Backend

* Python
* FastAPI / Flask
* MiDaS Depth Estimation
* OpenCV
* AI summarization models

### Storage & Processing

* File handling system
* Image preprocessing pipeline
* PDF rendering pipeline

---

## Workflow

1. User uploads an text extractable PDF
2. Backend processes the file
3. AI generates depth information and summary
4. System creates a 3D AR card
5. Card is stored and linked to the original file
6. Mobile app detects specialized object using yolo and visualizes the card in AR
7. Users can interact with the card and download the original document
8. Geofencing technique to allow only specified areas

---

## AR Experience

The generated AR cards can be placed and viewed in real-world environments using mobile devices. Users can:

* Read AI-generated summaries
* 3D visualizations
* Download original files directly from AR

---


## Project Goal

The goal of this project is to bridge Artificial Intelligence and Augmented Reality to create smarter and more interactive ways of visualizing digital content in physical space.
This project is currently built on Educational content delivery for users to download document without the need to login to any website.

---

