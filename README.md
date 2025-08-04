# OCR-Based-Number-Plate-Recognition-System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

This project is an intelligent system that uses Artificial Intelligence to automatically identify vehicles by reading their license plates from images. It demonstrates a complete pipeline from visual detection to data management, all controlled through a user-friendly graphical interface.

![pic2](https://github.com/user-attachments/assets/5e3adb1a-0a37-4727-906c-2cef94566ebe)


## How It Works: The AI Pipeline

The system uses a two-stage computer vision process to achieve automated recognition:

1.  **License Plate Detection:** A custom-trained **YOLOv8 model**, a state-of-the-art object detection algorithm, scans the input image to precisely locate the vehicle's license plate.

2.  **Optical Character Recognition (OCR):** The detected plate region is then passed to an **EasyOCR** model. This powerful recognition engine analyzes the image of the plate and converts the characters and numbers into digital text.

The extracted plate number can then be used for logging, verification, or other data-driven actions within the application.

## Key Features

-   **Automated License Plate Recognition (ALPR):** Uses AI to read license plates directly from image files.
-   **AI-Powered Detection:** Leverages a custom-trained YOLOv8 model for high-accuracy detection.
-   **Intuitive GUI:** A clean interface built with Tkinter allows for easy interaction and data management.
-   **Data Logging:** Keeps a record of all recognized plates and their associated information.
-   **Vehicle Database Management:** Allows users to maintain a database of vehicle information.

## Technology Stack

-   **Language:** Python
-   **GUI:** Tkinter
-   **Object Detection:** Ultralytics YOLOv8
-   **Optical Character Recognition:** EasyOCR
-   **Image Processing:** OpenCV

## Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/fahadtariq1999/OCR-Based-Number-Plate-Recognition-System.git
cd OCR-Based-Number-Plate-Recognition-System
