from .auth import UserRegistration, ChangePasswordRequest, UserIdentity
from .article import ArticleCreateUpdate, ArticlePublic
from .profile import WorkHistoryItem, ProfileSchema, ProfilePublic

# Legacy Aliases for Stage 2 Stability
BlogPostCreateUpdate = ArticleCreateUpdate
