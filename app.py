# import os
# import time
# import streamlit as st
# from concurrent.futures import ThreadPoolExecutor
# from compression_encryption import (
#     compress_image,
#     evaluate_compression,
#     encrypt_image,
#     embed_hash_in_metadata,
#     compare_file_sizes,
#     upload_to_s3,
# )


# def process_image(uploaded_file, password):
#     status = []
#     results = {}
#     timestamps = {}  # to store timestamps for each step
#     overall_start = time.time()  # Start the overall timer

#     # Step 1: Save the uploaded file temporarily
#     try:
#         original_file_name = uploaded_file.name
#         temp_file_path = original_file_name
#         with open(temp_file_path, "wb") as f:
#             f.write(uploaded_file.read())
#         status.append("File uploaded successfully.")
#         print(f"[INFO] File uploaded: {original_file_name}")
#     except Exception as e:
#         status.append(f"Error uploading file: {e}")
#         print(f"[ERROR] Upload failed for {original_file_name}: {e}")
#         return status, None

#     # Step 2: Compress the image
#     try:
#         start = time.time()
#         compressed_path = compress_image(temp_file_path)
#         compression_metrics = evaluate_compression(temp_file_path, compressed_path)
#         timestamps['compression_time'] = time.time() - start  # Record compression time
#         status.append("Image compressed successfully.")
#         print(f"[INFO] Image compressed: {compressed_path}")
#     except Exception as e:
#         status.append(f"Error compressing image: {e}")
#         print(f"[ERROR] Compression failed for {original_file_name}: {e}")
#         return status, None

#     # Step 3: Encrypt the image
#     try:
#         start = time.time()
#         encrypted_path, image_hash = encrypt_image(compressed_path, password)
#         timestamps['encryption_time'] = time.time() - start  # Record encryption time
#         status.append("Image encrypted successfully.")
#         print(f"[INFO] Image encrypted: {encrypted_path}")
#     except Exception as e:
#         status.append(f"Error encrypting image: {e}")
#         print(f"[ERROR] Encryption failed for {original_file_name}: {e}")
#         return status, None

#     # Step 4: Embed metadata in the image
#     try:
#         start = time.time()
#         compression_settings = {"jpeg_quality": 90, "png_compression_level": 9}
#         metadata_path = embed_hash_in_metadata(compressed_path, image_hash, compression_settings)
#         size_comparison = compare_file_sizes(temp_file_path, metadata_path)
#         timestamps['metadata_embedding_time'] = time.time() - start  # Record metadata embedding time
#         status.append("Metadata embedded successfully.")
#         print(f"[INFO] Metadata embedded: {metadata_path}")
#     except Exception as e:
#         status.append(f"Error embedding metadata: {e}")
#         print(f"[ERROR] Metadata embedding failed for {original_file_name}: {e}")
#         return status, None

#     # Step 5: Upload compressed and metadata-embedded images to S3
#     try:
#         compressed_s3_url = upload_to_s3(compressed_path, "my-encrypted-images-bucket", f"compressed_{original_file_name}")
#         metadata_s3_url = upload_to_s3(metadata_path, "my-encrypted-images-bucket", f"metadata_{original_file_name}")
#         status.append("Images uploaded to S3 successfully.")
#         print(f"[INFO] Images uploaded to S3 for {original_file_name}.")
#     except Exception as e:
#         status.append(f"Error uploading to S3: {e}")
#         print(f"[ERROR] S3 upload failed for {original_file_name}: {e}")
#         return status, None

#     results.update({
#         "file_name": original_file_name,
#         "compression_metrics": compression_metrics,
#         "size_comparison": size_comparison,
#         "compressed_s3_url": compressed_s3_url,
#         "metadata_s3_url": metadata_s3_url
#     })

#     # Clean up temporary files
#     try:
#         os.remove(temp_file_path)
#         status.append("Temporary files cleaned up successfully.")
#         print(f"[INFO] Temporary files cleaned up for {original_file_name}.")
#     except Exception as e:
#         status.append(f"Error cleaning up temporary files: {e}")
#         print(f"[ERROR] Cleanup failed for {original_file_name}: {e}")

#     # Record overall time taken
#     timestamps['overall_time'] = time.time() - overall_start

#     # Print detailed results in the terminal
#     print("\n### Processing Results ###")
#     print(f"File Name: {results['file_name']}")
#     print("Compression Metrics:")
#     print(results["compression_metrics"])
#     print("Size Comparison:")
#     print(results["size_comparison"])
#     print(f"Compressed Image S3 URL: {results['compressed_s3_url']}")
#     print(f"Metadata-Embedded Image S3 URL: {results['metadata_s3_url']}")
#     print("Timestamps:")
#     print(f"Compression Time: {timestamps['compression_time']:.2f} seconds")
#     print(f"Encryption Time: {timestamps['encryption_time']:.2f} seconds")
#     print(f"Metadata Embedding Time: {timestamps['metadata_embedding_time']:.2f} seconds")
#     print(f"Overall Time: {timestamps['overall_time']:.2f} seconds")
#     print("#########################\n")

