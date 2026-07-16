import os
from django.core.exceptions import ValidationError

# Custom validator for file size
# def validate_file_size(file, size_limit=2*1024*1024):  # Default size limit to 5MB
#     if file.size > size_limit:
#         raise ValidationError(f"File size exceeds the {size_limit // (1024 * 1024)}MB limit.")

# Custom validator for file format (allowing only certain extensions)
def validate_file_format(file, allowed_formats=['.pdf']):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_formats:
        raise ValidationError(f"Invalid file format. Only {', '.join(allowed_formats)} are allowed.")
    


# Custom validator for file size
def validate_file_size(file, size_limit=2*1024*1024):  # Default size limit to 2MB
    if file.size > size_limit:
        size_in_mb = size_limit // (1024 * 1024)  # Convert size limit to MB
        raise ValidationError(f"File size exceeds the {size_in_mb}MB limit. The uploaded file is {file.size / (1024 * 1024):.2f}MB.")

# Custom validator for file format (allowing only certain extensions)
def validate_file_format_faculty(file, allowed_formats=['.pdf', '.jpg', '.jpeg']):
    # Get the file extension and convert to lowercase for comparison
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_formats:
        raise ValidationError(f"Invalid file format. Only {', '.join(allowed_formats)} are allowed. Your file has a {ext} extension.")
