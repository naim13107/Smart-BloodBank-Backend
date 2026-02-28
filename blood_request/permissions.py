from rest_framework import permissions

class IsRecipientOrAdmin(permissions.BasePermission):
    """
    Allows anyone to view, but only the recipient or admin to edit/delete.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user and request.user.is_staff:
            return True
            

        return obj.recipient == request.user