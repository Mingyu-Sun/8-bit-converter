# 8-bit Converter
Convert a given audio file into an 8-bit-style rendition. 

### Key features
- I/O: Import audio files and export results with a preview.
- Data manipulation: Pitch-extraction, filtering, quantization, and resynthesis.
- UI/UX: Provide a clean and intuitive user interface both in CLI and GUI.
- Data Structures used for performance comparison.

## Requirements

**Python Version:** This project requires Python version 3.10 or 3.11. 
It is not compatible with Python 3.12 or newer due to a dependency constraint.

## Usage

This application provides both a Command-Line Interface (CLI) and a Graphical User Interface (GUI).

If you wish to modify the source code, follow these steps to set up a reproducible development environment.

1. Ensure Correct Python Installation: Before proceeding, verify you are using a compatible Python version 
(3.10 ≤ Python ≤ 3.11).

2. Clone the repository and navigate into the directory:
    ```shell
    git clone https://github.com/Mingyu-Sun/8-bit-converter.git
    cd 8-bit-converter
    ```
3. Set up Virtual Environment: Create and activate a dedicated virtual environment using the compatible Python executable.
    ```shell
    # Create environment (Use the specific path if needed):
    python3.10 -m venv .venv
    # Activate environment (macOS/Linux):
    source .venv/bin/activate
    # Activate environment (Windows Command Prompt):
    .venv\Scripts\activate
    ```
4. Install all dependencies from the locked file:
    ```shell
    pip install -r requirements.txt
    ```
5. Install the project in editable mode (`-e`) so changes to the source code are reflected immediately.
    ```shell
    pip install -e .
    ``` 
6. Invocation (Development Mode)

    With the virtual environment active, you can invoke the entry points from anywhere:

   **GUI:** 
    ```shell
    8_bit_GUI
    ```
   **CLI:**
    ```shell
    8_bit_CLI
    ```

## Credits
All audio data used for testing, benchmarking, and demonstration is sourced from the **[Free Music Archive (FMA)](https://freemusicarchive.org/home)**.

Please refer to the [ATTRIBUTIONS.md](ATTRIBUTIONS.md) file for a complete list of tracks, authors, and licenses.