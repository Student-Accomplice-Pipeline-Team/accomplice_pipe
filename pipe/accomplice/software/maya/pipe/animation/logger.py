import time
class SimpleLogger():
    def __init__(self, main_prefix="SimpleLogger") -> None:
        self.log = ""
        self.print_errors = True
        self.print_info = True
        self.include_timestamps = True
        self.main_prefix = main_prefix

    def add_message(self, prefix, message, should_print):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S") if self.include_timestamps else ""
        new_message = f"{self.main_prefix}: \t {prefix} {message} {timestamp}\n"
        self.log += new_message
        if should_print:
            print(new_message)

    def error(self, message):
        self.add_message("ERROR:", message, self.print_errors)

    def info(self, message):
        self.add_message("INFO:", message, self.print_info)

    def get_log(self):
        return self.log