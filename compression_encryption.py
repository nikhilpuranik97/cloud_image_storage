import os
import hashlib
from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import pad
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import boto3

BUCKET_NAME = "my-encrypted-images-bucket"

# Create directories if they don't exist
if not os.path.exists("compressed_images"):
    os.makedirs("compressed_images")
if not os.path.exists("metadata_images"):
    os.makedirs("metadata_images")

# Upload to S3
def upload_to_s3(file_path, bucket_name, s3_key):
    s3_client = boto3.client("s3")
    s3_client.upload_file(file_path, bucket_name, s3_key)
    return f"s3://{bucket_name}/{s3_key}"

# Evaluate Compression Performance
def evaluate_compression(original_image, compressed_image):
    """
    Evaluate compression metrics: PSNR, SSIM, and Compression Ratio.

    Parameters:
    - original_image (str): Path to the original image.
    - compressed_image (str): Path to the compressed image.

    Returns:
    - dict: Compression metrics (PSNR, SSIM, Compression Ratio).
    """
    # Read images
    original = cv2.imread(original_image)
    compressed = cv2.imread(compressed_image)

    # Ensure dimensions match
    if original.shape != compressed.shape:
        compressed = cv2.resize(compressed, (original.shape[1], original.shape[0]))

    # Compute PSNR
    psnr_value = psnr(original, compressed, data_range=255)

    # Compute SSIM
    ssim_value = ssim(
        original,
        compressed,
        multichannel=True,
        channel_axis=-1
    )

    # Compute Compression Ratio
    compression_ratio = os.path.getsize(original_image) / os.path.getsize(compressed_image)

    return {
        "PSNR": psnr_value,
        "SSIM": ssim_value,
        "Compression Ratio": compression_ratio,
    }


# Compress Image (Optimized for PNG)
def compress_image(image_path):
    # Extract file name and extension
    file_name, file_extension = os.path.splitext(os.path.basename(image_path))

    if file_extension.lower() == ".png":
        # Optimize PNG compression
        image = Image.open(image_path)
        compressed_path = os.path.join("compressed_images", f"{file_name}.compressed{file_extension}")
        image.save(compressed_path, format="PNG", optimize=True, compress_level=7)
        return compressed_path
    elif file_extension.lower() in [".jpg", ".jpeg"]:
        # Handle JPEG compression (existing logic)
        image = cv2.imread(image_path)
        compressed_path = os.path.join("compressed_images", f"{file_name}.compressed{file_extension}")
        cv2.imwrite(compressed_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        return compressed_path
    else:
        raise ValueError("Unsupported file format for compression")

# Encrypt Image
def encrypt_image(file_path, password):
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000, dklen=32)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC)
    iv = cipher.iv
    with open(file_path, 'rb') as file:
        file_data = file.read()
    padded_data = pad(file_data, Blowfish.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    encrypted_path = "encrypted_image.enc"
    with open(encrypted_path, "wb") as enc_file:
        enc_file.write(iv + encrypted_data)
    return encrypted_path, hashlib.sha256(encrypted_data).hexdigest()

# Embed Hash in Metadata
def embed_hash_in_metadata(image_path, hash_string):
    # Extract file name and extension
    file_name, file_extension = os.path.splitext(os.path.basename(image_path))

    metadata_path = os.path.join("metadata_images", f"{file_name}.metadata-embedded{file_extension}")
    try:
        image = Image.open(image_path)
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Hash", hash_string[:16])  # Truncate hash for metadata

        # Save optimized PNG with metadata
        image.save(metadata_path, format="PNG", pnginfo=metadata, optimize=True, compress_level=7)
        return metadata_path
    except Exception as e:
        print(f"Error embedding hash in metadata for {image_path}: {e}")
        return None

# Compare File Sizes
def compare_file_sizes(original_path, metadata_path):
    original_size = os.path.getsize(original_path)
    metadata_size = os.path.getsize(metadata_path)
    size_difference = metadata_size - original_size
    percentage_difference = (size_difference / original_size) * 100
    return {
        "Original Size": original_size,
        "Metadata Size": metadata_size,
        "Difference (Bytes)": size_difference,
        "Difference (%)": percentage_difference
    }
