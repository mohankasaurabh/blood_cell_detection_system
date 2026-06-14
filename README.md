# 🩸 AI-Powered Blood Cell Detection & Parasitemia Analysis System

## Overview

The AI-Powered Blood Cell Detection & Parasitemia Analysis System is an end-to-end healthcare AI application that automatically detects, counts, and analyzes blood cells from microscopic blood smear images.

The system utilizes a custom-trained **YOLO11m object detection model** to identify:

* Red Blood Cells (RBC)
* White Blood Cells (WBC)
* Platelets
* Malaria Parasites

Beyond object detection, the project includes a complete deployment pipeline with:

* Flask Web Application
* SQLite Database
* PDF Report Generation
* CSV Export
* Cell Counting Analytics
* Parasitemia Calculation
* Detection History Management

This project demonstrates the complete lifecycle of an AI solution, from dataset preparation and model training to deployment and reporting.

---

# Project Highlights

### AI Features

✅ Blood Cell Detection

✅ Malaria Parasite Detection

✅ Automatic Cell Counting

✅ Parasitemia Percentage Calculation

✅ Confidence Analytics

✅ Annotated Detection Images

---

### Deployment Features

✅ Flask Dashboard

✅ SQLite Database

✅ PDF Report Generation

✅ CSV Export

✅ Upload & Analyze Images

✅ Detection History Tracking

✅ Dark / Light Theme Dashboard

---

# Problem Statement

Manual blood smear analysis is:

* Time-consuming
* Labor-intensive
* Susceptible to human error
* Dependent on trained pathologists

This project automates blood smear image analysis using Computer Vision and Deep Learning techniques, enabling faster and more consistent preliminary screening.

---

# Datasets Used

## 1. BCCD Dataset (Blood Cell Count and Detection)

Source:

https://github.com/Shenggan/BCCD_Dataset

Classes:

* RBC
* WBC
* Platelet

Purpose:

Blood Cell Detection

---

## 2. NIH Malaria Cell Dataset

Source:

https://lhncbc.nlm.nih.gov/LHC-downloads/

Classes:

* RBC
* Parasite

Purpose:

Malaria Parasite Detection

---

# Dataset Merging Strategy

Both datasets were converted to YOLO format and merged into a single unified dataset.

## Class Mapping

### BCCD Dataset

| Original Class | New Class ID |
| -------------- | ------------ |
| RBC            | 0            |
| WBC            | 1            |
| Platelet       | 2            |

### Malaria Dataset

| Original Class | New Class ID |
| -------------- | ------------ |
| RBC            | 0            |
| Parasite       | 3            |

### Final Unified Classes

```yaml
names:
  0: RBC
  1: WBC
  2: Platelet
  3: Parasite
```

---

# Final Dataset Structure

```text
final_dataset/

├── images
│   ├── train
│   └── val
│
├── labels
│   ├── train
│   └── val
│
└── data.yaml
```

---

# Dataset Statistics

## Object Distribution

| Class    | Instances |
| -------- | --------- |
| RBC      | 17,266    |
| WBC      | 89        |
| Platelet | 76        |
| Parasite | 419       |
| Total    | 17,850    |

---

## Image Distribution

| Split      | Images |
| ---------- | ------ |
| Train      | 1,221  |
| Validation | 315    |
| Total      | 1,536  |

---

# Model Architecture

## YOLO11m

Framework:

* Ultralytics YOLO
* PyTorch

Reasons for Choosing YOLO11m:

* Better feature extraction than YOLO11s
* Strong balance between speed and accuracy
* Improved small-object detection
* Better parasite detection performance
* Suitable for deployment

---

# Training Configuration

| Parameter       | Value           |
| --------------- | --------------- |
| Model           | YOLO11m         |
| Image Size      | 800 × 800       |
| Epochs          | 40              |
| Batch Size      | 8               |
| Optimizer       | Auto            |
| Mixed Precision | Enabled         |
| Device          | NVIDIA Tesla T4 |

---

# Data Augmentation

The following augmentations were applied during training:

* Mosaic
* MixUp
* Scaling
* Horizontal Flips
* HSV Augmentation
* Perspective Transform
* Translation

These augmentations improve model robustness and generalization.

---

# Training Pipeline

## Step 1

Download Datasets

* BCCD Dataset
* NIH Malaria Dataset

↓

## Step 2

Convert Annotations to YOLO Format

```text
x_center
y_center
width
height
```

↓

## Step 3

Remap Classes

```text
RBC       → 0
WBC       → 1
Platelet  → 2
Parasite  → 3
```

↓

## Step 4

Merge Datasets

