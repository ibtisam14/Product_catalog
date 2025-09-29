from rest_framework.response import Response

def custom_response(status_code, message, data=None, errors=None):
    return Response({
        "status_code": status_code,
        "message": message,
        "data": data,
        "errors": errors
    }, status=status_code)
