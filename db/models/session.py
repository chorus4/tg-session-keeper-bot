from sqlmodel import Field, SQLModel

class Session(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  session_string: str | None
  user: int | None = Field(default=None, foreign_key="user.id")
  number: int