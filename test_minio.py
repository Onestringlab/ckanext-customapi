# import boto3
# from botocore.client import Config

# # Konfigurasi kredensial
# minio_url = "https://minio-console.tech-dev.id"
# access_key = "Z0ipL40JwxLGZFGbMa9r"
# secret_key = "yVXacQHzmkv0gillaqBlAE3xjymLVYA5qdJsKmkd"

# # Membuat klien boto3
# s3_client = boto3.client(
#     's3',
#     endpoint_url=minio_url,  # URL MinIO Anda
#     aws_access_key_id=access_key,  # Access key MinIO Anda
#     aws_secret_access_key=secret_key,  # Secret key MinIO Anda
#     config=Config(signature_version='s3v4'),
#     region_name="us-east-1"  # Region default, tidak wajib untuk MinIO
# )

# # Contoh operasi: daftar bucket
# try:
#     response = s3_client.list_buckets()
#     print("Buckets yang tersedia:")
#     for bucket in response['Buckets']:
#         print(f"- {bucket['Name']}")
# except Exception as e:
#     print("Error:", e)



# from minio import Minio
# from minio.error import S3Error

# # Konfigurasi Minio
# endpoint = "minio-console.tech-dev.id"
# access_key = "ykYNAaCd5PYzP0zXFbDG"
# secret_key = "zPhRrK5UbuYJHEakxhGp8T90au7nOFWwWnPk8e4w"

# # Inisialisasi klien Minio
# client = Minio(
#     endpoint,
#     access_key=access_key,
#     secret_key=secret_key,
#     secure=False  # True jika menggunakan HTTPS
# )

# # Tes koneksi ke Minio
# try:
#     # Daftar bucket
#     print("Daftar bucket yang tersedia:")
#     buckets = client.list_buckets()
#     if not buckets:
#         print("Tidak ada bucket yang tersedia.")
#     else:
#         for bucket in buckets:
#             print(f" - {bucket.name}")

#     # Tes akses ke bucket tertentu
#     bucket_name = "sdi"
#     print(f"\nMenguji akses ke bucket '{bucket_name}'...")
#     if client.bucket_exists(bucket_name):
#         print(f"Bucket '{bucket_name}' tersedia.")
#         # Menampilkan daftar objek di bucket
#         objects = client.list_objects(bucket_name)
#         print(f"Daftar objek di bucket '{bucket_name}':")
#         has_objects = False
#         for obj in objects:
#             print(f" - {obj.object_name}")
#             has_objects = True
#         if not has_objects:
#             print(f"Bucket '{bucket_name}' kosong.")
#     else:
#         print(f"Bucket '{bucket_name}' tidak ditemukan.")

# except S3Error as e:
#     print(f"Error saat mengakses Minio: {e}")
# except Exception as e:
#     print(f"Unexpected Error: {str(e)}")


import boto3
from botocore.exceptions import ClientError

# Konfigurasi koneksi MinIO
minio_url = "https://minio.tech-dev.id"  # Gunakan domain tanpa port
access_key = "Z0ipL40JwxLGZFGbMa9r"
secret_key = "yVXacQHzmkv0gillaqBlAE3xjymLVYA5qdJsKmk"

# Membuat klien boto3
s3_client = boto3.client(
    's3',
    endpoint_url=minio_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

# Uji koneksi dengan operasi sederhana
try:
    s3_client.list_buckets()
    print("Koneksi berhasil!")
except ClientError as e:
    print("Error:", e)
