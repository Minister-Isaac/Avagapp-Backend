from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidUserRole(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "User role mismatch."
    default_code = 'error'