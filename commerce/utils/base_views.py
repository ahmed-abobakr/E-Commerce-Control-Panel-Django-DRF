from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class StandardizedResponseMixin:
    def success_response(self, data=None, message="Success", status_code=status.HTTP_200_OK):
        return Response({
            "status": status_code,
            "data": data,
            "message": message
        }, status=status_code)

    def error_response(self, message="Something went wrong", status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "status": status_code,
            "data": None,
            "message": message
        }, status=status_code)
        
    def handle_exception(self, exc):
        print(f"Exception happened and Handled: {str(exc)}")
        return self.error_response(message=str(exc), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class BaseAPIView(StandardizedResponseMixin, APIView):
    """
    Extend this base class to ensure all APIViews return consistent responses.
    You can also use StandardizedResponseMixin in GenericAPIView or ViewSet directly.
    """
    pass