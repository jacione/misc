import os
import imageio
from PIL import Image

# Directory containing the input images (replace with your path)
input_directory = "C:/Users/jacio/Box/Transfer/figures"

# Output GIF file name
output_gif_file = input_directory + "/output.gif"

# List to store image file names
image_files = []

# Load image files from the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".png"):
        image_files.append(os.path.join(input_directory, filename))

# Sort the image files by name (modify sorting logic as needed)
image_files.sort()

# Create a list to store image frames
frames = []

# Load and append each image to the frames list
for image_file in image_files:
    img = Image.open(image_file)
    frames.append(img)

# Save the frames as a GIF animation
imageio.help(".gif")
imageio.mimwrite(output_gif_file, frames, loop=0, duration=1000)  # Adjust duration as needed

print(f"GIF animation saved as '{output_gif_file}'.")

