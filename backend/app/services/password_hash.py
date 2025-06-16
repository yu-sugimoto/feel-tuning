from app.models import User
from passlib.context import CryptContext
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
def verify_password(plain_password, hashed_password):
    """パスワードの検証を行う関数。

    Args:
        plain_password (str): ユーザーが入力した平文のパスワード。
        hashed_password (str): データベースに保存されているハッシュ化されたパスワード。
    Returns:
        bool: パスワードが一致する場合はTrue、一致しない場合はFalse。
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """パスワードをハッシュ化する関数。
    
    Args:
        password (str): ユーザーが入力した平文のパスワード。
    Returns:
        str: ハッシュ化されたパスワード。
    """
    return pwd_context.hash(password)
 
def authenticate_user(db, email: str, password: str):
    """ユーザー認証を行う関数。
    
    Args:
        db (Session): データベースセッション。
        email (str): ユーザーのメールアドレス。
        password (str): ユーザーが入力したパスワード。
    Returns:
        User | bool: 認証に成功した場合はUserオブジェクト、失敗した場合はFalse。
    """
    print(f"入力されたemail: {email}")
    print(f"入力されたpassword: {password}")
    user = db.query(User).filter(User.email == email).first()
    print(f"ユーザーが見つかりました: {user.email}")
    print(f"DBに保存されているハッシュ: {user.hashed_password}")
    print(pwd_context.hash("test"))
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user