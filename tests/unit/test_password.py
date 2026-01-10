"""Unit tests for password utilities."""

import pytest
import string

from app.services.password import (
    hash_password,
    verify_password,
    generate_temp_password,
)


class TestHashPassword:
    """Tests for password hashing."""

    def test_hash_password_returns_string(self):
        """Should return a string hash."""
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_hash_password_different_from_input(self):
        """Hash should be different from original password."""
        password = "mypassword"
        result = hash_password(password)
        assert result != password

    def test_hash_password_produces_unique_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        password = "mypassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_bcrypt_format(self):
        """Hash should be in bcrypt format."""
        result = hash_password("mypassword")
        assert result.startswith("$2b$")


class TestVerifyPassword:
    """Tests for password verification."""

    def test_verify_correct_password(self):
        """Should verify correct password."""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Should reject incorrect password."""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        """Should handle empty password."""
        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    def test_verify_case_sensitive(self):
        """Password verification should be case sensitive."""
        password = "CaseSensitive"
        hashed = hash_password(password)
        assert verify_password("casesensitive", hashed) is False
        assert verify_password("CASESENSITIVE", hashed) is False
        assert verify_password("CaseSensitive", hashed) is True


class TestGenerateTempPassword:
    """Tests for temporary password generation."""

    def test_generate_temp_password_default_length(self):
        """Should generate password of default length (12)."""
        password = generate_temp_password()
        assert len(password) == 12

    def test_generate_temp_password_custom_length(self):
        """Should generate password of specified length."""
        password = generate_temp_password(length=20)
        assert len(password) == 20

    def test_generate_temp_password_has_lowercase(self):
        """Should contain at least one lowercase letter."""
        password = generate_temp_password()
        assert any(c in string.ascii_lowercase for c in password)

    def test_generate_temp_password_has_uppercase(self):
        """Should contain at least one uppercase letter."""
        password = generate_temp_password()
        assert any(c in string.ascii_uppercase for c in password)

    def test_generate_temp_password_has_digit(self):
        """Should contain at least one digit."""
        password = generate_temp_password()
        assert any(c in string.digits for c in password)

    def test_generate_temp_password_has_special(self):
        """Should contain at least one special character."""
        password = generate_temp_password()
        assert any(c in "!@#$%^&*" for c in password)

    def test_generate_temp_password_unique(self):
        """Each call should generate a unique password."""
        passwords = [generate_temp_password() for _ in range(100)]
        assert len(set(passwords)) == 100
