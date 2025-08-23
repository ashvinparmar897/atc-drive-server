from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserOut, ForgotPasswordRequest, ResetPasswordRequest, UserLogin, AdminCreateUser, UserUpdate
from app.schemas.token import Token
from app.crud.user import create_user, get_user, get_users, update_user, delete_user, update_user_password, is_admin, can_edit, can_view
from app.core.security import verify_password, create_access_token, get_password_hash
from app.api.deps import get_db, get_current_active_user
from app.services.email_service import email_service
from app.models.user import RoleEnum
import secrets
import datetime
from typing import List

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = get_user(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = get_user(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with default viewer role
    user.role = RoleEnum.viewer
    new_user = create_user(db, user)
    
    # Send welcome email
    try:
        email_service.send_welcome_email(new_user.email, new_user.username)
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
    
    return new_user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = get_user(db, user_data.username)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user(db, request.email)
    if not user:
        # Don't reveal if user exists or not for security
        return {"msg": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    db.commit()
    
    # Send email
    try:
        email_service.send_password_reset_email(request.email, reset_token, user.username)
        return {"msg": "Password reset link sent to your email"}
    except Exception as e:
        # Reset the token if email fails
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to send reset email")

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = get_user(db, request.email)
    if not user or user.reset_token != request.reset_token:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    if user.reset_token_expires < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")
    
    # Update password
    updated_user = update_user_password(db, user.id, request.new_password)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return {"msg": "Password reset successfully"}

# Admin endpoints
@router.post("/admin/create", response_model=UserOut)
def admin_create_user(user: AdminCreateUser, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if username or email already exists
    existing_user = get_user(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = get_user(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = create_user(db, user)
    return new_user

@router.get("/admin/users", response_model=List[UserOut])
def admin_list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.put("/admin/users/{user_id}", response_model=UserOut)
def admin_update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    updated_user = update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"msg": "User deleted successfully"} 