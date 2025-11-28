# 8-bit Converter
Convert a given audio file into an 8-bit-style rendition. 

### Key features
- I/O: Import audio files and export results with a preview.
- Data manipulation: Pitch-extraction, filtering, quantization, and resynthesis.
- UI/UX: Provide a clean and intuitive user interface both in CLI and GUI.
- Data Structures used for performance comparison.

## Usage

This application provides both a Command-Line Interface (CLI) and a Graphical User Interface (GUI).

If you wish to modify the source code, contribute, or build the application from scratch, follow these steps to set up 
a reproducible development environment.

1. Clone the repository and navigate into the directory:
    ```shell
    git clone https://github.com/Mingyu-Sun/8-bit-converter.git
    cd 8-bit-converter
   ```
2. Create and activate a new virtual environment (optional, but recommended):
   ```shell
    python -m venv .venv
    # Activate the environment (Command varies by OS)
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows (Command Prompt):
    .venv\Scripts\activate
    ```
3. Install all dependencies from the locked file:
    ```shell
    pip install -r requirements.txt
    ```
4. Install the project in editable mode (`-e`) so changes to the source code are reflected immediately without re-installing.
   ```shell
    pip install -e .
    ``` 
5. Invocation (Development Mode)

    With the virtual environment active, you can invoke the entry points from anywhere:

   - GUI: 
    ```shell
   8_bit_GUI
    ```
   - CLI:
   ```shell
   8_bit_CLI
    ```

## Credits
All test are done by using music from [Free Music Archive](https://freemusicarchive.org/home).
