import pytest
from unittest.mock import MagicMock, patch
from src.services.auth_service import AuthService
from src.exceptions import UnauthorizedException
from src.models.user import User

@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def mock_token_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_user_repo, mock_token_repo):
    return AuthService(user_repository=mock_user_repo, token_repository=mock_token_repo)

def test_change_email_success(auth_service):
    # Setup
    user_id = "user123"
    current_password = "OldPassword123!"
    new_email = "new@example.com"
    
    user = MagicMock(spec=User)
    user.check_password.return_value = True
    user.token_version = 1
    
    with patch.object(auth_service, 'get_user_or_raise', return_value=user):
        # Act
        auth_service.change_email(user_id=user_id, current_password=current_password, new_email=new_email)

        # Assert
        assert user.email == new_email
        assert user.token_version == 2
        auth_service._user_repository.save.assert_called_once_with(user)

def test_change_email_invalid_password(auth_service):
    # Setup
    user_id = "user123"
    current_password = "WrongPassword"
    
    user = MagicMock(spec=User)
    user.check_password.return_value = False
    
    with patch.object(auth_service, 'get_user_or_raise', return_value=user):
        # Act & Assert
        with pytest.raises(UnauthorizedException, match="Invalid current password"):
            auth_service.change_email(user_id=user_id, current_password=current_password, new_email="new@example.com")

def test_delete_account_success(auth_service):
    # Setup
    user_id = "user123"
    current_password = "CorrectPassword123!"
    
    user = MagicMock(spec=User)
    user.id = user_id
    user.check_password.return_value = True

    with patch.object(auth_service, 'get_user_or_raise', return_value=user):
        # Act
        with patch("src.services.auth_service.dispatch_event") as mock_dispatch:
            auth_service.delete_account(user_id=user_id, current_password=current_password)
            
            # Assert
            auth_service._user_repository.delete.assert_called_once_with(user)
            mock_dispatch.assert_called()

def test_delete_account_invalid_password(auth_service):
    # Setup
    user_id = "user123"
    current_password = "WrongPassword"
    
    user = MagicMock(spec=User)
    user.check_password.return_value = False
    
    with patch.object(auth_service, 'get_user_or_raise', return_value=user):
        # Act & Assert
        with pytest.raises(UnauthorizedException, match="Invalid current password"):
            auth_service.delete_account(user_id=user_id, current_password=current_password)