```text
BCCD + Malaria
```

↓

## Step 5

Generate data.yaml

```yaml
path: /content/final_dataset

train: images/train
val: images/val

names:
  0: RBC
  1: WBC
  2: Platelet
  3: Parasite
```

↓

## Step 6

Train YOLO11m

```python
model.train(
    data="data.yaml",
    imgsz=800,
    epochs=40,
    batch=8
)
```

---

# Final Model Performance

## Overall Metrics

| Metric    | Value |
| --------- | ----- |
| Precision | 0.898 |
| Recall    | 0.956 |
| mAP@50    | 0.961 |
| mAP@50-95 | 0.730 |

---

## Per-Class Metrics

| Class    | Precision | Recall | mAP50 | mAP50-95 |
| -------- | --------- | ------ | ----- | -------- |
| RBC      | 0.965     | 0.983  | 0.993 | 0.831    |
| WBC      | 0.967     | 0.984  | 0.988 | 0.812    |
| Platelet | 0.852     | 0.911  | 0.946 | 0.521    |
| Parasite | 0.741     | 0.919  | 0.834 | 0.757    |

---

# Key Achievement

### Malaria Parasite Detection

| Metric    | Value |
| --------- | ----- |
| Recall    | 91.9% |
| mAP@50    | 83.4% |
| mAP@50-95 | 75.7% |

The Parasite class is the most clinically important component of this project.

A high recall score helps reduce missed parasite detections, making the system useful for AI-assisted screening workflows.

---

# System Architecture

```text
Microscopic Blood Smear Image
                │
                ▼
         YOLO11m Detection
                │
                ▼
        Blood Cell Detection
                │
                ▼
          Cell Counter
                │
                ▼
     Parasitemia Calculator
                │
                ▼
      PDF/CSV Report Engine
                │
                ▼
        SQLite Database
                │
                ▼
         Flask Dashboard
```

---

# Detection Pipeline

```text
Upload Image
      ↓
YOLO11m Detection
      ↓
Detect RBC
Detect WBC
Detect Platelets
Detect Parasites
      ↓
Count Cells
      ↓
Calculate Parasitemia
      ↓
Generate Reports
      ↓
Store Results
      ↓
Display Dashboard
```

---

# Parasitemia Calculation

Formula:

Parasitemia (%) = (Parasite Count / RBC Count) × 100

Example:

```text
RBC Count = 452
Parasite Count = 17

Parasitemia = 3.76%
```

---

# Project Structure

```text
blood_cell_detection_system/

├── app.py

├── models/
│   └── best.pt

├── database/
│   └── reports.db

├── reports/
│   ├── pdf/
│   └── csv/

├── templates/
│   ├── index.html
│   ├── result.html
│   └── reports.html

├── static/
│   ├── uploads/
│   ├── outputs/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── main.js
│   │
│   └── images/

├── utils/
│   ├── detector.py
│   ├── counter.py
│   ├── calculator.py
│   ├── reports.py
│   └── database.py

├── requirements.txt
└── README.md
```

---

# Generated Outputs

Training Outputs:

* best.pt
* last.pt
* results.png
* results.csv
* confusion_matrix.png
* confusion_matrix_normalized.png
* BoxF1_curve.png
* BoxPR_curve.png
* BoxP_curve.png
* BoxR_curve.png

Deployment Outputs:

* Annotated Images
* PDF Reports
* CSV Reports
* SQLite Records

---

# Limitations

Current dataset imbalance:

```text
RBC       : 17,266
WBC       : 89
Platelet  : 76
Parasite  : 419
```

Challenges:

* Limited platelet samples
* Limited WBC samples
* Small-object detection remains difficult
* Performance depends on image quality

---

# Future Improvements

## Dataset Expansion

Collect more:

* WBC Samples
* Platelet Samples
* Parasite Samples

## Model Improvements

Experiment with:

* YOLO11l
* YOLO11x
* RT-DETR
* Ensemble Models

## Deployment Enhancements

* Batch Image Processing
* Webcam Detection
* Docker Deployment
* Cloud Hosting
* User Authentication
* Advanced Analytics Dashboard

---

# Medical Disclaimer

This project is intended for:

* Research
* Education
* Portfolio Demonstration
* AI Learning

This system is **not intended for clinical diagnosis** and should not replace professional medical evaluation.

All final diagnostic decisions must be made by qualified healthcare professionals.

---

# Author

**Saurabh Kumar Mohanka**

B.Tech Computer Science Engineering

Specialization:

* Artificial Intelligence
* Computer Vision
* Deep Learning
* Healthcare AI

---

# License

This project is released for educational and research purposes.
