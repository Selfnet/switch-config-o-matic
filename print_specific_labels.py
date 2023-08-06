import labelprinter.draw
import labelprinter.printer
import config
import os
import time


def main():
    switch_names = [
        f.split(".")[0]
        for f in os.listdir(config.switch_config_dir)
        if f.endswith(".cfg")
    ]
    switches_to_print = [n for n in switch_names if False]  # Some condition

    for name in switches_to_print:
        small_label = labelprinter.draw.render_small_label(name)
        labelprinter.printer.print_to_ip(small_label, config.labelprinter_hostname)
        time.sleep(5)

        large_label = labelprinter.draw.render_text(name, None, None, True)
        labelprinter.printer.print_to_ip(large_label, config.labelprinter_hostname)
        time.sleep(5)


if __name__ == "__main__":
    main()
