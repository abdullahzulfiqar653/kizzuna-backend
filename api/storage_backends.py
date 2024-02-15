from storages.backends.s3boto3 import S3Boto3Storage


class PrivateMediaStorage(S3Boto3Storage):
    location = "private"
    default_acl = "private"
    file_overwrite = False
    custom_domain = False

    def _get_write_parameters(self, name, content=None):
        params = super()._get_write_parameters(name, content)
        filename = name.split("/")[-1]
        params["ContentDisposition"] = f'attachment; filename="{filename}"'
        return params
