"""Password strength validation utilities."""
import re
from typing import Tuple


class PasswordValidator:
    """Validate password strength and security."""
    
    MIN_LENGTH = 12
    MIN_UPPERCASE = 1
    MIN_LOWERCASE = 1
    MIN_DIGITS = 1
    MIN_SPECIAL = 1
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters"
        
        if len(re.findall(r'[A-Z]', password)) < PasswordValidator.MIN_UPPERCASE:
            return False, "Password must contain at least 1 uppercase letter"
        
        if len(re.findall(r'[a-z]', password)) < PasswordValidator.MIN_LOWERCASE:
            return False, "Password must contain at least 1 lowercase letter"
        
        if len(re.findall(r'\d', password)) < PasswordValidator.MIN_DIGITS:
            return False, "Password must contain at least 1 digit"
        
        if len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', password)) < PasswordValidator.MIN_SPECIAL:
            return False, "Password must contain at least 1 special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def get_strength(password: str) -> str:
        """Get password strength level."""
        if not password:
            return "None"
        
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        if score <= 2:
            return "Weak"
        elif score <= 4:
            return "Medium"
        elif score <= 6:
            return "Strong"
        else:
            return "Very Strong"