#     results['timestamps'] = timestamps  # Include timestamps in results
#     return status, results



# # Streamlit UI
# st.title("Batch Image Processing Workflow with Detailed Status Updates")

# uploaded_files = st.file_uploader("Upload Images (Max: 5)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
# password = st.text_input("Enter a password for encryption", type="password")

# if st.button("Submit"):
#     if not uploaded_files or not password:
#         st.error("Please upload at least one image and enter a password.")
#     elif len(uploaded_files) > 5:
#         st.error("You can upload a maximum of 5 images at a time.")
#     else:
#         with ThreadPoolExecutor() as executor:
#             for uploaded_file in uploaded_files:
#                 st.write(f"### Processing `{uploaded_file.name}`")
#                 status_placeholder = st.empty()  # Placeholder for updating status dynamically

#                 # Process the file and get status updates
#                 status_updates, results = process_image(uploaded_file, password)

#                 # Display each status update dynamically
#                 for update in status_updates:
#                     status_placeholder.write(update)
#                     st.write(f"✔ {update}")  # Show success messages dynamically
                
#                 # Optionally, show a success message for overall completion
#                 if results:
#                     st.success(f"Processing complete for `{uploaded_file.name}`.")


import os
import time
import boto3
import pandas as pd
import streamlit as st  # Import Streamlit for the UI
from concurrent.futures import ThreadPoolExecutor
from compression_encryption import (
    compress_image,
    evaluate_compression,
    embed_hash_in_metadata,
    compare_file_sizes,
    upload_to_s3,
)

BUCKET_NAME_SOURCE = "source-images-bucket-folder"
BUCKET_NAME_PROCESSED = "processed-images-bucket-folder"

# Process the image
def process_image(uploaded_file, password):
    status = []
    results = {}
    timestamps = {}  # To store timestamps for each step
    overall_start = time.time()  # Start the overall timer

    # Step 1: Save the uploaded file temporarily
    try:
        start = time.time()
        original_file_name = uploaded_file.name
        temp_file_path = original_file_name
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.read())
        timestamps["file_upload_time"] = time.time() - start
        status.append("File uploaded successfully.")
        print(f"[INFO] File uploaded: {original_file_name}")
    except Exception as e:
        status.append(f"Error uploading file: {e}")
        print(f"[ERROR] Upload failed for {original_file_name}: {e}")
        return status, None

    # Step 2: Compress the image
    try:
        start = time.time()
        compressed_path = compress_image(temp_file_path)
        compression_metrics = evaluate_compression(temp_file_path, compressed_path)
        timestamps["compression_time"] = time.time() - start
        status.append("Image compressed successfully.")
        print(f"[INFO] Image compressed: {compressed_path}")
    except Exception as e:
        status.append(f"Error compressing image: {e}")
        print(f"[ERROR] Compression failed for {original_file_name}: {e}")
        return status, None

    # Step 3: Upload the compressed file to the source S3 bucket with password in metadata
    try:
        start = time.time()
        s3_client = boto3.client('s3')

        compressed_s3_key = f"compressed/{os.path.basename(compressed_path)}"
        metadata = {
            "encryption-password": password,
            "original-file-name": original_file_name,
            "processing-time": f"{time.time() - overall_start:.2f}s",
        }  # Embed user-provided password and additional metadata

        # Upload file with metadata
        s3_client.upload_file(
            compressed_path,
            BUCKET_NAME_SOURCE,
            compressed_s3_key,
            ExtraArgs={"Metadata": metadata}
        )
        timestamps["upload_to_s3_time"] = time.time() - start
        status.append("Compressed file uploaded to source S3 bucket. Encryption Lambda triggered.")
        print(f"[INFO] Compressed file uploaded: {compressed_s3_key}")
    except Exception as e:
        status.append(f"Error uploading compressed image to S3: {e}")
        print(f"[ERROR] S3 upload failed for {original_file_name}: {e}")
        return status, None

    # Step 4: Wait for encrypted file (Optional polling step)
    try:
        start = time.time()
        encrypted_s3_key = f"encrypted/{os.path.splitext(os.path.basename(compressed_path))[0]}.enc"
        encrypted_file_url = f"s3://{BUCKET_NAME_PROCESSED}/{encrypted_s3_key}"

        # Optional: Poll for the file
        if wait_for_encrypted_file(BUCKET_NAME_PROCESSED, encrypted_s3_key):
            timestamps["encryption_time"] = time.time() - start
            status.append(f"Encrypted file ready: {encrypted_file_url}")
            print(f"[INFO] Encrypted file available at: {encrypted_file_url}")
        else:
            raise Exception("Timed out waiting for encrypted file.")
    except Exception as e:
        status.append(f"Error waiting for encrypted file: {e}")
        print(f"[ERROR] Polling failed for encrypted file: {e}")
        return status, None

    # Step 5: File size comparison
    try:
        size_comparison = compare_file_sizes(temp_file_path, compressed_path)
        encryption_overhead = (
            os.path.getsize(compressed_path) - os.path.getsize(temp_file_path)
        ) / os.path.getsize(temp_file_path) * 100
        timestamps["file_size_comparison_time"] = time.time() - start
        status.append("File size comparison completed.")
        print(f"[INFO] File size comparison: {size_comparison}")
    except Exception as e:
        status.append(f"Error comparing file sizes: {e}")
        print(f"[ERROR] File size comparison failed: {e}")
        return status, None

    # Step 6: Generate results and cleanup
    results.update({
        "file_name": original_file_name,
        "compression_metrics": compression_metrics,
        "size_comparison": size_comparison,
        "compressed_s3_key": f"s3://{BUCKET_NAME_SOURCE}/{compressed_s3_key}",
        "encrypted_s3_url": encrypted_file_url,
        "encryption_details": {
            "Algorithm": "Blowfish CBC",
            "Key Length": "256 bits",
            "Encryption Overhead (%)": round(encryption_overhead, 2),
        },
        "metadata_details": metadata,  # Include all metadata keys for display
        "timestamps": timestamps
    })

    try:
        os.remove(temp_file_path)
        status.append("Temporary files cleaned up successfully.")
        print(f"[INFO] Temporary files cleaned up for {original_file_name}.")
    except Exception as e:
        status.append(f"Error cleaning up temporary files: {e}")
        print(f"[ERROR] Cleanup failed for {original_file_name}: {e}")

    timestamps["overall_time"] = time.time() - overall_start
    results["timestamps"] = timestamps  # Include timestamps in results

    return status, results


