# SQLAlchemyのベースクラスを定義するファイル
from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative

# SQLAlchemyのベースクラスを定義するためのモジュール
# このクラスは、SQLAlchemyのモデルクラスの基底クラスとして使用される
@as_declarative()
class Base:
    id: Any
    __name__: str

    # SQLAlchemyのモデルクラスで使用されるテーブル名を自動的に生成する
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()