from app.extensions import db
from app.models.base import BaseModel, UUIDMixin

class Role(UUIDMixin, BaseModel):
    __tablename__ = 'roles'
    
    role_name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )
    
    users = db.relationship(
        'User', 
        back_populates='role', 
        lazy='selectin'
    )
    
    def __repr__(self):
        return (
            f"<Role {self.role_name}>"
        )