import cmd
import os
import sys
import shlex
import soundfile as sf

from core import *


class ConverterCLI(cmd.Cmd):
    intro = ('--------------------- 8-bit Converter ---------------------\n'
             'Welcome to the 8-bit Converter CLI!\n'
             'Type "help" or "?" to list commands. Type "exit" to leave.')
    prompt = ">> "

    VALID_FORMATS = ["wav", "mp3", "flac"]
    VALID_SAMPLE_RATE = ["44100", "22050", "48000"]

    def do_convert(self, arg):
        """
        Syntax: convert <input_path> [output_format] [output_sample_rate]

        Converts a file.
        - input_path (Required): The file to convert. Use quotes if it has spaces.
        - output_format (Optional): The format of the output file. Defaults to 'wav'.
        - output_sample_rate (Optional): The sample rate of the output file. Defaults to 44100.
        """
        args = shlex.split(arg)

        if len(args) < 1:
            print('Error: Missing required argument "input_path".')
            print("Usage: convert <input_path> [output_format] [output_sample_rate]")
            return

        input_path = args[0]

        output_format = args[1].lower() if len(args) >= 2 else "wav"

        output_sample_rate = args[2] if len(args) >= 3 else "44100"

        if output_format not in self.VALID_FORMATS:
            print(f"Error: '{output_format}' is not supported.")
            print(f"Available choices: {', '.join(self.VALID_FORMATS)}")
            return

        if output_sample_rate not in self.VALID_SAMPLE_RATE:
            print(f"Error: '{output_sample_rate}' is not supported.")
            print(f"Available choices: {', '.join(self.VALID_SAMPLE_RATE)}")
            return

        print(f">>> Processing file: '{input_path}'\n")

        try:
            events = to_events(input_path)
            sorted_events, runtime, num_of_operation = ds_comparison(events)

            print("================ Data Structure Comparison ================\n"
                  "++++++++++ list.sort() (Python built-in method) ++++++++++\n"
                  f"Runtime: {runtime[0] * 1000:.2f} ms\n"
                  "+++++++ Self-implemented Priority Queue (Min-Heap) +++++++\n"
                  f"Runtime: {runtime[1] * 1000:.2f} ms\n"
                  f"# comparisons: {num_of_operation[0]}\n"
                  f"# swaps: {num_of_operation[1]}\n"
                  "++++++++++++ Self-implemented Red-Black Tree +++++++++++++\n"
                  f"Runtime: {runtime[2] * 1000:.2f} ms\n"
                  f"# comparisons: {num_of_operation[2]}\n"
                  f"# rotations: {num_of_operation[3]}\n")

            output_data = to_8_bit(sorted_events, int(output_sample_rate))
            sf.write(f"{os.path.basename(input_path)}_8bit.{output_format}", output_data, int(output_sample_rate))
            print(f'>>> Converted "{input_path}" -> "{os.path.basename(input_path)}_8bit.{output_format}"\n')

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)

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
        pass

    def default(self, line):
        print(f"Unknown command: {line}. Type 'help' for valid commands.")


if __name__ == "__main__":
    try:
        ConverterCLI().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")