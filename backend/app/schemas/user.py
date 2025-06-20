from pydantic import BaseModel
from pydantic import EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    # nickname: str | None = None  # サインアップ時にニックネームをオプションとする

class UserRead(UserBase):
    id: int
    # nickname: str | None = None  # ニックネームを使用する場合にはコメントアウトを外す

    model_config = {
        "from_attributes": True
    }