# Poll for encrypted file
def wait_for_encrypted_file(bucket_name, encrypted_key, timeout=180):  # Timeout 3 minutes
    s3_client = boto3.client('s3')
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            s3_client.head_object(Bucket=bucket_name, Key=encrypted_key)
            return True  # File exists
        except s3_client.exceptions.ClientError:
            time.sleep(5)  # Wait for 5 seconds before retrying
    return False  # Timeout


# Streamlit UI
st.title("Batch Image Processing Workflow with Detailed Status Updates")

uploaded_files = st.file_uploader("Upload Images (Max: 5)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
password = st.text_input("Enter a password for encryption", type="password")

if st.button("Submit"):
    if not uploaded_files or not password:
        st.error("Please upload at least one image and enter a password.")
    elif len(uploaded_files) > 5:
        st.error("You can upload a maximum of 5 images at a time.")
    else:
        with ThreadPoolExecutor() as executor:
            for uploaded_file in uploaded_files:
                st.write(f"### Processing `{uploaded_file.name}`")
                status_placeholder = st.empty()  # Placeholder for updating status dynamically

                # Process the file and get status updates
                status_updates, results = process_image(uploaded_file, password)

                # Display each status update dynamically
                for update in status_updates:
                    status_placeholder.write(update)
                    st.write(f"✔ {update}")  # Show success messages dynamically

                # Display results
                if results:
                    st.success(f"Processing complete for `{uploaded_file.name}`.")

                    # Compression Metrics
                    compression_df = pd.DataFrame([results["compression_metrics"]])
                    st.write("### Compression Metrics:")
                    st.table(compression_df)

                    # File Size Comparison
                    size_comparison_df = pd.DataFrame([results["size_comparison"]])
                    st.write("### File Size Comparison:")
                    st.table(size_comparison_df)

                    # Encryption Details
                    encryption_df = pd.DataFrame([results["encryption_details"]])
                    st.write("### Encryption Details:")
                    st.table(encryption_df)

                    # Metadata Details (Masking the password)
                    metadata_details = results["metadata_details"].copy()
                    metadata_details["encryption-password"] = "******"  # Mask the password
                    metadata_df = pd.DataFrame([metadata_details])
                    st.write("### Metadata Details:")
                    st.table(metadata_df)

                    # Time Metrics (Transposing for better display)
                    time_metrics_df = pd.DataFrame.from_dict(results["timestamps"], orient="index", columns=["Time Taken (s)"])
                    st.write("### Time Metrics:")
                    st.table(time_metrics_df)









# import os
# import streamlit as st
# import boto3

# # AWS S3 configuration
# s3 = boto3.client('s3')
# SOURCE_BUCKET = 'source-images-bucket-folder'

# st.title("Batch Image Upload to S3 (Lambda Trigger)")

# # File uploader for images
# uploaded_files = st.file_uploader("Upload Images (Max: 5)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# if st.button("Upload to S3"):
#     if not uploaded_files:
#         st.error("Please upload at least one image.")
#     elif len(uploaded_files) > 5:
#         st.error("You can upload a maximum of 5 images at a time.")
#     else:
#         for uploaded_file in uploaded_files:
#             try:
#                 file_name = uploaded_file.name
#                 local_path = file_name

#                 # Save file locally
#                 with open(local_path, "wb") as f:
#                     f.write(uploaded_file.read())

#                 # Upload file to S3
#                 s3.upload_file(local_path, SOURCE_BUCKET, file_name)
#                 st.success(f"File `{file_name}` uploaded successfully to {SOURCE_BUCKET}.")
#                 os.remove(local_path)  # Remove local file after upload
#             except Exception as e:
#                 st.error(f"Failed to upload {file_name}: {e}")`
