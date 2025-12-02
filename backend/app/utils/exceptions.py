class RefreshPlusException(Exception):
    """Base exception for Refresh Plus application"""
    pass

class InsufficientPointsException(RefreshPlusException):
    """Raised when user doesn't have enough points"""
    pass

class BookingConflictException(RefreshPlusException):
    """Raised when there's a booking conflict"""
    pass

class WishlistFullException(RefreshPlusException):
    """Raised when wishlist is full"""
    pass

class ResourceNotFoundException(RefreshPlusException):
    """Raised when a resource is not found"""
    pass
