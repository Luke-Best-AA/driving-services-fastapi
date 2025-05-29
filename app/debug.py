class Debug:
    enabled = False  # Set to True to enable debug messages
    output_stream = None  # Allows configurable output stream

    @staticmethod
    def log(message: str):
        if Debug.enabled:
            stream = Debug.output_stream or print  # Use output_stream if set, otherwise default to print
            if stream == print:
                print(f"[DEBUG] {message}")
            else:
                stream.write(f"[DEBUG] {message}\n")
