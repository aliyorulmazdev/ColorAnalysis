from PIL import Image, ImageDraw, ImageFont
from tkinter import Tk, filedialog, Label, Button, Entry
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Function definitions
def select_image():
    global input_image_path, output_text_path
    input_image_path = filedialog.askopenfilename()
    if input_image_path:
        output_text_path = input_image_path.replace(".", "_output_analysis.") + ".txt"
        update_output_label()
        update_info_label("Click 'Analyze' to process the image.")

def cmyk_to_rgb(c, m, y, k):
    r = 255 * (1 - c / 100) * (1 - k / 100)
    g = 255 * (1 - m / 100) * (1 - k / 100)
    b = 255 * (1 - y / 100) * (1 - k / 100)
    return int(r), int(g), int(b)

def generate_pdf(image_path, output_pdf_path, num_slices, cmyk_values):
    image = Image.open(image_path)
    image_width, image_height = image.size

    # Set the desired width and height for the canvas
    canvas_width_mm = 1410
    canvas_height_mm = 100
    canvas_width_points = canvas_width_mm * 2.83465  # 1 inch = 25.4 mm
    canvas_height_points = canvas_height_mm * 2.83465

    pdf_canvas = canvas.Canvas(output_pdf_path, pagesize=(canvas_width_points, canvas_height_points))
    slice_width = canvas_width_points // num_slices
    font_size = 20

    # Define color_names here
    color_names = [
        colors.CMYKColor(1.0, 0, 0, 0),  # 100% Cyan
        colors.CMYKColor(0, 1.0, 0, 0),  # 100% Magenta
        colors.CMYKColor(0, 0, 1.0, 0),  # 100% Yellow
        colors.CMYKColor(0, 0, 0, 1.0),  # 100% Black
        colors.CMYKColor(0, 0, 0, 1.0)   # 100% Black (Second instance)
    ]

    for i, values in enumerate(cmyk_values):
        x_position = i * slice_width + slice_width // 2
        y_position = canvas_height_points // 2

        # Add slices to the PDF with strokes and without fill
        pdf_canvas.setStrokeColorCMYK(1.0, 1.0, 1.0, 1.0)  # 100% CMYK
        pdf_canvas.rect(i * slice_width, 0, slice_width, canvas_height_points, fill=0)

        # Modify the text to display CMYK values below each other and aligned to the left
        text_lines = [
            f"C: {values[0]}",
            f"M: {values[1]}",
            f"Y: {values[2]}",
            f"K: {values[3]}",
            f"Hazne {i + 1}"
        ]
        for j, line in enumerate(text_lines):
            color = color_names[j]  # Set font color based on predefined values
            pdf_canvas.setFillColor(color)
            pdf_canvas.setFont("Helvetica", font_size)
            pdf_canvas.drawString(i * slice_width + 5, y_position + (j * 15), line)


    pdf_canvas.save()

def analyze_image():
    if input_image_path:
        cmyk_values = annotate_cmyk_intensity(input_image_path, output_image_path, output_text_path, num_slices)
        update_info_label("Image analysis complete. Check the output.")
        generate_pdf(input_image_path, 'output_analysis.pdf', num_slices, cmyk_values)

def annotate_cmyk_intensity(image_path, output_image_path, output_text_path, num_slices):
    image = Image.open(image_path)

    slice_width = image.width // num_slices
    slices = [image.crop((i * slice_width, 0, (i + 1) * slice_width, image.height)) for i in range(num_slices)]

    cmyk_values = []

    for i, slice_image in enumerate(slices):
        cmyk_intensity = calculate_cmyk_intensity(slice_image)
        normalized_cmyk_intensity = normalize_intensity(cmyk_intensity)
        rounded_cmyk_intensity = [round(value) for value in normalized_cmyk_intensity]

        # Adjusted x-position calculation to ensure slices cover the entire image
        annotate_on_image(image, i * slice_width + slice_width // 2, image.height // 2, rounded_cmyk_intensity, f"P {i + 1}", slice_width)

        cmyk_values.append(rounded_cmyk_intensity)

    image.save(output_image_path)

    with open(output_text_path, 'w') as text_file:
        for i, values in enumerate(cmyk_values):
            text_file.write(f"Slice {i + 1}: Cyan={values[0]}, Magenta={values[1]}, Yellow={values[2]}, Black={values[3]}\n")

    return cmyk_values
def calculate_cmyk_intensity(image):
    cmyk_intensity = [sum(channel.getdata()) / len(channel.getdata()) for channel in image.split()]
    return cmyk_intensity

def normalize_intensity(intensity):
    normalized_intensity = [(value / 255) * 100 for value in intensity]
    return normalized_intensity

def annotate_on_image(image, x, y, intensity, slice_info, slice_width):
    draw = ImageDraw.Draw(image)
    
    font_size = 1 * image.width // 100
    font = ImageFont.truetype("arial.ttf", size=font_size)
    
    text = f"C: {intensity[0]}\nM: {intensity[1]}\nY: {intensity[2]}\nK: {intensity[3]}\n\n{slice_info}"

    stroke_width = 1
    draw.rectangle([x - slice_width // 2, y - image.height // 2, x + slice_width // 2, y + image.height // 2], outline=(255, 255, 255), width=stroke_width)

    draw.text((x - slice_width // 2 + stroke_width, y - image.height // 2 + stroke_width), text, font=font, fill=(255, 255, 255))

# GUI setup
root = Tk()
root.title("CMYK Image Analyzer")
root.geometry("800x600")

# Entry fields for canvas width, canvas height, and number of slices
canvas_width_label = Label(root, text="Canvas Width (mm):")
canvas_width_label.pack()
canvas_width_entry = Entry(root)
canvas_width_entry.pack()

canvas_height_label = Label(root, text="Canvas Height (mm):")
canvas_height_label.pack()
canvas_height_entry = Entry(root)
canvas_height_entry.pack()

num_slices_label = Label(root, text="Number of Slices:")
num_slices_label.pack()
num_slices_entry = Entry(root)
num_slices_entry.pack()

input_label = Label(root, text="Select Input Image:")
input_label.pack()

select_button = Button(root, text="Select", command=select_image)
select_button.pack()

output_label = Label(root, text="Output Image: ")
output_label.pack()

info_label = Label(root, text="")
info_label.pack()

analyze_button = Button(root, text="Analyze", command=analyze_image)
analyze_button.pack()

# Set default values
input_image_path = ""
output_image_path = ""
output_text_path = "output_analysis.txt"
num_slices = 32

def select_image():
    global input_image_path, output_text_path
    input_image_path = filedialog.askopenfilename()
    if input_image_path:
        output_text_path = input_image_path.replace(".", "_output_analysis.") + ".txt"
        update_output_label()
        update_info_label("Click 'Analyze' to process the image.")

def update_output_label():
    global output_image_path, output_text_path
    output_image_path = input_image_path.replace(".", "_output.")
    output_label.config(text=f"Output Image: {output_image_path}")

def update_info_label(message):
    info_label.config(text=message)

def analyze_image():
    global input_image_path, output_text_path, num_slices

    # Retrieve values from entry fields
    canvas_width_mm = float(canvas_width_entry.get())
    canvas_height_mm = float(canvas_height_entry.get())
    num_slices = int(num_slices_entry.get())

    # Update canvas dimensions in the code
    canvas_width_points = canvas_width_mm * 2.83465
    canvas_height_points = canvas_height_mm * 2.83465

root.mainloop()
