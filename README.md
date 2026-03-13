# BlindDistance

BlindDistance is an assistive technology application powered by computer vision, specifically designed to help visually impaired individuals navigate their surroundings safely. It leverages an Orbbec Astra 3D camera to scan the environment in real-time, detecting obstacles, measuring their distances, and identifying potential hazards (like stairs or sudden drops) to provide audible feedback.

## Key Features
* **Real-time Obstacle Detection:** Uses the `ultralytics` YOLOv8 model for detecting objects in the frame.
* **Spatial Depth Mapping:** Uses `openni` to interface with the Astra Camera's depth sensor stream, turning pixel coordinates into physical distances (in millimeters).
* **Audible Warnings:** Uses `pyttsx3` and `pygame` to provide spoken warnings based on distance thresholds or specific threat types, ensuring a hands-free non-visual experience.
* **Floor Drop / Stair Detection:** Uses a moving exponential average of the floor's physical depth to determine if the ground suddenly drops off deeply ahead.
* **Dataset Recording:** Allows recording annotated depth and color frames locally for training or tuning models.

## Architecture & Components
* **`main.py`**: The main entry point integrating camera handling, AI detection, and the audio alert system in a central event loop. 
* **`utils/`**: Helper modules (if applicable) for configuring text-to-speech, camera hardware settings, or mathematical geometry handling.
* **`dataset/`**: Used for storing generated `.csv` mapping and annotated images whenever the recording mode is turned on.
* **`OpenNI2/`**: The necessary directory containing the camera drivers required to interface with the Orbbec equipment.

## Installation Requirements
Requires **Python 3.12 (64-bit)** and the **Microsoft Visual C++ 2013 Redistributable (x64)** for legacy OpenNI components.

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install the prerequisites:
   ```bash
   pip install -r requirements.txt
   ```
   
## Usage
* Plug in the Orbbec Astra Camera via USB.
* Ensure the Orbbec sensor drivers are installed on the OS.
* Run the project:
   ```bash
   python main.py
   ```
* **Controls:**
  * `r`: Toggle data recording mode.
  * `1-5`: Assign specific label classes to the recorded data.
  * `q`: Quit the application gracefully.

## Troubleshooting
If you encounter `DeviceOpen using default: no devices found`, check that the camera translates correctly in Device Manager and is not simultaneously requested by another program (like the Orbbec Viewer).
