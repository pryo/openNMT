from google.cloud import storage


bucket_name='learnable-proj-model'
# client = storage.Client()
# bucket = client.get_bucket(config.MODEL_BUCKET)
# blob = bucket.blob(config.)
def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print('Blob {} downloaded to {}.'.format(
        source_blob_name,
        destination_file_name))
download_blob(bucket_name,'averaged-10-epoch.pt','averaged-10-epoch.pt')