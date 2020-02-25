import sys
import os
import argparse
import json
import struct
import requests

import PIL
import PIL.Image


def color_download(dict_input):

    filename = dict_input["source"].split("/")[-1]
    if os.path.exists(filename) is not True:
        o_req = requests.get(dict_input["source"], stream=True)

        with open(filename, "wb") as f:
            f.write(o_req.raw.read())

    return PIL.Image.open(filename)


def color_sampling(dict_input):

    o_image = color_download(dict_input)

    color_number = 0
    list_color = []
    for row in range(dict_input["row_count"]):
        y = dict_input["row_size"] * row
        y += dict_input["adjust_y"]

        for col in range(dict_input["col_count"]):
            x = dict_input["col_size"] * col
            x += dict_input["adjust_x"]

            col_r, col_g, col_b = o_image.getpixel((x, y))[0:3]
            dict_color = {
                "name": dict_input["color_name"][len(list_color)],
                "pixel": [x, y],
                "idx": len(list_color),
                "color": [col_r, col_g, col_b, 0xFF]
            }
            list_color.append(dict_color)
            if len(list_color) == len(dict_input["color_name"]):
                break

    with open(dict_input["name"], "w") as f:
        json.dump({"colors": list_color}, f)

    return list_color


def main():

    o_parser = argparse.ArgumentParser()
    o_parser.add_argument("-i",
                          "--input",
                          help="Input json filename",
                          required=True)
    o_parser.add_argument("-o", "--output", help="Output json filename")

    args = o_parser.parse_args()

    with open(args.input, "r") as f:
        dict_input = json.load(f)

    list_color = color_sampling(dict_input)

    with open(dict_input["dist"], "wb") as h:
        h.write("AR2 COLOR PRESET\r\n".encode("utf-16-le"))
        h.write(struct.pack("HH", 0x308F, 0xFF00))

        color_count = len(list_color)
        color_data = b""
        color_code = "ARSwatchFileVersion-3".encode("utf-16-le")
        color_code += struct.pack("H", 0x00)
        color_name = b""

        for r in list_color:
            color_data += struct.pack("4B", r["color"][2], r["color"][1],
                                      r["color"][0], r["color"][3])
            color_name += r["name"].encode("utf-16-le")
            color_name += struct.pack("H", 0x00)

        data_size = len(color_data) + len(color_code) + len(color_name)

        h.write(struct.pack("III", data_size, 0x00000000, color_count))
        h.write(color_data)
        h.write(color_code)
        h.write(color_name)


if __name__ == "__main__":
    main()
