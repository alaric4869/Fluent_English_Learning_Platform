from fastapi import Depends
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.database import get_db


def get_frontend_services(
    session: Session = Depends(get_db),
) -> ApplicationServices:
    return build_application_services(session)
