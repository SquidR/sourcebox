from PIL import Image, ImageDraw

size = 1024

img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

power_styles = {
    512: {"color": (255, 130, 0, 125), "width": 6},    # yellow
    256: {"color": (255, 50, 0, 125), "width": 2},       # red
    128: {"color": (255, 50, 0, 125), "width": 2},       # red
    64: {"color": (255, 165, 0, 30), "width": 1},  # orange
    32: {"color": (255, 165, 0, 30), "width": 1},   # orange
}

for power in sorted(power_styles.keys()):
    style = power_styles[power]
    step = power
    for x in range(0, size, step):
        draw.line([(x, 0), (x, size)], fill=style["color"], width=style["width"])
    for y in range(0, size, step):
        draw.line([(0, y), (size, y)], fill=style["color"], width=style["width"])

border_color = power_styles[512]["color"]
border_width = power_styles[512]["width"]
draw.line([(size - 1, 0), (size - 1, size)], fill=border_color, width=border_width)  # right border
draw.line([(0, size - 1), (size, size - 1)], fill=border_color, width=border_width)  # bottom border

img.save("assets/img/grid.png")