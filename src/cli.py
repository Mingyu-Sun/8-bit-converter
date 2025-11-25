import cmd
import os
import shlex
import soundfile as sf

from core import *

""" ==================== Helper ==================== """
def validate_input_file(filename):
    """
    Validates the input file format, then checks for the filename in two locations:
    1. current_dir/input/filename
    2. current_dir/filename
    """
    file_extension = os.path.splitext(filename)[1]

    if file_extension not in [".wav", ".mp3", ".flac"]:
        return -1

    cwd = os.getcwd()

    priority_dir = os.path.join(cwd, 'input')
    path1 = os.path.join(priority_dir, filename)
    if os.path.exists(path1):
        return path1

    path2 = os.path.join(cwd, filename)
    if os.path.exists(path2):
        return path2

    return None

def bordered(text):
    """ Adds borders to text """
    lines = text.splitlines()
    width = max(len(s) for s in lines)
    res = ['┌' + '─' * width + '┐']
    for s in lines:
        res.append('│' + (s + ' ' * width)[:width] + '│')
    res.append('└' + '─' * width + '┘')
    return '\n'.join(res)


class ConverterCLI(cmd.Cmd):
    intro = (' 8-bit Converter '.center(60, '=') + '\n' +
             'Welcome to the 8-bit Converter CLI!' + '\n'
             'Type "help" or "?" to list commands. Type "exit" to leave.')
    prompt = ">> "

    VALID_FORMATS = ["wav", "mp3", "flac"]
    VALID_SAMPLE_RATE = ["44100", "22050", "48000"]

    def do_convert(self, arg):
        """
        Syntax: convert <input_path> [output_format] [output_sample_rate]

        Converts an audio file to an 8-bit style audio.
        - input_path (Required): The file to convert. Use quotes if it has spaces.
        - output_format (Optional): The format of the output file. Defaults to 'wav'.
        - output_sample_rate (Optional): The sample rate of the output file. Defaults to 44100.
        """
        args = shlex.split(arg)

        if len(args) < 1:
            print('Error: Missing required argument "input_path".')
            print("Usage: convert <input_path> [output_format] [output_sample_rate]")
            return

        input_path = validate_input_file(args[0])
        if input_path == -1:
            print(f"Error: 'File format {os.path.splitext(args[0])[1]}' is not supported\n"
                  f"Available choices: {', '.join(self.VALID_FORMATS)}")
            return
        if input_path is None:
            print(f"Error: File '{args[0]}' not found in 'input/' or current directory.")
            return

        output_format = args[1].lower() if len(args) >= 2 else "wav"

        output_sample_rate = args[2] if len(args) >= 3 else "44100"

        if output_format not in self.VALID_FORMATS:
            print(f"Error: '{output_format}' is not supported.\n"
                  f"Available choices: {', '.join(self.VALID_FORMATS)}")
            return

        if output_sample_rate not in self.VALID_SAMPLE_RATE:
            print(f"Error: '{output_sample_rate}' is not supported.\n"
                  f"Available choices: {', '.join(self.VALID_SAMPLE_RATE)}")
            return

        print(f">>> Processing file: '{input_path}'\n")

        events = to_events(input_path)
        sorted_events, runtime, num_of_operation = ds_comparison(events)

        print(bordered(" Data Structure Comparison ".center(58, '=') + '\n' +
              f"Number of Audio Events: {len(sorted_events)}".center(58) + '\n' +
              " list.sort() (Python built-in method) ".center(58, '-') + '\n' +
              f"Runtime: {runtime[0] * 1000:.2f} ms".center(58) + '\n' +
              " Self-implemented Priority Queue (Min-Heap) ".center(58, '-') + '\n' +
              f"Runtime: {runtime[1] * 1000:.2f} ms".center(58) + '\n' +
              f"# comparisons: {num_of_operation[0]}".center(58) + '\n' +
              f"# swaps: {num_of_operation[1]}".center(58) + '\n' +
              " Self-implemented Red-Black Tree ".center(58, '-') + '\n' +
              f"Runtime: {runtime[2] * 1000:.2f} ms".center(58) + '\n' +
              f"# comparisons: {num_of_operation[2]}".center(58) + '\n' +
              f"# rotations: {num_of_operation[3]}".center(58)))

        output_data = to_8_bit(sorted_events, int(output_sample_rate))
        sf.write(f"{os.path.basename(input_path)}_8bit.{output_format}", output_data, int(output_sample_rate))
        print(f'>>> Converted "{input_path}" -> "{os.path.basename(input_path)}_8bit.{output_format}"\n')


    def complete_convert(self, text, line, begidx, endidx):
        """
        Provides tab completion for the output_format (2nd arg) and output_sample_rate (3rd arg).
        """
        parts = shlex.split(line[:begidx])

        current_arg_index = len(parts)

        if current_arg_index == 2:
            return [f for f in self.VALID_FORMATS if f.startswith(text)]

        elif current_arg_index == 3:
            return [sr for sr in self.VALID_SAMPLE_RATE if sr.startswith(text)]

        return []

    def do_exit(self, arg):
        """Exit the converter."""
        return True

    def emptyline(self):
        """ Ignore empty line """
        pass

    def default(self, line):
        """ Handle unknown command """
        print(f"Unknown command: {line}. Type 'help' for valid commands.")


def run_cli():
    """ CLI entry point """
    try:
        ConverterCLI().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")